"""
브랜드 특성 분석 스크립트
- 리뷰 텍스트를 기반으로 브랜드를 3축으로 분류
- Mass/Premium
- 필수재/사치재 (Necessity/Luxury)
- 기술/감성 (Technology/Emotion)
"""

import json
import os
from anthropic import Anthropic

# API 키 설정
client = Anthropic()

REVIEW_FILE = os.path.join(os.path.dirname(__file__), "crawled_reviews.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "brand_analysis.json")

ANALYSIS_PROMPT = """당신은 화장품 브랜드 분석 전문가입니다.
아래 브랜드의 리뷰들을 분석하여 브랜드 특성을 3개 축으로 평가해주세요.

## 브랜드: {brand_name}

## 리뷰 샘플 (총 {review_count}개 중 {sample_count}개):
{reviews}

## 분석 기준

### 1. Mass vs Premium (-100 ~ +100)
- **Mass (-100)**: 대중적, 저렴한 가격대, 일상적 사용, 가성비 강조
  - 키워드: 저렴, 가성비, 매일, 부담없이, 학생, 데일리
- **Premium (+100)**: 고급, 프리미엄 가격대, 특별한 경험, 품질 강조
  - 키워드: 고급스러운, 럭셔리, 선물, 특별한 날, 백화점

### 2. 필수재 vs 사치재 (-100 ~ +100)
- **필수재 (-100)**: 기본 케어, 필수품, 기능적 필요
  - 키워드: 매일 쓰는, 기본, 필수, 없으면 안됨, 꼭 필요한
- **사치재 (+100)**: 기분전환, 자기보상, 즐거움 추구
  - 키워드: 기분전환, 힐링, 나를 위한, 사치, 특별한

### 3. 기술 vs 감성 (-100 ~ +100)
- **기술 (-100)**: 성분, 효능, 과학적 근거 강조
  - 키워드: 성분, 효과, 개선, 트러블, 피부과, 임상
- **감성 (+100)**: 향기, 패키지, 사용 경험, 감정 강조
  - 키워드: 향기, 기분, 예쁜, 행복, 설렘, 분위기

## 출력 형식 (JSON)
{{
  "mass_premium": 점수(-100~100),
  "necessity_luxury": 점수(-100~100),
  "tech_emotion": 점수(-100~100),
  "reasoning": "분석 근거 요약 (2-3문장)",
  "keywords": ["추출된", "주요", "키워드들"]
}}

JSON만 출력하세요."""


def load_reviews():
    """리뷰 데이터 로드"""
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def sample_reviews(reviews, max_samples=30, max_chars=8000):
    """리뷰 샘플링 (토큰 제한 고려)"""
    # 긴 리뷰 우선 선택 (더 많은 정보 포함)
    sorted_reviews = sorted(reviews, key=lambda x: len(x.get('content', '')), reverse=True)

    sampled = []
    total_chars = 0

    for review in sorted_reviews[:max_samples]:
        content = review.get('content', '')
        if total_chars + len(content) > max_chars:
            break
        sampled.append(content)
        total_chars += len(content)

    return sampled


def analyze_brand(brand_name, reviews):
    """단일 브랜드 분석"""
    sampled = sample_reviews(reviews)
    reviews_text = "\n---\n".join([f"[리뷰 {i+1}]\n{r}" for i, r in enumerate(sampled)])

    prompt = ANALYSIS_PROMPT.format(
        brand_name=brand_name,
        review_count=len(reviews),
        sample_count=len(sampled),
        reviews=reviews_text
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    # JSON 파싱
    response_text = response.content[0].text.strip()

    # JSON 블록 추출
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {
            "mass_premium": 0,
            "necessity_luxury": 0,
            "tech_emotion": 0,
            "reasoning": "파싱 실패",
            "keywords": [],
            "raw_response": response_text
        }

    return result


def main():
    print("=" * 60)
    print("브랜드 특성 분석 시작")
    print("=" * 60)

    data = load_reviews()
    brands = data.get('brands', [])

    print(f"총 {len(brands)}개 브랜드 분석 예정\n")

    results = {}

    for i, brand in enumerate(brands):
        brand_name = brand.get('brandName', 'Unknown')
        reviews = brand.get('reviews', [])

        print(f"[{i+1}/{len(brands)}] {brand_name} 분석 중... ({len(reviews)}개 리뷰)")

        try:
            analysis = analyze_brand(brand_name, reviews)
            results[brand_name] = {
                "review_count": len(reviews),
                **analysis
            }
            print(f"  → Mass/Premium: {analysis.get('mass_premium', 'N/A')}")
            print(f"  → 필수재/사치재: {analysis.get('necessity_luxury', 'N/A')}")
            print(f"  → 기술/감성: {analysis.get('tech_emotion', 'N/A')}")
        except Exception as e:
            print(f"  → 오류: {e}")
            results[brand_name] = {"error": str(e)}

    # 결과 저장
    output = {
        "analyzed_at": data.get('crawled_at'),
        "total_brands": len(brands),
        "brands": results
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"분석 완료! 결과 저장: {OUTPUT_FILE}")
    print("=" * 60)

    # 결과 요약 출력
    print("\n## 분석 결과 요약\n")
    print(f"{'브랜드':<15} {'Mass/Premium':>12} {'필수/사치':>12} {'기술/감성':>12}")
    print("-" * 55)

    for brand_name, result in sorted(results.items(), key=lambda x: x[1].get('mass_premium', 0)):
        if 'error' not in result:
            mp = result.get('mass_premium', 0)
            nl = result.get('necessity_luxury', 0)
            te = result.get('tech_emotion', 0)
            print(f"{brand_name:<15} {mp:>12} {nl:>12} {te:>12}")


if __name__ == "__main__":
    main()
