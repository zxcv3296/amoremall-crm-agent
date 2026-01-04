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

# 브랜드 클러스터 정의 (7개 클러스터)
BRAND_CLUSTERS = {
    "테크니컬 홈케어족": ["메이크온", "바이탈뷰티", "아이오페"],
    "하이엔드 품격가": ["설화수", "헤라", "에이피뷰티"],
    "웰니스 힐링 탐험가": ["롱테이크", "퍼즐우드", "오설록"],
    "연구소 기반 해결사": ["미쟝센", "한율", "에스트라", "프리메라", "비레디", "마몽드", "려"],
    "트렌디 Z세대": ["라네즈", "에스쁘아", "앞바다즈", "에뛰드", "해피바스"],
    "합리적 큐레이터": ["아모레퍼시픽", "홀리추얼", "오딧세이", "이니스프리", "아모레성수"],
    "실속형 가계 수호자": ["라보에이치", "일리윤", "아모레베이직", "메디안"]
}

# 카테고리 클러스터 정의
# 연구소 기반 해결사: 범용 카테고리(클렌징, 스킨케어) 제외 - 특화 카테고리만
CATEGORY_CLUSTERS = {
    "테크니컬 홈케어족": [
        "뷰티디바이스", "페이셜케어 기기", "구강케어 기기", "헤어케어 기기",
        "헬스케어 기기", "기타 디바이스"
    ],
    "웰니스 힐링 탐험가": [
        "뷰티푸드", "건강식품", "차(TEA)", "간식", "향수", "캔들", "디퓨저", "소품&도구"
    ],
    "연구소 기반 해결사": [
        "스페셜 케어", "트러블 케어", "안티에이징", "미백", "주름개선"
    ]
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


def count_category_matches(categories, target_categories):
    """카테고리 매칭 개수 계산"""
    if not categories:
        return 0
    count = 0
    for cat in categories:
        for target in target_categories:
            if target in cat or cat in target:
                count += 1
                break
    return count


def parse_categories(category_str):
    """카테고리 문자열을 리스트로 파싱"""
    if pd.isna(category_str) or category_str == "":
        return []
    return [c.strip() for c in str(category_str).split(",")]


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


def rule_based_classify(row, avg_amount_top10_threshold=None, total_amount_q1=None, avg_session_q3=None):
    """
    규칙 기반 페르소나 분류 - 점수 기반 방식
    각 페르소나별로 조건 매칭 점수를 계산하여 가장 높은 점수의 페르소나로 분류

    Args:
        row: 고객 데이터 행
        avg_amount_top10_threshold: avg_amount 상위 10% 기준값 (외부에서 계산하여 전달)
        total_amount_q1: total_amount 1분위수 기준값
        avg_session_q3: avg_session_minutes 3분위수 기준값

    Returns:
        dict: {
            'persona': 분류된 페르소나,
            'rule': 매칭된 조건들,
            'confidence': 신뢰도 (매칭 비율 기반)
        }
    """
    # 데이터 추출
    age = row.get('age', 30)
    if pd.isna(age):
        age = 30

    primary_brands = parse_brands(row.get('primary_brand', ''))
    primary_categories = parse_categories(row.get('primary_category', ''))

    avg_amount = row.get('avg_amount', 30000)
    if pd.isna(avg_amount):
        avg_amount = 30000

    total_amount = row.get('total_amount', 0)
    if pd.isna(total_amount):
        total_amount = 0

    average_transaction_value = row.get('average_transaction_value', 50000)
    if pd.isna(average_transaction_value):
        average_transaction_value = 50000

    preferred_promotion = str(row.get('preferred_promotion', ''))

    visit_frequency = str(row.get('visit_frequency', '중'))

    diversity = row.get('diversity', 0.5)
    if pd.isna(diversity):
        diversity = 0.5

    avg_session_minutes = row.get('avg_session_minutes', 5)
    if pd.isna(avg_session_minutes):
        avg_session_minutes = 5

    skin_type = str(row.get('skin_type', ''))
    concerns = str(row.get('concerns', ''))

    # 기본 임계값 설정 (외부에서 전달되지 않은 경우)
    if avg_amount_top10_threshold is None:
        avg_amount_top10_threshold = 100000
    if total_amount_q1 is None:
        total_amount_q1 = 50000
    if avg_session_q3 is None:
        avg_session_q3 = 10

    # 각 페르소나별 브랜드/카테고리 매칭 수 계산
    tech_match = count_brand_matches(primary_brands, BRAND_CLUSTERS["테크니컬 홈케어족"])
    tech_cat_match = count_category_matches(primary_categories, CATEGORY_CLUSTERS.get("테크니컬 홈케어족", []))

    highend_match = count_brand_matches(primary_brands, BRAND_CLUSTERS["하이엔드 품격가"])

    wellness_match = count_brand_matches(primary_brands, BRAND_CLUSTERS["웰니스 힐링 탐험가"])
    wellness_cat_match = count_category_matches(primary_categories, CATEGORY_CLUSTERS.get("웰니스 힐링 탐험가", []))

    research_match = count_brand_matches(primary_brands, BRAND_CLUSTERS["연구소 기반 해결사"])
    research_cat_match = count_category_matches(primary_categories, CATEGORY_CLUSTERS.get("연구소 기반 해결사", []))

    trendy_match = count_brand_matches(primary_brands, BRAND_CLUSTERS["트렌디 Z세대"])

    curator_match = count_brand_matches(primary_brands, BRAND_CLUSTERS["합리적 큐레이터"])

    practical_match = count_brand_matches(primary_brands, BRAND_CLUSTERS["실속형 가계 수호자"])

    # 공통 조건 계산
    has_skin_concern = (
        skin_type not in ['', '없음', '고민없음', 'nan', 'None'] or
        concerns not in ['', '없음', '고민없음', 'nan', 'None']
    )

    # ==========================================
    # 각 페르소나별 점수 계산 (조건당 1점, 브랜드 매칭은 가중치 2)
    # ==========================================
    scores = {}
    matched_rules = {}

    # 1. 테크니컬 홈케어족 (3개 조건: 브랜드, 카테고리, avg_amount)
    tech_score = 0
    tech_rules = []
    if tech_match >= 1:
        tech_score += 2 * tech_match  # 브랜드 가중치
        tech_rules.append(f"브랜드({tech_match}개)")
    if tech_cat_match >= 1:
        tech_score += 1
        tech_rules.append(f"카테고리({tech_cat_match}개)")
    if avg_amount >= avg_amount_top10_threshold:
        tech_score += 1
        tech_rules.append(f"avg_amount 상위10%")
    scores["테크니컬 홈케어족"] = tech_score
    matched_rules["테크니컬 홈케어족"] = tech_rules

    # 2. 하이엔드 품격가 (3개 조건: 브랜드, 프로모션, 객단가)
    highend_score = 0
    highend_rules = []
    if highend_match >= 1:
        highend_score += 2 * highend_match
        highend_rules.append(f"브랜드({highend_match}개)")
    if preferred_promotion in ['신상품', '한정판매']:
        highend_score += 1
        highend_rules.append(f"프로모션({preferred_promotion})")
    if average_transaction_value >= 90000:
        highend_score += 1
        highend_rules.append(f"객단가({average_transaction_value:,.0f}≥90,000)")
    scores["하이엔드 품격가"] = highend_score
    matched_rules["하이엔드 품격가"] = highend_rules

    # 3. 웰니스 힐링 탐험가 (3개 조건: 브랜드, 카테고리, total_amount)
    wellness_score = 0
    wellness_rules = []
    if wellness_match >= 1:
        wellness_score += 2 * wellness_match
        wellness_rules.append(f"브랜드({wellness_match}개)")
    if wellness_cat_match >= 1:
        wellness_score += 1
        wellness_rules.append(f"카테고리({wellness_cat_match}개)")
    if total_amount >= total_amount_q1:
        wellness_score += 1
        wellness_rules.append(f"total_amount≥Q1")
    scores["웰니스 힐링 탐험가"] = wellness_score
    matched_rules["웰니스 힐링 탐험가"] = wellness_rules

    # 4. 연구소 기반 해결사 (브랜드 필수 + 피부고민/카테고리 보조)
    # 브랜드 매칭 없으면 0점 (브랜드가 핵심 조건)
    research_score = 0
    research_rules = []
    if research_match >= 1:
        research_score += 2 * research_match
        research_rules.append(f"브랜드({research_match}개)")
        # 보조 조건: 브랜드 매칭시에만 추가 점수
        if research_cat_match >= 1:
            research_score += 0.5  # 카테고리는 보조 (0.5점)
            research_rules.append(f"카테고리({research_cat_match}개)")
        if has_skin_concern:
            research_score += 0.5  # 피부고민도 보조 (0.5점)
            research_rules.append("피부고민있음")
    scores["연구소 기반 해결사"] = research_score
    matched_rules["연구소 기반 해결사"] = research_rules

    # 5. 트렌디 Z세대 (3개 조건: 브랜드, 나이, 프로모션)
    trendy_score = 0
    trendy_rules = []
    if trendy_match >= 1:
        trendy_score += 2 * trendy_match
        trendy_rules.append(f"브랜드({trendy_match}개)")
    if age < 25:
        trendy_score += 1.5  # 나이 조건 가중치 높임
        trendy_rules.append(f"age({age})<25")
    if preferred_promotion in ['신상품', '사은품증정']:
        trendy_score += 1
        trendy_rules.append(f"프로모션({preferred_promotion})")
    scores["트렌디 Z세대"] = trendy_score
    matched_rules["트렌디 Z세대"] = trendy_rules

    # 6. 합리적 큐레이터 (4개 조건: 방문빈도, 브랜드, diversity, 체류시간)
    curator_score = 0
    curator_rules = []
    if visit_frequency in ['높음', '중', '중간']:
        curator_score += 1
        curator_rules.append(f"방문빈도({visit_frequency})")
    if curator_match >= 1:
        curator_score += 2 * curator_match
        curator_rules.append(f"브랜드({curator_match}개)")
    if diversity >= 0.5:
        curator_score += 1
        curator_rules.append(f"diversity({diversity:.2f})")
    if avg_session_minutes >= avg_session_q3:
        curator_score += 1
        curator_rules.append(f"체류시간({avg_session_minutes:.0f}분)")
    scores["합리적 큐레이터"] = curator_score
    matched_rules["합리적 큐레이터"] = curator_rules

    # 7. 실속형 가계 수호자 (핵심: 할인 프로모션 + 저가 객단가)
    practical_score = 0
    practical_rules = []
    if average_transaction_value <= 50000:
        practical_score += 1.5  # 저가 객단가 가중치 상향
        practical_rules.append(f"객단가({average_transaction_value:,.0f}≤50,000)")
    if preferred_promotion in ['할인판매', '할인']:
        practical_score += 2  # 할인 프로모션 = 핵심 특성 (2점)
        practical_rules.append(f"프로모션({preferred_promotion})")
    if practical_match >= 1:
        practical_score += 2 * practical_match
        practical_rules.append(f"브랜드({practical_match}개)")
    scores["실속형 가계 수호자"] = practical_score
    matched_rules["실속형 가계 수호자"] = practical_rules

    # ==========================================
    # 최고 점수 페르소나 선택
    # ==========================================
    max_score = max(scores.values())

    if max_score == 0:
        # 점수가 모두 0인 경우 ML로 fallback
        return {
            'persona': None,
            'rule': None,
            'confidence': 0
        }

    # 최고 점수 페르소나 선택 (동점시 첫번째)
    best_persona = max(scores, key=scores.get)
    best_rules = matched_rules[best_persona]

    # 신뢰도 계산: 최대 가능 점수 대비 실제 점수 비율
    max_possible = {
        "테크니컬 홈케어족": 4,    # 브랜드2 + 카테고리1 + avg_amount1
        "하이엔드 품격가": 4,      # 브랜드2 + 프로모션1 + 객단가1
        "웰니스 힐링 탐험가": 4,   # 브랜드2 + 카테고리1 + total_amount1
        "연구소 기반 해결사": 3,   # 브랜드2 + 카테고리0.5 + 피부고민0.5 (브랜드 필수)
        "트렌디 Z세대": 4.5,       # 브랜드2 + 나이1.5 + 프로모션1
        "합리적 큐레이터": 5,      # 방문1 + 브랜드2 + div1 + 체류1
        "실속형 가계 수호자": 5.5  # 객단가1.5 + 프로모션2 + 브랜드2
    }

    confidence = min(0.95, max(0.5, max_score / max_possible.get(best_persona, 4)))

    # 점수 차이 정보도 포함
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    second_best = sorted_scores[1] if len(sorted_scores) > 1 else (None, 0)

    rule_str = " + ".join(best_rules) if best_rules else "조건없음"
    if second_best[1] > 0:
        rule_str += f" (2위: {second_best[0]} {second_best[1]:.1f}점)"

    return {
        'persona': best_persona,
        'rule': f"[점수:{max_score:.1f}] {rule_str}",
        'confidence': confidence
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

    def predict(self, customer_data, avg_amount_top10_threshold=None, total_amount_q1=None, avg_session_q3=None):
        """
        단일 고객 데이터로 페르소나 예측 (하이브리드)

        Args:
            customer_data: dict 형태의 고객 데이터
            avg_amount_top10_threshold: avg_amount 상위 10% 기준값
            total_amount_q1: total_amount 1분위수 기준값
            avg_session_q3: avg_session_minutes 3분위수 기준값

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
        rule_result = rule_based_classify(
            customer_data,
            avg_amount_top10_threshold=avg_amount_top10_threshold,
            total_amount_q1=total_amount_q1,
            avg_session_q3=avg_session_q3
        )

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
        # 데이터 기반 임계값 계산
        avg_amount_top10_threshold = None
        total_amount_q1 = None
        avg_session_q3 = None

        if 'avg_amount' in customers_df.columns:
            avg_amount_top10_threshold = customers_df['avg_amount'].quantile(0.9)

        if 'total_amount' in customers_df.columns:
            total_amount_q1 = customers_df['total_amount'].quantile(0.25)

        if 'avg_session_minutes' in customers_df.columns:
            avg_session_q3 = customers_df['avg_session_minutes'].quantile(0.75)

        predictions = []
        confidences = []
        methods = []
        rules = []

        for idx, row in customers_df.iterrows():
            result = self.predict(
                row.to_dict(),
                avg_amount_top10_threshold=avg_amount_top10_threshold,
                total_amount_q1=total_amount_q1,
                avg_session_q3=avg_session_q3
            )
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
