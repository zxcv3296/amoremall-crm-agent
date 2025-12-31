# -*- coding: utf-8 -*-
"""
RandomForest 기반 발신목적 분류기 학습
=====================================
ml_personas.py (100개) + ml_answer_key.py 라벨 사용
"""
import os
import sys
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from typing import Dict, List, Any

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_answer_key import ML_ANSWER_KEY

# ml_personas는 상위 폴더에 있음
sys.path.insert(0, r'c:\Users\MSI\AISystem-2402')
from ml_personas import ml_personas


class PurposeModelTrainer:
    """발신목적 분류 모델 학습기"""

    PURPOSE_LABELS = [
        "promotion",
        "new_product",
        "best_curation",
        "repurchase",
        "churn_prevention",
        "seasonal_gift"
    ]

    FEATURE_NAMES = [
        # 위험/이탈 관련 (2)
        "risk_level_encoded",      # 낮음=0, 중간=1, 높음=2, 매우높음=3
        "churn_probability",

        # 구매 관련 (4)
        "total_count",
        "avg_order_value",
        "last_purchase_days_ago",
        "cycle_ratio",             # derived: last_purchase_days_ago / avg_interval

        # 프로모션 관련 (3)
        "coupon_usage_rate",
        "discount_sensitivity_encoded",  # 낮음=0, 중간=1, 높음=2, 매우높음=3
        "full_price_ratio",

        # 브랜드 관련 (2)
        "diversity",
        "loyalty_encoded",         # 낮음=0, 중간=1, 높음=2, 매우높음=3

        # 시즌/선물 관련 (1)
        "gift_purchase_ratio",

        # 행동 태그 관련 (6) - binary flags
        "tag_할인_민감",
        "tag_신제품_관심",
        "tag_재구매_패턴",
        "tag_이탈_위험",
        "tag_선물_구매",
        "tag_충성_고객",
    ]

    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(self.PURPOSE_LABELS)
        self.model_path = os.path.join(os.path.dirname(__file__), "purpose_model.pkl")

    def _encode_level(self, level: str) -> int:
        """레벨 문자열을 숫자로 인코딩"""
        mapping = {
            "낮음": 0, "낮": 0,
            "중간": 1, "중": 1,
            "높음": 2, "높": 2,
            "매우 높음": 3, "매우높음": 3
        }
        return mapping.get(level, 1)  # 기본값 중간

    def _check_tags(self, tags: List[str], keywords: List[str]) -> int:
        """태그에 특정 키워드가 포함되어 있는지 확인"""
        tag_str = ' '.join(tags).lower()
        for kw in keywords:
            if kw in tag_str:
                return 1
        return 0

    def extract_features(self, persona: Dict[str, Any]) -> np.ndarray:
        """페르소나에서 특성 벡터 추출"""
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
            purchase.get("avg_order_value", 50000) / 100000,  # 정규화
            purchase.get("last_purchase_days_ago", 30) / 90,  # 정규화
            min(cycle_ratio, 2.0),  # cap at 2.0

            # 프로모션
            promotion.get("coupon_usage_rate", 0.5),
            self._encode_level(promotion.get("discount_sensitivity", "중간")),
            promotion.get("full_price_ratio", 0.5),

            # 브랜드
            brand.get("diversity", 0.5),
            self._encode_level(brand.get("loyalty", "중간")),

            # 시즌/선물
            seasonal.get("gift_purchase_ratio", 0.2),

            # 행동 태그 (binary)
            self._check_tags(behavior_tags, ["할인", "쿠폰", "세일"]),
            self._check_tags(behavior_tags, ["신제품", "얼리", "트렌드", "최신"]),
            self._check_tags(behavior_tags, ["재구매", "루틴", "단골", "충성"]),
            self._check_tags(behavior_tags, ["이탈", "휴면", "감소", "중단"]),
            self._check_tags(behavior_tags, ["선물", "기프트"]),
            self._check_tags(behavior_tags, ["충성", "프리미엄", "vip", "단골"]),
        ]

        return np.array(features, dtype=np.float32)

    def prepare_training_data(self) -> tuple:
        """학습 데이터 준비"""
        X = []
        y = []

        for persona in ml_personas:
            pid = persona["id"]
            if pid not in ML_ANSWER_KEY:
                continue

            features = self.extract_features(persona)
            label = ML_ANSWER_KEY[pid]["primary"]

            X.append(features)
            y.append(label)

        X = np.array(X)
        y = self.label_encoder.transform(y)

        return X, y

    def train(self, n_estimators: int = 100, max_depth: int = 10) -> Dict[str, Any]:
        """모델 학습"""
        print("=" * 60)
        print("RandomForest 발신목적 분류기 학습")
        print("=" * 60)

        # 데이터 준비
        X, y = self.prepare_training_data()
        print(f"\n학습 데이터: {len(X)}개 페르소나")
        print(f"특성 수: {len(self.FEATURE_NAMES)}개")
        print(f"클래스: {self.PURPOSE_LABELS}")

        # 클래스 분포 확인
        unique, counts = np.unique(y, return_counts=True)
        print("\n클래스 분포:")
        for label_idx, count in zip(unique, counts):
            label_name = self.label_encoder.inverse_transform([label_idx])[0]
            print(f"  {label_name}: {count}개")

        # 모델 학습
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            class_weight='balanced'  # 클래스 불균형 처리
        )

        # 교차 검증
        print(f"\n5-fold 교차 검증 중...")
        cv_scores = cross_val_score(self.model, X, y, cv=5)
        print(f"CV 점수: {cv_scores}")
        print(f"평균 정확도: {cv_scores.mean()*100:.1f}% (+/- {cv_scores.std()*100:.1f}%)")

        # 전체 데이터로 최종 학습
        self.model.fit(X, y)

        # 특성 중요도
        print("\n특성 중요도 (상위 10개):")
        importances = list(zip(self.FEATURE_NAMES, self.model.feature_importances_))
        importances.sort(key=lambda x: x[1], reverse=True)
        for name, imp in importances[:10]:
            print(f"  {name}: {imp*100:.1f}%")

        # 모델 저장
        model_data = {
            "model": self.model,
            "label_encoder": self.label_encoder,
            "feature_names": self.FEATURE_NAMES,
            "purpose_labels": self.PURPOSE_LABELS,
            "cv_accuracy": cv_scores.mean(),
            "feature_importances": dict(importances)
        }

        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"\n모델 저장 완료: {self.model_path}")

        return {
            "cv_accuracy": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "n_samples": len(X),
            "n_features": len(self.FEATURE_NAMES),
            "feature_importances": dict(importances[:5])
        }

    def evaluate_on_training_data(self):
        """학습 데이터에 대한 상세 평가"""
        if self.model is None:
            print("모델이 학습되지 않았습니다.")
            return

        X, y = self.prepare_training_data()
        predictions = self.model.predict(X)
        proba = self.model.predict_proba(X)

        print("\n" + "=" * 60)
        print("학습 데이터 평가 결과")
        print("=" * 60)

        correct = 0
        primary_match = 0

        for i, persona in enumerate(ml_personas):
            pid = persona["id"]
            if pid not in ML_ANSWER_KEY:
                continue

            pred_idx = predictions[i - (ml_personas[0]["id"] - 21)]  # offset 보정
            pred_label = self.label_encoder.inverse_transform([pred_idx])[0]

            answer = ML_ANSWER_KEY[pid]
            is_primary = pred_label == answer["primary"]
            is_correct = pred_label in [answer["primary"]] + answer.get("alternatives", [])

            if is_primary:
                primary_match += 1
            if is_correct:
                correct += 1

            status = "[O] 1순위" if is_primary else "[O] 대안" if is_correct else "[X] 오답"
            confidence = max(proba[i - (ml_personas[0]["id"] - 21)]) * 100

            if not is_correct:  # 오답만 출력
                print(f"  {pid}. {persona['display_name']}: 예측={pred_label}, 정답={answer['primary']} {status}")

        total = len([p for p in ml_personas if p["id"] in ML_ANSWER_KEY])
        print(f"\n결과:")
        print(f"  1순위 일치: {primary_match}/{total} ({primary_match/total*100:.1f}%)")
        print(f"  전체 정답: {correct}/{total} ({correct/total*100:.1f}%)")


def main():
    """메인 학습 실행"""
    trainer = PurposeModelTrainer()
    result = trainer.train(n_estimators=100, max_depth=8)
    trainer.evaluate_on_training_data()

    print("\n" + "=" * 60)
    print("학습 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
