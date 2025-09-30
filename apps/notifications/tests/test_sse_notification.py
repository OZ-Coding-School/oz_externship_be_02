from __future__ import annotations

import json
import socket
import threading
import time
from datetime import date
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, cast

import httpx
import uvicorn
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

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
class EventStreamHTTPXTests(TestCase):
    """Uvicorn으로 실제 ASGI 서버를 띄워 /events/?channel=user-<id> SSE를 통합 테스트"""

    server: ClassVar[uvicorn.Server | None] = None
    server_thread: ClassVar[threading.Thread | None] = None
    base_url: ClassVar[str]
    user: ClassVar["DjangoUser"]  # ← 문자열 타입 힌트로 선언

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="sse@test.com",
            password="Pw123456!",
            nickname="tester",
            name="Tester",
            phone_number="01000000000",
            gender="male",
            birthday=date(1990, 1, 1),
        )

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
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

    # SSE 한 이벤트만 파싱
    def _read_one_event(self, resp: httpx.Response, timeout_sec: float = 10.0) -> Optional[Dict[str, Any]]:
        deadline = time.time() + timeout_sec
        buf: list[str] = []
        for line in resp.iter_lines():
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
            if time.time() > deadline:
                break
        return None

    def test_client_receives_streamed_notification(self) -> None:
        url = f"{type(self).base_url}/events/?channel=user-{self._uid}"
        with httpx.Client(timeout=None, cookies=self.cookies) as client:
            # 1) SSE 스트림 연결
            with client.stream("GET", url, headers={"Accept": "text/event-stream"}) as resp:
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.headers["content-type"].startswith("text/event-stream"))

                # 2) 알림 생성 → post_save 신호에서 send_event
                Notification.objects.create(
                    user_id=self._uid,
                    content="hello via sse",
                    notification_type=Notification.NotificationType.ADD_APPLICATION,
                    back_url_link="/x",
                )

                # 3) 이벤트 수신
                evt = self._read_one_event(resp, timeout_sec=10.0)
                if evt is None:
                    self.fail("SSE 이벤트를 받지 못했습니다(타임아웃).")

                self.assertEqual(evt.get("_event"), "notification")
                self.assertEqual(evt.get("content"), "hello via sse")
                self.assertEqual(evt.get("back_url_link"), "/x")
