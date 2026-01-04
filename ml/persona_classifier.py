# -*- coding: utf-8 -*-
"""
페르소나 분류 모델 - Streamlit 연동용
- 고객 데이터를 받아 7개 페르소나 중 하나로 분류
- 순수 ML 기반 (RandomForest + GradientBoosting 앙상블)
- derived_data.py 모듈을 사용하여 파생지표 계산
"""
import pandas as pd
import numpy as np
import pickle
import os
import glob
import sys
from datetime import datetime, date
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# derived_data.py import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
try:
    from derived_data import (
        calc_age, calc_diversity, calc_full_price_ratio, calc_discount_sensitivity,
        calc_total_amount, calc_membership_tier, calc_days_ago, add_derived_columns
    )
    HAS_DERIVED_DATA = True
except ImportError:
    HAS_DERIVED_DATA = False


# ============================================================
# 파생 데이터 계산 함수들 (derived_data.py fallback)
# ============================================================

def _parse_date(date_str):
    """날짜 문자열을 datetime 객체로 변환"""
    if pd.isna(date_str) or not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ["%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def calculate_age(birthday_str, target_date=None):
    """
    만나이 계산 (derived_data.py의 calc_age 사용)
    - 생일 전: (현재 연도 - 출생 연도) - 1
    - 생일 후: (현재 연도 - 출생 연도)
    """
    if target_date is None:
        target_date = datetime.now()
    elif isinstance(target_date, str):
        target_date = _parse_date(target_date) or datetime.now()
    elif isinstance(target_date, date) and not isinstance(target_date, datetime):
        target_date = datetime.combine(target_date, datetime.min.time())

    if HAS_DERIVED_DATA:
        return calc_age({'birthday': birthday_str}, target_date)

    # fallback
    birthday = _parse_date(birthday_str)
    if birthday is None:
        return None
    age = target_date.year - birthday.year
    if (target_date.month, target_date.day) < (birthday.month, birthday.day):
        age -= 1
    return age if age >= 14 else None


def calculate_days_ago(date_str, target_date=None):
    """경과일 계산 (derived_data.py의 calc_days_ago 사용)"""
    if target_date is None:
        target_date = datetime.now()
    elif isinstance(target_date, str):
        target_date = _parse_date(target_date) or datetime.now()
    elif isinstance(target_date, date) and not isinstance(target_date, datetime):
        target_date = datetime.combine(target_date, datetime.min.time())

    if HAS_DERIVED_DATA:
        return calc_days_ago(date_str, target_date)

    # fallback
    dt = _parse_date(date_str)
    if dt is None:
        return None
    return (target_date - dt).days


def calculate_diversity(primary_brand_str, primary_category_str):
    """
    다양성 지수 계산 (derived_data.py의 calc_diversity 사용)
    diversity = [2 - {(1/brand개수) + (1/category개수)}] / 2
    """
    if HAS_DERIVED_DATA:
        return calc_diversity({
            'primary_brand': primary_brand_str,
            'primary_category': primary_category_str
        })

    # fallback
    if pd.isna(primary_brand_str) or not primary_brand_str:
        brand_count = 1
    else:
        brands = [b.strip() for b in str(primary_brand_str).split(",") if b.strip()]
        brand_count = max(1, len(brands))

    if pd.isna(primary_category_str) or not primary_category_str:
        category_count = 1
    else:
        categories = [c.strip() for c in str(primary_category_str).split(",") if c.strip()]
        category_count = max(1, len(categories))

    diversity = (2 - (1/brand_count + 1/category_count)) / 2
    return round(max(0, min(1, diversity)), 2)


def calculate_discount_sensitivity(coupon_usage_rate, event_participation_rate):
    """할인민감도 = (coupon_usage_rate + event_participation_rate) / 2"""
    coupon = float(coupon_usage_rate) if not pd.isna(coupon_usage_rate) else 0.0
    event = float(event_participation_rate) if not pd.isna(event_participation_rate) else 0.0
    return round((coupon + event) / 2, 2)


def calculate_full_price_ratio(coupon_usage_rate, event_participation_rate):
    """정가 구매 비율 = 1 - (coupon_usage_rate + event_participation_rate)"""
    coupon = float(coupon_usage_rate) if not pd.isna(coupon_usage_rate) else 0.0
    event = float(event_participation_rate) if not pd.isna(event_participation_rate) else 0.0
    return round(max(0, 1 - (coupon + event)), 2)


def calculate_total_amount(total_count, avg_amount):
    """총 구매 금액 = total_count * avg_amount"""
    count = int(total_count) if not pd.isna(total_count) else 0
    avg = float(avg_amount) if not pd.isna(avg_amount) else 0.0
    return int(count * avg)


def calculate_membership_tier(total_amount):
    """
    멤버십 티어 (total_amount 기준)
    E: >= 250만, R: 150~250만, O: 100~150만, M: 50~100만, A: < 50만
    """
    if total_amount >= 2500000:
        return 'E'
    elif total_amount >= 1500000:
        return 'R'
    elif total_amount >= 1000000:
        return 'O'
    elif total_amount >= 500000:
        return 'M'
    else:
        return 'A'


def calculate_derived_data(customer_data, target_date=None):
    """
    고객 데이터에서 모든 파생 데이터를 계산하여 추가

    Args:
        customer_data: dict 형태의 고객 데이터
        target_date: 지정일 (Streamlit에서 전달, 기본값: 오늘)

    Returns:
        dict: 파생 데이터가 추가된 고객 데이터
    """
    if target_date is None:
        target_date = datetime.now()
    elif isinstance(target_date, str):
        target_date = _parse_date(target_date) or datetime.now()

    data = customer_data.copy()

    # 1. total_amount (다른 파생지표에서 사용)
    total_amount = calculate_total_amount(
        data.get('total_count', 0),
        data.get('avg_amount', 0)
    )
    data['total_amount'] = total_amount

    # 2. membership_tier (total_amount 기준)
    data['membership_tier'] = calculate_membership_tier(total_amount)

    # 3. age (만나이)
    age = calculate_age(data.get('birthday'), target_date)
    if age is not None:
        data['age'] = age

    # 4. diversity (다양성 지수)
    data['diversity'] = calculate_diversity(
        data.get('primary_brand'),
        data.get('primary_category')
    )

    # 5. discount_sensitivity, full_price_ratio
    # CSV에 coupon_usage_rate, event_participation_rate가 없으므로 기본값 사용
    coupon = data.get('coupon_usage_rate', 0.3)
    event = data.get('event_participation_rate', 0.2)
    data['discount_sensitivity'] = calculate_discount_sensitivity(coupon, event)
    data['full_price_ratio'] = calculate_full_price_ratio(coupon, event)

    # 6. Days ago 계산들
    data['signup_days_ago'] = calculate_days_ago(data.get('signup_day'), target_date)
    data['visit_days_ago'] = calculate_days_ago(data.get('last_visit_day'), target_date)
    data['view_days_ago'] = calculate_days_ago(data.get('last_view_day'), target_date)
    data['save_days_ago'] = calculate_days_ago(data.get('last_save_day'), target_date)
    data['cart_days_ago'] = calculate_days_ago(data.get('last_cart_day'), target_date)
    data['purchase_days_ago'] = calculate_days_ago(data.get('last_purchase_day'), target_date)

    return data


def calculate_derived_data_df(df, target_date=None):
    """
    DataFrame의 모든 행에 파생 데이터 계산하여 추가

    Args:
        df: pandas DataFrame
        target_date: 지정일 (Streamlit에서 전달)

    Returns:
        DataFrame: 파생 데이터 컬럼이 추가된 DataFrame
    """
    if HAS_DERIVED_DATA:
        return add_derived_columns(df, target_date)

    # fallback - 직접 계산
    if target_date is None:
        target_date = datetime.now()
    elif isinstance(target_date, str):
        target_date = _parse_date(target_date) or datetime.now()

    result_df = df.copy()

    # total_amount
    result_df['total_amount'] = result_df.apply(
        lambda row: calculate_total_amount(row.get('total_count', 0), row.get('avg_amount', 0)),
        axis=1
    )

    # membership_tier
    result_df['membership_tier'] = result_df['total_amount'].apply(calculate_membership_tier)

    # age
    result_df['age'] = result_df['birthday'].apply(
        lambda x: calculate_age(x, target_date)
    )

    # diversity
    result_df['diversity'] = result_df.apply(
        lambda row: calculate_diversity(row.get('primary_brand'), row.get('primary_category')),
        axis=1
    )

    # Days ago
    date_columns = {
        'signup_days_ago': 'signup_day',
        'visit_days_ago': 'last_visit_day',
        'view_days_ago': 'last_view_day',
        'save_days_ago': 'last_save_day',
        'cart_days_ago': 'last_cart_day',
        'purchase_days_ago': 'last_purchase_day'
    }

    for new_col, source_col in date_columns.items():
        if source_col in result_df.columns:
            result_df[new_col] = result_df[source_col].apply(
                lambda x: calculate_days_ago(x, target_date)
            )

    return result_df

# 브랜드 클러스터 정의 (7개 클러스터 - 30개 브랜드)
# 2024.01 라벨링 데이터 기반 업데이트
BRAND_CLUSTERS = {
    "테크니컬 홈케어족": ["메이크온", "아이오페", "에이피뷰티", "바이탈뷰티", "홀리추얼"],
    "하이엔드 품격가": ["설화수", "헤라", "아모레퍼시픽", "에이피뷰티", "홀리추얼"],
    "웰니스 힐링 탐험가": ["퍼즐우드", "오설록", "롱테이크", "해피바스"],
    "연구소 기반 해결사": ["아이오페", "에스트라", "프리메라", "마몽드", "한율", "비레디", "려", "미쟝센"],
    "트렌디 Z세대": ["에뛰드", "에스쁘아", "아모레성수", "롱테이크", "앞바다즈"],
    "합리적 큐레이터": ["라네즈", "이니스프리", "미쟝센", "바이탈뷰티", "오딧세이"],
    "실속형 가계 수호자": ["일리윤", "라보에이치", "메디안", "해피바스", "아모레베이직", "이니스프리"]
}

# 페르소나별 특성 정의 (CRM 메시지 생성용)
# 2024.01 라벨링 데이터 기반 업데이트
PERSONA_PROFILES = {
    "테크니컬 홈케어족": {
        "description": "뷰티 디바이스와 고기능성 스킨케어를 선호하는 전문 홈케어 고객",
        "shopping_pattern": "프리미엄 기능성 제품 선호, 기술력과 효능 중시",
        "tier": "premium",
        "keywords": ["뷰티디바이스", "홈케어", "고기능성", "LED", "갈바닉"],
        "primary_categories": ["뷰티디바이스", "스킨케어", "뷰티푸드"],
        "price_sensitivity": "낮음",
        "preferred_brands": ["메이크온", "아이오페", "에이피뷰티", "홀리추얼"],
        "message_tone": "전문적이고 기술적인, 효능 중심의 설명"
    },
    "하이엔드 품격가": {
        "description": "프리미엄 럭셔리 브랜드를 선호하는 품격있는 VIP 고객",
        "shopping_pattern": "프리미엄 브랜드 충성, 정가 구매 비율 높음, 샘플/사은품 선호",
        "tier": "premium",
        "keywords": ["럭셔리", "프리미엄", "한방", "안티에이징", "선물"],
        "primary_categories": ["스킨케어", "메이크업", "선물추천"],
        "price_sensitivity": "낮음",
        "preferred_brands": ["설화수", "헤라", "아모레퍼시픽", "에이피뷰티"],
        "message_tone": "고급스럽고 우아한, 품격있는 표현"
    },
    "웰니스 힐링 탐험가": {
        "description": "웰니스, 힐링, 라이프스타일 브랜드에 관심있는 탐험형 고객",
        "shopping_pattern": "새로운 브랜드/제품 탐색, 체험 중시, 샘플 선호",
        "tier": "mid",
        "keywords": ["웰니스", "힐링", "티", "향기", "라이프스타일"],
        "primary_categories": ["뷰티푸드", "차(TEA)", "바디", "향수"],
        "price_sensitivity": "중간",
        "preferred_brands": ["롱테이크", "퍼즐우드", "오설록", "이니스프리"],
        "message_tone": "편안하고 여유로운, 새로운 경험 강조"
    },
    "연구소 기반 해결사": {
        "description": "피부 고민 해결을 위해 과학적/더마 브랜드를 선호하는 고객",
        "shopping_pattern": "성분과 효능 중시, 문제 해결형 구매, 꼼꼼한 비교",
        "tier": "mid",
        "keywords": ["더마", "민감성", "진정", "과학적", "효능"],
        "primary_categories": ["스킨케어", "남성", "세트"],
        "price_sensitivity": "중간",
        "preferred_brands": ["아이오페", "에스트라", "프리메라", "마몽드", "한율"],
        "message_tone": "전문적이고 신뢰감 있는, 효능/성분 중심 설명"
    },
    "트렌디 Z세대": {
        "description": "트렌드에 민감한 MZ세대, SNS 영향력이 큰 활발한 소비자",
        "shopping_pattern": "트렌디한 제품 선호, 가성비 중시, 이벤트 참여 활발",
        "tier": "affordable",
        "keywords": ["트렌디", "컬러", "SNS", "신상", "한정판"],
        "primary_categories": ["메이크업", "향수", "바디"],
        "price_sensitivity": "높음",
        "preferred_brands": ["에뛰드", "에스쁘아", "아모레성수", "롱테이크"],
        "message_tone": "발랄하고 트렌디한, SNS 감성의 표현"
    },
    "합리적 큐레이터": {
        "description": "합리적인 가격대에서 좋은 품질을 추구하는 똑똑한 소비자",
        "shopping_pattern": "가성비 중시, 리뷰 꼼꼼히 확인, 다양한 브랜드 시도",
        "tier": "mid",
        "keywords": ["가성비", "합리적", "베스트셀러", "추천", "리뷰"],
        "primary_categories": ["스킨케어", "헤어", "바디", "세트"],
        "price_sensitivity": "중간",
        "preferred_brands": ["라네즈", "이니스프리", "미쟝센", "바이탈뷰티"],
        "message_tone": "실용적이고 합리적인, 가치 중심의 표현"
    },
    "실속형 가계 수호자": {
        "description": "가족용 생활용품 중심 구매, 할인/쿠폰에 민감한 알뜰 소비자",
        "shopping_pattern": "할인/쿠폰 적극 활용, 대용량 선호, 사은품 중시",
        "tier": "affordable",
        "keywords": ["가족", "대용량", "할인", "실속", "생활용품"],
        "primary_categories": ["바디", "생활용품", "구강", "헤어"],
        "price_sensitivity": "높음",
        "preferred_brands": ["일리윤", "메디안", "라보에이치", "해피바스", "아모레베이직"],
        "message_tone": "실용적이고 혜택 중심의, 가성비 강조 표현"
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


def extract_features(row, target_date=None):
    """
    고객 데이터에서 특성 추출

    customer_data_1000.csv 기준 컬럼 구조 (2026.01 최종):
    - primary_brand: 콤마로 구분된 브랜드 목록
    - primary_category: 콤마로 구분된 카테고리 (스킨케어>크림 형식)
    - preferred_promotion: 신상품/사은품증정/할인판매/한정판매
    - visit_frequency: 텍스트 (낮음/중간/높음)
    - total_count, avg_amount, avg_session_minutes

    파생 데이터 (derived_data.py로 계산):
    - age: 만나이 (birthday에서 계산)
    - diversity: 다양성 지수 (브랜드/카테고리 수로 계산)
    - membership_tier: 멤버십 티어 (total_amount 기준)
    - total_amount: 총 구매금액 (total_count * avg_amount)
    """
    # 브랜드 파싱 - primary_brand 컬럼 사용
    primary_brands = parse_brands(row.get("primary_brand", ""))

    # 각 페르소나별 브랜드 점수
    brand_scores = []
    for persona in BRAND_CLUSTERS.keys():
        brand_score = count_brand_matches(primary_brands, BRAND_CLUSTERS[persona])
        brand_scores.append(brand_score)

    # ===== 파생 데이터 계산 =====

    # 나이 계산 (birthday에서 만나이 계산)
    age = row.get("age", None)
    if age is None or pd.isna(age):
        age = calculate_age(row.get("birthday", ""), target_date)
        if age is None:
            age = 30  # 기본값

    # total_amount 계산
    total_count = row.get("total_count", 0)
    if pd.isna(total_count):
        total_count = 0
    avg_amount = row.get("avg_amount", 30000)
    if pd.isna(avg_amount):
        avg_amount = 30000
    total_amount = calculate_total_amount(total_count, avg_amount)

    # membership_tier 계산 (total_amount 기준)
    tier = row.get("membership_tier", None)
    if tier is None or pd.isna(tier):
        tier = calculate_membership_tier(total_amount)
    # E(최상위) > R > O > M > A(최하위) 순서로 인코딩
    tier_map = {"E": 4, "R": 3, "O": 2, "M": 1, "A": 0}
    tier_encoded = tier_map.get(tier, 1)

    # diversity 계산 (브랜드/카테고리 수 기준)
    diversity = row.get("diversity", None)
    if diversity is None or pd.isna(diversity):
        diversity = calculate_diversity(
            row.get("primary_brand", ""),
            row.get("primary_category", "")
        )
    else:
        diversity = float(diversity)

    # ===== CSV에 있는 데이터 =====

    # preferred_promotion으로 프로모션 선호도 인코딩
    # 새 데이터: 신상품/사은품증정/할인판매/한정판매
    preferred_promotion = row.get("preferred_promotion", "")
    if pd.isna(preferred_promotion):
        preferred_promotion = ""
    promo_map = {
        "할인판매": 3, "할인": 3,
        "한정판매": 2, "포인트": 2,
        "사은품증정": 1, "사은품": 1,
        "신상품": 0, "샘플": 0
    }
    promo_encoded = promo_map.get(preferred_promotion, 1)

    # visit_frequency 처리 (텍스트)
    visit_freq = row.get("visit_frequency", "중간")
    if pd.isna(visit_freq):
        freq_encoded = 1
    elif isinstance(visit_freq, str):
        freq_map = {"낮음": 0, "중간": 1, "높음": 2}
        freq_encoded = freq_map.get(visit_freq, 1)
    else:
        freq_encoded = min(2, int(float(visit_freq)))

    # avg_session_minutes - 평균 세션 시간
    avg_session = row.get("avg_session_minutes", 10)
    if pd.isna(avg_session):
        avg_session = 10
    avg_session = float(avg_session)

    # 피부타입/고민 인코딩
    skin_type = row.get("skin_type", "없음")
    if pd.isna(skin_type) or skin_type == "없음":
        skin_encoded = 0.5
    else:
        skin_map = {"건성": 0.2, "극건성": 0.1, "지성": 0.8, "수분부족지성": 0.7, "복합성": 0.5, "민감성": 0.3}
        skin_encoded = skin_map.get(skin_type, 0.5)

    concerns = row.get("concerns", "고민없음")
    if pd.isna(concerns) or concerns == "고민없음" or concerns == "없음":
        concern_count = 0
    else:
        concern_count = len([c.strip() for c in str(concerns).split(",") if c.strip()])

    features = [
        age / 100,
        diversity,  # 파생 데이터
        tier_encoded / 4,  # 파생 데이터 (membership_tier)
        promo_encoded / 3,
        freq_encoded / 2,
        avg_amount / 100000,
        total_count / 50,
        avg_session / 60,  # 최대 60분 기준 정규화
        skin_encoded,
        min(concern_count / 5, 1.0),  # 고민 개수 (최대 5개 기준)
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


def convert_to_app_persona(customer_data, predicted_persona, confidence, target_date=None):
    """
    고객 데이터를 기존 앱의 페르소나 형식으로 변환
    customer_data_1000.csv 기준 컬럼 구조 지원 (2026.01 최종)

    Args:
        customer_data: dict 형태의 고객 데이터
        predicted_persona: 예측된 페르소나 이름
        confidence: 신뢰도
        target_date: 지정일 (Streamlit에서 전달, 파생지표 계산용)

    Returns:
        dict: 기존 앱의 페르소나 형식
    """
    profile = PERSONA_PROFILES.get(predicted_persona, {})

    # ===== 파생 데이터 계산 (target_date 기준) =====
    derived = calculate_derived_data(customer_data, target_date)

    # 피부 고민 파싱 ("고민없음" 처리 포함)
    concerns_str = customer_data.get('concerns', '')
    if isinstance(concerns_str, str) and concerns_str and concerns_str not in ['없음', '고민없음']:
        concerns = [c.strip() for c in concerns_str.split(',') if c.strip() and c.strip() not in ['없음', '고민없음']]
    else:
        concerns = []

    # 피부 타입 ("없음" 처리)
    skin_type = customer_data.get('skin_type', '')
    if pd.isna(skin_type) or skin_type == '없음' or not skin_type:
        skin_type = '복합성'

    # 나이 (파생 데이터에서 가져옴)
    age = derived.get('age', 30)
    if age is None:
        age = 30
    name = customer_data.get('name', '고객')

    # 멤버십 티어 (파생 데이터 - total_amount 기준)
    # E(최상위) > R > O > M > A(최하위)
    tier_display_map = {'E': 'VIP', 'R': '골드', 'O': '실버', 'M': '브론즈', 'A': '일반'}
    raw_tier = derived.get('membership_tier', 'A')
    membership_tier = tier_display_map.get(raw_tier, '일반')

    # 총 구매금액 (파생 데이터)
    total_amount = derived.get('total_amount', 0)

    # diversity (파생 데이터)
    diversity = derived.get('diversity', 0.5)

    # discount_sensitivity (파생 데이터) - 텍스트 변환
    discount_sens_val = derived.get('discount_sensitivity', 0.25)
    if discount_sens_val >= 0.35:
        discount_sens = "높음"
    elif discount_sens_val >= 0.2:
        discount_sens = "중간"
    else:
        discount_sens = "낮음"

    # full_price_ratio (파생 데이터)
    full_price_ratio = derived.get('full_price_ratio', 0.5)

    # 경과일 (파생 데이터)
    signup_days_ago = derived.get('signup_days_ago') or 365
    visit_days_ago = derived.get('visit_days_ago') or 7
    purchase_days_ago = derived.get('purchase_days_ago') or 14

    # ===== CSV에 있는 데이터 =====

    # 구매 데이터
    total_count = customer_data.get('total_count', 0)
    if pd.isna(total_count):
        total_count = 0
    avg_amount = customer_data.get('avg_amount', 30000)
    if pd.isna(avg_amount):
        avg_amount = 30000

    # preferred_promotion 처리 (새 데이터 형식)
    preferred_promotion = customer_data.get('preferred_promotion', '')
    if pd.isna(preferred_promotion):
        preferred_promotion = '신상품'
    # 표시용 변환
    promo_display_map = {
        '신상품': '샘플', '사은품증정': '사은품', '할인판매': '할인', '한정판매': '포인트'
    }
    preferred_type = promo_display_map.get(preferred_promotion, preferred_promotion)

    # 주 브랜드 추출 (primary_brand)
    primary_brands_str = customer_data.get('primary_brand', '')
    if pd.isna(primary_brands_str) or not primary_brands_str:
        primary_brand = "라네즈"
    elif isinstance(primary_brands_str, str) and primary_brands_str:
        primary_brand = primary_brands_str.split(',')[0].strip()
    else:
        primary_brand = "라네즈"

    # 최근 카테고리 파싱 (primary_category - 스킨케어>크림 형식)
    categories_str = customer_data.get('primary_category', '')
    if isinstance(categories_str, str) and categories_str:
        # "스킨케어>크림" 형식에서 대분류만 추출
        recent_categories = []
        for c in categories_str.split(','):
            c = c.strip()
            if '>' in c:
                recent_categories.append(c.split('>')[0].strip())
            elif c:
                recent_categories.append(c)
        recent_categories = list(set(recent_categories))  # 중복 제거
    else:
        recent_categories = []

    # visit_frequency 처리
    visit_freq = customer_data.get('visit_frequency', '중간')
    if pd.isna(visit_freq):
        visit_freq = '중간'

    # avg_session_minutes 처리
    avg_session = customer_data.get('avg_session_minutes', 10)
    if pd.isna(avg_session):
        avg_session = 10

    # 이탈 위험도 계산 (파생 데이터 기반)
    if discount_sens_val >= 0.35 and full_price_ratio < 0.3:
        risk_level = "높음"
        churn_prob = 0.4
    elif discount_sens_val >= 0.25:
        risk_level = "중"
        churn_prob = 0.25
    else:
        risk_level = "낮음"
        churn_prob = 0.1

    # 브랜드 충성도 (diversity 기반)
    if diversity < 0.3:
        loyalty = "높음"
    elif diversity < 0.6:
        loyalty = "중간"
    else:
        loyalty = "낮음"

    return {
        "id": customer_data.get('customer_id', 0),
        "name": name,
        "display_name": f"{name}({int(age)}세)",
        "age": int(age),
        "skin_type": skin_type,
        "concerns": concerns if concerns else ["보습"],
        "interests": profile.get('keywords', [])[:3],
        "shopping_pattern": profile.get('shopping_pattern', '일반 쇼핑'),
        "lifestyle": profile.get('description', ''),
        "tier": profile.get('tier', 'mid'),

        # 페르소나 분류 정보
        "persona_cluster": predicted_persona,
        "persona_confidence": confidence,

        # 행동 데이터 (파생 데이터 사용)
        "activity": {
            "last_visit_days_ago": int(visit_days_ago),
            "visit_frequency": visit_freq,
            "avg_session_minutes": int(avg_session),
            "signup_days_ago": int(signup_days_ago)
        },

        "purchase": {
            "total_count": int(total_count),
            "last_purchase_days_ago": int(purchase_days_ago),
            "avg_interval": 30,
            "total_amount": int(total_amount),
            "avg_amount": int(avg_amount),
            "recent_categories": recent_categories
        },

        "brand": {
            "purchase_counts": {primary_brand: int(total_count) if total_count > 0 else 1},
            "primary_brand": primary_brand,
            "loyalty": loyalty,
            "diversity": float(diversity)
        },

        "promotion": {
            "discount_sensitivity": discount_sens,
            "discount_sensitivity_value": float(discount_sens_val),
            "event_participation_rate": 0.0,  # CSV에 없음
            "preferred_type": preferred_type,
            "coupon_usage_rate": 0.0,  # CSV에 없음
            "full_price_ratio": float(full_price_ratio)
        },

        "risk": {
            "level": risk_level,
            "factors": [],
            "churn_probability": churn_prob
        },

        "seasonal": {
            "gift_purchases": False,
            "peak_seasons": [],
            "seasonal_events": []
        },

        "membership": {
            "tier": membership_tier,
            "tier_criteria": "",
            "points": 0
        }
    }


# 테스트용 샘플 고객 7명 (각 페르소나별 대표)
# customer_data_1000.csv 컬럼 구조 기준 (2026.01 최종)
# - 파생 데이터(membership_tier, age, diversity 등)는 derived_data.py로 계산
SAMPLE_CUSTOMERS = [
    {
        # 테크니컬 홈케어족 대표 - 뷰티 디바이스/고기능성 스킨케어
        "customer_id": "C005",
        "name": "송성민",
        "birthday": "1986.09.27",
        "signup_day": "2025.06.27",
        "last_purchase_day": "2025.10.06",
        "last_visit_day": "2025.12.26",
        "last_view_day": "2025.12.03",
        "last_save_day": "2025.12.26",
        "last_cart_day": "2025.12.09",
        "skin_type": "없음",
        "concerns": "고민없음",
        "total_count": 6,
        "avg_amount": 67678,
        "visit_frequency": "낮음",
        "primary_brand": "메이크온,롱테이크,아모레퍼시픽",
        "primary_category": "뷰티디바이스>마사지,뷰티디바이스>리프팅,스킨케어>크림,스킨케어>세럼,스킨케어>에센스",
        "preferred_promotion": "할인판매",
        "avg_session_minutes": 2
    },
    {
        # 하이엔드 품격가 대표 - 프리미엄 럭셔리 브랜드
        "customer_id": "C006",
        "name": "홍지은",
        "birthday": "1991.03.12",
        "signup_day": "2025.11.13",
        "last_purchase_day": "2025.11.02",
        "last_visit_day": "2025.12.26",
        "last_view_day": "2025.12.14",
        "last_save_day": "2025.12.04",
        "last_cart_day": "2025.12.24",
        "skin_type": "복합성",
        "concerns": "건조함,탄력없음,민감성",
        "total_count": 16,
        "avg_amount": 37085,
        "visit_frequency": "낮음",
        "primary_brand": "아모레퍼시픽,롱테이크,아모레성수",
        "primary_category": "스킨케어>에센스,스킨케어>크림,스킨케어>세럼,라이프>향",
        "preferred_promotion": "사은품증정",
        "avg_session_minutes": 10
    },
    {
        # 웰니스 힐링 탐험가 대표 - 라이프스타일/힐링
        "customer_id": "C010",
        "name": "장태영",
        "birthday": "1997.03.17",
        "signup_day": "2025.07.26",
        "last_purchase_day": "2025.12.20",
        "last_visit_day": "2025.12.05",
        "last_view_day": "2025.11.09",
        "last_save_day": "2025.11.20",
        "last_cart_day": "2025.10.25",
        "skin_type": "없음",
        "concerns": "고민없음",
        "total_count": 26,
        "avg_amount": 42734,
        "visit_frequency": "낮음",
        "primary_brand": "오설록,해피바스",
        "primary_category": "라이프>티,바디>워시",
        "preferred_promotion": "신상품",
        "avg_session_minutes": 6
    },
    {
        # 연구소 기반 해결사 대표 - 더마/과학적 브랜드
        "customer_id": "C009",
        "name": "정지호",
        "birthday": "1998.04.01",
        "signup_day": "2025.10.02",
        "last_purchase_day": "2025.10.19",
        "last_visit_day": "2025.12.22",
        "last_view_day": "2025.12.19",
        "last_save_day": "2025.12.14",
        "last_cart_day": "2025.12.19",
        "skin_type": "극건성",
        "concerns": "건조함",
        "total_count": 10,
        "avg_amount": 50452,
        "visit_frequency": "중간",
        "primary_brand": "마몽드",
        "primary_category": "스킨케어>크림,스킨케어>토너",
        "preferred_promotion": "할인판매",
        "avg_session_minutes": 11
    },
    {
        # 트렌디 Z세대 대표 - MZ세대 트렌디
        "customer_id": "C007",
        "name": "신수진",
        "birthday": "2006.11.19",
        "signup_day": "2025.07.21",
        "last_purchase_day": "2025.11.03",
        "last_visit_day": "2025.12.03",
        "last_view_day": "2025.11.11",
        "last_save_day": "2025.11.02",
        "last_cart_day": "2025.11.29",
        "skin_type": "없음",
        "concerns": "고민없음",
        "total_count": 40,
        "avg_amount": 31886,
        "visit_frequency": "중간",
        "primary_brand": "롱테이크,설화수,에뛰드,헤라",
        "primary_category": "스킨케어>크림,스킨케어>세럼,스킨케어>에센스,메이크업>베이스,메이크업>립",
        "preferred_promotion": "한정판매",
        "avg_session_minutes": 20
    },
    {
        # 합리적 큐레이터 대표 - 가성비 중시
        "customer_id": "C008",
        "name": "권서현",
        "birthday": "1980.11.17",
        "signup_day": "2025.05.06",
        "last_purchase_day": "2025.11.22",
        "last_visit_day": "2025.11.20",
        "last_view_day": "2025.11.18",
        "last_save_day": "2025.10.07",
        "last_cart_day": "2025.11.08",
        "skin_type": "수분부족지성",
        "concerns": "모공",
        "total_count": 33,
        "avg_amount": 21682,
        "visit_frequency": "낮음",
        "primary_brand": "아이오페,프리메라,에스트라,미쟝센,해피바스",
        "primary_category": "스킨케어>앰플,스킨케어>세럼,바디>오일,스킨케어>크림,스킨케어>토너",
        "preferred_promotion": "할인판매",
        "avg_session_minutes": 9
    },
    {
        # 실속형 가계 수호자 대표 - 가족용/생활용품
        "customer_id": "C004",
        "name": "강현우",
        "birthday": "1966.09.17",
        "signup_day": "2025.07.05",
        "last_purchase_day": "2025.10.05",
        "last_visit_day": "2025.11.23",
        "last_view_day": "2025.11.16",
        "last_save_day": "2025.10.17",
        "last_cart_day": "2025.10.15",
        "skin_type": "수분부족지성",
        "concerns": "모공,칙칙함",
        "total_count": 15,
        "avg_amount": 40601,
        "visit_frequency": "낮음",
        "primary_brand": "이니스프리,에스트라",
        "primary_category": "바디>로션,스킨케어>크림,스킨케어>토너",
        "preferred_promotion": "할인판매",
        "avg_session_minutes": 4
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
        # birthday에서 나이 계산
        birthday = customer.get('birthday', '')
        if birthday:
            try:
                birth_year = int(str(birthday).split(".")[0])
                age = 2025 - birth_year
            except:
                age = 30
        else:
            age = 30
        print(f"\n【{customer['name']}({age}세)】")
        print(f"  주 브랜드: {customer['primary_brand']}")
        print(f"  예측 페르소나: {result['persona']}")
        print(f"  신뢰도: {result['confidence']*100:.1f}%")

        # 앱 형식으로 변환
        app_persona = convert_to_app_persona(customer, result['persona'], result['confidence'])
        print(f"  앱 형식 변환: {app_persona['display_name']} - {app_persona['persona_cluster']}")
