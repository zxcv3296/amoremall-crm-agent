# AI 발신 목적 추천 시스템 비교 분석

## 1. 시스템 개요

CRM 마케팅 메시지 발송 시, 고객 페르소나를 분석하여 최적의 **발신 목적**을 추천하는 시스템입니다.

### 발신 목적 6가지
| ID | 발신 목적 | 설명 |
|----|----------|------|
| `promotion` | 프로모션 | 할인, 적립금, 쿠폰 등 혜택 안내 |
| `new_product` | 신제품 안내 | 새로 출시된 제품 소개 |
| `best_curation` | 베스트 큐레이션 | 인기 상품, 브랜드 베스트 추천 |
| `repurchase` | 재구매 & 리텐션 | 구매 주기 도래 고객 재구매 유도 |
| `churn_prevention` | 휴면 방지 | 이탈 위험 고객 재활성화 |
| `seasonal_gift` | 선물 & 시즌 | 명절, 기념일 선물 구매 유도 |

---

## 2. Rule-Based (휴리스틱) 방식

### 2.1 구현 원리
**고정된 우선순위**에 따라 조건을 순차적으로 체크하여 첫 번째로 만족하는 발신 목적을 반환합니다.

### 2.2 우선순위 및 조건

```
우선순위 1: 휴면 방지 (churn_prevention)
├─ 조건: risk.level in ["높음", "매우 높음"] OR churn_probability >= 0.5
├─ 신뢰도: 90% (고정)
└─ 대안: promotion

우선순위 2: 재구매 (repurchase)
├─ 조건: cycle_ratio >= 0.8 (구매주기 80% 이상 도래)
│         cycle_ratio = last_purchase_days_ago / avg_interval
├─ 신뢰도: 85% (고정)
└─ 대안: best_curation

우선순위 3: 선물/시즌 (seasonal_gift)
├─ 조건: gift_purchase_ratio > 0.5
├─ 신뢰도: 80% (고정)
└─ 대안: best_curation

우선순위 4: 프로모션 (promotion)
├─ 조건: coupon_usage_rate > 0.6
│         OR full_price_ratio < 0.3
│         OR discount_sensitivity in ["높음", "매우 높음"]
├─ 신뢰도: 80% (고정)
└─ 대안: new_product

우선순위 5: 신제품 안내 (new_product)
├─ 조건: behavior_tags에 "신제품/얼리/트렌드" 포함
│         OR brand.diversity > 0.6
├─ 신뢰도: 75% (고정)
└─ 대안: best_curation

우선순위 6: 베스트 큐레이션 (best_curation)
├─ 조건: loyalty in ["높음", "매우 높음"]
│         OR full_price_ratio > 0.6
├─ 신뢰도: 75% (고정)
└─ 대안: repurchase

기본값: 프로모션 (promotion)
├─ 조건: 위 모든 조건 불만족 시
├─ 신뢰도: 60% (고정)
└─ 대안: new_product, best_curation
```

### 2.3 코드 예시 (핵심 로직)
```python
def _predict_heuristic(self, persona):
    risk = persona.get("risk", {})
    purchase = persona.get("purchase", {})

    # 1순위: 휴면 방지
    churn_prob = risk.get("churn_probability", 0)
    if risk.get("level") in ["높음", "매우 높음"] or churn_prob >= 0.5:
        return {"recommended_purpose": "churn_prevention", "confidence": 0.9}

    # 2순위: 재구매
    last_days = purchase.get("last_purchase_days_ago", 0)
    avg_interval = purchase.get("avg_interval", 30)
    cycle_ratio = last_days / avg_interval if avg_interval > 0 else 0

    if cycle_ratio >= 0.8:
        return {"recommended_purpose": "repurchase", "confidence": 0.85}

    # ... 이하 생략
```

### 2.4 장점
- **빠름**: 0.003ms/건 (단순 조건문)
- **해석 용이**: 왜 이 결과가 나왔는지 명확
- **일관성**: 같은 입력 → 같은 출력
- **의존성 없음**: sklearn 등 라이브러리 불필요

### 2.5 단점
- **고정된 우선순위**: 실제 상황과 맞지 않을 수 있음
  - 예: 구매주기 도래(80%)인데 할인 민감 고객 → repurchase 반환
  - 실제로는 promotion이 더 적합할 수 있음
- **복합 조건 처리 불가**: 여러 특성의 상호작용 반영 못함
- **신뢰도가 가짜**: 항상 고정값 반환 (실제 불확실성 반영 안함)

---

## 3. RandomForest (ML) 방식

### 3.1 구현 원리
100개의 결정 트리(Decision Tree)가 **투표**하여 가장 많은 표를 받은 클래스를 예측합니다. 각 트리는 서로 다른 샘플과 특성 조합으로 학습됩니다.

### 3.2 학습 데이터

**데이터셋**
- 학습 페르소나: 100개 (ID 21~120, `ml_personas.py`)
- 정답 레이블: 100개 (`ml_answer_key.py`, 수동 라벨링)
- 테스트 페르소나: 21개 (ID 1~21, `data.py`)

**클래스 분포 (균형)**
```
promotion:        17개 (17%)
new_product:      17개 (17%)
best_curation:    17개 (17%)
repurchase:       17개 (17%)
churn_prevention: 16개 (16%)
seasonal_gift:    16개 (16%)
```

### 3.3 입력 특성 (18개)

```python
features = [
    # === 위험/이탈 관련 (2개) ===
    encode_level(risk.level),        # 0=낮음, 1=중간, 2=높음, 3=매우높음
    risk.churn_probability,          # 0.0 ~ 1.0

    # === 구매 관련 (4개) ===
    purchase.total_count,            # 총 구매 횟수
    purchase.avg_order_value / 100000,  # 평균 주문금액 (정규화)
    purchase.last_purchase_days_ago / 90,  # 마지막 구매 후 경과일 (정규화)
    min(cycle_ratio, 2.0),           # 구매주기 도래율 (파생특성)

    # === 프로모션 관련 (3개) ===
    promotion.coupon_usage_rate,     # 쿠폰 사용률 0.0 ~ 1.0
    encode_level(promotion.discount_sensitivity),  # 할인 민감도
    promotion.full_price_ratio,      # 정가 구매 비율

    # === 브랜드 관련 (2개) ===
    brand.diversity,                 # 브랜드 다양성 0.0 ~ 1.0
    encode_level(brand.loyalty),     # 브랜드 충성도

    # === 시즌/선물 관련 (1개) ===
    seasonal.gift_purchase_ratio,    # 선물 구매 비율

    # === 행동 태그 (6개, Binary) ===
    check_tags(["할인", "쿠폰", "세일"]),     # 할인 민감 태그
    check_tags(["신제품", "얼리", "트렌드"]), # 신제품 관심 태그
    check_tags(["재구매", "루틴", "단골"]),   # 재구매 패턴 태그
    check_tags(["이탈", "휴면", "감소"]),     # 이탈 위험 태그
    check_tags(["선물", "기프트"]),           # 선물 구매 태그
    check_tags(["충성", "프리미엄", "vip"]),  # 충성 고객 태그
]
```

### 3.4 모델 하이퍼파라미터

```python
RandomForestClassifier(
    n_estimators=100,      # 트리 개수
    max_depth=8,           # 최대 깊이 (과적합 방지)
    random_state=42,       # 재현성
    class_weight='balanced' # 클래스 불균형 처리
)
```

### 3.5 특성 중요도 (학습 결과)

```
1. tag_repurchase (재구매 태그):  10.6%
2. tag_new (신제품 태그):         8.6%
3. avg_order (평균 주문금액):      8.4%
4. gift_ratio (선물 구매 비율):   7.3%
5. last_purchase (마지막 구매):   7.2%
6. tag_discount (할인 태그):      6.9%
7. churn_probability (이탈확률): 6.5%
8. coupon_rate (쿠폰 사용률):     6.2%
...
```

### 3.6 예측 과정

```python
def _predict_ml(self, persona):
    # 1. 특성 추출 (18개)
    features = self._extract_features(persona)

    # 2. 100개 트리의 확률 투표
    proba = self.model.predict_proba(features)[0]
    # 예: [0.12, 0.08, 0.35, 0.25, 0.15, 0.05]
    #     promotion, new_product, best_curation, repurchase, churn, gift

    # 3. 최고 확률 클래스 선택
    pred_idx = np.argmax(proba)  # 2 (best_curation)
    confidence = proba[pred_idx]  # 0.35 (35%)

    # 4. 대안 추출 (10% 이상인 것)
    alternatives = [repurchase, churn_prevention]  # 25%, 15%

    return {
        "recommended_purpose": "best_curation",
        "confidence": 0.35,
        "alternative_purposes": ["repurchase", "churn_prevention"]
    }
```

### 3.7 장점
- **높은 정확도**: 90.5% (vs Rule 61.9%)
- **복합 패턴 학습**: 여러 특성의 상호작용 반영
- **실제 신뢰도**: 확률 기반으로 불확실성 표현
- **대안 제시**: 2순위, 3순위 추천도 가능

### 3.8 단점
- **느림**: 4.6ms/건 (1500배 느림)
- **블랙박스**: 왜 이 결과인지 설명 어려움
- **학습 데이터 필요**: 라벨링된 데이터 필요
- **과적합 위험**: 학습 데이터와 다른 분포에서 성능 저하 가능

---

## 4. 성능 비교

### 4.1 정확도 (21개 테스트 페르소나 기준)

| 지표 | Rule-Based | RandomForest | 차이 |
|------|------------|--------------|------|
| **1순위 정확도** | 61.9% (13/21) | **90.5% (19/21)** | +28.6%p |
| **전체 정확도** (대안 포함) | 81.0% (17/21) | **100% (21/21)** | +19.0%p |

### 4.2 속도

| 지표 | Rule-Based | RandomForest | 배율 |
|------|------------|--------------|------|
| **평균 예측 시간** | **0.003ms** | 4.614ms | 1538x |
| **최대 예측 시간** | **0.008ms** | 5.278ms | 660x |
| **1만건 처리 시간** | **0.03초** | 46초 | - |

### 4.3 신뢰도 분석

| 지표 | Rule-Based | RandomForest |
|------|------------|--------------|
| **평균 신뢰도** | 81.2% | 63.0% |
| **최소 신뢰도** | 75.0% | 29.0% |
| **최대 신뢰도** | 90.0% | 99.0% |
| **신뢰도 의미** | 가짜 (고정값) | 실제 (확률 기반) |

### 4.4 케이스별 비교

```
ID  이름         RF 예측          Rule 예측        정답              RF   Rule
─────────────────────────────────────────────────────────────────────────────
 1  민지(25세)   promotion        repurchase       promotion         O    X
 4  지현(45세)   best_curation    repurchase       best_curation     O    X
 6  예린(35세)   churn_prevention churn_prevention churn_prevention  O    O
10  채원(42세)   promotion        repurchase       promotion         O    X
12  지수(29세)   promotion        repurchase       promotion         O    X
17  서아(21세)   promotion        repurchase       promotion         O    X
18  혜진(37세)   best_curation    repurchase       best_curation     O    X
─────────────────────────────────────────────────────────────────────────────
```

**Rule-Based가 틀리는 주요 패턴:**
- `repurchase`를 과도하게 예측 (구매주기 80% 도래 조건이 너무 넓음)
- 할인 민감 고객(`promotion`)을 `repurchase`로 오분류
- 충성 고객(`best_curation`)을 `repurchase`로 오분류

---

## 5. 선택 가이드

### 5.1 RandomForest 권장 상황
- 정확도가 중요한 경우
- 배치 처리 (야간 대량 처리)
- 대안 추천이 필요한 경우
- 실제 불확실성을 알아야 하는 경우

### 5.2 Rule-Based 권장 상황
- 실시간 대량 처리 (초당 수만건)
- 설명 가능성이 필요한 경우 (왜 이 목적인가?)
- 라이브러리 의존성을 피하고 싶은 경우
- 시스템 리소스가 제한적인 경우

### 5.3 현재 시스템 권장
**RandomForest 사용 권장**
- 4.6ms는 실시간 서비스에도 충분히 빠름
- 정확도 차이(90.5% vs 61.9%)가 큼
- 대안 추천으로 UX 향상 가능

---

## 6. 파일 구조

```
notion/
├── ml_classifier.py      # 통합 분류기 (RF + Rule 폴백)
├── simple_train.py       # RF 학습 스크립트
├── purpose_model.pkl     # 학습된 RF 모델
├── ml_answer_key.py      # 100개 학습 데이터 라벨
├── answer_key.py         # 21개 테스트 데이터 라벨
├── data.py               # 21개 테스트 페르소나
└── train_result.txt      # 학습 로그

c:\Users\MSI\AISystem-2402\
└── ml_personas.py        # 100개 학습 페르소나
```

---

## 7. 향후 개선 방향

1. **학습 데이터 확장**: 100개 → 500개+ (실제 고객 데이터)
2. **특성 추가**: 최근 구매 카테고리, 시즌 정보 등
3. **앙상블**: RF + XGBoost + LightGBM 투표
4. **온라인 학습**: 새 데이터로 모델 지속 업데이트
5. **A/B 테스트**: 실제 마케팅 성과(전환율, 클릭률)로 평가
