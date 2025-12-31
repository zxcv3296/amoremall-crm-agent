# -*- coding: utf-8 -*-
"""
ML 기반 발신목적 분류기
======================
RandomForest 모델 사용 (ml_trainer.py로 학습)
모델이 없으면 휴리스틱 폴백
"""
import os
import pickle
import numpy as np
from typing import Dict, Any, List


class MLPurposeClassifier:
    """
    발신목적 분류기

    ML 모델 파일이 있으면 RandomForest 사용, 없으면 휴리스틱 폴백
    """

    PURPOSE_NAMES = {
        "promotion": "프로모션",
        "new_product": "신제품 안내",
        "best_curation": "베스트 큐레이션",
        "repurchase": "재구매 & 리텐션",
        "churn_prevention": "휴면 방지",
        "seasonal_gift": "선물 & 시즌"
    }

    def __init__(self):
        """분류기 초기화"""
        self.model = None
        self.model_data = None
        self.model_path = os.path.join(os.path.dirname(__file__), "purpose_model.pkl")

        # 모델 파일이 있으면 로드 시도
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model_data = pickle.load(f)
                    # RandomForest 모델인지 확인
                    if isinstance(self.model_data, dict) and "model" in self.model_data:
                        self.model = self.model_data["model"]
                        self.label_encoder = self.model_data.get("label_encoder")
            except Exception as e:
                print(f"ML 모델 로드 실패: {e}")
                self.model = None

    def predict(self, persona: Dict[str, Any]) -> Dict[str, Any]:
        """
        페르소나 분석 → 발신 목적 추천

        ML 모델이 있으면 사용, 없으면 휴리스틱
        """
        # RandomForest 모델이 있으면 사용
        if self.model is not None and hasattr(self.model, 'predict_proba'):
            return self._predict_ml(persona)

        # 없으면 휴리스틱 사용
        return self._predict_heuristic(persona)

    def _encode_level(self, level: str) -> int:
        """레벨 문자열을 숫자로 인코딩"""
        mapping = {
            "낮음": 0, "낮": 0,
            "중간": 1, "중": 1,
            "높음": 2, "높": 2,
            "매우 높음": 3, "매우높음": 3
        }
        return mapping.get(level, 1)

    def _check_tags(self, tags: List[str], keywords: List[str]) -> int:
        """태그에 특정 키워드가 포함되어 있는지 확인"""
        tag_str = ' '.join(tags).lower()
        for kw in keywords:
            if kw in tag_str:
                return 1
        return 0

    def _extract_features(self, persona: Dict[str, Any]) -> np.ndarray:
        """페르소나에서 특성 벡터 추출 (ml_trainer.py와 동일)"""
        risk = persona.get("risk", {})
        purchase = persona.get("purchase", {})
        promotion = persona.get("promotion", {})
        brand = persona.get("brand", {})
        seasonal = persona.get("seasonal", {})
        behavior_tags = persona.get("behavior_tags", [])

        # 파생 특성 계산
        last_days = purchase.get("last_purchase_days_ago", 0)
        avg_interval = purchase.get("avg_interval", 30)
        cycle_ratio = last_days / avg_interval if avg_interval > 0 else 0

        features = [
            # 위험/이탈
            self._encode_level(risk.get("level", "중간")),
            risk.get("churn_probability", 0.3),

            # 구매
            purchase.get("total_count", 0),
            purchase.get("avg_order_value", 50000) / 100000,
            purchase.get("last_purchase_days_ago", 30) / 90,
            min(cycle_ratio, 2.0),

            # 프로모션
            promotion.get("coupon_usage_rate", 0.5),
            self._encode_level(promotion.get("discount_sensitivity", "중간")),
            promotion.get("full_price_ratio", 0.5),

            # 브랜드
            brand.get("diversity", 0.5),
            self._encode_level(brand.get("loyalty", "중간")),

            # 시즌/선물
            seasonal.get("gift_purchase_ratio", 0.2),

            # 행동 태그
            self._check_tags(behavior_tags, ["할인", "쿠폰", "세일"]),
            self._check_tags(behavior_tags, ["신제품", "얼리", "트렌드", "최신"]),
            self._check_tags(behavior_tags, ["재구매", "루틴", "단골", "충성"]),
            self._check_tags(behavior_tags, ["이탈", "휴면", "감소", "중단"]),
            self._check_tags(behavior_tags, ["선물", "기프트"]),
            self._check_tags(behavior_tags, ["충성", "프리미엄", "vip", "단골"]),
        ]

        return np.array(features, dtype=np.float32).reshape(1, -1)

    def _predict_ml(self, persona: Dict[str, Any]) -> Dict[str, Any]:
        """RandomForest 모델 기반 예측"""
        try:
            features = self._extract_features(persona)
            proba = self.model.predict_proba(features)[0]
            pred_idx = np.argmax(proba)
            confidence = proba[pred_idx]

            # 라벨 디코딩
            purpose_id = self.label_encoder.inverse_transform([pred_idx])[0]

            # 대안 목적 (2, 3순위)
            sorted_indices = np.argsort(proba)[::-1]
            alternatives = []
            for idx in sorted_indices[1:3]:
                if proba[idx] > 0.1:  # 10% 이상인 것만
                    alt_purpose = self.label_encoder.inverse_transform([idx])[0]
                    alternatives.append(alt_purpose)

            # 핵심 요소 추출
            key_factors = self._get_key_factors(persona, purpose_id)

            return {
                "recommended_purpose": purpose_id,
                "purpose_name": self.PURPOSE_NAMES.get(purpose_id, purpose_id),
                "confidence": float(confidence),
                "reasoning": self._generate_reasoning(persona, purpose_id, confidence),
                "alternative_purposes": alternatives,
                "key_factors": key_factors,
                "method": "RandomForest"
            }
        except Exception as e:
            # ML 예측 실패시 휴리스틱 폴백
            result = self._predict_heuristic(persona)
            result["ml_error"] = str(e)
            return result

    def _get_key_factors(self, persona: Dict[str, Any], purpose: str) -> List[str]:
        """목적별 핵심 요소 추출"""
        factors = []
        risk = persona.get("risk", {})
        purchase = persona.get("purchase", {})
        promotion = persona.get("promotion", {})
        brand = persona.get("brand", {})
        seasonal = persona.get("seasonal", {})

        if purpose == "churn_prevention":
            factors = ["이탈위험", f"확률 {risk.get('churn_probability', 0)*100:.0f}%"]
        elif purpose == "repurchase":
            last_days = purchase.get("last_purchase_days_ago", 0)
            avg_interval = purchase.get("avg_interval", 30)
            factors = ["구매주기", f"경과 {last_days}/{avg_interval}일"]
        elif purpose == "promotion":
            factors = ["할인민감도", f"쿠폰 {promotion.get('coupon_usage_rate', 0)*100:.0f}%"]
        elif purpose == "new_product":
            factors = ["신제품관심", f"다양성 {brand.get('diversity', 0)*100:.0f}%"]
        elif purpose == "best_curation":
            factors = ["브랜드충성도", brand.get("loyalty", "중간")]
        elif purpose == "seasonal_gift":
            factors = ["선물구매", f"비율 {seasonal.get('gift_purchase_ratio', 0)*100:.0f}%"]

        return factors

    def _generate_reasoning(self, persona: Dict[str, Any], purpose: str, confidence: float) -> str:
        """추천 이유 생성"""
        reasons = {
            "churn_prevention": f"이탈 위험 고객 (확률 {persona.get('risk', {}).get('churn_probability', 0)*100:.0f}%)",
            "repurchase": "구매 주기 도래, 재구매 유도 적합",
            "promotion": f"할인 민감 고객 (쿠폰 사용률 {persona.get('promotion', {}).get('coupon_usage_rate', 0)*100:.0f}%)",
            "new_product": "신제품/트렌드 관심 높음",
            "best_curation": f"브랜드 충성도 높음 ({persona.get('brand', {}).get('loyalty', '중간')})",
            "seasonal_gift": f"선물 구매 비율 높음 ({persona.get('seasonal', {}).get('gift_purchase_ratio', 0)*100:.0f}%)"
        }
        return reasons.get(purpose, "ML 모델 분석 결과")

    def _predict_heuristic(self, persona: Dict[str, Any]) -> Dict[str, Any]:
        """
        휴리스틱 기반 발신목적 추천

        우선순위:
        1. 이탈 위험 → churn_prevention
        2. 구매 주기 도래 → repurchase
        3. 선물 구매 비율 높음 → seasonal_gift
        4. 할인 민감도 높음 → promotion
        5. 신제품 관심 → new_product
        6. 충성도 높음 → best_curation
        7. 기본값 → promotion
        """
        risk = persona.get("risk", {})
        purchase = persona.get("purchase", {})
        promotion = persona.get("promotion", {})
        brand = persona.get("brand", {})
        seasonal = persona.get("seasonal", {})
        activity = persona.get("activity", {})
        behavior_tags = persona.get("behavior_tags", [])

        # 1순위: 휴면 방지 (이탈 위험)
        churn_prob = risk.get("churn_probability", 0)
        if risk.get("level") in ["높음", "매우 높음"] or churn_prob >= 0.5:
            return {
                "recommended_purpose": "churn_prevention",
                "purpose_name": "휴면 방지",
                "confidence": 0.9,
                "reasoning": f"이탈 위험도 높음 (확률: {churn_prob*100:.0f}%)",
                "alternative_purposes": ["promotion"],
                "key_factors": ["이탈위험", "접속감소"],
                "method": "heuristic"
            }

        # 2순위: 재구매 (구매 주기 도래)
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
                "method": "heuristic"
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
                "method": "heuristic"
            }

        # 4순위: 프로모션 (할인 민감도)
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
                "method": "heuristic"
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
                "method": "heuristic"
            }

        # 6순위: 베스트 큐레이션 (충성도 높음)
        loyalty = brand.get("loyalty", "중간")
        if loyalty in ["높음", "매우 높음"] or full_price > 0.6:
            return {
                "recommended_purpose": "best_curation",
                "purpose_name": "베스트 큐레이션",
                "confidence": 0.75,
                "reasoning": f"브랜드 충성도 {loyalty}, 정가 구매 {full_price*100:.0f}%",
                "alternative_purposes": ["repurchase"],
                "key_factors": ["브랜드충성도", "정가구매율"],
                "method": "heuristic"
            }

        # 기본값: 프로모션
        return {
            "recommended_purpose": "promotion",
            "purpose_name": "프로모션",
            "confidence": 0.6,
            "reasoning": "범용 프로모션 추천",
            "alternative_purposes": ["new_product", "best_curation"],
            "key_factors": ["기본추천"],
            "method": "heuristic"
        }

    def train(self, training_data: list):
        """
        모델 학습 (TODO)

        Args:
            training_data: [(persona, correct_purpose), ...]
        """
        # TODO: 실제 ML 모델 학습 구현
        # 현재는 저장만
        self.model = {"trained": True, "samples": len(training_data)}

        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)

        print(f"모델 저장 완료: {self.model_path}")


# 테스트
if __name__ == "__main__":
    classifier = MLPurposeClassifier()

    # 테스트 페르소나
    test_persona = {
        "risk": {"level": "낮음", "churn_probability": 0.2},
        "purchase": {"last_purchase_days_ago": 25, "avg_interval": 30},
        "promotion": {"coupon_usage_rate": 0.7, "full_price_ratio": 0.3},
        "brand": {"loyalty": "중", "diversity": 0.4}
    }

    result = classifier.predict(test_persona)
    print(f"추천: {result['purpose_name']} ({result['confidence']*100:.0f}%)")
    print(f"이유: {result['reasoning']}")
