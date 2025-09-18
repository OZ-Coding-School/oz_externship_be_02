import logging
import os
from typing import Any, Optional, cast

import google.generativeai as genai_impl
from dotenv import load_dotenv
from google.generativeai import types

logger = logging.getLogger("django")


# 타입 정의
class GenerativeModel:
    def __init__(self, model_name: str) -> None: ...
    def generate_content(
        self,
        prompt: str,
        generation_config: Optional[types.GenerationConfig] = None,
    ) -> Any: ...


class Genai:
    def configure(self, api_key: str) -> None: ...

    GenerativeModel = GenerativeModel


# API 키 설정
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# genai_impl 모듈을 mypy가 이해할 수 있는 타입으로 캐스팅
genai: Genai = cast(Genai, genai_impl)
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 모델 및 설정
MODEL_NAME = "gemini-2.5-flash-lite"
config = types.GenerationConfig(
    max_output_tokens=512,  # 응답 길이 제한(속도 개선)
    temperature=0.5,  # 낮출수록 일관된 결과
    top_p=0.8,  # 샘플링 제한(짧고 깔끔한 응답)
)


def generate_study_summary(content: str, author_name: str, date_str: str) -> str:
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY가 설정되지 않아 AI 요약 생성에 실패했습니다.")
        return "AI 요약 생성 실패"

    model: GenerativeModel = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
    다음 스터디 기록 내용을 반드시 아래 형식을 지켜 요약해줘

    ### {date_str} {author_name}님의 학습 기록 요약해줘

    ## 학습 내용 요약
    - {content}의 핵심 내용을 연결된 문장 2~4줄로 요약해줘

    ## 학습한 키워드
    - 관련된 키워드를 최소 3개 이상 나열해줘

    ## 추가로 학습하면 좋을 내용 추천
    - 반드시 3~5개 추천해줘
    - 만약 특별한 추천이 없다면 '기록된 학습 내용을 보강할 수 있는 심화 자료 탐색'과 같이 일반적인 학습 방향을 제시해줘
    """

    try:
        response = model.generate_content(prompt, generation_config=config)

        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        candidates = getattr(response, "candidates", [])
        if candidates:
            parts = getattr(candidates[0].content, "parts", [])
            return "\n".join([getattr(p, "text", "") for p in parts]).strip() or "AI 요약 생성 실패"

        return "AI 요약 생성 실패"

    except Exception as e:
        logger.error(f"AI 요약 생성 실패: {e}", exc_info=True)
        return "AI 요약 생성 실패"
