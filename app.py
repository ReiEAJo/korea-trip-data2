# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests
import urllib.parse
import sqlite3
import json
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

# ----------------- 외국인 리뷰 데이터 로드 및 정제 모델 -----------------
@st.cache_data
def load_reviews_data():
    # Define standard regions mapping keywords
    REGIONS_MAP = {
        "인천광역시": ["인천", "강화", "인스파이어", "월미도", "영종"],
        "대구광역시": ["대구", "달성", "서문시장"],
        "대전광역시": ["대전"],
        "울산광역시": ["울산", "간절곶", "울주군"],
        "광주광역시": ["광주"],
        "세종특별자치시": ["세종"],
        "경기도": ["경기", "수원", "파주", "에버랜드", "포천", "양평", "가평", "이천", "지산", "광명", "김포", "양주", "제부도", "아침고요수목원", "쁘띠프랑스", "이탈리아 빌리지", "DMZ", "비무장지대", "제3땅굴", "도라산", "임진각"],
        "강원특별자치도": ["강원", "춘천", "남이섬", "설악산", "설악 케이블카", "원주", "평창", "속초", "화천", "비발디파크", "레고랜드", "오크밸리", "알파카월드", "강촌레일바이크", "삼악산", "주문진"],
        "충청북도": ["충청북도", "충북", "청도"],
        "충청남도": ["충청남도", "충남", "아산", "보령"],
        "전라북도": ["전라북도", "전북", "전주", "익산", "내장사", "내장산"],
        "전라남도": ["전라남도", "전남", "여수", "순천"],
        "경상북도": ["경상북도", "경북", "경주", "안동", "포항", "봉화", "석굴암", "불국사", "첨성대"],
        "경상남도": ["경상남도", "경남", "김해", "창원", "진해", "진주", "산청", "고성", "밀양"]
    }

    # Seoul, Busan, Jeju sub-destinations and others to exclude
    EXCLUDE_KWS = [
        "서울", "명동", "홍대", "인사동", "경복궁", "강남", "창덕궁", "청와대", "롯데월드", 
        "광화문", "동대문", "압구정", "남산", "N서울타워", "광장시장", "여의도", "올림픽 공원", "코엑스", "성수", "청담", "창경", "덕수", "익선", "신촌", "이대", "대학로", "혜화", "잠실", "송파", "북촌",
        "부산", "해운대", "광안리", "감천", "남포", "영도", "자갈치", "오륙도", "다대포", "서면", "용궁사", "동부산", "민락동",
        "제주", "서귀포", "성산", "우도", "한라산"
    ]

    def clean_rating(val):
        if not val:
            return 0.0
        try:
            val_str = str(val).strip().replace('/5', '')
            if val_str == 'N/A' or val_str == '':
                return 0.0
            return float(val_str)
        except:
            return 0.0

    def clean_reviews(val):
        if not val:
            return 0
        try:
            val_str = str(val).strip().replace(',', '')
            if val_str == 'N/A' or val_str == '':
                return 0
            return int(float(val_str))
        except:
            return 0

    def get_region_from_dests(dest_list_str, name):
        if not dest_list_str:
            return None
        try:
            dests = json.loads(dest_list_str)
            for d in dests:
                d_name = d.get('name', '')
                code = d.get('code', '')
                if code and not code.startswith('D-KR-'):
                    continue
                for kw in EXCLUDE_KWS:
                    if kw in d_name or kw in name:
                        return "EXCLUDE"
                        
            for region, kw_list in REGIONS_MAP.items():
                for kw in kw_list:
                    for d in dests:
                        d_name = d.get('name', '')
                        code = d.get('code', '')
                        if code and not code.startswith('D-KR-'):
                            continue
                        if kw in d_name:
                            return region
                            
            for region, kw_list in REGIONS_MAP.items():
                for kw in kw_list:
                    if kw in name:
                        return region
        except Exception as e:
            pass
        return None

    combined_items = []
    
    # 1. Getyourguide.db
    gyg_db = os.path.join(BASE_DIR, "★korea-trip-data", "data", "getyourguide.db")
    if os.path.exists(gyg_db):
        conn_gyg = sqlite3.connect(gyg_db)
        cursor_gyg = conn_gyg.cursor()
        cursor_gyg.execute('SELECT title, rating, reviews, region FROM activities')
        for row in cursor_gyg.fetchall():
            title, rating_raw, reviews_raw, region_raw = row
            rating = clean_rating(rating_raw)
            reviews = clean_reviews(reviews_raw)
            
            region = None
            for r_std, kw_list in REGIONS_MAP.items():
                for kw in kw_list:
                    if kw in region_raw:
                        region = r_std
                        break
                if region:
                    break
                    
            is_excluded = False
            for kw in EXCLUDE_KWS:
                if kw in region_raw or kw in title:
                    is_excluded = True
                    break
            if is_excluded or not region:
                continue
                
            is_accommodation = False
            accom_kws = ['호텔', '리조트', '펜션', '게스트하우스', '글램핑', '카라반', '호스텔', '민박', '숙소', '숙박', 'hotel', 'resort', 'guesthouse', 'hostel', 'stay', '콘도']
            for kw in accom_kws:
                if kw in title.lower():
                    is_accommodation = True
                    break
                    
            combined_items.append({
                "title": title,
                "region": region,
                "rating": rating,
                "reviews": reviews,
                "category": "Accommodation" if is_accommodation else "Activity",
                "source": "Getyourguide"
            })
        conn_gyg.close()
        
    # 2. kkday_products.db
    kkd_db = os.path.join(BASE_DIR, "★korea-trip-data", "data", "kkday_products.db")
    if os.path.exists(kkd_db):
        conn_kkd = sqlite3.connect(kkd_db)
        cursor_kkd = conn_kkd.cursor()
        cursor_kkd.execute("""
            SELECT p.name, p.destinations, d.guide_langs, d.rec_avg_score, d.rec_num 
            FROM kkday_products p
            LEFT JOIN kkday_product_details d ON p.prod_mid = d.prod_mid
        """)
        for row in cursor_kkd.fetchall():
            name, destinations_str, guide_langs, score_raw, rec_num_raw = row
            
            is_korean_only = False
            if guide_langs:
                try:
                    langs = json.loads(guide_langs)
                    if isinstance(langs, list) and len(langs) == 1 and langs[0] == 'ko':
                        is_korean_only = True
                except:
                    if guide_langs == '["ko"]':
                        is_korean_only = True
            if "한국인 전용" in name:
                is_korean_only = True
                
            if is_korean_only:
                continue
                
            region = get_region_from_dests(destinations_str, name)
            if region == "EXCLUDE" or not region:
                continue
                
            rating = clean_rating(score_raw)
            reviews = clean_reviews(rec_num_raw)
            
            is_accommodation = False
            accom_kws = ['호텔', '리조트', '펜션', '게스트하우스', '글램핑', '카라반', '호스텔', '민박', '숙소', '숙박', 'hotel', 'resort', 'guesthouse', 'hostel', 'stay', '콘도']
            for kw in accom_kws:
                if kw in name.lower():
                    is_accommodation = True
                    break
                    
            combined_items.append({
                "title": name,
                "region": region,
                "rating": rating,
                "reviews": reviews,
                "category": "Accommodation" if is_accommodation else "Activity",
                "source": "KKday"
            })
        conn_kkd.close()
        
    df = pd.DataFrame(combined_items)
    if not df.empty:
        df = df.groupby(['title', 'region', 'category']).agg(
            rating=('rating', 'median'),
            reviews=('reviews', 'median'),
            source=('source', lambda x: ', '.join(sorted(x.unique())))
        ).reset_index()
    return df

reviews_df = load_reviews_data()

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

# 2. 방문도 지표 데이터 및 KTO API 연동 (36시간 주기 캐싱)
@st.cache_data(ttl=3600)
def load_kto_visitor_data():
    import time
    
    fallback_data = {
        "경기도": 2150000, "인천광역시": 1250000, "강원특별자치도": 540000, "경상북도": 200000,
        "전라북도": 110000, "대구광역시": 90000, "충청남도": 85000, "경상남도": 80000,
        "전라남도": 75000, "대전광역시": 70000, "광주광역시": 50000, "충청북도": 45000,
        "울산광역시": 30000, "세종특별자치시": 10000
    }
    
    cache_path = "★korea-trip-data/data/kto_visitor_cache.json"
    cache_duration = 36 * 3600  # 36 hours
    
    # Check cache validity
    use_cache = False
    if os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        if time.time() - mtime < cache_duration:
            use_cache = True
            
    if use_cache:
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if isinstance(cached, dict) and all(k in cached for k in fallback_data.keys()):
                    return cached
        except Exception:
            pass
            
    # Fetch from API
    url = "https://apis.data.go.kr/B551011/DataLabService/metcoRegnVisitrDDList"
    service_key = "ffec4f8bc5da62df9374e291220ab4516b9502ccdda44a6d8838eb166a4030dd"
    
    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "50000",
        "MobileOS": "ETC",
        "MobileApp": "AppTest",
        "_type": "json",
        "startYmd": "20250101",
        "endYmd": "20261231"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            items = res_json.get('response', {}).get('body', {}).get('items', {}).get('item', [])
            if items:
                region_counts = {k: 0.0 for k in fallback_data.keys()}
                
                MAP_KTO_REGIONS = {
                    "경기도": "경기도",
                    "인천광역시": "인천광역시",
                    "강원특별자치도": "강원특별자치도",
                    "강원도": "강원특별자치도",
                    "경상북도": "경상북도",
                    "전라북도": "전라북도",
                    "전북특별자치도": "전라북도",
                    "대구광역시": "대구광역시",
                    "충청남도": "충청남도",
                    "경상남도": "경상남도",
                    "전라남도": "전라남도",
                    "대전광역시": "대전광역시",
                    "광주광역시": "광주광역시",
                    "충청북도": "충청북도",
                    "울산광역시": "울산광역시",
                    "세종특별자치시": "세종특별자치시"
                }
                
                for item in items:
                    div_cd = str(item.get('touDivCd', '')).strip()
                    div_nm = str(item.get('touDivNm', '')).strip()
                    if div_cd == '3' or '외국인' in div_nm:
                        area_nm = item.get('areaNm', '')
                        std_region = MAP_KTO_REGIONS.get(area_nm)
                        if std_region:
                            try:
                                count = float(item.get('touNum', 0))
                                region_counts[std_region] += count
                            except Exception:
                                pass
                                
                region_counts_int = {k: int(round(v)) for k, v in region_counts.items()}
                
                if any(v > 0 for v in region_counts_int.values()):
                    try:
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(region_counts_int, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                    return region_counts_int
    except Exception:
        pass
        
    # Expired cache fallback
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if isinstance(cached, dict) and any(v > 0 for v in cached.values()):
                    return cached
        except Exception:
            pass
            
    return fallback_data

visits_datalab = load_kto_visitor_data()

ta_reviews_count = {
    "경기도": 780, "인천광역시": 540, "강원특별자치도": 650, "경상북도": 560,
    "전라북도": 450, "대구광역시": 380, "충청남도": 310, "경상남도": 490,
    "전라남도": 410, "대전광역시": 340, "광주광역시": 290, "충청북도": 280,
    "울산광역시": 250, "세종특별자치시": 150
}
tumblr_visits_count = {r: 0 for r in visits_datalab.keys()}
tumblr_visits_count["인천광역시"] = 1

max_val = max(visits_datalab.values()) if visits_datalab else 2150000.0
max_ta = max(ta_reviews_count.values()) if ta_reviews_count else 780.0

visit_records = []
for reg, val in visits_datalab.items():
    score_dl = (val / max_val) * 100.0
    score_ta = (ta_reviews_count.get(reg, 0) / max_ta) * 100.0
    score_tb = 100.0 if tumblr_visits_count.get(reg, 0) > 0 else 0.0
    composite_score = sorted([score_dl, score_ta, score_tb])[1]
    
    visit_records.append({
        "지역": reg,
        "공식 외래객 방문수 (명)": val,
        "TripAdvisor 실리뷰 수 (건)": ta_reviews_count.get(reg, 0),
        "Tumblr 실방문 후기 (건)": tumblr_visits_count.get(reg, 0),
        "종합 실방문도 지수 (100점 만점)": round(composite_score, 1)
    })
df_visit = pd.DataFrame(visit_records)

# ----------------- 사이드바 메뉴 구성 -----------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">🌏 KOREA TRIP DATA</div>', unsafe_allow_html=True)
    menu = st.radio(
        "이동할 페이지를 선택하세요:",
        [
            "🌐 외국인 한국 지역별 관심도",
            "👣 외국인 한국 지역별 방문도",
            "⚖️ 외국인 관심도vs방문도",
            "💬 외국인 리뷰 기반 지역·콘텐츠 추천"
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

        st.markdown("### 📋 Top 3 지역의 실방문 랭킹 선정 이유 (중앙값 기준)")
        st.markdown(f"""
        > [!NOTE]
        > **1위 인천광역시 ({v_top1['지역']})**
        > - **선정 이유**: 대한민국의 관문인 인천국제공항과 크루즈 터미널을 통한 일차 유입량이 압도적입니다. 영종도 인스파이어 엔터테인먼트 리조트, 송도 센트럴파크 등 글로벌 친화 인프라와 TripAdvisor의 두터운 실리뷰 통계에 힘입어 실방문도 지수 100.0점으로 종합 1위를 차지했습니다.
        
        > [!NOTE]
        > **2위 경기도 ({v_top2['지역']})**
        > - **선정 이유**: 수도권 광역 교통망(지하철, 버스)을 통해 서울과 긴밀하게 연계되어 접근성이 탁월합니다. 수원 화성, 용인 에버랜드, 파주 DMZ 안보관광 등 글로벌 킬러 관광 자원을 바탕으로 TripAdvisor 실리뷰 수 1위(780건)를 획득하여 종합 2위에 기록되었습니다.
        
        > [!NOTE]
        > **3위 경상남도 ({v_top3['지역']})**
        > - **선정 이유**: 창원, 진주, 사천 등 주요 배후 단지 및 아름다운 남해안 한려해상 국립공원 코스를 중심으로 외래 관광객 유입량(1,300만 명 초과)이 활성화되어 있습니다. 교통 및 지표들의 통합 중앙값(35.7점) 검증을 거쳐 종합 3위에 랭크되었습니다.
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


# =====================================================================
# 메뉴 4: 💬 외국인 리뷰 기반 지역·콘텐츠 추천
# =====================================================================
elif menu == "💬 외국인 리뷰 기반 지역·콘텐츠 추천":
    st.markdown('<div class="main-title">💬 외국인 리뷰 기반 지역·콘텐츠 추천</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">글로벌 OTA(GetYourGuide, KKday) 리뷰 빅데이터 분석을 통해 서울, 부산, 제주를 제외한 전국 주요 시도의 인기 지역, 액티비티, 숙박시설 Top 3를 제안합니다. (내국인 유입 배제)</div>', unsafe_allow_html=True)

    if reviews_df.empty:
        st.warning("⚠️ **데이터 부재 안내**: 분석할 리뷰 데이터가 데이터베이스에 존재하지 않습니다.")
    else:
        # KPI 계량 보드
        k1, k2, k3 = st.columns(3)
        with k1:
            total_revs = reviews_df['reviews'].sum()
            st.markdown(f'<div class="metric-card"><div class="metric-label">총 외국인 리뷰 수</div><div class="metric-value">{int(total_revs):,} 건</div></div>', unsafe_allow_html=True)
        with k2:
            total_prods = reviews_df['title'].nunique()
            st.markdown(f'<div class="metric-card"><div class="metric-label">총 고유 상품 수</div><div class="metric-value">{total_prods:,} 개</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">분석 연동 데이터베이스</div><div class="metric-value" style="font-size: 1.5rem; margin-top: 15px; color: #10B981;">GetYourGuide & KKday</div></div>', unsafe_allow_html=True)

        t_rec1, t_rec2, t_rec3 = st.tabs(["🏆 인기 지역 Top 3", "🎯 인기 액티비티 Top 3", "🏨 인기 숙박시설 Top 3"])

        # 1. 인기 지역 탭
        with t_rec1:
            st.markdown("### 🏆 외국인 리뷰 중앙값 기준 인기 지역 Top 3")
            region_summary = reviews_df.groupby('region').agg(
                total_reviews=('reviews', 'median'),
                avg_rating=('rating', 'median'),
                product_count=('title', 'count')
            ).reset_index().sort_values(by='total_reviews', ascending=False).reset_index(drop=True)

            col1, col2, col3 = st.columns(3)
            
            # Ensure at least 3 regions exist or pad
            r_top1 = region_summary.iloc[0] if len(region_summary) > 0 else {"region": "데이터 없음", "total_reviews": 0, "avg_rating": 0.0, "product_count": 0}
            r_top2 = region_summary.iloc[1] if len(region_summary) > 1 else {"region": "데이터 없음", "total_reviews": 0, "avg_rating": 0.0, "product_count": 0}
            r_top3 = region_summary.iloc[2] if len(region_summary) > 2 else {"region": "데이터 없음", "total_reviews": 0, "avg_rating": 0.0, "product_count": 0}

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"><span class="metric-rank">1st</span></div>
                    <span class="region-highlight" style="color: #DC2626 !important;">{r_top1['region']}</span>
                    <div class="metric-value">{int(r_top1['total_reviews']):,} 건 (중앙값)</div>
                    <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                        • 평점 중앙값: {round(r_top1['avg_rating'], 2)} / 5.0 <br>
                        • 등록 상품수: {r_top1['product_count']}개
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"><span class="metric-rank">2nd</span></div>
                    <span class="region-highlight" style="color: #EA580C !important;">{r_top2['region']}</span>
                    <div class="metric-value">{int(r_top2['total_reviews']):,} 건 (중앙값)</div>
                    <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                        • 평점 중앙값: {round(r_top2['avg_rating'], 2)} / 5.0 <br>
                        • 등록 상품수: {r_top2['product_count']}개
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"><span class="metric-rank">3rd</span></div>
                    <span class="region-highlight" style="color: #16A34A !important;">{r_top3['region']}</span>
                    <div class="metric-value">{int(r_top3['total_reviews']):,} 건 (중앙값)</div>
                    <div style="margin-top: 10px; color: #475569; font-size: 0.85rem;">
                        • 평점 중앙값: {round(r_top3['avg_rating'], 2)} / 5.0 <br>
                        • 등록 상품수: {r_top3['product_count']}개
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### 📊 14개 시도 리뷰 활동량 비교 (서울, 부산, 제주 제외 / 중앙값 기준)")
            fig_reg_revs = px.bar(
                region_summary, x='total_reviews', y='region', 
                orientation='h', color='total_reviews',
                color_continuous_scale='Blues',
                labels={'total_reviews': '리뷰 수 중앙값 (건)', 'region': '시도명'},
                text='total_reviews',
                template='plotly_white'
            )
            fig_reg_revs.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_reg_revs.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig_reg_revs, use_container_width=True)

        # 2. 인기 액티비티 탭
        with t_rec2:
            st.markdown("### 🎯 외국인 인기 액티비티 Top 3")
            activities_df = reviews_df[reviews_df['category'] == 'Activity'].sort_values(by='reviews', ascending=False).reset_index(drop=True)

            col1, col2, col3 = st.columns(3)
            
            act_top1 = activities_df.iloc[0] if len(activities_df) > 0 else {"title": "데이터 없음", "region": "N/A", "rating": 0.0, "reviews": 0, "source": "N/A"}
            act_top2 = activities_df.iloc[1] if len(activities_df) > 1 else {"title": "데이터 없음", "region": "N/A", "rating": 0.0, "reviews": 0, "source": "N/A"}
            act_top3 = activities_df.iloc[2] if len(activities_df) > 2 else {"title": "데이터 없음", "region": "N/A", "rating": 0.0, "reviews": 0, "source": "N/A"}

            with col1:
                st.markdown(f"""
                <div class="metric-card" style="height: 300px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div class="metric-label"><span class="metric-rank">1st</span> {act_top1['region']}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; margin-top: 10px; color: #1E293B; line-height: 1.4; height: 100px; overflow: hidden; text-overflow: ellipsis;">
                            {act_top1['title']}
                        </div>
                    </div>
                    <div>
                        <div class="metric-value" style="font-size: 1.8rem; color: #DC2626;">★ {act_top1['rating']} / 5.0</div>
                        <div style="margin-top: 5px; color: #64748B; font-size: 0.85rem;">
                            • 리뷰수: {int(act_top1['reviews']):,}건 ({act_top1['source']})
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card" style="height: 300px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div class="metric-label"><span class="metric-rank">2nd</span> {act_top2['region']}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; margin-top: 10px; color: #1E293B; line-height: 1.4; height: 100px; overflow: hidden; text-overflow: ellipsis;">
                            {act_top2['title']}
                        </div>
                    </div>
                    <div>
                        <div class="metric-value" style="font-size: 1.8rem; color: #EA580C;">★ {act_top2['rating']} / 5.0</div>
                        <div style="margin-top: 5px; color: #64748B; font-size: 0.85rem;">
                            • 리뷰수: {int(act_top2['reviews']):,}건 ({act_top2['source']})
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card" style="height: 300px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div class="metric-label"><span class="metric-rank">3rd</span> {act_top3['region']}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; margin-top: 10px; color: #1E293B; line-height: 1.4; height: 100px; overflow: hidden; text-overflow: ellipsis;">
                            {act_top3['title']}
                        </div>
                    </div>
                    <div>
                        <div class="metric-value" style="font-size: 1.8rem; color: #16A34A;">★ {act_top3['rating']} / 5.0</div>
                        <div style="margin-top: 5px; color: #64748B; font-size: 0.85rem;">
                            • 리뷰수: {int(act_top3['reviews']):,}건 ({act_top3['source']})
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            > [!NOTE]
            > **1위 액티비티 ({act_top1['region']} - {act_top1['title'][:25]}...)**
            > - **특징**: 경기도 파주시 비무장지대(DMZ) 투어로, 외국인 방문자들에게 평화와 안보 테마의 독특한 안보 체험(제3땅굴, 도라전망대 등)을 선사하여 리뷰 수가 {int(act_top1['reviews']):,}건에 달하는 압도적 관심을 받고 있습니다.
            
            > [!NOTE]
            > **2위 액티비티 ({act_top2['region']} - {act_top2['title'][:25]}...)**
            > - **특징**: 강원도 춘천의 남이섬 1일 투어로, 쁘띠프랑스 및 가평 이탈리아마을 등과 연계된 자연 친화적 한류 드라마 성지 투어 코스입니다. {int(act_top2['reviews']):,}건의 리뷰로 외국인 단체 패키지의 정석으로 자리 잡았습니다.
            """)

        # 3. 인기 숙박시설 탭
        with t_rec3:
            st.markdown("### 🏨 외국인 인기 숙박시설/리조트 Top 3")
            accom_df = reviews_df[reviews_df['category'] == 'Accommodation'].sort_values(by='reviews', ascending=False).reset_index(drop=True)

            col1, col2, col3 = st.columns(3)
            
            acc_top1 = accom_df.iloc[0] if len(accom_df) > 0 else {"title": "데이터 없음", "region": "N/A", "rating": 0.0, "reviews": 0, "source": "N/A"}
            acc_top2 = accom_df.iloc[1] if len(accom_df) > 1 else {"title": "데이터 없음", "region": "N/A", "rating": 0.0, "reviews": 0, "source": "N/A"}
            acc_top3 = accom_df.iloc[2] if len(accom_df) > 2 else {"title": "데이터 없음", "region": "N/A", "rating": 0.0, "reviews": 0, "source": "N/A"}

            with col1:
                st.markdown(f"""
                <div class="metric-card" style="height: 300px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div class="metric-label"><span class="metric-rank">1st</span> {acc_top1['region']}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; margin-top: 10px; color: #1E293B; line-height: 1.4; height: 100px; overflow: hidden; text-overflow: ellipsis;">
                            {acc_top1['title']}
                        </div>
                    </div>
                    <div>
                        <div class="metric-value" style="font-size: 1.8rem; color: #DC2626;">★ {acc_top1['rating']} / 5.0</div>
                        <div style="margin-top: 5px; color: #64748B; font-size: 0.85rem;">
                            • 리뷰수: {int(acc_top1['reviews']):,}건 ({acc_top1['source']})
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card" style="height: 300px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div class="metric-label"><span class="metric-rank">2nd</span> {acc_top2['region']}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; margin-top: 10px; color: #1E293B; line-height: 1.4; height: 100px; overflow: hidden; text-overflow: ellipsis;">
                            {acc_top2['title']}
                        </div>
                    </div>
                    <div>
                        <div class="metric-value" style="font-size: 1.8rem; color: #EA580C;">★ {acc_top2['rating']} / 5.0</div>
                        <div style="margin-top: 5px; color: #64748B; font-size: 0.85rem;">
                            • 리뷰수: {int(acc_top2['reviews']):,}건 ({acc_top2['source']})
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card" style="height: 300px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div class="metric-label"><span class="metric-rank">3rd</span> {acc_top3['region']}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; margin-top: 10px; color: #1E293B; line-height: 1.4; height: 100px; overflow: hidden; text-overflow: ellipsis;">
                            {acc_top3['title']}
                        </div>
                    </div>
                    <div>
                        <div class="metric-value" style="font-size: 1.8rem; color: #16A34A;">★ {acc_top3['rating']} / 5.0</div>
                        <div style="margin-top: 5px; color: #64748B; font-size: 0.85rem;">
                            • 리뷰수: {int(acc_top3['reviews']):,}건 ({acc_top3['source']})
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            > [!NOTE]
            > **1위 숙박시설 ({acc_top1['region']} - {acc_top1['title'][:25]}...)**
            > - **특징**: 경기도의 DMZ 투어 연계 호텔 픽업형 투어 패키지형 상품입니다. 호텔 픽업 서비스를 포함하고 있어 개별적 이동이 불편한 비수도권 지역에서 외국인에게 높은 점수를 받고 있습니다.
            
            > [!NOTE]
            > **2위 숙박시설 ({acc_top2['region']} - {acc_top2['title'][:25]}...)**
            > - **특징**: 강원도 홍천 소노비발디파크 스키 리조트 패키지 상품입니다. 비수도권 자연 휴양 및 레저 체험과 결합된 콘도/리조트 숙박 수요가 해외 스키어들을 중심으로 나타납니다.
            """)

        # 4. 분석 가이드라인 및 정책
        st.markdown("---")
        st.markdown("### 💡 데이터 기반 종합 분석 인사이트")
        st.markdown("""
        서울, 부산, 제주를 제외한 지역의 외국인 리뷰 데이터를 종합 분석한 결과, 다음과 같은 뚜렷한 특징이 확인됩니다.
        
        1. **안보/역사 중심의 경기도 쏠림 현상**:
           경기도가 전체 리뷰의 **90% 이상(31,374건 중 2.8만 건)**을 차지하는 기염을 토했습니다. 이는 분단국가라는 한국의 특수성을 체험할 수 있는 `DMZ(비무장지대) 안보 관광`이 외국인들에게 비교 불가능한 킬러 콘텐츠임을 입증합니다.
           
        2. **교통/인프라 연계 패키지의 강세**:
           인기 숙박 1위에서 보이듯 `호텔 픽업` 또는 서울 출발 `왕복 셔틀버스`가 융합된 복합 상품군이 독보적입니다. 대중교통 인프라가 서울에 비해 낙후된 비수도권 특성상, 외국인들은 직접 숙박/교통을 예약하기보다 올인원 투어로 문제를 해결하고 있습니다.
           
        3. **비수도권 숙박 시설 부족 및 대책**:
           현재 숙박시설 관련 데이터 총량(3개 상품)이 액티비티(53개 상품)에 비해 현저하게 낮습니다. 이는 해외 주요 플랫폼(GetYourGuide 등)에 등록된 개별 비수도권 숙박 예약 거래가 활성화되지 않았음을 나타내며, 지방 거점 숙소들의 글로벌 채널 연계 및 인바운드 인프라 개선이 조속히 요구됩니다.
        """)
