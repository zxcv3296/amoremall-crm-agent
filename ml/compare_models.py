# -*- coding: utf-8 -*-
"""RandomForest vs XGBoost 비교"""
import sys
import os
import time
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "model_comparison.txt")

# 결과 저장용
results = []

def log(msg):
    results.append(str(msg))

try:
    log("=" * 60)
    log("RandomForest vs XGBoost 비교")
    log("=" * 60)

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import cross_val_score

    try:
        from xgboost import XGBClassifier
        log("XGBoost 로드 성공")
    except ImportError:
        log("XGBoost 설치 필요: pip install xgboost")
        sys.exit(1)

    # 경로 설정
    notion_path = r"c:\Users\MSI\AISystem-2402\AISystem-2402\notion"
    root_path = r"c:\Users\MSI\AISystem-2402"

    for p in [notion_path, root_path]:
        if p in sys.path:
            sys.path.remove(p)
    sys.path.insert(0, notion_path)
    sys.path.insert(1, root_path)

    # 데이터 로드
    from ml_personas import ml_personas

    import importlib.util
    spec = importlib.util.spec_from_file_location("ml_answer_key", os.path.join(notion_path, "ml_answer_key.py"))
    ml_answer_key_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ml_answer_key_module)
    ML_ANSWER_KEY = ml_answer_key_module.ML_ANSWER_KEY

    log(f"\n학습 데이터: {len(ml_personas)}개")

    # 특성 추출
    PURPOSE_LABELS = ["promotion", "new_product", "best_curation", "repurchase", "churn_prevention", "seasonal_gift"]

    def encode_level(level):
        mapping = {"낮음": 0, "낮": 0, "중간": 1, "중": 1, "높음": 2, "높": 2, "매우 높음": 3, "매우높음": 3}
        return mapping.get(level, 1)

    def check_tags(tags, keywords):
        tag_str = ' '.join(tags).lower()
        return 1 if any(kw in tag_str for kw in keywords) else 0

    def extract_features(persona):
        risk = persona.get("risk", {})
        purchase = persona.get("purchase", {})
        promotion = persona.get("promotion", {})
        brand = persona.get("brand", {})
        seasonal = persona.get("seasonal", {})
        behavior_tags = persona.get("behavior_tags", [])

        last_days = purchase.get("last_purchase_days_ago", 0)
        avg_interval = purchase.get("avg_interval", 30)
        cycle_ratio = last_days / avg_interval if avg_interval > 0 else 0

        return [
            encode_level(risk.get("level", "중간")),
            risk.get("churn_probability", 0.3),
            purchase.get("total_count", 0),
            purchase.get("avg_order_value", 50000) / 100000,
            purchase.get("last_purchase_days_ago", 30) / 90,
            min(cycle_ratio, 2.0),
            promotion.get("coupon_usage_rate", 0.5),
            encode_level(promotion.get("discount_sensitivity", "중간")),
            promotion.get("full_price_ratio", 0.5),
            brand.get("diversity", 0.5),
            encode_level(brand.get("loyalty", "중간")),
            seasonal.get("gift_purchase_ratio", 0.2),
            check_tags(behavior_tags, ["할인", "쿠폰", "세일"]),
            check_tags(behavior_tags, ["신제품", "얼리", "트렌드", "최신"]),
            check_tags(behavior_tags, ["재구매", "루틴", "단골"]),
            check_tags(behavior_tags, ["이탈", "휴면", "감소", "중단"]),
            check_tags(behavior_tags, ["선물", "기프트"]),
            check_tags(behavior_tags, ["충성", "프리미엄", "vip"]),
        ]

    X, y = [], []
    for persona in ml_personas:
        pid = persona["id"]
        if pid in ML_ANSWER_KEY:
            X.append(extract_features(persona))
            y.append(ML_ANSWER_KEY[pid]["primary"])

    X = np.array(X, dtype=np.float32)
    label_encoder = LabelEncoder()
    label_encoder.fit(PURPOSE_LABELS)
    y_encoded = label_encoder.transform(y)

    log(f"특성 shape: {X.shape}")

    # 모델 정의
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight='balanced'
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
    }

    log("\n" + "=" * 60)
    log("모델별 성능 비교")
    log("=" * 60)

    for name, model in models.items():
        log(f"\n### {name} ###")

        # 학습 시간
        start = time.perf_counter()
        model.fit(X, y_encoded)
        train_time = (time.perf_counter() - start) * 1000
        log(f"학습 시간: {train_time:.1f}ms")

        # Cross-validation
        cv_scores = cross_val_score(model, X, y_encoded, cv=5)
        log(f"CV 정확도: {cv_scores.mean()*100:.1f}% (+/- {cv_scores.std()*100:.1f}%)")

        # 예측 시간 (100회 평균)
        times = []
        for _ in range(100):
            start = time.perf_counter()
            model.predict(X[:1])
            times.append((time.perf_counter() - start) * 1000)
        avg_time = np.mean(times)
        log(f"예측 시간: {avg_time:.3f}ms/건")

        # 학습 데이터 정확도
        preds = model.predict(X)
        train_acc = (preds == y_encoded).mean()
        log(f"학습 정확도: {train_acc*100:.1f}%")

    # 21개 테스트 페르소나로 평가
    log("\n" + "=" * 60)
    log("21개 테스트 페르소나 평가")
    log("=" * 60)

    spec2 = importlib.util.spec_from_file_location("answer_key", os.path.join(notion_path, "answer_key.py"))
    answer_key_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(answer_key_module)
    ANSWER_KEY = answer_key_module.ANSWER_KEY

    from data.personas import personas as test_personas

    for name, model in models.items():
        model.fit(X, y_encoded)  # 재학습

        correct_primary = 0
        correct_total = 0

        for persona in test_personas:
            pid = persona["id"]
            if pid not in ANSWER_KEY:
                continue

            features = np.array([extract_features(persona)], dtype=np.float32)
            pred_idx = model.predict(features)[0]
            pred_label = label_encoder.inverse_transform([pred_idx])[0]

            answer = ANSWER_KEY[pid]
            if pred_label == answer["primary"]:
                correct_primary += 1
                correct_total += 1
            elif pred_label in answer.get("correct_purposes", []):
                correct_total += 1

        log(f"\n{name}:")
        log(f"  1순위 정확도: {correct_primary}/21 ({correct_primary/21*100:.1f}%)")
        log(f"  전체 정확도: {correct_total}/21 ({correct_total/21*100:.1f}%)")

    log("\n" + "=" * 60)
    log("비교 완료!")
    log("=" * 60)

except Exception as e:
    import traceback
    log(f"\nERROR: {e}")
    log(traceback.format_exc())

# 결과 저장
with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(results))

# 콘솔 출력도 시도
print("\n".join(results))
