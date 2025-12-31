# -*- coding: utf-8 -*-
"""
ML 학습용 페르소나 정답 레이블 (수동 라벨링)
===========================================
100개 페르소나(ID 21~120)에 대한 발신목적 정답

라벨링 기준:
1. churn_prevention: 이탈위험 높음, 접속감소, 구매중단
2. repurchase: 재구매 위주 쇼핑, 루틴고객, 단골
3. seasonal_gift: 선물 위주 쇼핑, 선물구매비율 높음
4. promotion: 할인민감도 높음, 쿠폰의존, 세일대기
5. new_product: 신제품 선호, 얼리어답터, 트렌드민감
6. best_curation: 브랜드충성도 높음, 프리미엄선호, 정가구매
"""

# 발신목적 레이블
# primary: 최적 발신목적 (1개)
# alternatives: 대안 발신목적 (0~2개)

ML_ANSWER_KEY = {
    # === ID 21~37: 할인 민감 고객군 (promotion) ===
    21: {"primary": "promotion", "alternatives": ["repurchase"], "reason": "쿠폰사용률 78%, 할인민감도 높음, behavior_tags: 할인_민감/쿠폰_의존/세일_대기"},
    22: {"primary": "promotion", "alternatives": [], "reason": "할인민감도 매우높음, 쿠폰사용률 66%, behavior_tags: 할인_민감/가격_비교"},
    23: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 80%, 할인민감도 매우높음, behavior_tags: 쿠폰_의존/세일_대기/가격_비교"},
    24: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 91%, 할인민감도 매우높음, behavior_tags: 가격_비교/세일_대기"},
    25: {"primary": "promotion", "alternatives": [], "reason": "할인민감도 매우높음, 쿠폰사용률 67%, behavior_tags: 가격_비교/쿠폰_의존"},
    26: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 77%, 할인민감도 높음, behavior_tags: 할인_민감/쿠폰_의존"},
    27: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 91%, 할인민감도 매우높음, behavior_tags: 할인_민감/세일_대기/가격_비교"},
    28: {"primary": "promotion", "alternatives": ["repurchase"], "reason": "쿠폰사용률 69%, 할인민감도 높음, behavior_tags: 할인_민감/가격_비교/세일_대기"},
    29: {"primary": "promotion", "alternatives": [], "reason": "할인민감도 매우높음, 쿠폰사용률 61%, behavior_tags: 할인_민감/가격_비교"},
    30: {"primary": "promotion", "alternatives": ["new_product"], "reason": "할인민감도 매우높음, diversity 높음, behavior_tags: 할인_민감/세일_대기"},
    31: {"primary": "promotion", "alternatives": ["repurchase"], "reason": "쿠폰사용률 60%, 할인민감도 높음, behavior_tags: 가격_비교/쿠폰_의존"},
    32: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 95%, 할인민감도 매우높음, behavior_tags: 세일_대기/쿠폰_의존/할인_민감"},
    33: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 71%, 할인민감도 매우높음, behavior_tags: 세일_대기/쿠폰_의존/할인_민감"},
    34: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 89%, 할인민감도 높음, behavior_tags: 쿠폰_의존/할인_민감"},
    35: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 61%, 할인민감도 높음, behavior_tags: 세일_대기/할인_민감"},
    36: {"primary": "promotion", "alternatives": ["new_product"], "reason": "쿠폰사용률 76%, diversity 높음, behavior_tags: 가격_비교/세일_대기/할인_민감"},
    37: {"primary": "promotion", "alternatives": [], "reason": "쿠폰사용률 89%, 할인민감도 높음, behavior_tags: 쿠폰_의존/할인_민감"},

    # === ID 38~54: 신제품 선호 고객군 (new_product) ===
    38: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, preferred_type: 신제품샘플, behavior_tags: 신제품_관심/트렌드_민감/얼리어답터"},
    39: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, preferred_type: 신제품샘플, behavior_tags: 리뷰_작성/신제품_관심"},
    40: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, diversity 94%, behavior_tags: 신제품_관심/얼리어답터"},
    41: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 66%, behavior_tags: 리뷰_작성/트렌드_민감/얼리어답터"},
    42: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, preferred_type: 신제품샘플, behavior_tags: 신제품_관심/얼리어답터"},
    43: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 64%, behavior_tags: 얼리어답터/리뷰_작성"},
    44: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, preferred_type: 신제품샘플, behavior_tags: 얼리어답터/리뷰_작성/트렌드_민감"},
    45: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 76%, behavior_tags: 트렌드_민감/얼리어답터/리뷰_작성"},
    46: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, VIP 멤버십, behavior_tags: 리뷰_작성/트렌드_민감"},
    47: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 66%, behavior_tags: 트렌드_민감/리뷰_작성/신제품_관심"},
    48: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 63%, behavior_tags: 리뷰_작성/신제품_관심/얼리어답터"},
    49: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 63%, behavior_tags: 트렌드_민감/리뷰_작성"},
    50: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 69%, behavior_tags: 얼리어답터/리뷰_작성"},
    51: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 67%, behavior_tags: 리뷰_작성/신제품_관심/얼리어답터"},
    52: {"primary": "new_product", "alternatives": [], "reason": "shopping_pattern: 신제품 선호, preferred_type: 신제품샘플, behavior_tags: 리뷰_작성/신제품_관심/얼리어답터"},
    53: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 65%, behavior_tags: 리뷰_작성/트렌드_민감/얼리어답터"},
    54: {"primary": "new_product", "alternatives": ["best_curation"], "reason": "shopping_pattern: 신제품 선호, full_price_ratio 68%, behavior_tags: 얼리어답터/리뷰_작성"},

    # === ID 55~71: 프리미엄/충성 고객군 (best_curation) ===
    55: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 매우높음, full_price_ratio 79%, VVIP, behavior_tags: 브랜드_충성/정가_구매"},
    56: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 높음, full_price_ratio 75%, 설화수 VIP, behavior_tags: 프리미엄_선호/품질_중시"},
    57: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 높음, full_price_ratio 75%, VVIP, behavior_tags: 정가_구매/프리미엄_선호"},
    58: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 매우높음, full_price_ratio 64%, 설화수 VVIP, behavior_tags: 프리미엄_선호/정가_구매"},
    59: {"primary": "best_curation", "alternatives": [], "reason": "loyalty 높음, full_price_ratio 80%, VIP, behavior_tags: 프리미엄_선호/브랜드_충성/정가_구매"},
    60: {"primary": "best_curation", "alternatives": [], "reason": "loyalty 매우높음, full_price_ratio 77%, VVIP, behavior_tags: 프리미엄_선호/품질_중시/브랜드_충성"},
    61: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 매우높음, full_price_ratio 65%, 설화수 VIP, behavior_tags: 브랜드_충성/품질_중시/정가_구매"},
    62: {"primary": "best_curation", "alternatives": [], "reason": "loyalty 높음, full_price_ratio 80%, VVIP, behavior_tags: 브랜드_충성/정가_구매/프리미엄_선호"},
    63: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 높음, full_price_ratio 76%, VIP, behavior_tags: 정가_구매/브랜드_충성/프리미엄_선호"},
    64: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 매우높음, full_price_ratio 67%, VIP, behavior_tags: 품질_중시/브랜드_충성/정가_구매"},
    65: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 높음, full_price_ratio 77%, VIP, behavior_tags: 브랜드_충성/품질_중시/정가_구매"},
    66: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 높음, full_price_ratio 78%, VIP, behavior_tags: 프리미엄_선호/품질_중시"},
    67: {"primary": "best_curation", "alternatives": [], "reason": "loyalty 높음, full_price_ratio 90%, VVIP, behavior_tags: 브랜드_충성/프리미엄_선호"},
    68: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 높음, full_price_ratio 63%, VIP, behavior_tags: 품질_중시/정가_구매"},
    69: {"primary": "best_curation", "alternatives": ["repurchase"], "reason": "loyalty 높음, full_price_ratio 85%, VIP, behavior_tags: 정가_구매/브랜드_충성"},
    70: {"primary": "best_curation", "alternatives": [], "reason": "loyalty 높음, full_price_ratio 69%, VIP, behavior_tags: 정가_구매/브랜드_충성"},
    71: {"primary": "best_curation", "alternatives": [], "reason": "loyalty 매우높음, full_price_ratio 83%, VIP, behavior_tags: 브랜드_충성/정가_구매/품질_중시"},

    # === ID 72~88: 재구매/루틴 고객군 (repurchase) ===
    72: {"primary": "repurchase", "alternatives": ["best_curation"], "reason": "shopping_pattern: 재구매 위주, loyalty 높음, behavior_tags: 루틴_고객/단골/제품_충성"},
    73: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 높음, behavior_tags: 재구매_패턴/루틴_고객"},
    74: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 재구매_패턴/단골"},
    75: {"primary": "repurchase", "alternatives": ["best_curation"], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 루틴_고객/제품_충성"},
    76: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 단골/제품_충성"},
    77: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 제품_충성/재구매_패턴"},
    78: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 루틴_고객/재구매_패턴/제품_충성"},
    79: {"primary": "repurchase", "alternatives": ["best_curation"], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 단골/제품_충성/루틴_고객"},
    80: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 높음, behavior_tags: 재구매_패턴/제품_충성/단골"},
    81: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 제품_충성/재구매_패턴"},
    82: {"primary": "repurchase", "alternatives": ["best_curation"], "reason": "shopping_pattern: 재구매 위주, full_price_ratio 69%, behavior_tags: 재구매_패턴/제품_충성"},
    83: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 높음, behavior_tags: 단골/제품_충성/루틴_고객"},
    84: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 루틴_고객/단골/재구매_패턴"},
    85: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 루틴_고객/단골"},
    86: {"primary": "repurchase", "alternatives": ["best_curation"], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, 설화수 VIP, behavior_tags: 루틴_고객/단골"},
    87: {"primary": "repurchase", "alternatives": ["best_curation"], "reason": "shopping_pattern: 재구매 위주, loyalty 높음, full_price_ratio 69%, behavior_tags: 루틴_고객/재구매_패턴/제품_충성"},
    88: {"primary": "repurchase", "alternatives": [], "reason": "shopping_pattern: 재구매 위주, loyalty 매우높음, behavior_tags: 제품_충성/재구매_패턴"},

    # === ID 89~104: 이탈 위험 고객군 (churn_prevention) ===
    89: {"primary": "churn_prevention", "alternatives": ["promotion"], "reason": "risk.level: 높음, churn_probability 82%, behavior_tags: 경쟁사_관심/접속_감소/이탈_위험"},
    90: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 높음, churn_probability 74%, last_purchase 72일 전, behavior_tags: 구매_중단/이탈_위험"},
    91: {"primary": "churn_prevention", "alternatives": ["promotion"], "reason": "risk.level: 매우높음, churn_probability 52%, last_purchase 54일 전, behavior_tags: 구매_중단/경쟁사_관심"},
    92: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 매우높음, churn_probability 84%, last_purchase 52일 전, behavior_tags: 경쟁사_관심/이탈_위험"},
    93: {"primary": "churn_prevention", "alternatives": ["promotion"], "reason": "risk.level: 매우높음, churn_probability 52%, last_purchase 67일 전, behavior_tags: 구매_중단/경쟁사_관심/접속_감소"},
    94: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 높음, churn_probability 63%, last_purchase 90일 전, behavior_tags: 접속_감소/이탈_위험/경쟁사_관심"},
    95: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 매우높음, churn_probability 71%, last_purchase 85일 전, behavior_tags: 경쟁사_관심/이탈_위험/접속_감소"},
    96: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 매우높음, churn_probability 68%, last_purchase 68일 전, behavior_tags: 구매_중단/접속_감소/경쟁사_관심"},
    97: {"primary": "churn_prevention", "alternatives": ["promotion"], "reason": "risk.level: 높음, churn_probability 71%, last_purchase 52일 전, behavior_tags: 접속_감소/이탈_위험"},
    98: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 높음, churn_probability 64%, last_purchase 52일 전, behavior_tags: 경쟁사_관심/접속_감소/이탈_위험"},
    99: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 매우높음, churn_probability 63%, last_purchase 74일 전, behavior_tags: 경쟁사_관심/접속_감소"},
    100: {"primary": "churn_prevention", "alternatives": ["promotion"], "reason": "risk.level: 높음, churn_probability 70%, last_purchase 70일 전, behavior_tags: 접속_감소/경쟁사_관심"},
    101: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 매우높음, churn_probability 83%, last_purchase 88일 전, behavior_tags: 접속_감소/이탈_위험"},
    102: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 높음, churn_probability 77%, last_purchase 70일 전, behavior_tags: 구매_중단/이탈_위험/경쟁사_관심"},
    103: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 높음, churn_probability 77%, last_purchase 59일 전, behavior_tags: 경쟁사_관심/접속_감소"},
    104: {"primary": "churn_prevention", "alternatives": [], "reason": "risk.level: 높음, churn_probability 71%, last_purchase 86일 전, behavior_tags: 경쟁사_관심/접속_감소"},

    # === ID 105~120: 선물 구매 고객군 (seasonal_gift) ===
    105: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 92%, 설화수 골드, behavior_tags: 명절_구매/세트_선호/고가_선물"},
    106: {"primary": "seasonal_gift", "alternatives": [], "reason": "shopping_pattern: 선물 위주, gift_ratio 84%, 설화수 골드, behavior_tags: 선물_전문/세트_선호"},
    107: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 88%, loyalty 높음, behavior_tags: 명절_구매/선물_전문/고가_선물"},
    108: {"primary": "seasonal_gift", "alternatives": [], "reason": "shopping_pattern: 선물 위주, gift_ratio 71%, preferred_type: 사은품, behavior_tags: 세트_선호/명절_구매/선물_전문"},
    109: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 87%, 설화수 골드, behavior_tags: 선물_전문/명절_구매/세트_선호"},
    110: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 89%, full_price_ratio 68%, behavior_tags: 고가_선물/선물_전문/세트_선호"},
    111: {"primary": "seasonal_gift", "alternatives": [], "reason": "shopping_pattern: 선물 위주, gift_ratio 88%, loyalty 높음, behavior_tags: 세트_선호/선물_전문"},
    112: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 85%, full_price_ratio 84%, behavior_tags: 세트_선호/선물_전문"},
    113: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 76%, loyalty 높음, behavior_tags: 고가_선물/세트_선호/명절_구매"},
    114: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 80%, full_price_ratio 78%, behavior_tags: 선물_전문/세트_선호/고가_선물"},
    115: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 86%, full_price_ratio 89%, behavior_tags: 명절_구매/선물_전문"},
    116: {"primary": "seasonal_gift", "alternatives": [], "reason": "shopping_pattern: 선물 위주, gift_ratio 74%, full_price_ratio 76%, behavior_tags: 고가_선물/명절_구매"},
    117: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 88%, loyalty 높음, behavior_tags: 명절_구매/세트_선호/선물_전문"},
    118: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 72%, loyalty 높음, behavior_tags: 명절_구매/세트_선호/선물_전문"},
    119: {"primary": "seasonal_gift", "alternatives": [], "reason": "shopping_pattern: 선물 위주, gift_ratio 77%, preferred_type: 선물포장, behavior_tags: 세트_선호/명절_구매"},
    120: {"primary": "seasonal_gift", "alternatives": ["best_curation"], "reason": "shopping_pattern: 선물 위주, gift_ratio 76%, full_price_ratio 81%, preferred_type: 선물포장"},
}


def get_label_distribution():
    """레이블 분포 통계"""
    from collections import Counter
    primary_counts = Counter(v["primary"] for v in ML_ANSWER_KEY.values())
    return dict(primary_counts)


def get_label_for_persona(persona_id: int) -> dict:
    """페르소나 ID로 레이블 조회"""
    return ML_ANSWER_KEY.get(persona_id, None)


if __name__ == "__main__":
    print("=" * 60)
    print("ML 학습용 정답 레이블 통계")
    print("=" * 60)

    dist = get_label_distribution()
    total = len(ML_ANSWER_KEY)

    print(f"\n총 {total}개 페르소나 라벨링 완료\n")
    print("발신목적별 분포:")
    for purpose, count in sorted(dist.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {purpose:20s}: {count:3d}개 ({pct:5.1f}%)")

    print("\n" + "=" * 60)
