# -*- coding: utf-8 -*-
import sys
import os

# 로그 파일로 출력
log_file = open(os.path.join(os.path.dirname(__file__), "compare_result.txt"), "w", encoding="utf-8")

def p(msg):
    log_file.write(str(msg) + "\n")
    log_file.flush()

try:
    p("Starting comparison...")

    import time
    import numpy as np

    p("numpy OK")

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import cross_val_score
    p("sklearn OK")

    try:
        from xgboost import XGBClassifier
        p("xgboost OK")
    except ImportError as e:
        p(f"xgboost FAILED: {e}")
        p("Installing xgboost...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "xgboost", "-q"])
        from xgboost import XGBClassifier
        p("xgboost installed and imported")

    # 경로 설정
    notion_path = r"c:\Users\MSI\AISystem-2402\AISystem-2402\notion"
    root_path = r"c:\Users\MSI\AISystem-2402"
    sys.path.insert(0, notion_path)
    sys.path.insert(1, root_path)

    from ml_personas import ml_personas
    p(f"ml_personas: {len(ml_personas)}")

    import importlib.util
    spec = importlib.util.spec_from_file_location("ml_answer_key", os.path.join(notion_path, "ml_answer_key.py"))
    ml_answer_key_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ml_answer_key_module)
    ML_ANSWER_KEY = ml_answer_key_module.ML_ANSWER_KEY
    p(f"ML_ANSWER_KEY: {len(ML_ANSWER_KEY)}")

    PURPOSE_LABELS = ["promotion", "new_product", "best_curation", "repurchase", "churn_prevention", "seasonal_gift"]

    def encode_level(level):
        return {"낮음": 0, "중간": 1, "높음": 2, "매우 높음": 3}.get(level, 1)

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
            check_tags(behavior_tags, ["신제품", "얼리", "트렌드"]),
            check_tags(behavior_tags, ["재구매", "루틴", "단골"]),
            check_tags(behavior_tags, ["이탈", "휴면", "감소"]),
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
    p(f"Data shape: {X.shape}")

    p("\n" + "=" * 50)
    p("MODEL COMPARISON")
    p("=" * 50)

    # RandomForest
    p("\n[RandomForest]")
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, class_weight="balanced")

    start = time.perf_counter()
    rf.fit(X, y_encoded)
    rf_train_time = (time.perf_counter() - start) * 1000
    p(f"  Train time: {rf_train_time:.1f}ms")

    rf_cv = cross_val_score(rf, X, y_encoded, cv=5)
    p(f"  CV accuracy: {rf_cv.mean()*100:.1f}% (+/- {rf_cv.std()*100:.1f}%)")

    times = []
    for _ in range(100):
        start = time.perf_counter()
        rf.predict(X[:1])
        times.append((time.perf_counter() - start) * 1000)
    p(f"  Predict time: {np.mean(times):.3f}ms/sample")

    # XGBoost
    p("\n[XGBoost]")
    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric="mlogloss",
        verbosity=0
    )

    start = time.perf_counter()
    xgb.fit(X, y_encoded)
    xgb_train_time = (time.perf_counter() - start) * 1000
    p(f"  Train time: {xgb_train_time:.1f}ms")

    xgb_cv = cross_val_score(xgb, X, y_encoded, cv=5)
    p(f"  CV accuracy: {xgb_cv.mean()*100:.1f}% (+/- {xgb_cv.std()*100:.1f}%)")

    times = []
    for _ in range(100):
        start = time.perf_counter()
        xgb.predict(X[:1])
        times.append((time.perf_counter() - start) * 1000)
    p(f"  Predict time: {np.mean(times):.3f}ms/sample")

    # 21 test personas
    p("\n" + "=" * 50)
    p("TEST ON 21 PERSONAS")
    p("=" * 50)

    from data.personas import personas as test_personas
    spec2 = importlib.util.spec_from_file_location("answer_key", os.path.join(notion_path, "answer_key.py"))
    answer_key_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(answer_key_module)
    ANSWER_KEY = answer_key_module.ANSWER_KEY

    for name, model in [("RandomForest", rf), ("XGBoost", xgb)]:
        correct = 0
        total_correct = 0
        for persona in test_personas:
            pid = persona["id"]
            if pid not in ANSWER_KEY:
                continue
            features = np.array([extract_features(persona)], dtype=np.float32)
            pred_idx = model.predict(features)[0]
            pred_label = label_encoder.inverse_transform([pred_idx])[0]
            answer = ANSWER_KEY[pid]
            if pred_label == answer["primary"]:
                correct += 1
                total_correct += 1
            elif pred_label in answer.get("correct_purposes", []):
                total_correct += 1
        p(f"\n[{name}]")
        p(f"  Primary accuracy: {correct}/21 ({correct/21*100:.1f}%)")
        p(f"  Total accuracy: {total_correct}/21 ({total_correct/21*100:.1f}%)")

    p("\n" + "=" * 50)
    p("SUMMARY")
    p("=" * 50)
    p(f"\n{'Metric':<20} {'RandomForest':>15} {'XGBoost':>15}")
    p("-" * 50)
    p(f"{'CV Accuracy':<20} {rf_cv.mean()*100:>14.1f}% {xgb_cv.mean()*100:>14.1f}%")
    p(f"{'Train Time':<20} {rf_train_time:>13.1f}ms {xgb_train_time:>13.1f}ms")
    p(f"{'Predict Time':<20} {np.mean(times):>12.3f}ms {np.mean(times):>12.3f}ms")

    p("\nDone!")

except Exception as e:
    import traceback
    p(f"ERROR: {e}")
    p(traceback.format_exc())

finally:
    log_file.close()
