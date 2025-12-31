# -*- coding: utf-8 -*-
"""
발신목적 추천 시스템
====================
ML 기반 분류 (무료, 빠름, 정확도 높음)
LLM 폴백 옵션 (유료, API 필요)
"""
import os
import sys
from typing import Optional

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ML 분류기 임포트
from ml.ml_classifier import MLPurposeClassifier


class PurposeRecommender:
    """발신 목적 추천 (ML 기반)"""

    PURPOSE_NAMES = {
        "promotion": "프로모션",
        "new_product": "신제품 안내",
        "best_curation": "베스트 큐레이션",
        "repurchase": "재구매 & 리텐션",
        "churn_prevention": "휴면 방지",
        "seasonal_gift": "선물 & 시즌"
    }

    def __init__(self, api_key: str = None, use_llm: bool = False, model: str = None):
        """
        Args:
            api_key: HuggingFace API 키 (LLM 사용시만 필요)
            use_llm: LLM 사용 여부 (기본: False = ML 사용)
            model: LLM 모델명 (LLM 사용시)
        """
        self.use_llm = use_llm
        self.api_key = api_key

        # ML 분류기 초기화
        self.ml_classifier = MLPurposeClassifier()

        # 모델 파일 존재 확인
        model_path = os.path.join(os.path.dirname(__file__), "purpose_model.pkl")
        if not os.path.exists(model_path):
            print("ML 모델이 없습니다. 학습을 먼저 실행하세요: python ml_classifier.py")

        # LLM 클라이언트 (옵션)
        self.llm_client = None
        if use_llm and api_key:
            try:
                from huggingface_hub import InferenceClient
                self.llm_client = InferenceClient(api_key=api_key)
                self.llm_model = model or "Qwen/Qwen2.5-7B-Instruct"
            except ImportError:
                print("huggingface_hub 설치 필요: pip install huggingface_hub")

    def recommend_purpose(self, persona: dict) -> dict:
        """
        페르소나 분석 → 발신 목적 추천

        Args:
            persona: 페르소나 데이터

        Returns:
            {
                "recommended_purpose": "purpose_id",
                "purpose_name": "발신목적명",
                "confidence": 0.0~1.0,
                "reasoning": "추천 이유",
                "alternative_purposes": ["대안1", "대안2"],
                "key_factors": ["핵심 판단 요소들"]
            }
        """
        # ML 분류기 사용 (기본)
        try:
            result = self.ml_classifier.predict(persona)
            result['method'] = 'ML'
            return result
        except FileNotFoundError:
            # 모델 파일 없으면 휴리스틱 폴백
            return self._fallback_recommendation(persona, "모델 파일 없음")
        except Exception as e:
            return self._fallback_recommendation(persona, str(e))

    def _fallback_recommendation(self, persona: dict, error: str) -> dict:
        """
        API/ML 실패 시 휴리스틱 기반 추천
        """
        risk = persona.get("risk", {})
        purchase = persona.get("purchase", {})
        promotion = persona.get("promotion", {})
        brand = persona.get("brand", {})
        seasonal = persona.get("seasonal", {})
        behavior_tags = persona.get("behavior_tags", [])

        # 1순위: 휴면 방지
        if risk.get("level") in ["높음", "매우 높음"] or risk.get("churn_probability", 0) >= 0.5:
            return {
                "recommended_purpose": "churn_prevention",
                "purpose_name": "휴면 방지",
                "confidence": 0.9,
                "reasoning": f"이탈 위험도 높음 (확률: {risk.get('churn_probability', 0)*100:.0f}%)",
                "alternative_purposes": ["promotion"],
                "key_factors": ["이탈위험", "접속감소"],
                "method": "heuristic",
                "fallback": True,
                "error": error
            }

        # 2순위: 재구매
        last_days = purchase.get("last_purchase_days_ago", 0)
        avg_interval = purchase.get("avg_interval", 30)
        cycle_ratio = last_days / avg_interval if avg_interval > 0 else 0

        if cycle_ratio >= 0.8:
            return {
                "recommended_purpose": "repurchase",
                "purpose_name": "재구매 & 리텐션",
                "confidence": 0.85,
                "reasoning": f"구매 주기 {cycle_ratio*100:.0f}% 도래",
                "alternative_purposes": ["best_curation"],
                "key_factors": ["구매주기", "재구매패턴"],
                "method": "heuristic",
                "fallback": True,
                "error": error
            }

        # 3순위: 선물/시즌
        gift_ratio = seasonal.get("gift_purchase_ratio", 0)
        if gift_ratio > 0.5:
            return {
                "recommended_purpose": "seasonal_gift",
                "purpose_name": "선물 & 시즌",
                "confidence": 0.8,
                "reasoning": f"선물 구매 비율 {gift_ratio*100:.0f}%",
                "alternative_purposes": ["best_curation"],
                "key_factors": ["선물구매", "시즌패턴"],
                "method": "heuristic",
                "fallback": True,
                "error": error
            }

        # 4순위: 할인 민감도 체크
        coupon_rate = promotion.get("coupon_usage_rate", 0)
        full_price = promotion.get("full_price_ratio", 0.5)
        discount_sens = promotion.get("discount_sensitivity", "중간")

        if coupon_rate > 0.6 or full_price < 0.3 or discount_sens in ["높음", "매우 높음"]:
            return {
                "recommended_purpose": "promotion",
                "purpose_name": "프로모션",
                "confidence": 0.8,
                "reasoning": f"할인 민감도 높음 (쿠폰 사용 {coupon_rate*100:.0f}%)",
                "alternative_purposes": ["new_product"],
                "key_factors": ["할인민감도", "쿠폰사용률"],
                "method": "heuristic",
                "fallback": True,
                "error": error
            }

        # 5순위: 신제품 관심
        tag_str = ' '.join(behavior_tags)
        diversity = brand.get("diversity", 0.5)
        if '신제품' in tag_str or '얼리' in tag_str or '트렌드' in tag_str or diversity > 0.6:
            return {
                "recommended_purpose": "new_product",
                "purpose_name": "신제품 안내",
                "confidence": 0.75,
                "reasoning": "신제품/트렌드 관심 높음",
                "alternative_purposes": ["best_curation"],
                "key_factors": ["신제품관심", "브랜드다양성"],
                "method": "heuristic",
                "fallback": True,
                "error": error
            }

        # 6순위: 충성도 높음 → 큐레이션
        loyalty = brand.get("loyalty", "중간")
        if loyalty in ["높음", "매우 높음"] or full_price > 0.6:
            return {
                "recommended_purpose": "best_curation",
                "purpose_name": "베스트 큐레이션",
                "confidence": 0.75,
                "reasoning": f"브랜드 충성도 {loyalty}, 정가 구매 {full_price*100:.0f}%",
                "alternative_purposes": ["repurchase"],
                "key_factors": ["브랜드충성도", "정가구매율"],
                "method": "heuristic",
                "fallback": True,
                "error": error
            }

        # 기본값: 프로모션
        return {
            "recommended_purpose": "promotion",
            "purpose_name": "프로모션",
            "confidence": 0.6,
            "reasoning": "범용 프로모션 추천",
            "alternative_purposes": ["new_product", "best_curation"],
            "key_factors": ["기본추천"],
            "method": "heuristic",
            "fallback": True,
            "error": error
        }


def test_recommender():
    """테스트 함수"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from data.personas import personas
    from answer_key import ANSWER_KEY

    print("=" * 60)
    print("발신목적 추천 테스트 (ML 기반)")
    print("=" * 60)

    recommender = PurposeRecommender()

    correct = 0
    primary = 0
    total = len(personas)

    for persona in personas:
        pid = persona['id']
        result = recommender.recommend_purpose(persona)
        predicted = result['recommended_purpose']

        answer = ANSWER_KEY.get(pid, {})
        correct_purposes = answer.get('correct_purposes', [])
        primary_answer = answer.get('primary', '')

        is_correct = predicted in correct_purposes
        is_primary = predicted == primary_answer

        if is_correct:
            correct += 1
        if is_primary:
            primary += 1

        status = "[O] 1순위" if is_primary else "[O] 대안" if is_correct else "[X] 오답"
        method = result.get('method', 'unknown')
        print(f"{pid}. {persona['display_name']}: {result['purpose_name']} ({result['confidence']*100:.0f}%) [{method}] -> {status}")

    print(f"\n결과: 전체 {correct}/{total} ({correct/total*100:.1f}%), 1순위 {primary}/{total} ({primary/total*100:.1f}%)")


if __name__ == "__main__":
    test_recommender()
