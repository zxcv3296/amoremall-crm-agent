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

def cluster_brands(combined_data, n_clusters=8):
    """K-means 클러스터링"""
    brands = list(combined_data.keys())
    features = []

    for brand in brands:
        data = combined_data[brand]
        features.append([
            data['mass_premium'],
            data['necessity_luxury'],
            data['tech_emotion']
        ])

    # 정규화
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features_scaled)

    # 클러스터 중심점 역변환
    centers = scaler.inverse_transform(kmeans.cluster_centers_)

    # 클러스터 이름 자동 생성
    cluster_names = {}
    for i, center in enumerate(centers):
        mp, nl, te = center

        # 이름 결정 로직
        if mp > 30:
            price_tier = "프리미엄"
        elif mp > 0:
            price_tier = "중가"
        else:
            price_tier = "대중"

        if te > 30:
            style = "감성"
        elif te < -20:
            style = "기능"
        else:
            style = "밸런스"

        if nl > 20:
            need = "라이프스타일"
        elif nl < -40:
            need = "필수케어"
        else:
            need = ""

        name = f"{price_tier} {style}"
        if need:
            name = f"{price_tier} {need}"

        cluster_names[i] = {
            "name": name,
            "center": {
                "mass_premium": round(mp, 1),
                "necessity_luxury": round(nl, 1),
                "tech_emotion": round(te, 1)
            }
        }

    # 결과 매핑
    result = {}
    for idx, brand in enumerate(brands):
        cluster_id = int(clusters[idx])
        combined_data[brand]['cluster_id'] = cluster_id
        combined_data[brand]['cluster_name'] = cluster_names[cluster_id]['name']

    return combined_data, cluster_names

def main():
    print("=" * 60)
    print("종합 분석 시작")
    print("=" * 60)

    # 점수 종합
    combined = combine_scores()
    print(f"\n{len(combined)}개 브랜드 점수 종합 완료\n")

    # 클러스터링
    combined, cluster_info = cluster_brands(combined, n_clusters=8)

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
