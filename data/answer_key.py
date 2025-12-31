# -*- coding: utf-8 -*-
"""
원본 21개 페르소나 정답 레이블
============================
수동 라벨링 기준 (페르소나 특성 분석 기반)
"""

ANSWER_KEY = {
    # 1. 민지 (25세) - 활성, 가성비, 쿠폰80%, 할인민감도 높음
    1: {
        "primary": "promotion",
        "correct_purposes": ["promotion", "repurchase"],
        "reasoning": "쿠폰사용률 80%, 할인민감도 높음, 정가구매 20%만"
    },

    # 2. 서연 (32세) - VIP, 설화수 충성, 구매주기 93% 도래 (42/45일)
    2: {
        "primary": "repurchase",
        "correct_purposes": ["repurchase", "best_curation"],
        "reasoning": "구매주기 93% 도래, 높은 브랜드 충성도"
    },

    # 3. 수빈 (28세) - 민감성, 신제품_얼리어답터 태그, 신제품샘플 선호
    3: {
        "primary": "new_product",
        "correct_purposes": ["new_product", "best_curation"],
        "reasoning": "behavior_tags: 신제품_얼리어답터, preferred_type: 샘플"
    },

    # 4. 지현 (45세) - VVIP, 설화수 충성도 매우 높음, 정가구매 90%
    4: {
        "primary": "best_curation",
        "correct_purposes": ["best_curation", "seasonal_gift"],
        "reasoning": "충성도 높음, 정가구매 90%, VVIP, 선물구매 있음"
    },

    # 5. 하늘 (22세) - 신규(60일), 쿠폰90%, 할인민감 높음
    5: {
        "primary": "promotion",
        "correct_purposes": ["promotion", "new_product"],
        "reasoning": "신규고객이지만 쿠폰의존 90%, 할인민감도 높음"
    },

    # 6. 예린 (35세) - ★ 휴면위험! churn 72%, 75일 미구매, 접속 45일 전
    6: {
        "primary": "churn_prevention",
        "correct_purposes": ["churn_prevention"],
        "reasoning": "이탈확률 72%, 구매주기 2배 초과, 접속감소"
    },

    # 7. 소희 (38세) - VVIP, 선물구매자, 선물세트 선호, 시즌 구매
    7: {
        "primary": "best_curation",
        "correct_purposes": ["best_curation", "seasonal_gift"],
        "reasoning": "충성도 높음, VVIP, 정기구매자, 선물구매도 함"
    },

    # 8. 유나 (27세) - 신제품_관심 태그, 브랜드 다양성 85%, 신제품샘플 선호
    8: {
        "primary": "new_product",
        "correct_purposes": ["new_product", "promotion"],
        "reasoning": "behavior_tags: 신제품_관심, diversity 85%, 신제품샘플 선호"
    },

    # 9. 다은 (30세) - 모든 지표 중간, 구매주기 80% 도래
    9: {
        "primary": "repurchase",
        "correct_purposes": ["repurchase", "new_product", "promotion"],
        "reasoning": "구매주기 80% 도래, 다른 특징 없음"
    },

    # 10. 채원 (42세) - 프리미엄인데 할인의존, 쿠폰90%, 정가15%
    10: {
        "primary": "promotion",
        "correct_purposes": ["promotion", "repurchase"],
        "reasoning": "쿠폰사용률 90%, 정가구매 15%만, 세일_헌터 태그"
    },

    # 11. 은서 (24세) - 급성장 고객, 브랜드 충성 형성, 정가구매 70%
    11: {
        "primary": "repurchase",
        "correct_purposes": ["repurchase", "best_curation"],
        "reasoning": "급성장 고객, 짧은 구매주기(12일), 충성도 형성 중"
    },

    # 12. 지수 (29세) - 접속O 구매X, churn 45%, 할인민감 높음
    12: {
        "primary": "promotion",
        "correct_purposes": ["promotion", "churn_prevention"],
        "reasoning": "윈도우쇼퍼, 할인민감도 높음, 쿠폰80%로 전환 유도"
    },

    # 13. 현아 (33세) - ★ 이탈위험! churn 65%, 경쟁사_관심
    13: {
        "primary": "churn_prevention",
        "correct_purposes": ["churn_prevention", "promotion"],
        "reasoning": "이탈확률 65%, 경쟁사 이탈 위험, 접속/구매 감소"
    },

    # 14. 나연 (48세) - 선물 전문 구매자 90%, VVIP, 시즌 구매
    14: {
        "primary": "seasonal_gift",
        "correct_purposes": ["seasonal_gift", "best_curation"],
        "reasoning": "선물구매비율 90%, 시즌 구매자, 명절/크리스마스 집중"
    },

    # 15. 미주 (26세) - 인플루언서, 신제품 매니아, 정가구매 80%
    15: {
        "primary": "new_product",
        "correct_purposes": ["new_product"],
        "reasoning": "신제품_매니아 태그, 트렌드_리더, 발매일 구매"
    },

    # 16. 윤정 (39세) - 휴면복귀 직후, churn 35%, 재이탈 주의
    16: {
        "primary": "best_curation",
        "correct_purposes": ["best_curation", "repurchase"],
        "reasoning": "휴면복귀 후 방금 구매, 충성도 높음, 재정착 유도"
    },

    # 17. 서아 (21세) - 초저가, 쿠폰 100%, 정가구매 0%
    17: {
        "primary": "promotion",
        "correct_purposes": ["promotion"],
        "reasoning": "쿠폰의존 100%, 정가구매 0%, 초저가_고객 태그"
    },

    # 18. 혜진 (37세) - 멀티채널, 오프라인 선호, VIP
    18: {
        "primary": "best_curation",
        "correct_purposes": ["best_curation", "seasonal_gift"],
        "reasoning": "충성도 높음, 오프라인 병행, VIP, 정가구매 90%"
    },

    # 19. 소연 (31세) - 복합니즈, 다양한 브랜드, 쿠폰60%
    19: {
        "primary": "new_product",
        "correct_purposes": ["new_product", "promotion"],
        "reasoning": "브랜드 다양성 65%, 복합_니즈, 멀티_카테고리"
    },

    # 20. 정은 (52세) - VVIP, 재구매 위주, 구매주기 95% 도래
    20: {
        "primary": "repurchase",
        "correct_purposes": ["repurchase", "best_curation"],
        "reasoning": "구매주기 95% 도래, 재구매_위주 태그, VVIP"
    },

    # 21. 소희 (24세) - ★ 신규 25일, 첫구매 1회, 온보딩 대상
    21: {
        "primary": "promotion",
        "correct_purposes": ["promotion", "new_product"],
        "reasoning": "신규가입 25일, 첫구매만 완료, 온보딩_대상 태그, 쿠폰으로 2차구매 유도"
    },
}

# 정답 요약
def summarize():
    from collections import Counter
    primaries = [v["primary"] for v in ANSWER_KEY.values()]
    counts = Counter(primaries)

    print("원본 21개 페르소나 정답 분포:")
    for purpose, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {purpose}: {count}명 ({count/21*100:.1f}%)")

if __name__ == "__main__":
    summarize()
