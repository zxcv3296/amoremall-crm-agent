# -*- coding: utf-8 -*-
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "train_result.txt")
log_file = open(log_path, "w", encoding="utf-8")

def log(msg):
    log_file.write(str(msg) + "\n")
    log_file.flush()

try:
    log("=" * 60)
    log("ML Training Start")
    log("=" * 60)

    # Check sklearn
    log("\n1. Checking sklearn...")
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
        from sklearn.model_selection import cross_val_score
        log("   sklearn OK")
    except ImportError as e:
        log(f"   sklearn ERROR: {e}")
        log("   Run: pip install scikit-learn")
        sys.exit(1)

    import numpy as np
    log(f"   numpy OK: {np.__version__}")

    # Set paths - notion folder FIRST to load the correct ml_answer_key
    log("\n2. Setting paths...")
    notion_path = r"c:\Users\MSI\AISystem-2402\AISystem-2402\notion"
    root_path = r"c:\Users\MSI\AISystem-2402"

    # Remove any existing paths first
    for p in [notion_path, root_path]:
        if p in sys.path:
            sys.path.remove(p)

    # Add notion path FIRST so it takes priority
    sys.path.insert(0, notion_path)
    sys.path.insert(1, root_path)  # ml_personas is here
    log(f"   sys.path[0]: {sys.path[0]}")
    log(f"   sys.path[1]: {sys.path[1]}")

    # Load data
    log("\n3. Loading data...")

    # ml_personas from root folder
    from ml_personas import ml_personas
    log(f"   ml_personas: {len(ml_personas)} items")

    # Make sure we load ml_answer_key from notion folder
    import importlib.util
    spec = importlib.util.spec_from_file_location("ml_answer_key", os.path.join(notion_path, "ml_answer_key.py"))
    ml_answer_key_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ml_answer_key_module)
    ML_ANSWER_KEY = ml_answer_key_module.ML_ANSWER_KEY
    log(f"   ML_ANSWER_KEY: {len(ML_ANSWER_KEY)} items (from notion folder)")

    # Prepare features
    log("\n4. Extracting features...")

    PURPOSE_LABELS = ["promotion", "new_product", "best_curation", "repurchase", "churn_prevention", "seasonal_gift"]

    def encode_level(level):
        mapping = {"낮음": 0, "낮": 0, "중간": 1, "중": 1, "높음": 2, "높": 2, "매우 높음": 3, "매우높음": 3}
        return mapping.get(level, 1)

    def check_tags(tags, keywords):
        tag_str = ' '.join(tags).lower()
        for kw in keywords:
            if kw in tag_str:
                return 1
        return 0

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

    X = []
    y = []

    log(f"   ml_personas count: {len(ml_personas)}")
    log(f"   ML_ANSWER_KEY count: {len(ML_ANSWER_KEY)}")
    first_pid = ml_personas[0]['id']
    first_key = list(ML_ANSWER_KEY.keys())[0]
    log(f"   First persona ID: {first_pid} (type: {type(first_pid).__name__})")
    log(f"   First key: {first_key} (type: {type(first_key).__name__})")
    log(f"   21 in ML_ANSWER_KEY: {21 in ML_ANSWER_KEY}")
    log(f"   first_pid in ML_ANSWER_KEY: {first_pid in ML_ANSWER_KEY}")

    matched = 0
    for persona in ml_personas:
        pid = persona["id"]
        if pid not in ML_ANSWER_KEY:
            log(f"   Missing ID: {pid}")
            continue
        matched += 1
        features = extract_features(persona)
        label = ML_ANSWER_KEY[pid]["primary"]
        X.append(features)
        y.append(label)

    log(f"   Matched: {matched}")
    X = np.array(X, dtype=np.float32)
    log(f"   Features shape: {X.shape}")

    # Encode labels
    label_encoder = LabelEncoder()
    label_encoder.fit(PURPOSE_LABELS)
    y_encoded = label_encoder.transform(y)
    log(f"   Labels: {len(y_encoded)}")

    # Class distribution
    log("\n5. Class distribution:")
    unique, counts = np.unique(y_encoded, return_counts=True)
    for label_idx, count in zip(unique, counts):
        label_name = label_encoder.inverse_transform([label_idx])[0]
        log(f"   {label_name}: {count}")

    # Train model
    log("\n6. Training RandomForest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        class_weight='balanced'
    )

    # Cross validation
    log("   5-fold CV...")
    cv_scores = cross_val_score(model, X, y_encoded, cv=5)
    log(f"   CV scores: {cv_scores}")
    log(f"   Mean accuracy: {cv_scores.mean()*100:.1f}% (+/- {cv_scores.std()*100:.1f}%)")

    # Final fit
    model.fit(X, y_encoded)
    log("   Model trained!")

    # Feature importance
    log("\n7. Feature importance (top 5):")
    FEATURE_NAMES = [
        "risk_level", "churn_prob", "total_count", "avg_order", "last_purchase",
        "cycle_ratio", "coupon_rate", "discount_sens", "full_price", "diversity",
        "loyalty", "gift_ratio", "tag_discount", "tag_new", "tag_repurchase",
        "tag_churn", "tag_gift", "tag_loyal"
    ]
    importances = list(zip(FEATURE_NAMES, model.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    for name, imp in importances[:5]:
        log(f"   {name}: {imp*100:.1f}%")

    # Save model
    log("\n8. Saving model...")
    import pickle
    model_path = r"c:\Users\MSI\AISystem-2402\AISystem-2402\notion\purpose_model.pkl"
    model_data = {
        "model": model,
        "label_encoder": label_encoder,
        "feature_names": FEATURE_NAMES,
        "purpose_labels": PURPOSE_LABELS,
        "cv_accuracy": cv_scores.mean(),
        "feature_importances": dict(importances)
    }
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    log(f"   Saved to: {model_path}")

    # Evaluate
    log("\n9. Evaluation on training data:")
    predictions = model.predict(X)
    correct = 0
    primary_match = 0

    for i, persona in enumerate(ml_personas):
        pid = persona["id"]
        if pid not in ML_ANSWER_KEY:
            continue

        idx = i
        if idx >= len(predictions):
            continue

        pred_label = label_encoder.inverse_transform([predictions[idx]])[0]
        answer = ML_ANSWER_KEY[pid]

        if pred_label == answer["primary"]:
            primary_match += 1
            correct += 1
        elif pred_label in answer.get("alternatives", []):
            correct += 1

    total = len([p for p in ml_personas if p["id"] in ML_ANSWER_KEY])
    log(f"   Primary match: {primary_match}/{total} ({primary_match/total*100:.1f}%)")
    log(f"   Total correct: {correct}/{total} ({correct/total*100:.1f}%)")

    log("\n" + "=" * 60)
    log("TRAINING COMPLETED SUCCESSFULLY!")
    log("=" * 60)

except Exception as e:
    import traceback
    log(f"\nERROR: {e}")
    log(traceback.format_exc())

finally:
    log_file.close()
