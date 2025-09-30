from __future__ import annotations

import json
import socket
import threading
import time
from datetime import date
from importlib import reload
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Iterable, Optional, Union, cast

import httpx
import uvicorn
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, override_settings

from apps.notifications.models import Notification

if TYPE_CHECKING:
    from apps.users.models.user import User as DjangoUser

User = get_user_model()


def get_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return int(port)


@override_settings(
    # 반드시 ASGI로 라우팅되도록
    ASGI_APPLICATION="config.asgi.application",
    # 테스트에선 eventstream을 메모리 백엔드로
    EVENTSTREAM_BACKEND="django_eventstream.backends.memorybackend.MemoryBackend",
    EVENTSTREAM_REDIS_CONNECTION=None,
    EVENTSTREAM_ALLOW_ORIGIN="*",
    # 혹시 호스트 제한 있으면 넉넉히
    ALLOWED_HOSTS=["testserver", "127.0.0.1", "localhost"],
)
class EventStreamHTTPXTests(TransactionTestCase):
    """Uvicorn으로 실제 ASGI 서버를 띄워 /events/?channel=user-<id> SSE를 통합 테스트"""

    server: ClassVar[uvicorn.Server | None] = None
    server_thread: ClassVar[threading.Thread | None] = None
    base_url: ClassVar[str]
    user: ClassVar["DjangoUser"]  # ← 문자열 타입 힌트로 선언

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(
            email="sse@test.com",
            password="Pw123456!",
            nickname="tester",
            name="Tester",
            phone_number="01000000000",
            gender="male",
            birthday=date(1990, 1, 1),
        )
        import django_eventstream.eventstream as es  # type: ignore[import-untyped]

        es._backend = None  # 캐시 클리어
        reload(es)
        # 빈 포트 할당
        port = get_free_port()
        cls.base_url = f"http://127.0.0.1:{port}"

        # Uvicorn ASGI 서버를 백그라운드로 띄운다
        config = uvicorn.Config(
            "config.asgi:application",
            host="127.0.0.1",
            port=port,
            log_level="error",
            lifespan="off",  # 테스트 속도/안정용
        )
        cls.server = uvicorn.Server(config)
        cls.server_thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.server_thread.start()

        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                with httpx.Client(timeout=0.2) as c:
                    c.get(cls.base_url + "/")
                break
            except Exception:
                time.sleep(0.05)
        else:
            raise RuntimeError("Uvicorn test server failed to start")

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            if cls.server:
                cls.server.should_exit = True
            if cls.server_thread:
                cls.server_thread.join(timeout=5)
        finally:
            super().tearDownClass()

    def setUp(self) -> None:
        # 로그인 세션 만들고 쿠키 이식
        self.dclient = Client()
        # mypy 스텁이 기본 User 타입만 허용하므로 Any로 캐스트해 한 줄만 우회
        self.dclient.force_login(cast(Any, type(self).user))
        self.cookies: Dict[str, str] = {k: v.value for k, v in self.dclient.cookies.items()}
        # mypy가 Optional로 보지 않도록 미리 정수화
        self._uid: int = int(type(self).user.id)

    def _wait_subscription_ready(self, resp: httpx.Response, timeout_sec: float = 2.0) -> None:
        """
        SSE 구독이 실제로 붙어서 한 줄이라도 들어오기 시작했는지 짧게 확인.
        (빈 줄/코멘트여도 OK)
        """
        deadline = time.time() + timeout_sec
        it = resp.iter_lines()

        while time.time() < deadline:
            try:
                line = next(it)
            except StopIteration:
                # 스트림이 조기에 닫힌 경우
                break

            # 어떤 내용이든 한 줄이라도 받았으면 구독 준비 완료
            return

    # SSE 한 이벤트만 파싱
    def _read_one_event_from_lines(
        self,
        lines: Iterable[Union[str, bytes]],
        timeout_sec: float = 10.0,
    ) -> Optional[Dict[str, Any]]:
        deadline = time.time() + timeout_sec
        buf: list[str] = []
        it = iter(lines)

        while time.time() <= deadline:
            try:
                line = next(it)
            except StopIteration:
                break

            s = line.decode() if isinstance(line, (bytes, bytearray)) else str(line)
            s = s.rstrip("\r\n")

            if not s:
                etype: Optional[str] = None
                data_raw: Optional[str] = None
                for row in buf:
                    if row.startswith("event:"):
                        etype = row[6:].strip()
                    elif row.startswith("data:"):
                        data_raw = row[5:].strip()
                buf.clear()

                if data_raw:
                    payload: Dict[str, Any] = json.loads(data_raw)
                    if etype:
                        payload["_event"] = etype
                    return payload
            else:
                buf.append(s)

        return None

    def test_client_receives_streamed_notification(self) -> None:
        url = f"{type(self).base_url}/events/?channel=user-{self._uid}"
        with httpx.Client(timeout=None, cookies=self.cookies) as client:
            with client.stream("GET", url, headers={"Accept": "text/event-stream"}) as resp:
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.headers["content-type"].startswith("text/event-stream"))

                # 한 번만 만들고 끝까지 공유할 이터레이터
                lines = resp.iter_lines()

                # 스트림 오픈 후에 이벤트를 발생시켜야 소비 타이밍이 맞습니다
                Notification.objects.create(
                    user_id=self._uid,
                    content="hello via sse",
                    notification_type=Notification.NotificationType.ADD_APPLICATION,
                    back_url_link="/x",
                )

                # 이터레이터를 넘겨서 ‘한 번만’ 순회
                evt = self._read_one_event_from_lines(lines, timeout_sec=10.0)
                if evt is None:
                    self.fail("SSE 이벤트를 받지 못했습니다(타임아웃).")

                self.assertEqual(evt.get("_event"), "notification")
                self.assertEqual(evt.get("content"), "hello via sse")
                self.assertEqual(evt.get("back_url_link"), "/x")
