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
# 페르소나 데이터 (ML 분류 기반 7명 샘플 - 2025.01 업데이트)
# ============================================================
# customer_data_1000.csv 기준 데이터 구조 반영
# 7개 페르소나 클러스터:
# 1. 테크니컬 홈케어족 - 뷰티디바이스, 스킨케어, 뷰티푸드
# 2. 하이엔드 품격가 - 스킨케어, 메이크업, 선물추천
# 3. 웰니스 힐링 탐험가 - 뷰티푸드, 차(TEA), 바디
# 4. 연구소 기반 해결사 - 스킨케어, 남성, 세트
# 5. 트렌디 Z세대 - 메이크업, 향수, 바디
# 6. 합리적 큐레이터 - 스킨케어, 헤어, 바디
# 7. 실속형 가계 수호자 - 바디, 생활용품, 구강
#
# 멤버십 티어: A(일반) < B(브론즈) < C(실버) < D(골드) < E(VIP)

personas = [
    # ===== 페르소나 1: 서수진 (33세) - 테크니컬 홈케어족 =====
    {
        "id": 1,
        "name": "서수진",
        "display_name": "서수진(33세)",
        "age": 33,
        "skin_type": "복합성",
        "concerns": ["보습"],
        "interests": ["뷰티디바이스", "스킨케어", "뷰티푸드"],
        "shopping_pattern": "프리미엄 기능성 제품 선호, 기술력과 효능 중시",
        "lifestyle": "뷰티 디바이스와 고기능성 스킨케어를 선호하는 전문 홈케어 고객",
        "tier": "premium",

        # 페르소나 클러스터 정보
        "persona_cluster": "테크니컬 홈케어족",
        "persona_confidence": 0.92,

        # 행동 데이터 - 전환유도 (구매주기 도래)
        "activity": {
            "last_visit_days_ago": 7,
            "visit_frequency": "낮음",
            "avg_session_minutes": 8,
            "signup_days_ago": 150
        },

        "purchase": {
            "total_count": 23,
            "last_purchase_days_ago": 35,  # 구매주기 85% 도래 (35/41=0.85)
            "avg_interval": 41,
            "total_amount": 1663268,
            "avg_amount": 72316,
            "recent_categories": ["선케어"]
        },

        "brand": {
            "purchase_counts": {
                "에이피뷰티": 10,
                "아모레퍼시픽": 8,
                "미쟝센": 3,
                "비레디": 2
            },
            "primary_brand": "에이피뷰티",
            "loyalty": "높음",
            "diversity": 0.16
        },

        "promotion": {
            "discount_sensitivity": "낮음",
            "event_participation_rate": 0.55,
            "preferred_type": "샘플",
            "coupon_usage_rate": 0.18,
            "full_price_ratio": 0.63
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.12
        },

        "seasonal": {
            "gift_purchases": True,
            "peak_seasons": [],
            "seasonal_events": []
        },

        "membership": {
            "tier": "VIP",
            "tier_criteria": "E등급",
            "points": 50000
        }
    },

    # ===== 페르소나 2: 홍소희 (48세) - 하이엔드 품격가 =====
    {
        "id": 2,
        "name": "홍소희",
        "display_name": "홍소희(48세)",
        "age": 48,
        "skin_type": "복합성",
        "concerns": ["모공"],
        "interests": ["스킨케어", "메이크업", "선물추천"],
        "shopping_pattern": "프리미엄 브랜드 충성, 샘플/사은품 선호",
        "lifestyle": "프리미엄 럭셔리 브랜드를 선호하는 품격있는 VIP 고객",
        "tier": "premium",

        # 페르소나 클러스터 정보
        "persona_cluster": "하이엔드 품격가",
        "persona_confidence": 0.89,

        # 행동 데이터 - 재활성화 (휴면 위험)
        "activity": {
            "last_visit_days_ago": 45,
            "visit_frequency": "높음",
            "avg_session_minutes": 36,
            "signup_days_ago": 210
        },

        "purchase": {
            "total_count": 17,
            "last_purchase_days_ago": 90,  # 오래된 구매
            "avg_interval": 41,
            "total_amount": 1253903,
            "avg_amount": 73759,
            "recent_categories": ["클렌징"]
        },

        "brand": {
            "purchase_counts": {
                "아모레퍼시픽": 8,
                "설화수": 5,
                "헤라": 4
            },
            "primary_brand": "아모레퍼시픽",
            "loyalty": "높음",
            "diversity": 0.12
        },

        "promotion": {
            "discount_sensitivity": "중간",
            "event_participation_rate": 0.51,
            "preferred_type": "사은품",
            "coupon_usage_rate": 0.30,
            "full_price_ratio": 0.60
        },

        "risk": {
            "level": "높음",
            "factors": ["장기 미구매"],
            "churn_probability": 0.45  # 재활성화 조건 충족 (35% 이상)
        },

        "seasonal": {
            "gift_purchases": True,
            "peak_seasons": ["설날", "추석"],
            "seasonal_events": ["명절"]
        },

        "membership": {
            "tier": "골드",
            "tier_criteria": "D등급",
            "points": 120000
        }
    },

    # ===== 페르소나 3: 장태영 (29세) - 웰니스 힐링 탐험가 =====
    {
        "id": 3,
        "name": "장태영",
        "display_name": "장태영(29세)",
        "age": 29,
        "skin_type": "복합성",
        "concerns": ["보습"],
        "interests": ["뷰티푸드", "바디", "스킨케어"],
        "shopping_pattern": "새로운 브랜드/제품 탐색, 체험 중시, 샘플 선호",
        "lifestyle": "웰니스, 힐링, 라이프스타일 브랜드에 관심있는 탐험형 고객",
        "tier": "mid",

        # 페르소나 클러스터 정보
        "persona_cluster": "웰니스 힐링 탐험가",
        "persona_confidence": 0.88,

        # 행동 데이터
        "activity": {
            "last_visit_days_ago": 7,
            "visit_frequency": "낮음",
            "avg_session_minutes": 6,
            "signup_days_ago": 160
        },

        "purchase": {
            "total_count": 26,
            "last_purchase_days_ago": 14,
            "avg_interval": 36,
            "total_amount": 1111084,
            "avg_amount": 42734,
            "recent_categories": ["립"]
        },

        "brand": {
            "purchase_counts": {
                "오설록": 10,
                "해피바스": 8,
                "롱테이크": 5,
                "라네즈": 3
            },
            "primary_brand": "오설록",
            "loyalty": "중간",
            "diversity": 0.42
        },

        "promotion": {
            "discount_sensitivity": "중간",
            "event_participation_rate": 0.76,
            "preferred_type": "포인트",
            "coupon_usage_rate": 0.48,
            "full_price_ratio": 0.38
        },

        "risk": {
            "level": "중간",
            "factors": [],
            "churn_probability": 0.25
        },

        "seasonal": {
            "gift_purchases": True,
            "peak_seasons": [],
            "seasonal_events": []
        },

        "membership": {
            "tier": "VIP",
            "tier_criteria": "E등급",
            "points": 30000
        }
    },

    # ===== 페르소나 4: 정지호 (28세) - 연구소 기반 해결사 =====
    {
        "id": 4,
        "name": "정지호",
        "display_name": "정지호(28세)",
        "age": 28,
        "skin_type": "복합성",
        "concerns": ["보습"],
        "interests": ["스킨케어", "더마케어", "세트"],
        "shopping_pattern": "성분과 효능 중시, 문제 해결형 구매, 꼼꼼한 비교",
        "lifestyle": "피부 고민 해결을 위해 과학적/더마 브랜드를 선호하는 고객",
        "tier": "mid",

        # 페르소나 클러스터 정보
        "persona_cluster": "연구소 기반 해결사",
        "persona_confidence": 0.85,

        # 행동 데이터 - 온보딩 (신규 고객)
        "activity": {
            "last_visit_days_ago": 3,
            "visit_frequency": "중간",
            "avg_session_minutes": 11,
            "signup_days_ago": 45  # 신규 가입 90일 이하
        },

        "purchase": {
            "total_count": 2,  # 구매 5회 미만
            "last_purchase_days_ago": 7,
            "avg_interval": 21,
            "total_amount": 100904,
            "avg_amount": 50452,
            "recent_categories": ["클렌징", "스킨케어"]
        },

        "brand": {
            "purchase_counts": {
                "마몽드": 4,
                "아이오페": 3,
                "에스트라": 2,
                "프리메라": 1
            },
            "primary_brand": "마몽드",
            "loyalty": "높음",
            "diversity": 0.33
        },

        "promotion": {
            "discount_sensitivity": "중간",
            "event_participation_rate": 0.56,
            "preferred_type": "사은품",
            "coupon_usage_rate": 0.33,
            "full_price_ratio": 0.56
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
            "tier": "VIP",
            "tier_criteria": "E등급",
            "points": 15000
        }
    },

    # ===== 페르소나 5: 신수진 (20세) - 트렌디 Z세대 =====
    {
        "id": 5,
        "name": "신수진",
        "display_name": "신수진(20세)",
        "age": 20,
        "skin_type": "복합성",
        "concerns": ["보습"],
        "interests": ["메이크업", "향수", "바디"],
        "shopping_pattern": "트렌디한 제품 선호, 가성비 중시, 이벤트 참여 활발",
        "lifestyle": "트렌드에 민감한 MZ세대, SNS 영향력이 큰 활발한 소비자",
        "tier": "affordable",

        # 페르소나 클러스터 정보
        "persona_cluster": "트렌디 Z세대",
        "persona_confidence": 0.95,

        # 행동 데이터 - 재활성화 (이탈 위험)
        "activity": {
            "last_visit_days_ago": 60,
            "visit_frequency": "중간",
            "avg_session_minutes": 20,
            "signup_days_ago": 165
        },

        "purchase": {
            "total_count": 41,
            "last_purchase_days_ago": 120,  # 오래된 구매
            "avg_interval": 45,
            "total_amount": 1307326,
            "avg_amount": 31886,
            "recent_categories": ["립", "스킨케어"]
        },

        "brand": {
            "purchase_counts": {
                "롱테이크": 15,
                "에뛰드": 12,
                "헤라": 8,
                "설화수": 6
            },
            "primary_brand": "롱테이크",
            "loyalty": "낮음",
            "diversity": 0.74
        },

        "promotion": {
            "discount_sensitivity": "낮음",
            "event_participation_rate": 0.89,
            "preferred_type": "샘플",
            "coupon_usage_rate": 0.26,
            "full_price_ratio": 0.43
        },

        "risk": {
            "level": "높음",
            "factors": ["충성도 낮음", "장기 미방문"],
            "churn_probability": 0.65  # 재활성화 조건 충족 (35% 이상)
        },

        "seasonal": {
            "gift_purchases": True,
            "peak_seasons": ["여름"],
            "seasonal_events": []
        },

        "membership": {
            "tier": "브론즈",
            "tier_criteria": "B등급",
            "points": 35000
        }
    },

    # ===== 페르소나 6: 장수빈 (25세) - 합리적 큐레이터 =====
    {
        "id": 6,
        "name": "장수빈",
        "display_name": "장수빈(25세)",
        "age": 25,
        "skin_type": "복합성",
        "concerns": ["보습"],
        "interests": ["스킨케어", "헤어", "바디"],
        "shopping_pattern": "가성비 중시, 리뷰 꼼꼼히 확인, 다양한 브랜드 시도",
        "lifestyle": "합리적인 가격대에서 좋은 품질을 추구하는 똑똑한 소비자",
        "tier": "mid",

        # 페르소나 클러스터 정보
        "persona_cluster": "합리적 큐레이터",
        "persona_confidence": 0.87,

        # 행동 데이터 - 전환유도 (구매주기 도래)
        "activity": {
            "last_visit_days_ago": 5,
            "visit_frequency": "중간",
            "avg_session_minutes": 13,
            "signup_days_ago": 108
        },

        "purchase": {
            "total_count": 18,
            "last_purchase_days_ago": 18,  # 구매주기 90% 도래 (18/20=0.9)
            "avg_interval": 20,
            "total_amount": 1217502,
            "avg_amount": 67639,
            "recent_categories": ["메이크업", "선케어"]
        },

        "brand": {
            "purchase_counts": {
                "라보에이치": 6,
                "라네즈": 5,
                "아이오페": 4,
                "이니스프리": 3
            },
            "primary_brand": "라보에이치",
            "loyalty": "높음",
            "diversity": 0.24
        },

        "promotion": {
            "discount_sensitivity": "중간",
            "event_participation_rate": 0.79,
            "preferred_type": "사은품",
            "coupon_usage_rate": 0.14,
            "full_price_ratio": 0.54
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.05
        },

        "seasonal": {
            "gift_purchases": False,
            "peak_seasons": [],
            "seasonal_events": []
        },

        "membership": {
            "tier": "골드",
            "tier_criteria": "D등급",
            "points": 85000
        }
    },

    # ===== 페르소나 7: 류예린 (31세) - 실속형 가계 수호자 =====
    {
        "id": 7,
        "name": "류예린",
        "display_name": "류예린(31세)",
        "age": 31,
        "skin_type": "복합성",
        "concerns": ["보습"],
        "interests": ["바디", "생활용품", "헤어케어"],
        "shopping_pattern": "할인/쿠폰 적극 활용, 대용량 선호, 사은품 중시",
        "lifestyle": "가족용 생활용품 중심 구매, 할인/쿠폰에 민감한 알뜰 소비자",
        "tier": "affordable",

        # 페르소나 클러스터 정보
        "persona_cluster": "실속형 가계 수호자",
        "persona_confidence": 0.93,

        # 행동 데이터 - 온보딩 (신규 고객)
        "activity": {
            "last_visit_days_ago": 2,
            "visit_frequency": "낮음",
            "avg_session_minutes": 7,
            "signup_days_ago": 30  # 신규 가입 90일 이하
        },

        "purchase": {
            "total_count": 3,  # 구매 5회 미만
            "last_purchase_days_ago": 5,
            "avg_interval": 26,
            "total_amount": 102429,
            "avg_amount": 34143,
            "recent_categories": ["클렌징", "헤어케어"]
        },

        "brand": {
            "purchase_counts": {
                "해피바스": 18,
                "롱테이크": 10,
                "미쟝센": 8,
                "이니스프리": 5
            },
            "primary_brand": "해피바스",
            "loyalty": "높음",
            "diversity": 0.15
        },

        "promotion": {
            "discount_sensitivity": "높음",
            "event_participation_rate": 0.86,
            "preferred_type": "할인",
            "coupon_usage_rate": 0.62,
            "full_price_ratio": 0.26
        },

        "risk": {
            "level": "낮음",
            "factors": [],
            "churn_probability": 0.10
        },

        "seasonal": {
            "gift_purchases": False,
            "peak_seasons": [],
            "seasonal_events": []
        },

        "membership": {
            "tier": "브론즈",
            "tier_criteria": "B등급",
            "points": 45000
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
