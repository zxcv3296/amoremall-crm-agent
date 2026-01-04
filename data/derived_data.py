"""
파생데이터 계산 모듈
CSV 데이터에서 파생지표를 계산합니다.
"""

import pandas as pd
from datetime import datetime


def calc_total_amount(row):
    """총 구매액 = total_count * avg_amount"""
    return row['total_count'] * row['avg_amount']


def calc_average_transaction_value(row):
    """객단가 = total_amount / total_count"""
    if row['total_count'] == 0:
        return 0
    return row['total_amount'] / row['total_count']


def calc_membership_tier(row):
    """
    멤버십 티어 (total_amount 기준)
    E: >= 250만
    R: 150~250만
    O: 100~150만
    M: 50~100만
    A: < 50만
    """
    amount = row['total_amount']
    if amount >= 2500000:
        return 'E'
    elif amount >= 1500000:
        return 'R'
    elif amount >= 1000000:
        return 'O'
    elif amount >= 500000:
        return 'M'
    else:
        return 'A'


def calc_age(row, target_date):
    """
    만나이 계산
    생일 전: (현재 연도 - 출생 연도) - 1
    생일 후: (현재 연도 - 출생 연도)
    """
    try:
        birthday = datetime.strptime(str(row['birthday']), '%Y.%m.%d')
        age = target_date.year - birthday.year
        if (target_date.month, target_date.day) < (birthday.month, birthday.day):
            age -= 1
        return age
    except:
        return None


def calc_diversity(row):
    """
    다양성 = [2 - {(1/primary_brand 개수) + (1/primary_category 개수)}] / 2
    """
    brand_str = str(row.get('primary_brand', '')) if pd.notna(row.get('primary_brand')) else ''
    cat_str = str(row.get('primary_category', '')) if pd.notna(row.get('primary_category')) else ''

    brand_count = len([b for b in brand_str.split(',') if b.strip()]) if brand_str else 1
    cat_count = len([c for c in cat_str.split(',') if c.strip()]) if cat_str else 1

    brand_count = max(1, brand_count)
    cat_count = max(1, cat_count)

    diversity = (2 - (1/brand_count + 1/cat_count)) / 2
    return round(diversity, 2)


def calc_days_ago(date_str, target_date):
    """경과일 계산 = (지정일) - (해당 날짜)"""
    try:
        date = datetime.strptime(str(date_str), '%Y.%m.%d')
        return (target_date - date).days
    except:
        return None


def calc_discount_sensitivity(row):
    """할인민감도 = (coupon_usage_rate + event_participation_rate) / 2"""
    coupon = row.get('coupon_usage_rate', 0) or 0
    event = row.get('event_participation_rate', 0) or 0
    return round((coupon + event) / 2, 2)


def calc_full_price_ratio(row):
    """정가 구매 비율 = 1 - (coupon_usage_rate + event_participation_rate)"""
    coupon = row.get('coupon_usage_rate', 0) or 0
    event = row.get('event_participation_rate', 0) or 0
    return round(max(0, 1 - (coupon + event)), 2)


def add_derived_columns(df, target_date=None):
    """
    DataFrame에 모든 파생 컬럼 추가

    Args:
        df: 원본 DataFrame
        target_date: 지정일 (기본값: 오늘)

    Returns:
        파생 컬럼이 추가된 DataFrame
    """
    if target_date is None:
        target_date = datetime.now()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y.%m.%d')

    df = df.copy()

    # 1. total_amount (먼저 계산 - 다른 파생지표에서 사용)
    df['total_amount'] = df.apply(calc_total_amount, axis=1)

    # 2. average_transaction_value (객단가)
    df['average_transaction_value'] = df.apply(calc_average_transaction_value, axis=1).round(0).astype(int)

    # 3. membership_tier
    df['membership_tier'] = df.apply(calc_membership_tier, axis=1)

    # 4. age (만나이)
    df['age'] = df.apply(lambda row: calc_age(row, target_date), axis=1)

    # 5. diversity
    df['diversity'] = df.apply(calc_diversity, axis=1)

    # 6. 경과일 컬럼들
    df['signup_days_ago'] = df['signup_day'].apply(lambda x: calc_days_ago(x, target_date))
    df['visit_days_ago'] = df['last_visit_day'].apply(lambda x: calc_days_ago(x, target_date))
    df['view_days_ago'] = df['last_view_day'].apply(lambda x: calc_days_ago(x, target_date))
    df['save_days_ago'] = df['last_save_day'].apply(lambda x: calc_days_ago(x, target_date))
    df['cart_days_ago'] = df['last_cart_day'].apply(lambda x: calc_days_ago(x, target_date))
    df['purchase_days_ago'] = df['last_purchase_day'].apply(lambda x: calc_days_ago(x, target_date))

    # 7. discount_sensitivity, full_price_ratio (원본에 해당 컬럼이 있는 경우만)
    if 'coupon_usage_rate' in df.columns and 'event_participation_rate' in df.columns:
        df['discount_sensitivity'] = df.apply(calc_discount_sensitivity, axis=1)
        df['full_price_ratio'] = df.apply(calc_full_price_ratio, axis=1)

    return df


def process_csv(input_path, output_path=None, target_date=None):
    """
    CSV 파일을 읽어 파생데이터를 추가하고 저장

    Args:
        input_path: 입력 CSV 경로
        output_path: 출력 CSV 경로 (None이면 입력 파일 덮어쓰기)
        target_date: 지정일 (예: '2026.01.02')

    Returns:
        처리된 DataFrame
    """
    df = pd.read_csv(input_path)
    df = add_derived_columns(df, target_date)

    if output_path:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

    return df


# 테스트 실행
if __name__ == '__main__':
    import os

    # CSV 경로
    csv_path = os.path.join(os.path.dirname(__file__), 'customer_data_1000.csv')

    # 지정일 설정
    target_date = '2026.01.02'

    # 파생데이터 추가
    df = process_csv(csv_path, target_date=target_date)

    print('=== 파생데이터 계산 완료 ===')
    print(f'총 {len(df)}개 레코드')
    print(f'\n컬럼 목록: {df.columns.tolist()}')

    print('\n=== 샘플 데이터 (C001) ===')
    row = df[df['customer_id'] == 'C001'].iloc[0]
    print(f'total_amount: {row["total_amount"]:,}원')
    print(f'average_transaction_value: {row["average_transaction_value"]:,}원')
    print(f'membership_tier: {row["membership_tier"]}')
    print(f'age: {row["age"]}세')
    print(f'diversity: {row["diversity"]}')
    print(f'signup_days_ago: {row["signup_days_ago"]}일')
    print(f'visit_days_ago: {row["visit_days_ago"]}일')
    print(f'purchase_days_ago: {row["purchase_days_ago"]}일')

    print('\n=== 멤버십 티어 분포 ===')
    print(df['membership_tier'].value_counts().sort_index())
