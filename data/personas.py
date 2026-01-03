# -*- coding: utf-8 -*-
"""
아모레몰 CRM 데이터
- 상품: personas_full.py에서 import (1,053개)
- 페르소나: ML 분류 기반 5명 샘플 고객
"""

# 상품 데이터 import (1,053개)
from data.personas_full import products

# 브랜드 톤앤매너 데이터 (크롤링 30개 브랜드 기준)
brand_tones = {
    # ===== 프리미엄 스킨케어 =====
    "설화수": {
        "tone": "고급스럽고 우아한",
        "style": "한방 철학 기반, 품격있는 표현",
        "keywords": ["한방", "진설", "윤조", "자음생", "인삼"],
        "price_tier": "premium"
    },
    "헤라": {
        "tone": "세련되고 도시적인",
        "style": "서울 감성, 모던 럭셔리",
        "keywords": ["블랙쿠션", "센슈얼", "글로우"],
        "price_tier": "premium"
    },
    "아이오페": {
        "tone": "과학적이고 전문적인",
        "style": "바이오 사이언스 강조, 효능 중심",
        "keywords": ["레티놀", "바이오", "슈퍼바이탈"],
        "price_tier": "premium"
    },
    "아모레퍼시픽": {
        "tone": "최고급 럭셔리",
        "style": "아모레의 정수, 시그니처 한방 럭셔리",
        "keywords": ["타임레스폰스", "바이탈뷰티", "프리미엄"],
        "price_tier": "premium"
    },
    "홀리추얼": {
        "tone": "고급스럽고 의례적인",
        "style": "의식(ritual) 기반 럭셔리 케어",
        "keywords": ["리추얼", "의식", "명상", "홀리스틱"],
        "price_tier": "premium"
    },

    # ===== 미드레인지 스킨케어 =====
    "라네즈": {
        "tone": "활기차고 수분 가득한",
        "style": "젊고 트렌디한 감성, 수분 강조",
        "keywords": ["워터뱅크", "수분", "히알루론", "글로우"],
        "price_tier": "mid"
    },
    "프리메라": {
        "tone": "순수하고 건강한",
        "style": "민감피부 전문, 저자극 강조",
        "keywords": ["알파인베리", "오가니언스", "미라클씨드"],
        "price_tier": "mid"
    },
    "마몽드": {
        "tone": "여성스럽고 로맨틱한",
        "style": "꽃 성분 강조, 우아한 감성",
        "keywords": ["로즈워터", "레드에너지", "프로바이오틱스"],
        "price_tier": "mid"
    },
    "한율": {
        "tone": "전통적이고 정성스러운",
        "style": "한국 자연 원료, 정성 케어",
        "keywords": ["서리태콩", "달빛유자", "어린쑥"],
        "price_tier": "mid"
    },
    "에스트라": {
        "tone": "전문적이고 신뢰감 있는",
        "style": "더마 코스메틱, 피부과학 기반",
        "keywords": ["아토베리어", "테라크네", "더마"],
        "price_tier": "mid"
    },
    "비레디": {
        "tone": "남성적이고 깔끔한",
        "style": "남성 그루밍 전문, 실용적",
        "keywords": ["쿨링", "그루밍", "올인원"],
        "price_tier": "mid"
    },

    # ===== 영타겟/어포더블 =====
    "이니스프리": {
        "tone": "자연친화적이고 청량한",
        "style": "제주 자연 감성, 친환경 강조",
        "keywords": ["제주", "그린티", "비자", "자연유래"],
        "price_tier": "affordable"
    },
    "에뛰드": {
        "tone": "발랄하고 귀여운",
        "style": "10-20대 타겟, 컬러풀한 감성",
        "keywords": ["플레이컬러", "순정", "드로잉"],
        "price_tier": "affordable"
    },
    "에스쁘아": {
        "tone": "세련되고 프로페셔널한",
        "style": "메이크업 아티스트 감성, 트렌디",
        "keywords": ["프로테일러", "리얼스킨", "립스틱"],
        "price_tier": "mid"
    },
    "앞바다즈": {
        "tone": "자유롭고 개성있는",
        "style": "MZ세대 타겟, 독특한 감성",
        "keywords": ["개성", "트렌디", "유니크"],
        "price_tier": "affordable"
    },
    "아모레성수": {
        "tone": "트렌디하고 실험적인",
        "style": "성수동 감성, 힙한 브랜드",
        "keywords": ["성수", "트렌드", "리미티드"],
        "price_tier": "mid"
    },

    # ===== 더마/민감피부 =====
    "일리윤": {
        "tone": "순하고 안전한",
        "style": "아토피/민감피부 전문, 온 가족용",
        "keywords": ["세라마이드", "아토", "보습"],
        "price_tier": "affordable"
    },

    # ===== 헤어케어 =====
    "려": {
        "tone": "건강하고 윤기나는",
        "style": "탈모/두피케어 전문, 한방 헤어",
        "keywords": ["자양윤모", "청아", "함빛"],
        "price_tier": "mid"
    },
    "미쟝센": {
        "tone": "스타일리시하고 실용적인",
        "style": "헤어스타일링 전문, 트렌디",
        "keywords": ["퍼펙트세럼", "헬로버블"],
        "price_tier": "affordable"
    },
    "라보에이치": {
        "tone": "전문적이고 효과적인",
        "style": "두피과학 기반, 탈모케어 전문",
        "keywords": ["두피", "탈모", "볼륨"],
        "price_tier": "mid"
    },

    # ===== 바디/오럴케어 =====
    "해피바스": {
        "tone": "상쾌하고 기분 좋은",
        "style": "바디케어 전문, 가족용",
        "keywords": ["바디워시", "보습", "향기"],
        "price_tier": "affordable"
    },
    "메디안": {
        "tone": "깨끗하고 건강한",
        "style": "오럴케어 전문, 치약/칫솔",
        "keywords": ["치약", "미백", "잇몸"],
        "price_tier": "affordable"
    },
    "아모레베이직": {
        "tone": "실용적이고 기본에 충실한",
        "style": "생활용품, 기본 케어",
        "keywords": ["기본", "실용", "가성비"],
        "price_tier": "affordable"
    },

    # ===== 뷰티디바이스 =====
    "메이크온": {
        "tone": "혁신적이고 기술적인",
        "style": "뷰티디바이스 전문, 홈케어 기기",
        "keywords": ["디바이스", "LED", "갈바닉"],
        "price_tier": "premium"
    },
    "에이피뷰티": {
        "tone": "전문적이고 효과적인",
        "style": "프로페셔널 뷰티 솔루션",
        "keywords": ["프로", "전문가", "솔루션"],
        "price_tier": "premium"
    },

    # ===== 웰니스/라이프스타일 =====
    "오설록": {
        "tone": "우아하고 여유로운",
        "style": "제주 녹차 감성, 힐링",
        "keywords": ["녹차", "제주", "티", "힐링"],
        "price_tier": "mid"
    },
    "바이탈뷰티": {
        "tone": "건강하고 활력있는",
        "style": "이너뷰티, 건강기능식품",
        "keywords": ["콜라겐", "슬리머", "이너뷰티"],
        "price_tier": "mid"
    },
    "퍼즐우드": {
        "tone": "자연스럽고 편안한",
        "style": "라이프스타일, 향기 케어",
        "keywords": ["향", "디퓨저", "라이프스타일"],
        "price_tier": "mid"
    },
    "롱테이크": {
        "tone": "감각적이고 무드있는",
        "style": "향수/퍼퓸, 감성 케어",
        "keywords": ["향수", "퍼퓸", "무드"],
        "price_tier": "mid"
    },
    "오딧세이": {
        "tone": "남성적이고 세련된",
        "style": "남성 화장품 전문, 모던",
        "keywords": ["남성", "그루밍", "스킨케어"],
        "price_tier": "mid"
    },
}

# ============================================================
# 페르소나 데이터 (ML 분류 기반 5명 샘플)
# ============================================================
# 7개 페르소나 클러스터:
# - 하이엔드 품격가
# - 트렌디 Z세대
# - 테크니컬 홈케어족
# - 실속형 가계 수호자
# - 합리적 큐레이터
# - 연구소 기반 해결사
# - 웰니스 힐링 탐험가

personas = [
    # ===== 페르소나 1: 김서연 (42세) - 하이엔드 품격가 =====
    {
        "id": 1,
        "name": "김서연",
        "display_name": "김서연(42세)",
        "age": 42,
        "skin_type": "민감성",
        "concerns": ["주름", "탄력"],
        "interests": ["크림", "세럼", "에센스"],
        "shopping_pattern": "프리미엄 브랜드 충성, 정가 구매 비율 높음",
        "lifestyle": "프리미엄 럭셔리 브랜드를 선호하는 품격있는 고객",
        "tier": "premium",

        # 페르소나 클러스터 정보
        "persona_cluster": "하이엔드 품격가",
        "persona_confidence": 0.98,

        # 행동 데이터
        "activity": {
            "last_visit_days_ago": 5,
            "visit_frequency": "높음",
            "avg_session_minutes": 15,
            "signup_days_ago": 1200
        },

        "purchase": {
            "total_count": 28,
            "last_purchase_days_ago": 12,
            "avg_interval": 35,
            "total_amount": 4060000,
            "avg_amount": 145000,
            "recent_categories": ["크림", "세럼", "에센스"]
        },

        "brand": {
            "purchase_counts": {
                "설화수": 20,
                "헤라": 5,
                "아모레퍼시픽": 3
            },
            "primary_brand": "설화수",
            "loyalty": "높음",
            "diversity": 0.25
        },

        "promotion": {
            "discount_sensitivity": "낮음",
            "event_participation_rate": 0.3,
            "preferred_type": "샘플",
            "coupon_usage_rate": 0.15,
            "full_price_ratio": 0.82
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.08
        },

        "seasonal": {
            "gift_purchases": True,
            "peak_seasons": ["설날", "추석"],
            "seasonal_events": ["명절"]
        },

        "membership": {
            "tier": "VIP",
            "tier_criteria": "연 300만원 이상",
            "points": 220000
        }
    },

    # ===== 페르소나 2: 이지우 (21세) - 트렌디 Z세대 =====
    {
        "id": 2,
        "name": "이지우",
        "display_name": "이지우(21세)",
        "age": 21,
        "skin_type": "지성",
        "concerns": ["모공", "피지"],
        "interests": ["쿠션", "립", "선케어"],
        "shopping_pattern": "트렌디한 제품 선호, 가성비 중시",
        "lifestyle": "트렌드에 민감한 MZ세대, SNS 영향력",
        "tier": "affordable",

        # 페르소나 클러스터 정보
        "persona_cluster": "트렌디 Z세대",
        "persona_confidence": 0.997,

        # 행동 데이터
        "activity": {
            "last_visit_days_ago": 2,
            "visit_frequency": "높음",
            "avg_session_minutes": 20,
            "signup_days_ago": 300
        },

        "purchase": {
            "total_count": 12,
            "last_purchase_days_ago": 8,
            "avg_interval": 25,
            "total_amount": 384000,
            "avg_amount": 32000,
            "recent_categories": ["쿠션", "립", "선케어"]
        },

        "brand": {
            "purchase_counts": {
                "에뛰드": 6,
                "에스쁘아": 4,
                "아모레성수": 2
            },
            "primary_brand": "에뛰드",
            "loyalty": "중간",
            "diversity": 0.7
        },

        "promotion": {
            "discount_sensitivity": "높음",
            "event_participation_rate": 0.8,
            "preferred_type": "할인",
            "coupon_usage_rate": 0.65,
            "full_price_ratio": 0.35
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.12
        },

        "seasonal": {
            "gift_purchases": False,
            "peak_seasons": ["여름"],
            "seasonal_events": []
        },

        "membership": {
            "tier": "실버",
            "tier_criteria": "연 30만원 이상",
            "points": 15000
        }
    },

    # ===== 페르소나 3: 박민지 (38세) - 테크니컬 홈케어족 =====
    {
        "id": 3,
        "name": "박민지",
        "display_name": "박민지(38세)",
        "age": 38,
        "skin_type": "민감성",
        "concerns": ["진정", "보습"],
        "interests": ["디바이스", "세럼", "마스크"],
        "shopping_pattern": "고가 제품 선호, 기술력 중시",
        "lifestyle": "기술 기반 홈케어 디바이스와 고기능성 스킨케어를 선호",
        "tier": "premium",

        # 페르소나 클러스터 정보 (신뢰도가 낮아 연구소 기반 해결사로 분류됨)
        "persona_cluster": "연구소 기반 해결사",
        "persona_confidence": 0.567,

        # 행동 데이터
        "activity": {
            "last_visit_days_ago": 10,
            "visit_frequency": "중",
            "avg_session_minutes": 18,
            "signup_days_ago": 800
        },

        "purchase": {
            "total_count": 18,
            "last_purchase_days_ago": 25,
            "avg_interval": 40,
            "total_amount": 2250000,
            "avg_amount": 125000,
            "recent_categories": ["세럼", "크림", "마스크"]
        },

        "brand": {
            "purchase_counts": {
                "메이크온": 8,
                "아이오페": 6,
                "에스트라": 4
            },
            "primary_brand": "메이크온",
            "loyalty": "높음",
            "diversity": 0.3
        },

        "promotion": {
            "discount_sensitivity": "낮음",
            "event_participation_rate": 0.4,
            "preferred_type": "샘플",
            "coupon_usage_rate": 0.22,
            "full_price_ratio": 0.78
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.1
        },

        "seasonal": {
            "gift_purchases": True,
            "peak_seasons": ["겨울"],
            "seasonal_events": []
        },

        "membership": {
            "tier": "골드",
            "tier_criteria": "연 100만원 이상",
            "points": 85000
        }
    },

    # ===== 페르소나 4: 최수현 (35세) - 실속형 가계 수호자 =====
    {
        "id": 4,
        "name": "최수현",
        "display_name": "최수현(35세)",
        "age": 35,
        "skin_type": "복합성",
        "concerns": ["각질", "탄력"],
        "interests": ["바디케어", "헤어케어", "클렌징"],
        "shopping_pattern": "할인/쿠폰 적극 활용, 대용량 선호",
        "lifestyle": "가족용/생활용품 대량 구매, 할인에 민감",
        "tier": "affordable",

        # 페르소나 클러스터 정보
        "persona_cluster": "실속형 가계 수호자",
        "persona_confidence": 0.986,

        # 행동 데이터
        "activity": {
            "last_visit_days_ago": 3,
            "visit_frequency": "높음",
            "avg_session_minutes": 12,
            "signup_days_ago": 600
        },

        "purchase": {
            "total_count": 22,
            "last_purchase_days_ago": 7,
            "avg_interval": 20,
            "total_amount": 836000,
            "avg_amount": 38000,
            "recent_categories": ["바디케어", "헤어케어", "클렌징"]
        },

        "brand": {
            "purchase_counts": {
                "일리윤": 8,
                "라보에이치": 6,
                "메디안": 5,
                "아모레베이직": 3
            },
            "primary_brand": "일리윤",
            "loyalty": "높음",
            "diversity": 0.45
        },

        "promotion": {
            "discount_sensitivity": "높음",
            "event_participation_rate": 0.85,
            "preferred_type": "할인",
            "coupon_usage_rate": 0.75,
            "full_price_ratio": 0.42
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.15
        },

        "seasonal": {
            "gift_purchases": False,
            "peak_seasons": [],
            "seasonal_events": []
        },

        "membership": {
            "tier": "실버",
            "tier_criteria": "연 50만원 이상",
            "points": 28000
        }
    },

    # ===== 페르소나 5: 정하은 (29세) - 합리적 큐레이터 =====
    {
        "id": 5,
        "name": "정하은",
        "display_name": "정하은(29세)",
        "age": 29,
        "skin_type": "건성",
        "concerns": ["보습", "주름"],
        "interests": ["스킨케어", "세럼", "크림"],
        "shopping_pattern": "가성비 중시, 리뷰 꼼꼼히 확인",
        "lifestyle": "합리적인 가격대에서 좋은 품질을 추구",
        "tier": "mid",

        # 페르소나 클러스터 정보
        "persona_cluster": "합리적 큐레이터",
        "persona_confidence": 0.965,

        # 행동 데이터
        "activity": {
            "last_visit_days_ago": 7,
            "visit_frequency": "중",
            "avg_session_minutes": 15,
            "signup_days_ago": 450
        },

        "purchase": {
            "total_count": 15,
            "last_purchase_days_ago": 18,
            "avg_interval": 30,
            "total_amount": 720000,
            "avg_amount": 48000,
            "recent_categories": ["스킨케어", "세럼", "크림"]
        },

        "brand": {
            "purchase_counts": {
                "라네즈": 5,
                "이니스프리": 4,
                "한율": 3,
                "프리메라": 3
            },
            "primary_brand": "라네즈",
            "loyalty": "중간",
            "diversity": 0.55
        },

        "promotion": {
            "discount_sensitivity": "중간",
            "event_participation_rate": 0.6,
            "preferred_type": "포인트",
            "coupon_usage_rate": 0.45,
            "full_price_ratio": 0.52
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.18
        },

        "seasonal": {
            "gift_purchases": True,
            "peak_seasons": ["가을", "겨울"],
            "seasonal_events": []
        },

        "membership": {
            "tier": "골드",
            "tier_criteria": "연 70만원 이상",
            "points": 42000
        }
    },
]

# 발신 목적 옵션 (UI에서 사용)
PURPOSE_OPTIONS = [
    {
        "id": "promotion",
        "name": "프로모션",
        "description": "할인, 적립금, 쿠폰 등 혜택 안내",
        "target_conditions": ["활성고객", "프로모션_반응_좋음", "할인_민감"]
    },
    {
        "id": "new_product",
        "name": "신제품 안내",
        "description": "새로 출시된 제품 소개",
        "target_conditions": ["활성고객", "트렌드_민감", "신제품_관심"]
    },
    {
        "id": "best_curation",
        "name": "베스트 큐레이션",
        "description": "인기 상품, 브랜드 베스트 추천",
        "target_conditions": ["브랜드_충성도_높음", "활성고객"]
    },
    {
        "id": "repurchase",
        "name": "재구매 & 리텐션",
        "description": "구매 주기 도래 고객 재구매 유도",
        "target_conditions": ["구매주기_도래", "기존구매자"]
    },
    {
        "id": "churn_prevention",
        "name": "휴면 방지",
        "description": "이탈 위험 고객 재활성화",
        "target_conditions": ["휴면위험", "접속감소", "구매감소"]
    },
    {
        "id": "seasonal_gift",
        "name": "선물 & 시즌 이벤트",
        "description": "명절, 기념일 선물 추천",
        "target_conditions": ["선물구매_이력", "시즌_이벤트"]
    }
]
