# -*- coding: utf-8 -*-
"""
페르소나 분류기 학습 및 평가
============================
- 라벨링된 500개 데이터를 200:300으로 분할
- 200개로 학습, 300개로 테스트
"""
import pandas as pd
import numpy as np
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from persona_classifier_hybrid import HybridPersonaClassifier, rule_based_classify, extract_features

def load_labeled_data():
    """라벨링된 데이터 로드"""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'customer_data_1000.csv')
    df = pd.read_csv(data_path, encoding='utf-8-sig')

    # 라벨이 있는 데이터만 (페르소나가 있는 500개)
    labeled_df = df[df['persona'].notna() & (df['persona'] != '')]
    print(f"라벨링된 데이터: {len(labeled_df)}개")

    return labeled_df

def evaluate_rule_based(test_df):
    """규칙 기반만으로 평가"""
    y_true = []
    y_pred = []
    rule_matched = 0

    for idx, row in test_df.iterrows():
        true_label = row['persona']
        result = rule_based_classify(row.to_dict())

        if result['persona'] is not None:
            pred_label = result['persona']
            rule_matched += 1
        else:
            pred_label = "미분류"

        y_true.append(true_label)
        y_pred.append(pred_label)

    return y_true, y_pred, rule_matched

def evaluate_hybrid(classifier, test_df):
    """하이브리드 방식으로 평가"""
    y_true = []
    y_pred = []
    methods = {'rule': 0, 'ml': 0, 'brand_fallback': 0}

    for idx, row in test_df.iterrows():
        true_label = row['persona']
        result = classifier.predict(row.to_dict())

        y_true.append(true_label)
        y_pred.append(result['persona'])
        methods[result['method']] = methods.get(result['method'], 0) + 1

    return y_true, y_pred, methods

def main():
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("페르소나 분류기 학습 및 평가")
    print("=" * 70)

    # 1. 데이터 로드
    labeled_df = load_labeled_data()

    # 페르소나 분포 확인
    print("\n라벨링 데이터 페르소나 분포:")
    for persona, count in labeled_df['persona'].value_counts().items():
        print(f"  {persona}: {count}개")

    # 2. 학습/테스트 분할 (200:300)
    train_df, test_df = train_test_split(
        labeled_df,
        train_size=200,
        test_size=300,
        stratify=labeled_df['persona'],
        random_state=42
    )

    print(f"\n학습 데이터: {len(train_df)}개")
    print(f"테스트 데이터: {len(test_df)}개")

    # 3. 분류기 초기화 및 학습
    print("\n" + "=" * 70)
    print("모델 학습")
    print("=" * 70)

    classifier = HybridPersonaClassifier()
    classifier.is_trained = False  # 강제 재학습

    # 학습 데이터로 ML 모델 학습
    n_trained = classifier.train(train_df)
    print(f"ML 모델 학습 완료: {n_trained}개 샘플")

    # 4. 규칙 기반만으로 평가
    print("\n" + "=" * 70)
    print("규칙 기반 평가 (테스트셋 300개)")
    print("=" * 70)

    y_true_rule, y_pred_rule, rule_matched = evaluate_rule_based(test_df)

    # 규칙 매칭된 것만 평가
    matched_indices = [i for i, p in enumerate(y_pred_rule) if p != "미분류"]
    if matched_indices:
        y_true_matched = [y_true_rule[i] for i in matched_indices]
        y_pred_matched = [y_pred_rule[i] for i in matched_indices]
        rule_accuracy = accuracy_score(y_true_matched, y_pred_matched)
        print(f"규칙 매칭률: {rule_matched}/{len(test_df)} ({rule_matched/len(test_df)*100:.1f}%)")
        print(f"규칙 매칭된 케이스 정확도: {rule_accuracy*100:.1f}%")

    # 5. 하이브리드 평가
    print("\n" + "=" * 70)
    print("하이브리드 평가 (규칙 + ML)")
    print("=" * 70)

    y_true_hybrid, y_pred_hybrid, methods = evaluate_hybrid(classifier, test_df)

    hybrid_accuracy = accuracy_score(y_true_hybrid, y_pred_hybrid)
    print(f"\n전체 정확도: {hybrid_accuracy*100:.1f}%")

    print(f"\n분류 방식 통계:")
    for method, count in methods.items():
        print(f"  {method}: {count}개 ({count/len(test_df)*100:.1f}%)")

    # 6. 상세 분류 리포트
    print("\n" + "=" * 70)
    print("분류 리포트")
    print("=" * 70)

    personas = sorted(labeled_df['persona'].unique())
    print(classification_report(y_true_hybrid, y_pred_hybrid, target_names=personas, zero_division=0))

    # 7. 혼동 행렬
    print("\n" + "=" * 70)
    print("혼동 행렬")
    print("=" * 70)

    cm = confusion_matrix(y_true_hybrid, y_pred_hybrid, labels=personas)

    # 헤더 출력
    header = "실제\\예측"
    for p in personas:
        header += f" {p[:4]:>5}"
    print(header)

    for i, persona in enumerate(personas):
        row = f"{persona[:8]:<10}"
        for j in range(len(personas)):
            row += f" {cm[i][j]:>5}"
        print(row)

    # 8. 페르소나별 정확도
    print("\n" + "=" * 70)
    print("페르소나별 정확도")
    print("=" * 70)

    for persona in personas:
        true_indices = [i for i, y in enumerate(y_true_hybrid) if y == persona]
        if true_indices:
            correct = sum(1 for i in true_indices if y_pred_hybrid[i] == persona)
            total = len(true_indices)
            acc = correct / total * 100
            print(f"  {persona}: {correct}/{total} ({acc:.1f}%)")

    # 9. 오분류 샘플 분석
    print("\n" + "=" * 70)
    print("오분류 샘플 분석 (최대 10개)")
    print("=" * 70)

    misclassified = []
    for i, (true, pred) in enumerate(zip(y_true_hybrid, y_pred_hybrid)):
        if true != pred:
            row = test_df.iloc[i]
            misclassified.append({
                'name': row['name'],
                'age': row['age'],
                'true': true,
                'pred': pred,
                'brands': row['primary_brand'][:30] if pd.notna(row['primary_brand']) else ''
            })

    print(f"오분류: {len(misclassified)}/{len(test_df)}개")
    for i, m in enumerate(misclassified[:10]):
        print(f"  {i+1}. {m['name']}({m['age']}세): {m['true']} → {m['pred']}")
        print(f"     브랜드: {m['brands']}...")

if __name__ == "__main__":
    main()
