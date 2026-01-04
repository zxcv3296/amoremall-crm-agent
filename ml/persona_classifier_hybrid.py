# -*- coding: utf-8 -*-
"""
페르소나 분류 모델 - 하이브리드 방식
===================================
1차: 규칙 기반 분류 (명확한 조건에 해당하는 경우)
2차: ML 기반 분류 (규칙에 해당하지 않는 경우)
"""
import pandas as pd
import numpy as np
import pickle
import os
import glob
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# 브랜드 클러스터 정의 (7개 클러스터 - 30개 브랜드)
BRAND_CLUSTERS = {
    "테크니컬 홈케어족": ["메이크온", "아이오페", "바이탈뷰티"],
    "하이엔드 품격가": ["설화수", "헤라", "에이피뷰티", "라네즈", "아모레퍼시픽"],
    "웰니스 힐링 탐험가": ["퍼즐우드", "오설록", "롱테이크"],
    "연구소 기반 해결사": ["프리메라", "한율", "에스트라", "비레디", "려", "미쟝센", "마몽드"],
    "트렌디 Z세대": ["앞바다즈", "에스쁘아", "에뛰드", "아모레성수"],
    "합리적 큐레이터": ["오딧세이", "이니스프리", "홀리추얼"],
    "실속형 가계 수호자": ["일리윤", "라보에이치", "해피바스", "아모레베이직", "메디안"]
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


def get_dominant_persona_by_brand(brands):
    """
    브랜드 기반으로 가장 매칭이 많은 페르소나 반환
    Returns: (persona_name, match_count, total_brands) or (None, 0, 0)
    """
    if not brands:
        return None, 0, 0

    scores = {}
    for persona, cluster_brands in BRAND_CLUSTERS.items():
        score = count_brand_matches(brands, cluster_brands)
        scores[persona] = score

    max_score = max(scores.values())
    if max_score == 0:
        return None, 0, len(brands)

    # 가장 높은 점수의 페르소나
    best_persona = max(scores, key=scores.get)
    return best_persona, max_score, len(brands)


def rule_based_classify(row):
    """
    규칙 기반 페르소나 분류

    Returns:
        dict: {
            'persona': 분류된 페르소나 (None if no rule matched),
            'rule': 적용된 규칙,
            'confidence': 신뢰도
        }
    """
    # 데이터 추출
    age = row.get('age', 30)
    if pd.isna(age):
        age = 30

    primary_brands = parse_brands(row.get('primary_brand', ''))

    discount_sens = row.get('discount_sensitivity', '중간')
    discount_map = {"낮음": 0.25, "중간": 0.5, "높음": 0.75, "매우 높음": 1.0}
    discount_value = discount_map.get(str(discount_sens), 0.5)

    full_price_ratio = row.get('full_price_ratio', 0.5)
    if pd.isna(full_price_ratio):
        full_price_ratio = 0.5

    coupon_usage_rate = row.get('coupon_usage_rate', 0.5)
    if pd.isna(coupon_usage_rate):
        coupon_usage_rate = 0.5

    diversity = row.get('diversity', 0.5)
    if pd.isna(diversity):
        diversity = 0.5

    avg_amount = row.get('avg_amount', 30000)
    if pd.isna(avg_amount):
        avg_amount = 30000

    tier = row.get('membership_tier', 'M')

    # 브랜드 매칭 점수 계산
    brand_persona, brand_match_count, total_brands = get_dominant_persona_by_brand(primary_brands)
    brand_match_ratio = brand_match_count / total_brands if total_brands > 0 else 0

    # ==========================================
    # 규칙 기반 분류 (우선순위 순)
    # ==========================================

    # 각 페르소나별 브랜드 매칭 수 계산
    curator_brands = BRAND_CLUSTERS["합리적 큐레이터"]
    curator_match = count_brand_matches(primary_brands, curator_brands)

    research_brands = BRAND_CLUSTERS["연구소 기반 해결사"]
    research_match = count_brand_matches(primary_brands, research_brands)

    practical_brands = BRAND_CLUSTERS["실속형 가계 수호자"]
    practical_match = count_brand_matches(primary_brands, practical_brands)

    wellness_brands = BRAND_CLUSTERS["웰니스 힐링 탐험가"]
    wellness_match = count_brand_matches(primary_brands, wellness_brands)

    trendy_brands = BRAND_CLUSTERS["트렌디 Z세대"]
    trendy_match = count_brand_matches(primary_brands, trendy_brands)

    highend_brands = BRAND_CLUSTERS["하이엔드 품격가"]
    highend_match = count_brand_matches(primary_brands, highend_brands)

    tech_brands = BRAND_CLUSTERS["테크니컬 홈케어족"]
    tech_match = count_brand_matches(primary_brands, tech_brands)

    # 1. 트렌디 Z세대: 나이 < 25 AND 브랜드 매칭
    if age < 25 and trendy_match >= 1:
        return {
            'persona': '트렌디 Z세대',
            'rule': f'age({age}) < 25 AND 트렌디 브랜드 매칭({trendy_match}개)',
            'confidence': 0.9
        }

    # 2. 테크니컬 홈케어족: 메이크온 포함 AND (avg_amount > 100000 OR 아이오페/바이탈뷰티 포함)
    has_makeon = any('메이크온' in b for b in primary_brands)
    has_iope_vital = any(('아이오페' in b or '바이탈뷰티' in b) for b in primary_brands)
    if has_makeon and (avg_amount > 100000 or has_iope_vital):
        return {
            'persona': '테크니컬 홈케어족',
            'rule': f'메이크온 포함 AND (avg_amount({avg_amount}) > 100000 OR 아이오페/바이탈뷰티)',
            'confidence': 0.85
        }

    # 2-1. 테크니컬 홈케어족: 바이탈뷰티가 주 브랜드인 경우 (wellness보다 우선)
    has_vital_primary = any('바이탈뷰티' in b for b in primary_brands[:2]) if len(primary_brands) >= 1 else False
    if has_vital_primary and wellness_match == 0:
        return {
            'persona': '테크니컬 홈케어족',
            'rule': f'바이탈뷰티 주 브랜드 AND 웰니스 브랜드 없음',
            'confidence': 0.8
        }

    # 3. 하이엔드 품격가: 설화수/헤라 포함 AND full_price_ratio > 0.6 AND tier in [R, E]
    has_sulwhasoo_hera = any(('설화수' in b or '헤라' in b) for b in primary_brands)
    if has_sulwhasoo_hera and full_price_ratio > 0.6 and tier in ['R', 'E']:
        return {
            'persona': '하이엔드 품격가',
            'rule': f'설화수/헤라 포함 AND full_price_ratio({full_price_ratio:.2f}) > 0.6 AND tier={tier}',
            'confidence': 0.9
        }

    # 4. 웰니스 힐링 탐험가: 오설록/퍼즐우드/롱테이크 중 2개 이상 OR (1개 AND diversity > 0.5)
    # 단, 바이탈뷰티만 있는 경우는 테크니컬로 분류
    if wellness_match >= 2 or (wellness_match >= 1 and diversity > 0.5 and not has_vital_primary):
        return {
            'persona': '웰니스 힐링 탐험가',
            'rule': f'웰니스 브랜드 {wellness_match}개 매칭 AND diversity({diversity:.2f})',
            'confidence': 0.85
        }

    # 5. 합리적 큐레이터: 이니스프리/홀리추얼/오딧세이 포함
    #    - curator 브랜드가 research 브랜드보다 많거나 같으면 curator
    #    - 또는 curator만 있고 research가 없는 경우
    skin_type = str(row.get('skin_type', ''))
    concerns = str(row.get('concerns', ''))
    is_sensitive = '민감' in skin_type or '민감' in concerns or '진정' in concerns

    if curator_match >= 1:
        # curator 브랜드가 더 많거나 같은 경우
        if curator_match >= research_match:
            return {
                'persona': '합리적 큐레이터',
                'rule': f'합리적 큐레이터 브랜드({curator_match}) >= 연구소 브랜드({research_match})',
                'confidence': 0.85
            }
        # curator 브랜드가 있고, 민감성이 아닌 경우
        elif not is_sensitive:
            return {
                'persona': '합리적 큐레이터',
                'rule': f'합리적 큐레이터 브랜드 매칭({curator_match}) AND 비민감성',
                'confidence': 0.8
            }

    # 6. 연구소 기반 해결사: 프리메라/에스트라/한율/비레디 포함 AND 민감성/진정 관련
    has_research_core = any((b in ['프리메라', '에스트라', '한율', '비레디']) for b in primary_brands) or \
                        any(('프리메라' in b or '에스트라' in b or '한율' in b or '비레디' in b) for b in primary_brands)
    if has_research_core and is_sensitive:
        return {
            'persona': '연구소 기반 해결사',
            'rule': f'연구소 핵심 브랜드 포함 AND 민감성/진정 관련',
            'confidence': 0.85
        }

    # 6-1. 연구소 기반 해결사: 연구소 브랜드가 2개 이상
    if research_match >= 2:
        return {
            'persona': '연구소 기반 해결사',
            'rule': f'연구소 브랜드 {research_match}개 매칭',
            'confidence': 0.8
        }

    # 7. 실속형 가계 수호자: 일리윤/라보에이치/해피바스/메디안 포함 AND coupon_usage_rate > 0.5
    if practical_match >= 1 and coupon_usage_rate > 0.5:
        return {
            'persona': '실속형 가계 수호자',
            'rule': f'실속형 브랜드 {practical_match}개 매칭 AND coupon_usage_rate({coupon_usage_rate:.2f}) > 0.5',
            'confidence': 0.8
        }

    # 8. 하이엔드 품격가 (조건 완화): 설화수/헤라/라네즈/에이피뷰티 포함
    if highend_match >= 2 or (highend_match >= 1 and full_price_ratio > 0.5):
        return {
            'persona': '하이엔드 품격가',
            'rule': f'하이엔드 브랜드 {highend_match}개 OR full_price_ratio({full_price_ratio:.2f}) > 0.5',
            'confidence': 0.75
        }

    # 9. 브랜드 매칭이 50% 이상이면 해당 페르소나로 분류
    if brand_persona and brand_match_ratio >= 0.5:
        return {
            'persona': brand_persona,
            'rule': f'브랜드 매칭 비율 {brand_match_ratio:.0%} ({brand_match_count}/{total_brands})',
            'confidence': 0.7 + (brand_match_ratio * 0.2)
        }

    # 규칙에 해당하지 않음 → ML로 fallback
    return {
        'persona': None,
        'rule': None,
        'confidence': 0
    }


def extract_features(row):
    """고객 데이터에서 ML 특성 추출"""
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
    discount_encoded = discount_map.get(str(discount_sens), 1)

    loyalty = row.get("loyalty", "중간")
    loyalty_map = {"낮음": 0, "중간": 1, "높음": 2, "매우 높음": 3}
    loyalty_encoded = loyalty_map.get(str(loyalty), 1)

    visit_freq = row.get("visit_frequency", "중간")
    freq_map = {"낮음": 0, "중간": 1, "높음": 2}
    freq_encoded = freq_map.get(str(visit_freq), 1)

    tier = row.get("membership_tier", "M")
    tier_map = {"A": 0, "M": 1, "O": 2, "R": 3, "E": 4}
    tier_encoded = tier_map.get(str(tier), 1)

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


class HybridPersonaClassifier:
    """하이브리드 페르소나 분류기 - 규칙 기반 + ML"""

    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = os.path.join(os.path.dirname(__file__), "persona_model_hybrid.pkl")

        # 저장된 모델이 있으면 로드
        if os.path.exists(self.model_path):
            self.load()

    def train(self, train_df=None):
        """ML 모델 학습"""
        if train_df is None:
            # 기본 학습 데이터 로드
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            csv_files = glob.glob(os.path.join(data_dir, 'customer_data_*.csv'))

            if csv_files:
                # 가장 최신 파일 사용
                latest_file = max(csv_files, key=os.path.getctime)
                train_df = pd.read_csv(latest_file, encoding='utf-8-sig')

                # 라벨이 있는 데이터만 사용 (미라벨링 제외)
                train_df = train_df[train_df['persona'].notna() & (train_df['persona'] != '')]
            else:
                print("학습 데이터 파일을 찾을 수 없습니다.")
                return 0

        # 특성 추출
        X_train, y_train = [], []
        for idx, row in train_df.iterrows():
            if pd.notna(row.get("persona")) and row.get("persona") != "":
                X_train.append(extract_features(row))
                y_train.append(row["persona"])

        if len(X_train) == 0:
            print("학습할 데이터가 없습니다.")
            return 0

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
        단일 고객 데이터로 페르소나 예측 (하이브리드)

        Args:
            customer_data: dict 형태의 고객 데이터

        Returns:
            dict: {
                'persona': 예측된 페르소나,
                'confidence': 신뢰도,
                'method': 'rule' or 'ml',
                'rule': 적용된 규칙 (규칙 기반인 경우),
                'probabilities': 각 페르소나별 확률 (ML인 경우)
            }
        """
        # 1차: 규칙 기반 분류 시도
        rule_result = rule_based_classify(customer_data)

        if rule_result['persona'] is not None:
            return {
                'persona': rule_result['persona'],
                'confidence': rule_result['confidence'],
                'method': 'rule',
                'rule': rule_result['rule'],
                'probabilities': {}
            }

        # 2차: ML 기반 분류
        if not self.is_trained:
            self.train()

        if not self.is_trained:
            # 학습 실패시 브랜드 기반 fallback
            primary_brands = parse_brands(customer_data.get('primary_brand', ''))
            brand_persona, _, _ = get_dominant_persona_by_brand(primary_brands)
            return {
                'persona': brand_persona or '합리적 큐레이터',
                'confidence': 0.5,
                'method': 'brand_fallback',
                'rule': '브랜드 기반 기본 분류',
                'probabilities': {}
            }

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
            'method': 'ml',
            'rule': None,
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
        predictions = []
        confidences = []
        methods = []
        rules = []

        for idx, row in customers_df.iterrows():
            result = self.predict(row.to_dict())
            predictions.append(result['persona'])
            confidences.append(result['confidence'])
            methods.append(result['method'])
            rules.append(result.get('rule', ''))

        result_df = customers_df.copy()
        result_df['predicted_persona'] = predictions
        result_df['confidence'] = confidences
        result_df['prediction_method'] = methods
        result_df['applied_rule'] = rules

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


# 테스트용 샘플 고객
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
        "full_price_ratio": 0.52,
        "discount_sensitivity": "중간",
        "coupon_usage_rate": 0.45,
        "loyalty": "중간",
        "diversity": 0.55,
        "primary_brand": "이니스프리, 홀리추얼, 한율",
        "visit_frequency": "중"
    },
    {
        "customer_id": 1006,
        "name": "한소영",
        "age": 45,
        "skin_type": "복합성",
        "concerns": "주름, 탄력",
        "membership_tier": "E",
        "total_count": 35,
        "avg_amount": 95000,
        "full_price_ratio": 0.65,
        "discount_sensitivity": "중간",
        "coupon_usage_rate": 0.30,
        "loyalty": "높음",
        "diversity": 0.60,
        "primary_brand": "오설록, 퍼즐우드, 롱테이크",
        "visit_frequency": "높음"
    },
    {
        "customer_id": 1007,
        "name": "송예린",
        "age": 32,
        "skin_type": "민감성",
        "concerns": "민감, 진정",
        "membership_tier": "O",
        "total_count": 20,
        "avg_amount": 55000,
        "full_price_ratio": 0.50,
        "discount_sensitivity": "중간",
        "coupon_usage_rate": 0.40,
        "loyalty": "중간",
        "diversity": 0.40,
        "primary_brand": "프리메라, 에스트라, 한율",
        "visit_frequency": "중"
    }
]


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("하이브리드 페르소나 분류기 테스트 (규칙 기반 + ML)")
    print("=" * 70)

    # 분류기 초기화
    classifier = HybridPersonaClassifier()

    # 샘플 고객 예측
    print("\n" + "=" * 70)
    print("샘플 고객 페르소나 예측")
    print("=" * 70)

    for customer in SAMPLE_CUSTOMERS:
        result = classifier.predict(customer)
        print(f"\n【{customer['name']}({customer['age']}세)】")
        print(f"  주 브랜드: {customer['primary_brand']}")
        print(f"  예측 페르소나: {result['persona']}")
        print(f"  신뢰도: {result['confidence']*100:.1f}%")
        print(f"  분류 방식: {result['method']}")
        if result['rule']:
            print(f"  적용 규칙: {result['rule']}")

    # 생성된 데이터로 테스트
    print("\n" + "=" * 70)
    print("생성된 1000개 고객 데이터 분류 테스트")
    print("=" * 70)

    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'customer_data_1000.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, encoding='utf-8-sig')

        # 예측 수행
        result_df = classifier.predict_batch(df)

        # 분류 방식 통계
        print(f"\n분류 방식 통계:")
        method_counts = result_df['prediction_method'].value_counts()
        for method, count in method_counts.items():
            print(f"  {method}: {count}개 ({count/len(df)*100:.1f}%)")

        # 페르소나별 분포
        print(f"\n예측 페르소나 분포:")
        persona_counts = result_df['predicted_persona'].value_counts()
        for persona, count in persona_counts.items():
            print(f"  {persona}: {count}개 ({count/len(df)*100:.1f}%)")

        # 결과 저장
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'customer_data_1000_predicted.csv')
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n예측 결과 저장: {output_path}")
    else:
        print(f"데이터 파일을 찾을 수 없습니다: {data_path}")
