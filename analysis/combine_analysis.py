"""
3가지 분석 데이터 종합 및 클러스터 재분류
1. 주관적 분석 (brand_analysis.json)
2. 키워드 빈도 분석 (keyword_analysis.json)
3. 가격 분석 (price_analysis.json)
"""
import json
import os
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# 데이터 파일은 data 폴더에 있음
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def load_json(filename):
    filepath = os.path.join(BASE_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def combine_scores():
    """3가지 분석 결과 종합"""
    # 데이터 로드
    subjective = load_json("brand_analysis.json")
    keywords = load_json("keyword_analysis.json")
    price = load_json("price_analysis.json")

    combined = {}

    # 모든 브랜드 수집
    all_brands = set(subjective.get('brands', {}).keys())

    for brand in all_brands:
        subj = subjective.get('brands', {}).get(brand, {})
        kw = keywords.get('brands', {}).get(brand, {})
        pr = price.get('brands', {}).get(brand, {})

        if not subj or 'error' in subj:
            continue

        # Mass/Premium: 가격(50%) + 키워드(30%) + 주관(20%)
        price_score = pr.get('price_score', 0) if pr else 0
        kw_mp = kw.get('mass_premium', 0) if kw else 0
        subj_mp = subj.get('mass_premium', 0)

        mass_premium = (price_score * 0.5) + (kw_mp * 0.3) + (subj_mp * 0.2)

        # 필수재/사치재: 키워드(50%) + 주관(50%)
        kw_nl = kw.get('necessity_luxury', 0) if kw else 0
        subj_nl = subj.get('necessity_luxury', 0)

        necessity_luxury = (kw_nl * 0.5) + (subj_nl * 0.5)

        # 기술/감성: 키워드(60%) + 주관(40%)
        kw_te = kw.get('tech_emotion', 0) if kw else 0
        subj_te = subj.get('tech_emotion', 0)

        tech_emotion = (kw_te * 0.6) + (subj_te * 0.4)

        combined[brand] = {
            "mass_premium": round(mass_premium, 1),
            "necessity_luxury": round(necessity_luxury, 1),
            "tech_emotion": round(tech_emotion, 1),
            "avg_price": pr.get('avg_price', 0) if pr else 0,
            "review_count": subj.get('review_count', 0),
            "scores_breakdown": {
                "mass_premium": {
                    "price": price_score,
                    "keyword": kw_mp,
                    "subjective": subj_mp
                },
                "necessity_luxury": {
                    "keyword": kw_nl,
                    "subjective": subj_nl
                },
                "tech_emotion": {
                    "keyword": kw_te,
                    "subjective": subj_te
                }
            }
        }

    return combined

def cluster_brands(combined_data, n_clusters=7):
    """K-means 클러스터링 - 7개 고정 클러스터"""

    # 7개 클러스터 정의
    CLUSTER_DEFINITIONS = {
        "프리미엄 기능": {
            "description": "첨단 뷰티 테크놀로지와 고성능 원료를 결합하여 즉각적인 피부 개선 효과를 제공하는 하이엔드 라인",
            "persona": "테크니컬 홈케어족",
            "criteria": {"mp_min": 0, "te_max": -10}  # 중가 이상 + 기술 중심
        },
        "프리미엄 밸런스": {
            "description": "독보적인 브랜드 헤리티지와 심미적 가치, 최상의 고객 경험을 제공하는 럭셔리 토탈 케어 라인",
            "persona": "하이엔드 품격가",
            "criteria": {"mp_min": 15, "te_min": 10}  # 프리미엄 + 감성적
        },
        "중가 라이프스타일": {
            "description": "단순한 화장품을 넘어 향기, 휴식, 취향 등 일상 전반의 감성적 만족과 웰니스를 지향하는 라인",
            "persona": "웰니스 힐링 탐험가",
            "criteria": {"nl_min": 20, "te_min": 70}  # 라이프스타일 + 고감성
        },
        "중가 필수케어": {
            "description": "피부 전문가의 처방이나 연구소 데이터 기반의 더마 솔루션을 통해 피부 근본 문제를 해결하는 기능성 라인",
            "persona": "연구소 기반 해결사",
            "criteria": {"mp_min": -35, "mp_max": 0, "nl_max": -20, "te_max": 15}  # 중가 + 필수재 + 기능
        },
        "대중 감성": {
            "description": "최신 트렌드를 반영한 감각적인 디자인과 색조 중심의 제품군으로 자기표현과 즐거움을 제공하는 라인",
            "persona": "트렌디 Z세대",
            "criteria": {"mp_max": -15, "te_min": 20}  # 대중적 + 감성
        },
        "대중 밸런스": {
            "description": "검증된 품질과 합리적인 가격대를 유지하며 일상적인 뷰티 루틴을 책임지는 대중적 프리미엄 라인",
            "persona": "합리적 큐레이터",
            "criteria": {"mp_min": -30, "mp_max": 5, "nl_min": -45, "nl_max": 0}  # 중간 + 밸런스
        },
        "대중 필수케어": {
            "description": "온 가족이 안심하고 사용할 수 있는 가성비 중심의 생활 밀착형 대용량 및 저자극 케어 라인",
            "persona": "실속형 가계 수호자",
            "criteria": {"mp_max": -35, "nl_max": -45}  # 대중 + 필수재
        }
    }

    def assign_cluster(mp, nl, te):
        """점수 기반 클러스터 할당"""
        # 우선순위에 따른 클러스터 할당

        # 1. 중가 라이프스타일 (향기/감성 특화)
        if nl > 20 and te > 60:
            return "중가 라이프스타일"

        # 2. 프리미엄 기능 (고가 + 기술)
        if mp > -10 and te < -15:
            return "프리미엄 기능"

        # 3. 프리미엄 밸런스 (프리미엄 + 밸런스/감성)
        if mp > 10 and te > 0:
            return "프리미엄 밸런스"

        # 4. 대중 감성 (대중적 + 감성)
        if mp < -15 and te > 25 and nl > -35:
            return "대중 감성"

        # 5. 대중 필수케어 (저가 + 필수재)
        if mp < -35 and nl < -40:
            return "대중 필수케어"

        # 6. 중가 필수케어 (중간 가격 + 필수재/기능)
        if mp > -40 and mp < 5 and nl < -25 and te < 20:
            return "중가 필수케어"

        # 7. 대중 밸런스 (나머지)
        return "대중 밸런스"

    # 각 브랜드에 클러스터 할당
    cluster_names = {name: {"name": name, **info} for name, info in CLUSTER_DEFINITIONS.items()}

    for brand, data in combined_data.items():
        mp = data['mass_premium']
        nl = data['necessity_luxury']
        te = data['tech_emotion']

        cluster_name = assign_cluster(mp, nl, te)
        combined_data[brand]['cluster_name'] = cluster_name

    return combined_data, cluster_names

def main():
    print("=" * 60)
    print("종합 분석 시작")
    print("=" * 60)

    # 점수 종합
    combined = combine_scores()
    print(f"\n{len(combined)}개 브랜드 점수 종합 완료\n")

    # 클러스터링
    combined, cluster_info = cluster_brands(combined, n_clusters=7)

    # 클러스터별 브랜드 정리
    clusters = {}
    for brand, data in combined.items():
        cluster_name = data['cluster_name']
        if cluster_name not in clusters:
            clusters[cluster_name] = []
        clusters[cluster_name].append({
            "brand": brand,
            "mass_premium": data['mass_premium'],
            "necessity_luxury": data['necessity_luxury'],
            "tech_emotion": data['tech_emotion'],
            "avg_price": data['avg_price']
        })

    # 결과 출력
    print("=" * 60)
    print("클러스터 분류 결과")
    print("=" * 60)

    for cluster_name, brands in sorted(clusters.items()):
        print(f"\n## {cluster_name} ({len(brands)}개 브랜드)")
        for b in sorted(brands, key=lambda x: -x['avg_price']):
            print(f"  - {b['brand']:<15} 가격:{b['avg_price']:>8,}원 | MP:{b['mass_premium']:>+6.1f} NL:{b['necessity_luxury']:>+6.1f} TE:{b['tech_emotion']:>+6.1f}")

    # 결과 저장
    output = {
        "method": "combined_analysis",
        "weights": {
            "mass_premium": {"price": 0.5, "keyword": 0.3, "subjective": 0.2},
            "necessity_luxury": {"keyword": 0.5, "subjective": 0.5},
            "tech_emotion": {"keyword": 0.6, "subjective": 0.4}
        },
        "clusters": {name: info for name, info in cluster_info.items()},
        "cluster_summary": {k: [b['brand'] for b in v] for k, v in clusters.items()},
        "brands": combined
    }

    output_file = os.path.join(BASE_DIR, "combined_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {output_file}")

    # 점수 표 출력
    print("\n" + "=" * 80)
    print("종합 점수표")
    print("=" * 80)
    print(f"{'브랜드':<15} {'평균가격':>10} {'Mass/Prem':>10} {'필수/사치':>10} {'기술/감성':>10} {'클러스터':<15}")
    print("-" * 80)

    for brand, data in sorted(combined.items(), key=lambda x: -x[1]['mass_premium']):
        print(f"{brand:<15} {data['avg_price']:>10,} {data['mass_premium']:>+10.1f} {data['necessity_luxury']:>+10.1f} {data['tech_emotion']:>+10.1f} {data['cluster_name']:<15}")

if __name__ == "__main__":
    main()
