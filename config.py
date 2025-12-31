# -*- coding: utf-8 -*-
"""
설정 파일 - 하드코딩된 값들 중앙화
=================================
버전: 1.0
최종 수정: 2024-12
"""

# ========================================
# 모델 설정
# ========================================

# 지원 모델 목록 및 비용 (2024-12 기준)
# 비용: 입력 ~400토큰 + 출력 ~300토큰 기준
MODEL_OPTIONS = {
    "Qwen/Qwen2.5-7B-Instruct": {
        "display_name": "Qwen 2.5 7B (무료)",
        "provider": "huggingface",
        "api_url": "https://router.huggingface.co/v1/chat/completions",
        "cost_per_call_krw": 0,
        "quality_score": 75,
        "stability": 3,
    },
    "gpt-4o-mini": {
        "display_name": "GPT-4o-mini (₩0.33/건) ⭐추천",
        "provider": "openai",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "cost_per_call_krw": 0.33,
        "quality_score": 87,
        "stability": 5,
    },
    "gpt-4.1-nano": {
        "display_name": "GPT-4.1 Nano (₩0.22/건)",
        "provider": "openai",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "cost_per_call_krw": 0.22,
        "quality_score": 82,
        "stability": 4,
    },
    "gpt-4.1-mini": {
        "display_name": "GPT-4.1 Mini (₩0.88/건)",
        "provider": "openai",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "cost_per_call_krw": 0.88,
        "quality_score": 90,
        "stability": 4,
    },
    "gpt-4.1": {
        "display_name": "GPT-4.1 (₩4.4/건)",
        "provider": "openai",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "cost_per_call_krw": 4.4,
        "quality_score": 95,
        "stability": 5,
    }
}

# 모델 비용 (토큰당, USD per 1M tokens)
MODEL_PRICING = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "Qwen/Qwen2.5-7B-Instruct": {"input": 0, "output": 0},  # 무료
}

# 환율 (원/달러)
EXCHANGE_RATE = 1400

# ========================================
# RAG 검색 설정
# ========================================

# 하이브리드 검색 가중치
VECTOR_WEIGHT = 0.6
BM25_WEIGHT = 0.4

# BM25 파라미터
BM25_K1 = 1.5
BM25_B = 0.75

# 임베딩 모델
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"

# ========================================
# 가격대 설정
# ========================================

# 페르소나 쇼핑패턴별 가격 범위
PRICE_RANGES = {
    "가성비": (0, 50000),
    "저렴": (0, 50000),
    "프리미엄": (50000, None),
    "럭셔리": (100000, None),
}

# 기본 가격 범위 (제한 없음)
DEFAULT_PRICE_RANGE = (0, None)

# ========================================
# 발신목적 설정
# ========================================

# 영문 ID → 한글명 매핑
PURPOSE_NAMES = {
    "promotion": "프로모션",
    "new_product": "신제품 안내",
    "best_curation": "베스트 큐레이션",
    "repurchase": "재구매 & 리텐션",
    "churn_prevention": "휴면 방지",
    "seasonal_gift": "선물 & 시즌"
}

# 발신목적 옵션 (UI용)
PURPOSE_OPTIONS = [
    ("promotion", "프로모션", "할인/쿠폰 혜택 안내"),
    ("new_product", "신제품 안내", "새로 출시된 제품 소개"),
    ("best_curation", "베스트 큐레이션", "브랜드 인기 상품 추천"),
    ("repurchase", "재구매 & 리텐션", "구매 주기 도래 고객"),
    ("churn_prevention", "휴면 방지", "이탈 위험 고객 재활성화"),
    ("seasonal_gift", "선물 & 시즌", "명절/기념일 선물 추천")
]

# ========================================
# 메시지 글자수 제한
# ========================================

TITLE_MAX_LENGTH = 40
BODY_MIN_LENGTH = 300
BODY_MAX_LENGTH = 350
BODY_TARGET_LENGTH = 320

# ========================================
# 고객 분석 임계값
# ========================================

# 이탈 확률 임계값
CHURN_HIGH_THRESHOLD = 0.5
CHURN_MEDIUM_THRESHOLD = 0.35

# 신규 고객 기준 (가입 후 일수)
NEW_CUSTOMER_DAYS = 90
NEW_CUSTOMER_PURCHASES = 3

# 구매 주기 도래 임계값
CYCLE_RATIO_THRESHOLD = 0.8

# ========================================
# UI 설정
# ========================================

# 메시지 히스토리 최대 개수
MAX_HISTORY_COUNT = 10

# 추천 상품 기본 개수
DEFAULT_PRODUCT_COUNT = 3
MAX_PRODUCT_COUNT = 5

# ========================================
# 캐시 설정
# ========================================

import os

# 캐시 디렉토리
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
FAISS_INDEX_PATH = os.path.join(CACHE_DIR, 'faiss_index')
BM25_CACHE_PATH = os.path.join(CACHE_DIR, 'bm25_cache.pkl')
DOCS_CACHE_PATH = os.path.join(CACHE_DIR, 'docs_cache.pkl')


# ========================================
# 헬퍼 함수
# ========================================

def get_model_display_name(model_id: str) -> str:
    """모델 ID → 표시 이름"""
    return MODEL_OPTIONS.get(model_id, {}).get("display_name", model_id)


def get_price_range_for_pattern(shopping_pattern: str) -> tuple:
    """쇼핑패턴 → 가격 범위"""
    for keyword, price_range in PRICE_RANGES.items():
        if keyword in shopping_pattern:
            return price_range
    return DEFAULT_PRICE_RANGE


def get_purpose_name(purpose_id: str) -> str:
    """영문 ID → 한글명"""
    return PURPOSE_NAMES.get(purpose_id, purpose_id)


def calculate_model_cost(model: str, input_tokens: int, output_tokens: int) -> dict:
    """
    모델 비용 계산

    Returns:
        {
            "input_cost_usd": float,
            "output_cost_usd": float,
            "total_cost_usd": float,
            "total_cost_krw": float,
            "is_free": bool
        }
    """
    pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost_usd = input_cost + output_cost
    total_cost_krw = total_cost_usd * EXCHANGE_RATE

    return {
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": total_cost_usd,
        "total_cost_krw": total_cost_krw,
        "is_free": pricing["input"] == 0 and pricing["output"] == 0
    }
