"""
키워드 빈도 분석 기반 브랜드 특성 점수 산정
"""
import json
import os
import re
from collections import Counter

# 데이터는 data 폴더에 위치
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
REVIEW_FILE = os.path.join(DATA_DIR, "crawled_reviews.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "keyword_analysis.json")

# 3축 키워드 사전
KEYWORDS = {
    "mass_premium": {
        "mass": ["저렴", "가성비", "싸게", "저가", "학생", "부담없", "데일리", "매일", "가격대비", "착한가격", "저렴한", "싼"],
        "premium": ["고급", "럭셔리", "프리미엄", "백화점", "선물", "고가", "비싼", "명품", "특별한", "귀한", "고급스러운", "럭셔리한"]
    },
    "necessity_luxury": {
        "necessity": ["필수", "기본", "매일쓰는", "없으면안", "꼭필요", "생필품", "필요한", "기초", "일상", "매일", "꾸준히", "습관"],
        "luxury": ["힐링", "기분전환", "나를위한", "사치", "특별한날", "보상", "기분좋", "행복", "여유", "휴식", "편안", "릴렉스"]
    },
    "tech_emotion": {
        "tech": ["성분", "효과", "개선", "트러블", "피부과", "임상", "기능", "효능", "피부결", "각질", "모공", "주름", "탄력", "미백", "보습력"],
        "emotion": ["향기", "향", "기분", "예쁜", "디자인", "패키지", "분위기", "느낌", "감성", "무드", "색감", "텍스처", "발림성"]
    }
}

def load_reviews():
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_keywords(text, keyword_list):
    """텍스트에서 키워드 출현 횟수 계산"""
    count = 0
    text_lower = text.lower()
    for keyword in keyword_list:
        count += len(re.findall(keyword, text_lower))
    return count

def analyze_brand(brand_name, reviews):
    """브랜드별 키워드 분석"""
    all_text = " ".join([r.get('content', '') for r in reviews])

    results = {}

    for axis, keywords in KEYWORDS.items():
        # 양쪽 키워드 카운트
        keys = list(keywords.keys())
        negative_count = count_keywords(all_text, keywords[keys[0]])  # mass, necessity, tech
        positive_count = count_keywords(all_text, keywords[keys[1]])  # premium, luxury, emotion

        total = negative_count + positive_count
        if total > 0:
            # -100 ~ +100 스케일로 변환
            score = ((positive_count - negative_count) / total) * 100
        else:
            score = 0

        results[axis] = {
            "score": round(score, 1),
            f"{keys[0]}_count": negative_count,
            f"{keys[1]}_count": positive_count,
            "total_keywords": total
        }

        # 상위 키워드 추출
        keyword_counts = {}
        for kw in keywords[keys[0]] + keywords[keys[1]]:
            cnt = len(re.findall(kw, all_text.lower()))
            if cnt > 0:
                keyword_counts[kw] = cnt

        results[axis]["top_keywords"] = dict(sorted(keyword_counts.items(), key=lambda x: -x[1])[:10])

    return results

def main():
    print("=" * 60)
    print("키워드 빈도 분석 시작")
    print("=" * 60)

    data = load_reviews()
    brands = data.get('brands', [])

    analysis_results = {}

    for brand in brands:
        brand_name = brand.get('brandName', 'Unknown')
        reviews = brand.get('reviews', [])

        print(f"\n[{brand_name}] 분석 중... ({len(reviews)}개 리뷰)")

        result = analyze_brand(brand_name, reviews)

        # 최종 점수
        mp_score = result['mass_premium']['score']
        nl_score = result['necessity_luxury']['score']
        te_score = result['tech_emotion']['score']

        print(f"  Mass/Premium: {mp_score:+.1f}")
        print(f"  필수재/사치재: {nl_score:+.1f}")
        print(f"  기술/감성: {te_score:+.1f}")

        analysis_results[brand_name] = {
            "review_count": len(reviews),
            "mass_premium": mp_score,
            "necessity_luxury": nl_score,
            "tech_emotion": te_score,
            "details": result
        }

    # 결과 저장
    output = {
        "analyzed_at": data.get('crawled_at'),
        "method": "keyword_frequency_analysis",
        "keywords_used": KEYWORDS,
        "brands": analysis_results
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"분석 완료! 저장: {OUTPUT_FILE}")
    print("=" * 60)

    # 요약 출력
    print("\n## 키워드 분석 결과 요약\n")
    print(f"{'브랜드':<15} {'Mass/Premium':>12} {'필수/사치':>12} {'기술/감성':>12}")
    print("-" * 55)

    for brand_name, result in sorted(analysis_results.items(), key=lambda x: x[1]['mass_premium']):
        mp = result['mass_premium']
        nl = result['necessity_luxury']
        te = result['tech_emotion']
        print(f"{brand_name:<15} {mp:>+12.1f} {nl:>+12.1f} {te:>+12.1f}")

if __name__ == "__main__":
    main()
