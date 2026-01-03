# -*- coding: utf-8 -*-
"""
발신목적 추천기 (AI 기반)
- 고객 페르소나와 행동 데이터를 기반으로 최적의 발신 목적 추천
"""

class PurposeRecommender:
    """발신목적 추천기"""

    def __init__(self, api_key=None):
        self.api_key = api_key

        # 페르소나 클러스터별 추천 발신 목적
        self.persona_purpose_map = {
            "하이엔드 품격가": {
                "primary": "best_curation",
                "secondary": ["new_product", "seasonal_gift"],
                "reason": "프리미엄 브랜드 충성 고객으로 베스트 큐레이션 및 신제품에 관심"
            },
            "트렌디 Z세대": {
                "primary": "new_product",
                "secondary": ["promotion", "best_curation"],
                "reason": "트렌드에 민감하여 신제품과 프로모션에 높은 반응"
            },
            "테크니컬 홈케어족": {
                "primary": "new_product",
                "secondary": ["best_curation", "repurchase"],
                "reason": "기술 기반 신제품에 관심이 높고 재구매율도 높음"
            },
            "실속형 가계 수호자": {
                "primary": "promotion",
                "secondary": ["repurchase", "best_curation"],
                "reason": "할인과 프로모션에 민감하며 재구매 주기가 짧음"
            },
            "합리적 큐레이터": {
                "primary": "best_curation",
                "secondary": ["promotion", "repurchase"],
                "reason": "가성비 좋은 베스트 상품과 합리적 프로모션 선호"
            },
            "연구소 기반 해결사": {
                "primary": "new_product",
                "secondary": ["best_curation", "repurchase"],
                "reason": "피부 고민 해결을 위한 신제품과 효능 검증된 제품 선호"
            },
            "웰니스 힐링 탐험가": {
                "primary": "new_product",
                "secondary": ["seasonal_gift", "best_curation"],
                "reason": "새로운 경험과 웰니스 관련 시즌 제품에 관심"
            }
        }

        # 발신 목적 이름 매핑
        self.purpose_names = {
            "promotion": "프로모션",
            "new_product": "신제품 안내",
            "best_curation": "베스트 큐레이션",
            "repurchase": "재구매 & 리텐션",
            "churn_prevention": "휴면 방지",
            "seasonal_gift": "선물 & 시즌"
        }

    def recommend_purpose(self, persona):
        """
        고객 페르소나 기반 발신 목적 추천

        Args:
            persona: dict 형태의 페르소나 데이터

        Returns:
            dict: 추천 결과
        """
        # 페르소나 클러스터 확인
        persona_cluster = persona.get('persona_cluster', '')

        # 이탈 위험 확인
        risk = persona.get('risk', {})
        risk_level = risk.get('level', '낮음')
        churn_prob = risk.get('churn_probability', 0)

        # 이탈 위험이 높으면 휴면 방지 우선
        if risk_level == "높음" or churn_prob > 0.3:
            return {
                "recommended_purpose": "churn_prevention",
                "purpose_name": self.purpose_names["churn_prevention"],
                "confidence": 0.9,
                "reasoning": f"이탈 위험도가 높음({churn_prob*100:.0f}%)으로 휴면 방지 메시지 권장",
                "key_factors": ["이탈위험", f"위험도_{risk_level}"],
                "alternative_purposes": ["promotion", "repurchase"]
            }

        # 페르소나 클러스터 기반 추천
        if persona_cluster in self.persona_purpose_map:
            mapping = self.persona_purpose_map[persona_cluster]
            primary = mapping["primary"]

            return {
                "recommended_purpose": primary,
                "purpose_name": self.purpose_names.get(primary, primary),
                "confidence": 0.85,
                "reasoning": mapping["reason"],
                "key_factors": [persona_cluster, f"충성도_{persona.get('brand', {}).get('loyalty', '중')}"],
                "alternative_purposes": mapping["secondary"]
            }

        # 기본 추천: 프로모션
        return {
            "recommended_purpose": "promotion",
            "purpose_name": self.purpose_names["promotion"],
            "confidence": 0.6,
            "reasoning": "기본 추천: 프로모션 메시지",
            "key_factors": [],
            "alternative_purposes": ["best_curation", "new_product"]
        }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    # 테스트
    recommender = PurposeRecommender()

    # 테스트 페르소나
    test_persona = {
        "display_name": "김서연(42세)",
        "persona_cluster": "하이엔드 품격가",
        "brand": {"loyalty": "높음"},
        "risk": {"level": "낮음", "churn_probability": 0.08}
    }

    result = recommender.recommend_purpose(test_persona)
    print(f"추천 발신 목적: {result['purpose_name']}")
    print(f"신뢰도: {result['confidence']*100:.0f}%")
    print(f"이유: {result['reasoning']}")
