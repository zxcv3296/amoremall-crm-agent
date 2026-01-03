# -*- coding: utf-8 -*-
"""
페르소나 분류 모델 - Streamlit 연동용
- 고객 데이터를 받아 7개 페르소나 중 하나로 분류
- 순수 ML 기반 (RandomForest + GradientBoosting 앙상블)
"""
import pandas as pd
import numpy as np
import pickle
import os
import glob
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# 브랜드 클러스터 정의
BRAND_CLUSTERS = {
    "테크니컬 홈케어족": ["메이크온", "아이오페", "에스트라"],
    "하이엔드 품격가": ["설화수", "헤라", "에이피뷰티", "홀리추얼", "라네즈", "아모레퍼시픽"],
    "웰니스 힐링 탐험가": ["퍼즐우드", "오설록", "롱테이크"],
    "연구소 기반 해결사": ["프리메라", "한율", "이니스프리", "마몽드", "비레디", "정글몬스터", "에스트라"],
    "트렌디 Z세대": ["앞바다즈", "에스쁘아", "에뛰드", "아모레성수"],
    "합리적 큐레이터": ["라네즈", "한율", "프리메라"],
    "실속형 가계 수호자": ["일리윤", "라보에이치", "해피바스", "아모레베이직", "메디안", "아모스 프로페셔널", "아모스프로페셔널"]
}

# 페르소나별 특성 정의 (CRM 메시지 생성용)
PERSONA_PROFILES = {
    "테크니컬 홈케어족": {
        "description": "기술 기반 홈케어 디바이스와 고기능성 스킨케어를 선호",
        "shopping_pattern": "고가 제품 선호, 기술력 중시",
        "tier": "premium",
        "keywords": ["디바이스", "홈케어", "고기능성", "전문 케어"]
    },
    "하이엔드 품격가": {
        "description": "프리미엄 럭셔리 브랜드를 선호하는 품격있는 고객",
        "shopping_pattern": "프리미엄 브랜드 충성, 정가 구매 비율 높음",
        "tier": "premium",
        "keywords": ["럭셔리", "프리미엄", "한방", "안티에이징"]
    },
    "웰니스 힐링 탐험가": {
        "description": "웰니스, 힐링, 라이프스타일 브랜드에 관심",
        "shopping_pattern": "체험 중시, 새로운 브랜드 탐색",
        "tier": "mid",
        "keywords": ["웰니스", "힐링", "티", "아로마"]
    },
    "연구소 기반 해결사": {
        "description": "피부 고민 해결을 위해 연구소 기반 브랜드 선호",
        "shopping_pattern": "성분과 효능 중시, 문제 해결형 구매",
        "tier": "mid",
        "keywords": ["더마", "민감성", "진정", "과학적"]
    },
    "트렌디 Z세대": {
        "description": "트렌드에 민감한 MZ세대, SNS 영향력",
        "shopping_pattern": "트렌디한 제품 선호, 가성비 중시",
        "tier": "affordable",
        "keywords": ["트렌디", "컬러", "SNS", "신상"]
    },
    "합리적 큐레이터": {
        "description": "합리적인 가격대에서 좋은 품질을 추구",
        "shopping_pattern": "가성비 중시, 리뷰 꼼꼼히 확인",
        "tier": "mid",
        "keywords": ["가성비", "합리적", "베스트셀러", "추천"]
    },
    "실속형 가계 수호자": {
        "description": "가족용/생활용품 대량 구매, 할인에 민감",
        "shopping_pattern": "할인/쿠폰 적극 활용, 대용량 선호",
        "tier": "affordable",
        "keywords": ["가족", "대용량", "할인", "실속"]
    }
}


def parse_brands(brand_str):
    """브랜드 문자열을 리스트로 파싱"""
    if pd.isna(brand_str) or brand_str == "":
        return []
    return [b.strip() for b in str(brand_str).split(",")]


def count_brand_matches(brands, target_brands):
    """브랜드 매칭 개수 계산"""
    count = 0
    for brand in brands:
        for target in target_brands:
            if target in brand or brand in target:
                count += 1
                break
    return count


def extract_features(row):
    """고객 데이터에서 특성 추출"""
    # 브랜드 파싱
    primary_brands = parse_brands(row.get("primary_brand", ""))
    all_brands = primary_brands

    # 각 페르소나별 브랜드 점수
    brand_scores = []
    for persona in BRAND_CLUSTERS.keys():
        score = count_brand_matches(all_brands, BRAND_CLUSTERS[persona])
        brand_scores.append(score)

    # 기본 특성
    age = row.get("age", 30)
    if pd.isna(age):
        age = 30

    discount_sens = row.get("discount_sensitivity", "중간")
    discount_map = {"낮음": 0, "중간": 1, "높음": 2, "매우 높음": 3}
    discount_encoded = discount_map.get(discount_sens, 1)

    loyalty = row.get("loyalty", "중간")
    loyalty_map = {"낮음": 0, "중간": 1, "높음": 2, "매우 높음": 3}
    loyalty_encoded = loyalty_map.get(loyalty, 1)

    visit_freq = row.get("visit_frequency", "중간")
    freq_map = {"낮음": 0, "중간": 1, "높음": 2}
    freq_encoded = freq_map.get(visit_freq, 1)

    tier = row.get("membership_tier", "M")
    tier_map = {"A": 0, "M": 1, "O": 2, "R": 3, "E": 4}
    tier_encoded = tier_map.get(tier, 1)

    full_price_ratio = row.get("full_price_ratio", 0.5)
    if pd.isna(full_price_ratio):
        full_price_ratio = 0.5

    coupon_usage_rate = row.get("coupon_usage_rate", 0.5)
    if pd.isna(coupon_usage_rate):
        coupon_usage_rate = 0.5

    diversity = row.get("diversity", 0.5)
    if pd.isna(diversity):
        diversity = 0.5

    avg_amount = row.get("avg_amount", 30000)
    if pd.isna(avg_amount):
        avg_amount = 30000

    total_count = row.get("total_count", 0)
    if pd.isna(total_count):
        total_count = 0

    features = [
        age / 100,
        discount_encoded / 3,
        loyalty_encoded / 3,
        freq_encoded / 2,
        tier_encoded / 4,
        full_price_ratio,
        coupon_usage_rate,
        diversity,
        avg_amount / 100000,
        total_count / 50,
    ] + brand_scores

    return np.array(features, dtype=np.float32)


class PersonaClassifier:
    """페르소나 분류기 - Streamlit 연동용"""

    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = os.path.join(os.path.dirname(__file__), "persona_model.pkl")

        # 저장된 모델이 있으면 로드
        if os.path.exists(self.model_path):
            self.load()

    def train(self, train_df=None):
        """모델 학습"""
        if train_df is None:
            # 기본 학습 데이터 로드
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            xlsx_files = glob.glob(os.path.join(data_dir, '*.xlsx'))

            # 샘플 + 500개 데이터 사용
            sample_path = [f for f in xlsx_files if 'customers' not in f][0]
            full_path = [f for f in xlsx_files if 'customers' in f][0]

            sample_df = pd.read_excel(sample_path)
            full_df = pd.read_excel(full_path)

            # 200:300 분할
            train_split, _ = train_test_split(
                full_df,
                train_size=200,
                test_size=300,
                stratify=full_df['페르소나'],
                random_state=42
            )

            # 샘플 21개 추가
            train_df = pd.concat([train_split, sample_df], ignore_index=True)

        # 특성 추출
        X_train, y_train = [], []
        for idx, row in train_df.iterrows():
            X_train.append(extract_features(row))
            y_train.append(row["페르소나"])

        X_train = np.array(X_train)
        y_train = np.array(y_train)

        y_train_encoded = self.label_encoder.fit_transform(y_train)

        # 앙상블 모델
        rf = RandomForestClassifier(
            n_estimators=200, max_depth=15, min_samples_split=3,
            class_weight='balanced', random_state=42
        )
        gb = GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42
        )
        self.model = VotingClassifier(
            estimators=[('rf', rf), ('gb', gb)],
            voting='soft', weights=[2, 1]
        )

        self.model.fit(X_train, y_train_encoded)
        self.is_trained = True

        # 모델 저장
        self.save()

        return len(X_train)

    def predict(self, customer_data):
        """
        단일 고객 데이터로 페르소나 예측

        Args:
            customer_data: dict 형태의 고객 데이터

        Returns:
            dict: {
                'persona': 예측된 페르소나,
                'confidence': 신뢰도,
                'probabilities': 각 페르소나별 확률
            }
        """
        if not self.is_trained:
            self.train()

        features = extract_features(customer_data).reshape(1, -1)

        pred_idx = self.model.predict(features)[0]
        proba = self.model.predict_proba(features)[0]

        pred_label = self.label_encoder.inverse_transform([pred_idx])[0]
        confidence = proba[pred_idx]

        # 각 페르소나별 확률
        probabilities = {}
        for i, persona in enumerate(self.label_encoder.classes_):
            probabilities[persona] = float(proba[i])

        return {
            'persona': pred_label,
            'confidence': float(confidence),
            'probabilities': probabilities
        }

    def predict_batch(self, customers_df):
        """
        여러 고객 데이터를 일괄 예측

        Args:
            customers_df: DataFrame 형태의 고객 데이터

        Returns:
            DataFrame with predictions
        """
        if not self.is_trained:
            self.train()

        predictions = []
        confidences = []

        for idx, row in customers_df.iterrows():
            result = self.predict(row.to_dict())
            predictions.append(result['persona'])
            confidences.append(result['confidence'])

        result_df = customers_df.copy()
        result_df['predicted_persona'] = predictions
        result_df['confidence'] = confidences

        return result_df

    def save(self):
        """모델 저장"""
        model_data = {
            'model': self.model,
            'label_encoder': self.label_encoder,
            'is_trained': self.is_trained
        }
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

    def load(self):
        """모델 로드"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.label_encoder = model_data['label_encoder']
                self.is_trained = model_data['is_trained']
            return True
        return False


def convert_to_app_persona(customer_data, predicted_persona, confidence):
    """
    고객 데이터를 기존 앱의 페르소나 형식으로 변환

    Args:
        customer_data: dict 형태의 고객 데이터
        predicted_persona: 예측된 페르소나 이름
        confidence: 신뢰도

    Returns:
        dict: 기존 앱의 페르소나 형식
    """
    profile = PERSONA_PROFILES.get(predicted_persona, {})

    # 피부 고민 파싱
    concerns_str = customer_data.get('concerns', '')
    if isinstance(concerns_str, str):
        concerns = [c.strip() for c in concerns_str.split(',') if c.strip()]
    else:
        concerns = []

    # 나이 추출
    age = customer_data.get('age', 30)
    name = customer_data.get('name', '고객')

    # 멤버십 티어 변환
    tier_map = {'A': '일반', 'M': '실버', 'O': '골드', 'R': 'VIP', 'E': 'VVIP'}
    membership_tier = tier_map.get(customer_data.get('membership_tier', 'M'), '실버')

    # 이탈 위험도 계산
    discount_sens = customer_data.get('discount_sensitivity', '중간')
    loyalty = customer_data.get('loyalty', '중간')

    if loyalty == '낮음' or discount_sens == '매우 높음':
        risk_level = "높음"
        churn_prob = 0.4
    elif loyalty == '중간':
        risk_level = "중"
        churn_prob = 0.25
    else:
        risk_level = "낮음"
        churn_prob = 0.1

    # 구매 데이터
    total_count = customer_data.get('total_count', 0)
    avg_amount = customer_data.get('avg_amount', 30000)
    avg_interval = customer_data.get('avg_interval', 30)

    # primary_brand에서 주 브랜드 추출
    primary_brands = customer_data.get('primary_brand', '')
    if isinstance(primary_brands, str) and primary_brands:
        primary_brand = primary_brands.split(',')[0].strip()
    else:
        primary_brand = "라네즈"  # 기본값

    return {
        "id": customer_data.get('customer_id', 0),
        "name": name,
        "display_name": f"{name}({age}세)",
        "age": age,
        "skin_type": customer_data.get('skin_type', '복합성'),
        "concerns": concerns if concerns else ["보습"],
        "interests": profile.get('keywords', [])[:3],
        "shopping_pattern": profile.get('shopping_pattern', '일반 쇼핑'),
        "lifestyle": profile.get('description', ''),
        "tier": profile.get('tier', 'mid'),

        # 페르소나 분류 정보
        "persona_cluster": predicted_persona,
        "persona_confidence": confidence,

        # 행동 데이터
        "activity": {
            "last_visit_days_ago": 7,
            "visit_frequency": customer_data.get('visit_frequency', '중'),
            "avg_session_minutes": customer_data.get('avg_session_minutes', 10),
            "signup_days_ago": 365
        },

        "purchase": {
            "total_count": int(total_count) if not pd.isna(total_count) else 0,
            "last_purchase_days_ago": 14,
            "avg_interval": int(avg_interval) if not pd.isna(avg_interval) else 30,
            "total_amount": int(total_count * avg_amount) if not pd.isna(total_count) else 0,
            "avg_amount": int(avg_amount) if not pd.isna(avg_amount) else 30000,
            "recent_categories": []
        },

        "brand": {
            "purchase_counts": {primary_brand: int(total_count) if not pd.isna(total_count) else 1},
            "primary_brand": primary_brand,
            "loyalty": customer_data.get('loyalty', '중'),
            "diversity": customer_data.get('diversity', 0.5)
        },

        "promotion": {
            "discount_sensitivity": discount_sens,
            "event_participation_rate": customer_data.get('event_participation_rate', 0.5),
            "preferred_type": customer_data.get('preferred_type', '할인'),
            "coupon_usage_rate": customer_data.get('coupon_usage_rate', 0.5),
            "full_price_ratio": customer_data.get('full_price_ratio', 0.5)
        },

        "risk": {
            "level": risk_level,
            "factors": [],
            "churn_probability": churn_prob
        },

        "seasonal": {
            "gift_purchases": customer_data.get('gift_purchases', False),
            "peak_seasons": [],
            "seasonal_events": []
        },

        "membership": {
            "tier": membership_tier,
            "tier_criteria": "",
            "points": 0
        }
    }


# 테스트용 샘플 고객 5명 (각 페르소나별 대표)
SAMPLE_CUSTOMERS = [
    {
        "customer_id": 1001,
        "name": "김서연",
        "age": 42,
        "skin_type": "민감성",
        "concerns": "주름, 탄력",
        "membership_tier": "R",
        "total_count": 28,
        "avg_amount": 145000,
        "avg_interval": 35,
        "full_price_ratio": 0.82,
        "discount_sensitivity": "낮음",
        "coupon_usage_rate": 0.15,
        "loyalty": "높음",
        "diversity": 0.25,
        "primary_brand": "설화수, 헤라, 아모레퍼시픽",
        "visit_frequency": "높음"
    },
    {
        "customer_id": 1002,
        "name": "이지우",
        "age": 21,
        "skin_type": "지성",
        "concerns": "모공, 피지",
        "membership_tier": "M",
        "total_count": 12,
        "avg_amount": 32000,
        "avg_interval": 25,
        "full_price_ratio": 0.35,
        "discount_sensitivity": "높음",
        "coupon_usage_rate": 0.65,
        "loyalty": "중간",
        "diversity": 0.7,
        "primary_brand": "에뛰드, 에스쁘아, 아모레성수",
        "visit_frequency": "높음"
    },
    {
        "customer_id": 1003,
        "name": "박민지",
        "age": 38,
        "skin_type": "민감성",
        "concerns": "진정, 보습",
        "membership_tier": "O",
        "total_count": 18,
        "avg_amount": 125000,
        "avg_interval": 40,
        "full_price_ratio": 0.78,
        "discount_sensitivity": "낮음",
        "coupon_usage_rate": 0.22,
        "loyalty": "높음",
        "diversity": 0.3,
        "primary_brand": "메이크온, 아이오페, 에스트라",
        "visit_frequency": "중"
    },
    {
        "customer_id": 1004,
        "name": "최수현",
        "age": 35,
        "skin_type": "복합성",
        "concerns": "각질, 탄력",
        "membership_tier": "M",
        "total_count": 22,
        "avg_amount": 38000,
        "avg_interval": 20,
        "full_price_ratio": 0.42,
        "discount_sensitivity": "높음",
        "coupon_usage_rate": 0.75,
        "loyalty": "높음",
        "diversity": 0.45,
        "primary_brand": "일리윤, 라보에이치, 메디안, 아모레베이직",
        "visit_frequency": "높음"
    },
    {
        "customer_id": 1005,
        "name": "정하은",
        "age": 29,
        "skin_type": "건성",
        "concerns": "보습, 주름",
        "membership_tier": "O",
        "total_count": 15,
        "avg_amount": 48000,
        "avg_interval": 30,
        "full_price_ratio": 0.52,
        "discount_sensitivity": "중간",
        "coupon_usage_rate": 0.45,
        "loyalty": "중간",
        "diversity": 0.55,
        "primary_brand": "라네즈, 이니스프리, 한율, 프리메라",
        "visit_frequency": "중"
    }
]


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("페르소나 분류기 테스트")
    print("=" * 60)

    # 분류기 초기화 및 학습
    classifier = PersonaClassifier()

    if not classifier.is_trained:
        print("\n모델 학습 중...")
        n_samples = classifier.train()
        print(f"학습 완료: {n_samples}개 샘플")
    else:
        print("\n저장된 모델 로드 완료")

    # 샘플 고객 5명 예측
    print("\n" + "=" * 60)
    print("샘플 고객 5명 페르소나 예측")
    print("=" * 60)

    for customer in SAMPLE_CUSTOMERS:
        result = classifier.predict(customer)
        print(f"\n【{customer['name']}({customer['age']}세)】")
        print(f"  주 브랜드: {customer['primary_brand']}")
        print(f"  예측 페르소나: {result['persona']}")
        print(f"  신뢰도: {result['confidence']*100:.1f}%")

        # 앱 형식으로 변환
        app_persona = convert_to_app_persona(customer, result['persona'], result['confidence'])
        print(f"  앱 형식 변환: {app_persona['display_name']} - {app_persona['persona_cluster']}")
