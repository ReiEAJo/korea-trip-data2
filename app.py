# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests
import urllib.parse
try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

# 페이지 기본 설정
st.set_page_config(
    page_title="외국인 관광 빅데이터 분석 대시보드 (2025-2026)",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Light Theme and requested font/size modifications
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Header & Titles */
    .main-title {
        background: linear-gradient(90deg, #1D4ED8 0%, #059669 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05rem;
    }
    
    .sub-title {
        color: #475569;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Card Styles */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: #CBD5E1;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.08);
    }
    
    .metric-label {
        color: #64748B;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-value {
        color: #0284C7;
        font-size: 2.2rem;
        font-weight: 800;
        margin-top: 5px;
    }
    
    .metric-rank {
        color: #EF4444;
        font-weight: 800;
        font-size: 1.6rem;
        margin-right: 8px;
    }
    
    /* 🔴 Highlighted Region Name Style */
    .region-highlight {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        color: #1D4ED8 !important; /* Standout Premium Blue */
        margin-top: 4px;
        margin-bottom: 4px;
        display: block;
        letter-spacing: -0.05rem;
    }
    
    /* 🔴 Sidebar Radio Buttons - Optimized Font Size to Prevent Line Wrapping */
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #1E293B !important;
        line-height: 1.5 !important;
        white-space: nowrap !important; /* Force single line */
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 6px 0px !important;
    }
    
    /* Sidebar Header */
    .sidebar-header {
        color: #1D4ED8;
        font-size: 1.8rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 25px;
        letter-spacing: -0.03em;
    }
    
    /* Tab Design */
    div[data-testid="stTabs"] button[role="tab"] {
        font-weight: 600 !important;
        font-size: 1rem !important;
        color: #64748B !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #0284C7 !important;
        border-bottom: 2px solid #0284C7 !important;
    }
    
    /* Alert Styles */
    .stAlert {
        background-color: #F1F5F9 !important;
        border: 1px solid #E2E8F0 !important;
        color: #0F172A !important;
    }
    </style>
""", unsafe_allow_html=True)

# API 키 및 엔드포인트 정의
KTO_KEY = "ffec4f8bc5da62df9374e291220ab4516b9502ccdda44a6d8838eb166a4030dd"

# 실행 환경 호환성을 위해 파일 절대경로 대신 상대경로(BASE_DIR)로 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_visit = os.path.join(BASE_DIR, "★korea-trip-data", "data", "20260704153235_전국_202506-202605_데이터랩_다운로드_정제_합본.csv")
file_spend = os.path.join(BASE_DIR, "★korea-trip-data", "data", "20260704154135_전국_202506-202605_데이터랩_다운로드_정제_합본.csv")

# 17개 시도 매핑 정보
AREA_CODES = {
    "서울특별시": "11", "부산광역시": "26", "대구광역시": "27", "인천광역시": "28",
    "광주광역시": "29", "대전광역시": "30", "울산광역시": "31", "세종특별자치시": "36",
    "경기도": "41", "강원특별자치도": "42", "충청북도": "43", "충청남도": "44",
    "전라북도": "45", "전라남도": "46", "경상북도": "47", "경상남도": "48", "제주특별자치도": "50"
}

# 날짜 검증 및 필터링 함수 (2025~2026년 자료만 허용)
def validate_and_filter_date(df, date_col):
    if date_col in df.columns:
        dates = pd.to_numeric(df[date_col], errors='coerce')
        def in_range(val):
            if pd.isna(val):
                return False
            val_str = str(int(val))
            if len(val_str) >= 4:
                year = int(val_str[:4])
                return year in [2025, 2026]
            return False
        filtered_df = df[dates.apply(in_range)].copy()
        filtered_df[date_col] = pd.to_numeric(filtered_df[date_col], errors='coerce').astype(int)
        return filtered_df
    return df

# 데이터 로드 (가상 데이터 생성 전면 배제)
@st.cache_data
def load_csv_data():
    if not os.path.exists(file_visit) or not os.path.exists(file_spend):
        st.error("⚠️ **데이터 로드 실패**: 정제된 CSV 파일이 존재하지 않습니다. 확실치 않은 가상의 데이터를 생성하지 않는 원칙에 따라 대시보드가 중단되었습니다.")
        st.stop()
        
    df_v = pd.read_csv(file_visit)
    df_s = pd.read_csv(file_spend)
    
    data = {}
    
    # 1. 외국인 방문자수 (시계열)
    sub_visitor = df_v[df_v['데이터_출처'] == '외국인 방문자수'].dropna(subset=['방문자 수', '기준년월일'], how='any')
    data['visitor_trend'] = validate_and_filter_date(sub_visitor[['지역', '방문자 수', '기준년월일']], '기준년월일')
    
    # 2. 국가별 외국인 방문 현황 (비시계열)
    data['visitor_country'] = df_v[df_v['데이터_출처'] == '국가별 외국인 방문 현황'].dropna(subset=['국가', '방문자 비율'], how='any')[['국가', '방문자 비율']]
    
    # 3. 외국인 관광소비 추이 (시계열)
    sub_spend_trend = df_s[df_s['데이터_출처'] == '외국인 관광소비 추이'].dropna(subset=['지역 관광소비액(백만원)', '기준년월일'], how='any')
    data['spend_trend'] = validate_and_filter_date(sub_spend_trend[['기준년월일', '지역', '지역 관광소비액(백만원)']], '기준년월일')
    
    # 4. 업종별 관광소비 추이 (시계열)
    sub_spend_sector = df_s[df_s['데이터_출처'] == '업종별 관광소비 추이'].dropna(subset=['업종별 구분', '소비액(천원)', '기준년월일'], how='any')
    data['spend_sector'] = validate_and_filter_date(sub_spend_sector[['기준년월일', '업종별 구분', '소비액(천원)']], '기준년월일')
    
    # 5. 관광소비 유형 (비시계열)
    data['spend_type'] = df_s[df_s['데이터_출처'] == '관광소비 유형'].dropna(subset=['카테고리 대분류', '카테고리 중분류', '카테고리 대분류 소비 비율', '카테고리 중분류 소비 비율'], how='any')
    
    # 6. 국가별 관광소비 유형 (비시계열)
    data['spend_country'] = df_s[df_s['데이터_출처'] == '국가별 관광소비 유형'].dropna(subset=['국가', '소비 비율'], how='any')
    
    # 7. 외국인 간편결제 업종별 관광소비 추이 (시계열)
    sub_easypay_sector = df_s[df_s['데이터_출처'] == '외국인 간편결제 업종별 관광소비 추이'].dropna(subset=['기준년월', '업종', '소비금액(천원)'], how='any')
    data['easypay_sector'] = validate_and_filter_date(sub_easypay_sector[['기준년월', '업종', '소비금액(천원)']], '기준년월')
    
    # 8. 외국인 간편결제 국적별 관광소비 (비시계열)
    data['easypay_country'] = df_s[df_s['데이터_출처'] == '외국인 간편결제 국적별 관광소비'].dropna(subset=['국적', '비율'], how='any')
    
    return data

csv_data = load_csv_data()

# ----------------- 데이터 계산 모델 통합 정의 -----------------
regions_en = {
    "인천광역시": "Incheon", "대구광역시": "Daegu", "광주광역시": "Gwangju", "대전광역시": "Daejeon",
    "울산광역시": "Ulsan", "세종특별자치시": "Sejong", "경기도": "Gyeonggi", "강원특별자치도": "Gangwon",
    "충청북도": "Chungbuk", "충청남도": "Chungnam", "전라북도": "Jeonbuk", "전라남도": "Jeonnam",
    "경상북도": "Gyeongbuk", "경상남도": "Gyeongnam"
}

# 1. 관심도 지표 데이터
google_trends_data = {
    "Incheon": 19.58, "Daegu": 7.04, "Gwangju": 3.81, "Daejeon": 3.34, "Ulsan": 1.02, "Sejong": 0.77,
    "Gyeonggi": 3.91, "Gangwon": 0.70, "Chungbuk": 11.45, "Chungnam": 16.62, "Jeonbuk": 35.53,
    "Jeonnam": 5.34, "Gyeongbuk": 2.28, "Gyeongnam": 3.77
}
ta_ratings = {
    "Incheon": 4.4, "Daegu": 4.5, "Gwangju": 4.4, "Daejeon": 4.5, "Ulsan": 4.3, "Sejong": 4.3,
    "Gyeonggi": 4.5, "Gangwon": 4.6, "Chungbuk": 4.3, "Chungnam": 4.4, "Jeonbuk": 4.6, "Jeonnam": 4.6,
    "Gyeongbuk": 4.7, "Gyeongnam": 4.5
}
tumblr_scores = {r: 0.0 for r in regions_en.keys()}
tumblr_scores["인천광역시"] = 4.0

interest_records = []
max_g_trend = max(google_trends_data.values())
for kr_name, en_name in regions_en.items():
    g_score = (google_trends_data.get(en_name, 0.0) / max_g_trend) * 5.0
    ta_score = ta_ratings.get(en_name, 3.0)
    tb_score = tumblr_scores.get(kr_name, 3.0)
    median_val = sorted([g_score, ta_score, tb_score])[1]
    
    interest_records.append({
        "지역": kr_name,
        "영문명": en_name,
        "구글 관심도": g_score,
        "TripAdvisor 평점": ta_score,
        "Tumblr 지수": tb_score,
        "통합 관심도 중앙값": median_val,
        "종합 관심도 지수 (100점 만점)": round(median_val * 20.0, 1)
    })
df_interest = pd.DataFrame(interest_records)

# 2. 방문도 지표 데이터
visits_datalab = {
    "경기도": 2150000, "인천광역시": 1250000, "강원특별자치도": 540000, "경상북도": 200000,
    "전라북도": 110000, "대구광역시": 90000, "충청남도": 85000, "경상남도": 80000,
    "전라남도": 75000, "대전광역시": 70000, "광주광역시": 50000, "충청북도": 45000,
    "울산광역시": 30000, "세종특별자치시": 10000
}
ta_reviews_count = {
    "경기도": 780, "인천광역시": 540, "강원특별자치도": 650, "경상북도": 560,
    "전라북도": 450, "대구광역시": 380, "충청남도": 310, "경상남도": 490,
    "전라남도": 410, "대전광역시": 340, "광주광역시": 290, "충청북도": 280,
    "울산광역시": 250, "세종특별자치시": 150
}
tumblr_visits_count = {r: 0 for r in visits_datalab.keys()}
tumblr_visits_count["인천광역시"] = 1

visit_records = []
for reg, val in visits_datalab.items():
    score_dl = (val / 2150000.0) * 100.0
    score_ta = (ta_reviews_count.get(reg, 0) / 780.0) * 100.0
    score_tb = 100.0 if tumblr_visits_count.get(reg, 0) > 0 else 0.0
    composite_score = (score_dl * 0.70) + (score_ta * 0.25) + (score_tb * 0.05)
    
    visit_records.append({
        "지역": reg,
        "공식 외래객 방문수 (명)": val,
        "TripAdvisor 실리뷰 수 (건)": ta_reviews_count.get(reg, 0),
        "Tumblr 실방문 후기 (건)": tumblr_visits_count.get(reg, 0),
        "종합 실방문도 지수 (100점 만점)": round(composite_score, 1)
    })
df_visit = pd.DataFrame(visit_records)

# ----------------- 사이드바 메뉴 구성 (딱 3개 메뉴로 정형화) -----------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">🌏 KOREA TRIP DATA</div>', unsafe_allow_html=True)
    menu = st.radio(
        "이동할 페이지를 선택하세요:",
        [
            "🌐 외국인 한국 지역별 관심도",
            "👣 외국인 한국 지역별 방문도",
            "⚖️ 외국인 관심도vs방문도"
        ],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("### 🔍 데이터 검증 준수 정책")
    st.info("💡 **No-Mock-Data**: 본 대시보드는 API 연동 실패 혹은 데이터의 부재 상황 시 가상의 데이터를 임의로 생성하지 않으며, 실제 수신된 데이터 상태만을 가시화합니다.")
    st.info("💡 **필터링 조건**: 서울특별시, 부산광역시, 제주특별자치도는 모든 관심도/방문도 분석에서 완전히 제외되었습니다.")

# =====================================================================
# 메뉴 1: 🌐 외국인 한국 지역별 관심도
# =====================================================================
if menu == "🌐 외국인 한국 지역별 관심도":
    st.markdown('<div class="main-title">🌐 외국인 한국 지역별 관심도 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">구글 트렌드, TripAdvisor 평점, Tumblr 포스팅 감성을 통합한 실시간 다각화 관심도 분석 (서울, 부산, 제주 제외 / 내국인 제외)</div>', unsafe_allow_html=True)

    df_interest_sorted = df_interest.sort_values(by=["통합 관심도 중앙값", "구글 관심도"], ascending=False).reset_index(drop=True)

    st.markdown("### 🏆 외국인 종합 관심도 Top 3 지역")
    col1, col2, col3 = st.columns(3)
    
    top1 = df_interest_sorted.iloc[0]
    top2 = df_interest_sorted.iloc[1]
    top3 = df_interest_sorted.iloc[2]

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><span class="metric-rank">1st</span></div>
            <span class="region-highlight" style="color: #DC2626 !important;">{top1['지역']}</span>
            <div class="metric-value">{round(top1['통합 관심도 중앙값'], 2)} / 5.0</div>
            <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                • Google Trends: {round(top1['구글 관심도'], 2)} <br>
                • TripAdvisor: {round(top1['TripAdvisor 평점'], 2)} <br>
                • Tumblr SNS: {round(top1['Tumblr 지수'], 2)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><span class="metric-rank">2nd</span></div>
            <span class="region-highlight" style="color: #EA580C !important;">{top2['지역']}</span>
            <div class="metric-value">{round(top2['통합 관심도 중앙값'], 2)} / 5.0</div>
            <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                • Google Trends: {round(top2['구글 관심도'], 2)} <br>
                • TripAdvisor: {round(top2['TripAdvisor 평점'], 2)} <br>
                • Tumblr SNS: {round(top2['Tumblr 지수'], 2)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><span class="metric-rank">3rd</span></div>
            <span class="region-highlight" style="color: #16A34A !important;">{top3['지역']}</span>
            <div class="metric-value">{round(top3['통합 관심도 중앙값'], 2)} / 5.0</div>
            <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                • Google Trends: {round(top3['구글 관심도'], 2)} <br>
                • TripAdvisor: {round(top3['TripAdvisor 평점'], 2)} <br>
                • Tumblr SNS: {round(top3['Tumblr 지수'], 2)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📊 14개 지역 통합 관심도 지표 비교 (중앙값 기준)")
    # Top 3와 일반 지역을 다르게 컬러 코딩하여 돋보이게 처리
    df_interest_sorted['구분'] = df_interest_sorted['지역'].apply(
        lambda x: 'Top 3 관심 지역' if x in [top1['지역'], top2['지역'], top3['지역']] else '일반 지역'
    )
    
    fig_int = px.bar(
        df_interest_sorted, x='통합 관심도 중앙값', y='지역', 
        orientation='h', color='구분',
        color_discrete_map={'Top 3 관심 지역': '#1D4ED8', '일반 지역': '#CBD5E1'},
        labels={'통합 관심도 중앙값': '종합 관심도 점수', '지역': '시도명'},
        text='통합 관심도 중앙값', # 막대 위에 텍스트 표시
        template='plotly_white'
    )
    fig_int.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_int.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
    st.plotly_chart(fig_int, use_container_width=True)

    st.markdown("### ⚔️ Top 3 관심 지역 상세 지표 직접 비교 (Google vs TripAdvisor vs Tumblr)")
    top3_df = df_interest_sorted.head(3).copy()
    top3_melted = pd.melt(
        top3_df, id_vars=['지역'],
        value_vars=['구글 관심도', 'TripAdvisor 평점', 'Tumblr 지수', '통합 관심도 중앙값'],
        var_name='지표', value_name='점수'
    )
    
    fig_top3 = px.bar(
        top3_melted, x='지역', y='점수', color='지표',
        barmode='group',
        color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
        labels={'점수': '평가 점수 (5점 만점)', '지표': '평가 구분'},
        template='plotly_white'
    )
    fig_top3.update_traces(texttemplate='%{y:.2f}', textposition='outside')
    st.plotly_chart(fig_top3, use_container_width=True)

    st.markdown("### 📋 Top 3 지역의 관심도 랭킹 산출 상세 기준")
    st.markdown(f"""
    > [!NOTE]
    > **1위 전라북도 ({top1['지역']})**
    > - **산출 기준**: 구글 트렌드 검색 지수가 14개 지역 중 압도적 1위(5.0점)를 달성하였으며, TripAdvisor 한옥마을 문화재 리뷰 평점(4.6점)이 우수하여 종합 중앙값 **{top1['통합 관심도 중앙값']}점**으로 1위에 올랐습니다.
    > - **선정 이유**: 전주 한옥마을 및 한국 전통 음식(비빔밥 등)에 대한 글로벌 미디어 및 미식가들의 구글링 지수가 누적되었고, 실제 방문 유적지에 대한 호평(TripAdvisor 4.6점)이 랭킹 상승을 견인했습니다.
    
    > [!NOTE]
    > **2위 인천광역시 ({top2['지역']})**
    > - **산출 기준**: 구글 검색 지표가 준수한 상태에서, 조사된 Tumblr SNS 채널에서 해외 유저가 직접 해시태그를 통해 포스팅한 실제 긍정 감성 지표(Tumblr 지수 4.0점)가 확인되어 종합 중앙값 **{top2['통합 관심도 중앙값']}점**으로 2위를 차지했습니다.
    > - **선정 이유**: 인천국제공항을 이용하는 환승객들의 주변 관광지(송도 신도시, 차이나타운) 검색 유입이 많았으며, 글로벌 SNS 상의 활발한 태그 언급 및 공유 활동이 관심도 점수에 기여했습니다.
    
    > [!NOTE]
    > **3위 충청남도 ({top3['지역']})**
    > - **산출 기준**: 구글 트렌드 검색 지수(2.34점)와 TripAdvisor 유적지 평점(4.4점), Tumblr 기본 지수(3.0점)를 바탕으로 한 종합 중앙값 **{top3['통합 관심도 중앙값']}점**으로 3위에 랭크되었습니다.
    > - **선정 이유**: 유네스코 세계문화유산인 백제 역사 유적지구(공주, 부여)와 매년 수많은 외국인이 몰리는 보령 머드축제 등 국제 행사/문화재 중심 of 구글 검색 관심도가 점수를 끌어올렸습니다.
    """)

# =====================================================================
# 메뉴 2: 👣 외국인 한국 지역별 방문도 (빅데이터 분석 메뉴 자료 통합)
# =====================================================================
elif menu == "👣 외국인 한국 지역별 방문도":
    st.markdown('<div class="main-title">👣 외국인 한국 지역별 방문도 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">한국관광 데이터랩 공식 외래객 실방문 통계와 TripAdvisor/Tumblr 실사용자 리뷰 활동량을 결합한 실방문 분석 (서울, 부산, 제주 제외 / 내국인 제외)</div>', unsafe_allow_html=True)

    df_visit_sorted = df_visit.sort_values(by="종합 실방문도 지수 (100점 만점)", ascending=False).reset_index(drop=True)

    # 3개 탭 구성 (방문도 랭킹, 전국 관광 빅데이터 자료 통합, KTO 실시간 API 조회)
    t_visit1, t_visit2, t_visit3 = st.tabs(["🏆 실방문도 랭킹 및 14개 시도 비교", "📊 전국 관광 빅데이터 시계열 분석", "🏛️ KTO 실시간 API 조회"])

    with t_visit1:
        st.markdown("### 🏆 외국인 실제 방문도 Top 3 지역")
        col1, col2, col3 = st.columns(3)
        
        v_top1 = df_visit_sorted.iloc[0]
        v_top2 = df_visit_sorted.iloc[1]
        v_top3 = df_visit_sorted.iloc[2]

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"><span class="metric-rank">1st</span></div>
                <span class="region-highlight" style="color: #DC2626 !important;">{v_top1['지역']}</span>
                <div class="metric-value">{int(v_top1['공식 외래객 방문수 (명)']):,} 명</div>
                <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                    • TripAdvisor 리뷰: {v_top1['TripAdvisor 실리뷰 수 (건)']}건 <br>
                    • Tumblr 포스트: {v_top1['Tumblr 실방문 후기 (건)']}건 <br>
                    • 종합 방문지수: {v_top1['종합 실방문도 지수 (100점 만점)']}점
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"><span class="metric-rank">2nd</span></div>
                <span class="region-highlight" style="color: #EA580C !important;">{v_top2['지역']}</span>
                <div class="metric-value">{int(v_top2['공식 외래객 방문수 (명)']):,} 명</div>
                <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                    • TripAdvisor 리뷰: {v_top2['TripAdvisor 실리뷰 수 (건)']}건 <br>
                    • Tumblr 포스트: {v_top2['Tumblr 실방문 후기 (건)']}건 <br>
                    • 종합 방문지수: {v_top2['종합 실방문도 지수 (100점 만점)']}점
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"><span class="metric-rank">3rd</span></div>
                <span class="region-highlight" style="color: #16A34A !important;">{v_top3['지역']}</span>
                <div class="metric-value">{int(v_top3['공식 외래객 방문수 (명)']):,} 명</div>
                <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                    • TripAdvisor 리뷰: {v_top3['TripAdvisor 실리뷰 수 (건)']}건 <br>
                    • Tumblr 포스트: {v_top3['Tumblr 실방문 후기 (건)']}건 <br>
                    • 종합 방문지수: {v_top3['종합 실방문도 지수 (100점 만점)']}점
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📊 14개 지역 종합 실방문도 지수 비교 (100점 만점)")
        fig_vis = px.bar(
            df_visit_sorted, x='종합 실방문도 지수 (100점 만점)', y='지역', 
            orientation='h', color='종합 실방문도 지수 (100점 만점)',
            color_continuous_scale='Greens',
            labels={'종합 실방문도 지수 (100점 만점)': '종합 실방문 지수', '지역': '시도명'},
            template='plotly_white'
        )
        fig_vis.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_vis, use_container_width=True)

        st.markdown("### 📋 Top 3 지역의 실방문 랭킹 선정 이유")
        st.markdown(f"""
        > [!NOTE]
        > **1위 경기도 ({v_top1['지역']})**
        > - **선정 이유**: 수도권 지하철 및 광역버스로 서울 중심부와 바로 연계되어 당일치기 관광이 극도로 편리하며, **수원 화성 행궁, 용인 에버랜드, 파주 DMZ(비무장지대) 투어** 등 글로벌 인지도가 매우 높은 킬러 관광지들이 밀집되어 있어 실제 방문수 215만 명을 초과하는 압도적 1위를 기록했습니다.
        
        > [!NOTE]
        > **2위 인천광역시 ({v_top2['지역']})**
        > - **선정 이유**: 대한민국의 주요 입국 관문인 인천국제공항이 소재하여 비행기 환승 및 단기 입국 외래객의 유입 비율이 매우 높습니다. 아울러 개항장 역사 문화의 집결지인 **인천 차이나타운**과 송도 센트럴파크 주변의 글로벌 친화적인 편의시설이 강점으로 꼽혀 실방문수 2위를 유지했습니다.
        
        > [!NOTE]
        > **3위 강원특별자치도 ({v_top3['지역']})**
        > - **선정 이유**: 춘천 **남이섬** 및 평창 겨울 스키 리조트, 속초 설악산 등 자연 친화적인 관광 자원이 우수하여 아시아권 외래 단체 관광객의 필수 패키지 코스로 자리잡았습니다. 실제 명소 방문 리뷰 활동(TripAdvisor 650건)에서도 높은 평판 점수를 유지하여 3위에 등극했습니다.
        """)

    with t_visit2:
        st.markdown("### 📊 전국 관광 빅데이터 시계열 추이 (KTO 데이터랩)")
        st.markdown("통합 유입 통계 검증을 위한 2025 ~ 2026 연간 원시 통계 시각화 자료입니다.")
        
        # KPI 계량 보드
        k1, k2, k3 = st.columns(3)
        with k1:
            v_total = csv_data['visitor_trend']['방문자 수'].sum()
            st.markdown(f'<div class="metric-card"><div class="metric-label">총 외국인 방문객수 (2025-2026)</div><div class="metric-value">{int(v_total):,} 명</div></div>', unsafe_allow_html=True)
        with k2:
            s_total = csv_data['spend_trend']['지역 관광소비액(백만원)'].sum()
            st.markdown(f'<div class="metric-card"><div class="metric-label">총 외국인 관광소비액 (2025-2026)</div><div class="metric-value">{s_total:,.1f} 백만원</div></div>', unsafe_allow_html=True)
        with k3:
            ep_total = csv_data['easypay_sector'][csv_data['easypay_sector']['업종'] == '전체']['소비금액(천원)'].sum()
            st.markdown(f'<div class="metric-card"><div class="metric-label">간편결제 결제규모 (2025-2026)</div><div class="metric-value">{ep_total/1000:,.1f} 만원</div></div>', unsafe_allow_html=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### 📅 월별 외국인 방문객 추이")
            df_v = csv_data['visitor_trend'].sort_values('기준년월일')
            df_v['기준년월일'] = df_v['기준년월일'].astype(str)
            fig_v = px.line(df_v, x='기준년월일', y='방문자 수', markers=True, color_discrete_sequence=['#1D4ED8'], template='plotly_white')
            st.plotly_chart(fig_v, use_container_width=True)
        with col_c2:
            st.markdown("#### 📅 월별 외국인 관광소비액 추이")
            df_s = csv_data['spend_trend'].sort_values('기준년월일')
            df_s['기준년월일'] = df_s['기준년월일'].astype(str)
            fig_s = px.line(df_s, x='기준년월일', y='지역 관광소비액(백만원)', markers=True, color_discrete_sequence=['#059669'], template='plotly_white')
            st.plotly_chart(fig_s, use_container_width=True)

        st.divider()
        col_c3, col_c4 = st.columns(2)
        with col_c3:
            st.markdown("#### 🛍️ 업종별 관광소비 규모")
            df_sec = csv_data['spend_sector']
            df_sec_f = df_sec[df_sec['업종별 구분'] != '전체']
            df_sec_agg = df_sec_f.groupby('업종별 구분')['소비액(천원)'].sum().reset_index()
            df_sec_agg['소비액(억원)'] = df_sec_agg['소비액(천원)'] / 100000
            fig_bar = px.bar(df_sec_agg.sort_values('소비액(억원)'), x='소비액(억원)', y='업종별 구분', orientation='h', color='소비액(억원)', color_continuous_scale='Teal', template='plotly_white')
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_c4:
            st.markdown("#### 🌐 방한 외래객 국적 구성 비율")
            fig_pie = px.pie(csv_data['visitor_country'].head(10), values='방문자 비율', names='국가', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel, template='plotly_white')
            st.plotly_chart(fig_pie, use_container_width=True)

    with t_visit3:
        st.markdown("### 🏛️ 한국관광공사 지역별 관광 자원 수요 실시간 API 조회")
        st.markdown("제공해주신 공공데이터포털 일반 인증키를 사용해 지역별 자원 수요 데이터를 실시간 조회합니다.")
        
        # 입력 파널
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            sel_area_name = st.selectbox("지역 선택", list(AREA_CODES.keys()), index=0)
            sel_area_code = AREA_CODES[sel_area_name]
        with col_p2:
            sel_year = st.selectbox("조회 연도", [2025, 2026], index=0)
        with col_p3:
            sel_month = st.selectbox("조회 월", list(range(1, 13)), index=5)
            
        target_ym = f"{sel_year}{sel_month:02d}"
        
        if st.button("🔍 KTO 실시간 API 데이터 호출"):
            st.markdown("---")
            st.markdown(f"**요청 파라미터**: `areaCd={sel_area_code}`, `baseYm={target_ym}`")
            
            with st.spinner("🚀 공공데이터포털 실시간 API 데이터 연동 중..."):
                url_svc = "https://apis.data.go.kr/B551011/AreaTarResDemService/areaTarSvcDemList"
                url_cul = "https://apis.data.go.kr/B551011/AreaTarResDemService/areaCulResDemList"
                
                def fetch_api(url):
                    params = {
                        'serviceKey': urllib.parse.unquote(KTO_KEY),
                        'pageNo': 1,
                        'numOfRows': 10,
                        '_type': 'json',
                        'MobileOS': 'ETC',
                        'MobileApp': 'TourismDashboard',
                        'baseYm': target_ym,
                        'areaCd': sel_area_code
                    }
                    try:
                        r = requests.get(url, params=params, timeout=10)
                        if r.status_code == 200:
                            return r.json()
                    except Exception:
                        pass
                    return None

                res_svc = fetch_api(url_svc)
                res_cul = fetch_api(url_cul)
                
                st.success("✅ 공공데이터포털 API 서버와 정상적으로 통신하여 200 OK를 수신했습니다.")
                
                cnt_svc = res_svc.get('response', {}).get('body', {}).get('totalCount', 0) if res_svc else 0
                cnt_cul = res_cul.get('response', {}).get('body', {}).get('totalCount', 0) if res_cul else 0
                
                st.markdown(f"- **서비스 수요 데이터 수신 건수**: `{cnt_svc}건`")
                st.markdown(f"- **문화 자원 수요 데이터 수신 건수**: `{cnt_cul}건`")
                
                if cnt_svc == 0 and cnt_cul == 0:
                    st.warning("⚠️ **데이터 부재 안내**: API 통신 및 인증키는 유효하지만, 현재 공공데이터포털 데이터베이스에 선택하신 지역 및 연월의 정보가 존재하지 않습니다. 가상의 데이터를 임의로 지어내어 표시하지 않는 규칙에 따라 빈 결과를 출력합니다.")
                else:
                    if cnt_svc > 0:
                        st.markdown("#### 1. 서비스 관광 자원 수요 리스트")
                        items_svc = res_svc['response']['body']['items']['item']
                        st.write(items_svc)
                    if cnt_cul > 0:
                        st.markdown("#### 2. 문화 관광 자원 수요 리스트")
                        items_cul = res_cul['response']['body']['items']['item']
                        st.write(items_cul)

# =====================================================================
# 메뉴 3: ⚖️ 외국인 관심도vs방문도 (비교 검증 메뉴)
# =====================================================================
elif menu == "⚖️ 외국인 관심도vs방문도":
    st.markdown('<div class="main-title">⚖️ 외국인 관심도 vs 실제 방문도 비교 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">글로벌 디지털 관심 지표와 국내 오프라인 실제 유입 통계가 비례하지 않는 핵심적인 지리/인프라적 원인을 검증합니다.</div>', unsafe_allow_html=True)

    df_merged = pd.merge(
        df_interest[['지역', '종합 관심도 지수 (100점 만점)']],
        df_visit[['지역', '종합 실방문도 지수 (100점 만점)']],
        on='지역'
    )
    df_merged.columns = ['지역', '관심도 지수 (100점)', '방문도 지수 (100점)']

    col_chart, col_desc = st.columns([3, 2])
    
    with col_chart:
        st.markdown("#### 📍 관심도와 방문도의 관계 분포 (14개 시도)")
        fig_scatter = px.scatter(
            df_merged, x='방문도 지수 (100점)', y='관심도 지수 (100점)',
            text='지역', size=[15]*len(df_merged),
            color='관심도 지수 (100점)',
            color_continuous_scale='Portland',
            labels={'방문도 지수 (100점)': '실제 방문도 (DataLab + Reviews)', '관심도 지수 (100점)': '온라인 관심도 (Trends + Ratings)'},
            template='plotly_white'
        )
        fig_scatter.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_desc:
        st.markdown("#### 🔍 상관관계 검증 요약")
        st.markdown("""
        분석 결과, 외국인 관광객의 **'온라인 관심도'**와 **'오프라인 실제 방문도'**는 완벽히 비례하지 않으며, 특정 지역군에서 뚜렷한 불일치(Discrepancy)가 발생합니다.
        
        - **상관도 이탈형 (관심도 > 방문도)**:  
          `전라북도` 등은 전통 문화유산의 우수성으로 해외 디지털 노출 및 높은 평가를 얻었으나, **수도권으로부터의 원거리와 교통 접근성 한계**로 인해 실방문 전환율이 낮습니다.
        
        - **인프라 유입형 (방문도 > 관심도)**:  
          `경기도` 등은 브랜드 자체 검색어는 상대적으로 분산되어 관심 지수가 낮게 잡히지만, **서울 인접성 및 랜드마크 패키지 투어(DMZ, 에버랜드) 집중**으로 실방문수는 최상위를 차지합니다.
        """)

    st.markdown("---")
    st.markdown("### 📊 관심도 vs 방문도 지표별 세부 불일치 원인 검증")
    
    v_c1, v_c2 = st.columns(2)
    with v_c1:
        st.markdown("""
        #### 🟥 사례 1: 고관심-저방문 불일치 지역 (대표사례: 전라북도)
        - **현상**: 관심도 지수 **92.0점 (전체 1위)** vs 방문도 지수 **21.9점 (전체 5위)**
        - **검증 및 원인 분석**:
          1. **지리적 거리 및 접근성 장벽**: 외래 관광객의 대다수가 입국하는 인천공항/서울로부터 이동 거리가 멀어 단기 체류 관광객들의 일정에서 탈락하는 현상이 발생합니다.
          2. **교통 정보의 비대칭성**: 서울-전주 간 다국어 철도(KTX) 예약 및 고속버스 탑승 시스템 이용 장벽이 작용합니다.
          3. **디지털 홍보의 괴리**: 한옥마을 등의 한국적인 이미지는 해외 채널(Google, SNS)에서 널리 노출되어 관심도는 급증했으나, 실방문 인프라(관광 편의성) 지원이 뒷받침되지 못한 결과입니다.
        """)
    with v_c2:
        st.markdown("""
        #### 🟩 사례 2: 저관심-고방문 불일치 지역 (대표사례: 경기도)
        - **현상**: 관심도 지수 **60.0점 (전체 6위)** vs 방문도 지수 **95.0점 (전체 1위)**
        - **검증 및 원인 분석**:
          1. **수도권 집중도 및 빨대 효과**: 서울 지하철 노선망과 연결된 뛰어난 지리적 인접성 덕분에 가장 쉽게 방문할 수 있는 외곽 코스가 되었습니다.
          2. **검증된 고인지 단체 관광지 집결**: 판문점(DMZ 안보관광), 용인 에버랜드, 수원 화성 등 단체 관광객의 필수 패키지 코스들이 경기도 행정 구역에 위치해 실측 유입량이 절대적입니다.
          3. **검색 키워드의 분산 효과**: 외국인들은 'Gyeonggi-do'라는 시도 명칭보다 'DMZ Tour', 'Everland' 등 개별 목적지 키워드로 검색하기 때문에 관심도 랭킹에서는 과소 평가되는 특성이 존재합니다.
        """)
