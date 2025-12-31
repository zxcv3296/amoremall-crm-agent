"""
브랜드 포지셔닝 매트릭스 시각화
"""
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터는 data 폴더, 출력은 analysis 폴더
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
ANALYSIS_FILE = os.path.join(DATA_DIR, "combined_analysis.json")
OUTPUT_DIR = os.path.dirname(__file__)

def load_analysis():
    with open(ANALYSIS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_2d_matrix(brands_data, x_axis, y_axis, x_label, y_label, title, filename):
    """2D 매트릭스 생성"""
    fig, ax = plt.subplots(figsize=(14, 10))

    # 배경 사분면 색상
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.axvline(x=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

    # 사분면 배경색
    ax.fill_between([-100, 0], [0, 0], [100, 100], alpha=0.15, color='blue', label='Mass + 사치재/감성')
    ax.fill_between([0, 100], [0, 0], [100, 100], alpha=0.15, color='purple', label='Premium + 사치재/감성')
    ax.fill_between([-100, 0], [-100, -100], [0, 0], alpha=0.15, color='yellow', label='Mass + 필수재/기술')
    ax.fill_between([0, 100], [-100, -100], [0, 0], alpha=0.15, color='red', label='Premium + 필수재/기술')

    # 브랜드 플롯
    for brand_name, data in brands_data.items():
        if 'error' in data:
            continue
        x = data.get(x_axis, 0)
        y = data.get(y_axis, 0)

        # 점 크기는 리뷰 수에 비례
        size = max(50, min(300, data.get('review_count', 100)))

        ax.scatter(x, y, s=size, alpha=0.7, edgecolors='black', linewidth=0.5)
        ax.annotate(brand_name, (x, y), fontsize=9, ha='center', va='bottom',
                   xytext=(0, 5), textcoords='offset points')

    ax.set_xlim(-110, 110)
    ax.set_ylim(-110, 110)
    ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # 축 라벨 추가
    ax.text(-105, 0, '← Mass', fontsize=10, va='center', color='gray')
    ax.text(75, 0, 'Premium →', fontsize=10, va='center', color='gray')
    ax.text(0, -105, f'← {y_label.split("/")[0]}', fontsize=10, ha='center', color='gray')
    ax.text(0, 105, f'{y_label.split("/")[1]} →', fontsize=10, ha='center', color='gray')

    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"저장: {filename}")

def create_cluster_view(brands_data, cluster_summary):
    """클러스터 뷰 - combined_analysis.json의 cluster_summary 사용"""
    fig, ax = plt.subplots(figsize=(18, 14))

    # 클러스터별 색상 정의
    cluster_colors = {
        '프리미엄 기능': '#E74C3C',
        '프리미엄 밸런스': '#F39C12',
        '프리미엄 감성': '#9B59B6',
        '중가 라이프스타일': '#E91E63',
        '중가 필수케어': '#95A5A6',
        '대중 밸런스': '#3498DB',
        '대중 감성': '#27AE60',
        '대중 필수케어': '#1ABC9C',
    }

    # 8개 클러스터용 박스 위치 (4x2 그리드)
    box_positions = [
        (0.02, 0.72, 0.22, 0.25),   # 1행 1열
        (0.26, 0.72, 0.22, 0.25),   # 1행 2열
        (0.50, 0.72, 0.22, 0.25),   # 1행 3열
        (0.74, 0.72, 0.22, 0.25),   # 1행 4열
        (0.02, 0.38, 0.22, 0.30),   # 2행 1열 (더 큼)
        (0.26, 0.38, 0.22, 0.30),   # 2행 2열
        (0.50, 0.38, 0.22, 0.30),   # 2행 3열
        (0.74, 0.38, 0.22, 0.30),   # 2행 4열
    ]

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('아모레퍼시픽 브랜드 포지셔닝 맵\n(Mass/Premium × 필수재/사치재 × 기술/감성)\n가격·키워드·주관 종합 분석 기반 K-means 클러스터링',
                fontsize=14, fontweight='bold', pad=20)

    # 클러스터 순서 정의 (프리미엄 → 대중 순)
    cluster_order = [
        '프리미엄 기능', '프리미엄 밸런스', '중가 라이프스타일', '중가 필수케어',
        '대중 감성', '대중 밸런스', '대중 필수케어'
    ]

    i = 0
    for cluster_name in cluster_order:
        if cluster_name not in cluster_summary:
            continue
        brands = cluster_summary[cluster_name]
        if not brands:
            continue
        if i >= len(box_positions):
            break

        x, y, w, h = box_positions[i]
        color = cluster_colors.get(cluster_name, '#888888')

        # 박스 그리기
        rect = plt.Rectangle((x, y), w, h, fill=True,
                            facecolor=color, alpha=0.15,
                            edgecolor=color, linewidth=2)
        ax.add_patch(rect)

        # 클러스터 이름
        ax.text(x + w/2, y + h - 0.02, cluster_name,
               fontsize=10, fontweight='bold', ha='center', va='top',
               color=color)

        # 브랜드 수
        ax.text(x + w/2, y + h - 0.05, f'({len(brands)}개)',
               fontsize=8, ha='center', va='top', color='gray')

        # 브랜드 나열
        brand_text = '\n'.join(brands[:10])  # 최대 10개
        ax.text(x + w/2, y + h/2 - 0.03, brand_text,
               fontsize=8, ha='center', va='center')

        i += 1

    # 범례 추가
    legend_y = 0.25
    ax.text(0.5, legend_y, '분석 방법론', fontsize=11, fontweight='bold',
            ha='center', transform=ax.transAxes)
    ax.text(0.5, legend_y - 0.05,
            'Mass/Premium: 가격(50%) + 키워드(30%) + 주관(20%)\n'
            '필수재/사치재: 키워드(50%) + 주관(50%)\n'
            '기술/감성: 키워드(60%) + 주관(40%)',
            fontsize=9, ha='center', va='top', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'brand_cluster_map.png'), dpi=150,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print("저장: brand_cluster_map.png")

def main():
    print("브랜드 매트릭스 시각화 시작...")

    data = load_analysis()
    brands = data.get('brands', {})
    cluster_summary = data.get('cluster_summary', {})

    # 1. Mass/Premium vs 필수재/사치재
    create_2d_matrix(
        brands,
        'mass_premium', 'necessity_luxury',
        'Mass ←――――――――――――――――――→ Premium',
        '필수재/사치재',
        '브랜드 포지셔닝: Mass/Premium × 필수재/사치재',
        'matrix_mass_necessity.png'
    )

    # 2. Mass/Premium vs 기술/감성
    create_2d_matrix(
        brands,
        'mass_premium', 'tech_emotion',
        'Mass ←――――――――――――――――――→ Premium',
        '기술/감성',
        '브랜드 포지셔닝: Mass/Premium × 기술/감성',
        'matrix_mass_tech.png'
    )

    # 3. 필수재/사치재 vs 기술/감성
    create_2d_matrix(
        brands,
        'necessity_luxury', 'tech_emotion',
        '필수재 ←――――――――――――――――――→ 사치재',
        '기술/감성',
        '브랜드 포지셔닝: 필수재/사치재 × 기술/감성',
        'matrix_necessity_tech.png'
    )

    # 4. 클러스터 뷰
    create_cluster_view(brands, cluster_summary)

    print("\n시각화 완료!")

if __name__ == "__main__":
    main()
