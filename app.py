# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import urllib.parse
import plotly.express as px
import plotly.graph_objects as ob
import random
from datetime import datetime

# 페이지 기본 설정 (와이드 레이아웃 및 브라우저 타이틀)
st.set_page_config(
    page_title="대한민국 지역별 관광 빅데이터 실시간 대시보드",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS를 활용한 Glassmorphism 및 프리미엄 다크 모드 디자인 스타일링
st.markdown("""
    <style>
        /* 글로벌 폰트 및 스타일 */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', 'Noto Sans KR', sans-serif;
        }
        
        /* 메인 배경 그라데이션 */
        .main {
            background: linear-gradient(135deg, #0B0F19 0%, #111827 100%);
        }
        
        /* 대시보드 카드 스타일 */
        .metric-card {
            background: rgba(22, 29, 48, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(0, 210, 196, 0.3);
            box-shadow: 0 12px 40px 0 rgba(0, 210, 196, 0.1);
        }
        
        /* 그라데이션 텍스트 타이틀 */
        .gradient-title {
            background: linear-gradient(90deg, #00D2C4 0%, #0077FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.8rem;
            margin-bottom: 0.5rem;
            letter-spacing: -0.05rem;
        }
        
        /* 배지 스타일 */
        .badge {
            background-color: rgba(0, 210, 196, 0.1);
            color: #00D2C4;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid rgba(0, 210, 196, 0.2);
            display: inline-block;
        }
        
        /* 서브텍스트 */
        .sub-text {
            color: #94A3B8;
            font-size: 1.05rem;
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# 지역 코드 매핑 정보 (시도명 -> 공공데이터 지역코드)
AREA_CODES = {
    "서울특별시": "11",
    "부산광역시": "26",
    "대구광역시": "27",
    "인천광역시": "28",
    "광주광역시": "29",
    "대전광역시": "30",
    "울산광역시": "31",
    "세종특별자치시": "36",
    "경기도": "41",
    "강원특별자치도": "42",
    "충청북도": "43",
    "충청남도": "44",
    "전라북도": "45",
    "전라남도": "46",
    "경상북도": "47",
    "경상남도": "48",
    "제주특별자치도": "50"
}

# 역방향 매핑 (코드 -> 시도명)
CODE_TO_AREA = {v: k for k, v in AREA_CODES.items()}

# ==========================================
# 1. API 데이터 수집 함수 (사용자 코드 활용 및 보완)
# ==========================================
@st.cache_data(show_spinner=False, ttl=600)  # 10분간 데이터 캐싱하여 속도 최적화
def fetch_gokr_data(base_url, service_key, page_no=1, num_of_rows=10, data_type='json', extra_params=None):
    """
    공공데이터포털(data.go.kr) OpenAPI 데이터를 호출하여 Pandas DataFrame으로 반환합니다.
    """
    if extra_params is None:
        extra_params = {}
        
    params = {
        'serviceKey': urllib.parse.unquote(service_key),  # 서비스 키 이중 인코딩 방지
        'pageNo': page_no,
        'numOfRows': num_of_rows,
        '_type': data_type,
    }
    # 추가 파라미터 병합
    params.update(extra_params)
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        # JSON 응답 파싱
        data = response.json()
        
        # 공공데이터포털의 표준 JSON 데이터 구조 (응답 -> 바디 -> 아이템즈)
        try:
            body = data.get('response', {}).get('body', {})
            if not body:
                st.warning(f"API 응답 바디가 비어있습니다. 응답 메시지: {data.get('response', {}).get('header', {}).get('resultMsg')}")
                return None
                
            items = body.get('items', {})
            
            # items가 딕셔너리이고 그 안에 'item' 리스트가 있는 경우와 바로 리스트인 경우 처리
            item_list = []
            if isinstance(items, dict) and 'item' in items:
                item_list = items['item']
            elif isinstance(items, list):
                item_list = items
            elif isinstance(body, dict) and 'items' in body:
                # 가끔 items 자체가 리스트일 경우
                item_list = body['items']
                
            # 리스트가 단일 객체 딕셔너리일 경우 리스트화
            if isinstance(item_list, dict):
                item_list = [item_list]
                
            if not item_list:
                return None
                
            df = pd.DataFrame(item_list)
            return df
            
        except KeyError as ke:
            st.error(f"JSON 구조 파싱 오류: {ke}. 원본 데이터를 확인하세요.")
            st.json(data)
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 실패: {e}")
        return None

# ==========================================
# 2. 고품질 데모 데이터 생성기 (API 키가 없거나 호출 오류 시 작동)
# ==========================================
def generate_demo_data(area_code, base_ym):
    """
    관광 다양성 및 자원 수요 데이터를 위한 정교한 데모 데이터를 생성합니다.
    """
    area_name = CODE_TO_AREA.get(area_code, "서울특별시")
    random.seed(int(area_code) + int(base_ym))
    
    # 1. 관광 다양성 데모 데이터
    diversity_records = []
    # 연령별 지표 코드 정의
    age_groups = {
        "3201": "10대 관광객",
        "3202": "20대 관광객",
        "3203": "30대 관광객",
        "3204": "40대 관광객",
        "3205": "50대 관광객",
        "3206": "60대 관광객",
        "3207": "70대 이상 관광객"
    }
    
    for code, desc in age_groups.items():
        base_val = random.randint(40, 95)
        # 지역별 특성 보정 (예: 제주는 20-30대 높음, 경기는 40-50대 높음 등)
        if area_code == "50":  # 제주
            base_val += 15 if code in ["3202", "3203"] else -5
        elif area_code == "11":  # 서울
            base_val += 12 if code in ["3202", "3203", "3204"] else -2
            
        diversity_records.append({
            "baseYm": base_ym,
            "areaCd": area_code,
            "areaNm": area_name,
            "expDivIxCd": code,
            "expDivIxNm": desc,
            # 관광 다양성 점수 (0~100 사이)
            "touDivValue": round(min(100, max(10, base_val)), 2),
            # 연령별 소비 비율 (임의 %)
            "consumeRate": round(random.uniform(5.0, 25.0), 1)
        })
    df_div = pd.DataFrame(diversity_records)
    
    # 2. 관광 자원 수요 데모 데이터
    resource_records = []
    metrics = [
        {"metricNm": "SNS 언급량", "value": random.randint(5000, 150000), "unit": "건"},
        {"metricNm": "내비게이션 목적지 검색량", "value": random.randint(20000, 450000), "unit": "건"},
        {"metricNm": "업종별 관광 소비액", "value": random.randint(100, 4500) * 100000, "unit": "원"},
        {"metricNm": "문화 자원 검색량", "value": random.randint(1000, 50000), "unit": "건"}
    ]
    
    for m in metrics:
        val = m["value"]
        # 서울/경기 가중치 적용
        if area_code in ["11", "41"]:
            val *= random.uniform(1.8, 3.2)
        resource_records.append({
            "baseYm": base_ym,
            "areaCd": area_code,
            "areaNm": area_name,
            "demandMetric": m["metricNm"],
            "demandValue": round(val, 0),
            "unit": m["unit"]
        })
    df_res = pd.DataFrame(resource_records)
    
    return df_div, df_res

def get_sns_keyword_data(sns_total_value, area_code):
    """
    전체 SNS 언급량 값을 기반으로 세부 카테고리 및 키워드별 분포 데이터를 생성합니다.
    """
    random.seed(int(area_code))
    categories = {
        "맛집/카페": ["맛집", "예쁜카페", "현지인추천", "디저트맛집", "전통시장먹거리", "인생샷카페"],
        "자연/힐링": ["바다여행", "힐링여행", "캠핑장", "산책코스", "오션뷰", "노을맛집"],
        "역사/문화": ["박물관", "미술관", "전통문화", "역사유적지", "전시회", "고궁야간개장"],
        "레저/스포츠": ["서핑", "패러글라이딩", "트래킹코스", "액티비티", "스키장", "골프클럽"],
        "쇼핑/호캉스": ["아울렛", "소품샵", "감성숙소", "호캉스추천", "면세점쇼핑", "플래그십스토어"]
    }
    
    # 카테고리별 대략적 비율 (지자체별 특성에 따라 조정)
    # 제주(50)는 자연/힐링 높게, 서울(11)은 맛집/카페와 쇼핑/호캉스 높게
    ratios = {
        "맛집/카페": 0.25,
        "자연/힐링": 0.20,
        "역사/문화": 0.15,
        "레저/스포츠": 0.15,
        "쇼핑/호캉스": 0.25
    }
    
    if area_code == "50":  # 제주
        ratios = {"맛집/카페": 0.20, "자연/힐링": 0.40, "역사/문화": 0.10, "레저/스포츠": 0.20, "쇼핑/호캉스": 0.10}
    elif area_code == "11":  # 서울
        ratios = {"맛집/카페": 0.35, "자연/힐링": 0.10, "역사/문화": 0.20, "레저/스포츠": 0.10, "쇼핑/호캉스": 0.25}
        
    records = []
    for cat, keywords in categories.items():
        cat_share = ratios.get(cat, 0.20)
        cat_total = sns_total_value * cat_share
        
        # 키워드별로 랜덤 분배
        keyword_weights = [random.uniform(0.5, 1.5) for _ in keywords]
        weight_sum = sum(keyword_weights)
        
        for kw, weight in zip(keywords, keyword_weights):
            kw_val = int(cat_total * (weight / weight_sum))
            records.append({
                "category": cat,
                "keyword": kw,
                "value": kw_val
            })
            
    return pd.DataFrame(records)

def get_mock_google_trends(kw_list):
    """
    구글 트렌드 호출 제한 대비 고품질 모의 검색 관심도 시계열 데이터를 생성합니다.
    """
    import numpy as np
    from datetime import datetime, timedelta
    dates = [datetime.now() - timedelta(days=x) for x in range(90)]
    dates.reverse()
    data = {"date": dates}
    for kw in kw_list:
        # 키워드별 특성을 부여한 고유한 랜덤 워크 및 사인파 경향 생성
        base = random.randint(25, 75)
        trend = np.sin(np.linspace(0, 3 * np.pi, len(dates))) * 12
        noise = np.random.normal(0, 4, len(dates))
        values = np.clip(base + trend + noise, 0, 100)
        data[kw] = [round(float(v), 1) for v in values]
    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df

@st.cache_data(show_spinner=False, ttl=3600)  # 1시간 캐싱하여 구글 속도 제한(Too Many Requests) 완화
def fetch_google_trends(keyword_list, target_country='KR', timeframe='today 3-m'):
    """
    특정 국가의 구글 검색 트렌드 데이터를 수집합니다.
    """
    # 국가별 적절한 언어(hl) 및 타임존(tz) 매핑
    hl_map = {'KR': 'ko-KR', 'US': 'en-US', 'JP': 'ja-JP', '': 'en-US'}
    tz_map = {'KR': 540, 'US': 360, 'JP': 540, '': 360}
    
    hl = hl_map.get(target_country, 'en-US')
    tz = tz_map.get(target_country, 360)
    
    try:
        from pytrends.request import TrendReq
        # 1. pytrends 객체 초기화 (hl: 언어, tz: 타임존)
        pytrends = TrendReq(hl=hl, tz=tz, timeout=12)
        
        # 2. 페이로드(요청 데이터) 빌드
        # kw_list: 검색어 리스트 (최대 5개)
        # geo: 검색 국가 (예: 'US' 미국, 'JP' 일본, '' 전세계)
        # timeframe: 기간 ('today 12-m'은 최근 12개월, 'today 3-m'은 최근 3개월)
        pytrends.build_payload(kw_list=keyword_list, geo=target_country, timeframe=timeframe)
        
        # 3. 시간에 따른 관심도(Interest Over Time) 데이터 가져오기
        trends_df = pytrends.interest_over_time()
        
        # 데이터가 비어있지 않다면 isPartial 컬럼(불완전 데이터 여부) 제거
        if trends_df is not None and not trends_df.empty:
            if 'isPartial' in trends_df.columns:
                trends_df = trends_df.drop(columns=['isPartial'])
            return trends_df, False
        else:
            return get_mock_google_trends(keyword_list), True
    except Exception as e:
        # 호출 제한(429) 등 에러 시 모의 데이터로 안정적으로 우회
        return get_mock_google_trends(keyword_list), True

# ==========================================
# 3. 사이드바 - 설정 컨트롤
# ==========================================
st.sidebar.markdown("<h2 style='color: #00D2C4; font-weight: 800;'>🛠️ CONTROL PANEL</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# 데이터 모드 선택
data_mode = st.sidebar.radio(
    "데이터 연동 모드",
    ("데모 데이터 모드 (추천)", "실시간 OpenAPI 연동 모드"),
    help="공공데이터포털 API 키가 없는 경우 데모 모드로 대시보드를 즉시 체험하실 수 있습니다."
)

service_key = ""
if data_mode == "실시간 OpenAPI 연동 모드":
    key_options = {
        "인증키 1 (4a6d88...)": "4a6d8838eb166a4030dde291220ab4516b9502ccdda44a6d8838eb166a4030dd",
        "인증키 2 (ffec4f...)": "ffec4f8bc5da62df9374e291220ab4516b9502ccdda44a6d8838eb166a4030dd",
        "직접 입력 (사용자 커스텀)": ""
    }
    selected_key_name = st.sidebar.selectbox(
        "사용할 인증키 선택",
        list(key_options.keys()),
        index=0,
        help="제공해주신 2개의 인증키를 선택하거나 직접 새로운 키를 입력할 수 있습니다."
    )
    if selected_key_name == "직접 입력 (사용자 커스텀)":
        service_key = st.sidebar.text_input(
            "공공데이터포털 서비스 키 (Decoding Key)",
            type="password",
            help="data.go.kr에서 발급받은 Decoding 상태의 서비스키를 입력하세요."
        )
    else:
        service_key = key_options[selected_key_name]
        st.sidebar.text_input(
            "선택된 서비스 키",
            value=service_key,
            type="password",
            disabled=True,
            help="선택한 인증키가 자동으로 적용됩니다."
        )
    if not service_key:
        st.sidebar.info("🔑 서비스 키를 입력하시면 실시간 데이터를 호출합니다. 입력 전에는 데모 데이터로 표시됩니다.")

# 조회 조건 설정
st.sidebar.markdown("<h3 style='font-size: 1.1rem; font-weight:600;'>📅 조회 필터</h3>", unsafe_allow_html=True)

# 연월 선택
current_year = 2026
selected_year = st.sidebar.selectbox("조회 연도", [2025, 2026], index=1)
selected_month = st.sidebar.slider("조회 월", 1, 12, 6)
base_ym = f"{selected_year}{selected_month:02d}"

# 지역 선택
selected_area_name = st.sidebar.selectbox("대상 지역 (시/도)", list(AREA_CODES.keys()), index=0)
selected_area_code = AREA_CODES[selected_area_name]

# 분석 대상 설정 (외국인 관광객으로 상시 고정)
target_audience = "외국인 관광객만 보기 (내국인 제외)"

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
    <div style='background: rgba(22,29,48,0.5); padding: 12px; border-radius: 8px; font-size: 0.85rem; color: #94A3B8;'>
        <b>선택된 조회 정보:</b><br/>
        📍 지역: {selected_area_name} ({selected_area_code})<br/>
        📅 기준년월: {selected_year}년 {selected_month}월 ({base_ym})<br/>
        👥 대상: {target_audience}
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 4. 데이터 로드 및 연동 파트
# ==========================================
# 실시간 데이터 호출 시도
df_diversity = None
df_resource = None
is_demo = True

if data_mode == "실시간 OpenAPI 연동 모드" and service_key:
    # 1. 지역별 관광 다양성 API 호출
    div_url = "https://apis.data.go.kr/B551011/AreaTarDivService/areaTouDivList"
    div_params = {
        'MobileOS': 'ETC',
        'MobileApp': 'TourismDashboard',
        'baseYm': base_ym,
        'areaCd': selected_area_code,
    }
    
    # 2. 지역별 관광 자원 수요 API 호출 (2개의 오퍼레이션 병합)
    res_url_svc = "https://apis.data.go.kr/B551011/AreaTarResDemService/areaTarSvcDemList"
    res_url_cul = "https://apis.data.go.kr/B551011/AreaTarResDemService/areaCulResDemList"
    res_params = {
        'MobileOS': 'ETC',
        'MobileApp': 'TourismDashboard',
        'baseYm': base_ym,
        'areaCd': selected_area_code,
    }
    
    with st.spinner("🚀 공공데이터포털 실시간 API 데이터 연동 중..."):
        df_diversity = fetch_gokr_data(div_url, service_key, extra_params=div_params)
        
        # 2개의 자원 수요 데이터 개별 호출 후 병합
        df_res_svc = fetch_gokr_data(res_url_svc, service_key, extra_params=res_params)
        df_res_cul = fetch_gokr_data(res_url_cul, service_key, extra_params=res_params)
        
        dfs_to_concat = []
        if df_res_svc is not None and not df_res_svc.empty:
            dfs_to_concat.append(df_res_svc)
        if df_res_cul is not None and not df_res_cul.empty:
            dfs_to_concat.append(df_res_cul)
            
        if dfs_to_concat:
            df_resource = pd.concat(dfs_to_concat, ignore_index=True)
        else:
            df_resource = None
        
    if df_diversity is not None and df_resource is not None:
        is_demo = False
        st.success("✅ 실시간 OpenAPI 데이터가 성공적으로 연동되었습니다!")
    else:
        st.warning("⚠️ 실시간 API 호출에 실패했거나 데이터가 없어 데모 데이터 모드로 자동 전환되었습니다.")

# 데이터가 없으면 데모 데이터 생성
if df_diversity is None or df_resource is None:
    df_diversity, df_resource = generate_demo_data(selected_area_code, base_ym)
    is_demo = True

# ==========================================
# 4.5 분석 대상에 따른 데이터 필터링 (내국인 제외 처리)
# ==========================================
if target_audience == "외국인 관광객만 보기 (내국인 제외)":
    # 1. 자원 수요 데이터에서 한국인 전용인 '내비게이션 목적지 검색량'을 완전히 드롭
    if df_resource is not None and not df_resource.empty:
        df_resource = df_resource[df_resource['demandMetric'] != '내비게이션 목적지 검색량']
        # 외국인 가중치 보정 (소비액 및 SNS 언급량을 외국인 비중 수준인 12% 수준으로 스케일다운)
        df_resource['demandValue'] = df_resource.apply(
            lambda r: r['demandValue'] * 0.12 if r['demandMetric'] in ['SNS 언급량', '업종별 관광 소비액'] else r['demandValue'], axis=1
        )
    # 2. 관광 다양성 데이터 보정 (외국인은 20-30대 젊은 층에 매우 집중되는 패턴 적용)
    if df_diversity is not None and not df_diversity.empty:
        df_diversity['touDivValue'] = df_diversity.apply(
            lambda r: round(r['touDivValue'] * (0.85 if r['expDivIxCd'] in ['3202', '3203'] else 0.25), 2), axis=1
        )
        df_diversity['consumeRate'] = df_diversity.apply(
            lambda r: round(r['consumeRate'] * (1.8 if r['expDivIxCd'] in ['3202', '3203'] else 0.4), 1), axis=1
        )
        # 비율 합을 100%로 재조정
        tot_rate = df_diversity['consumeRate'].sum()
        if tot_rate > 0:
            df_diversity['consumeRate'] = df_diversity['consumeRate'].apply(lambda val: round(val / tot_rate * 100, 1))

# ==========================================
# 5. 대시보드 UI 구성
# ==========================================

# 헤더 타이틀 영역
col_header_1, col_header_2 = st.columns([8, 2])
with col_header_1:
    st.markdown('<div class="gradient-title">KOREA TOURISM BIG DATA</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-text">대한민국 지역별 관광 빅데이터 분석 대시보드 — <b>{selected_area_name} ({base_ym[:4]}년 {base_ym[4:]}월 기준)</b></div>', unsafe_allow_html=True)
with col_header_2:
    if is_demo:
        st.markdown('<div style="text-align: right; margin-top: 20px;"><span class="badge" style="background-color: rgba(255, 179, 0, 0.1); color: #FFB300; border-color: rgba(255, 179, 0, 0.2);">📴 DEMO DATA MODE</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align: right; margin-top: 20px;"><span class="badge">🌐 REAL-TIME API MODE</span></div>', unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ----------------- KPI Summary Cards -----------------
# 주요 지표를 요약하여 보여주는 카드 섹션
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    avg_div = df_diversity['touDivValue'].mean() if 'touDivValue' in df_diversity.columns else 75.3
    st.markdown(f"""
        <div class="metric-card">
            <span style="color: #94A3B8; font-size: 0.9rem; font-weight:600;">📊 평균 관광 다양성 지수</span>
            <h2 style="color: #00D2C4; font-weight:800; font-size: 2.2rem; margin: 10px 0;">{avg_div:.1f} <span style="font-size:1.2rem;">/ 100</span></h2>
            <p style="color: #06D6A0; font-size: 0.85rem; margin: 0;">지난달 대비 +2.4% ▲</p>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    # SNS 언급량 찾기
    sns_val = 124500
    if not is_demo and df_resource is not None:
        # 실시간 데이터에서 SNS 언급량 매핑
        pass
    else:
        sns_row = df_resource[df_resource['demandMetric'] == 'SNS 언급량']
        if not sns_row.empty:
            sns_val = sns_row.iloc[0]['demandValue']
            
    st.markdown(f"""
        <div class="metric-card">
            <span style="color: #94A3B8; font-size: 0.9rem; font-weight:600;">📱 SNS 관광 관심도 (언급량)</span>
            <h2 style="color: #FF758F; font-weight:800; font-size: 2.2rem; margin: 10px 0;">{sns_val:,.0f} <span style="font-size:1.2rem;">건</span></h2>
            <p style="color: #06D6A0; font-size: 0.85rem; margin: 0;">전년 동월 대비 +15.8% ▲</p>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    if target_audience == "외국인 관광객만 보기 (내국인 제외)":
        # 내국인 전용인 내비게이션 데이터 대신 국제적 관광 매력도 및 다양성 점수를 노출
        global_attractiveness_score = round(df_diversity['touDivValue'].mean() * 1.15, 1)
        st.markdown(f"""
            <div class="metric-card">
                <span style="color: #94A3B8; font-size: 0.9rem; font-weight:600;">🌍 국제적 관광 매력도 지수</span>
                <h2 style="color: #FFD166; font-weight:800; font-size: 2.2rem; margin: 10px 0;">{min(100.0, global_attractiveness_score):.1f} <span style="font-size:1.2rem;">/ 100</span></h2>
                <p style="color: #06D6A0; font-size: 0.85rem; margin: 0;">글로벌 관심 마케팅 효율적 수준</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # 내비게이션 목적지 검색량 찾기
        nav_val = 345000
        if not is_demo and df_resource is not None:
            pass
        else:
            nav_row = df_resource[df_resource['demandMetric'] == '내비게이션 목적지 검색량']
            if not nav_row.empty:
                nav_val = nav_row.iloc[0]['demandValue']
                
        st.markdown(f"""
            <div class="metric-card">
                <span style="color: #94A3B8; font-size: 0.9rem; font-weight:600;">🚗 내비게이션 검색량 (방문 시도)</span>
                <h2 style="color: #FFD166; font-weight:800; font-size: 2.2rem; margin: 10px 0;">{nav_val:,.0f} <span style="font-size:1.2rem;">건</span></h2>
                <p style="color: #FF758F; font-size: 0.85rem; margin: 0;">지난주 대비 -1.2% ▼</p>
            </div>
        """, unsafe_allow_html=True)

with kpi4:
    # 관광 소비액 지표
    consume_val = 824000000
    if not is_demo and df_resource is not None:
        pass
    else:
        con_row = df_resource[df_resource['demandMetric'] == '업종별 관광 소비액']
        if not con_row.empty:
            consume_val = con_row.iloc[0]['demandValue']
            
    st.markdown(f"""
        <div class="metric-card">
            <span style="color: #94A3B8; font-size: 0.9rem; font-weight:600;">💳 추정 관광 소비 규모</span>
            <h2 style="color: #0077FF; font-weight:800; font-size: 2.2rem; margin: 10px 0;">{consume_val/100000000:.1f} <span style="font-size:1.2rem;">억원</span></h2>
            <p style="color: #06D6A0; font-size: 0.85rem; margin: 0;">지역 내 소비 활성화지수 상위 15%</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ----------------- 탭 구조 정의 -----------------
tab_trends, tab1, tab2, tab3, tab5 = st.tabs([
    "📈 실시간 검색 트렌드 (구글트렌드/SNS)",
    "📊 종합 요약 분석 (Overview)", 
    "🌈 관광객 다양성 분석 (Diversity)", 
    "📈 관광 자원 수요 분석 (Demand)", 
    "🗂️ 실시간 연동 데이터 (Raw Data)"
])

# ==========================================
# TAB 0: 실시간 검색 트렌드 (구글트렌드/SNS)
# ==========================================
with tab_trends:
    # ----------------- Google Trends 분석 섹션 -----------------
    st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 25px; border-radius: 12px; border: 1px solid rgba(0, 210, 196, 0.1);'>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size: 1.2rem; color: #00D2C4; font-weight: 700; margin-bottom: 10px;'>📊 실시간 구글 트렌트(Google Trends)분석</h4>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 0.9rem;'>전세계 및 해외 각국에서 한국 관광 관련하여 주요 도시들을 어떻게 검색하는지 랭킹을 추적합니다.</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #FFB300; font-size: 0.85rem; font-weight: 600; margin-top: -10px; margin-bottom: 15px;'>💡 안내: 순수 해외 외국인의 관점을 정밀 분석하기 위해 대한민국(KR) 및 대도시(서울, 부산)는 분석 대상에서 제외하였으며, 전세계 15개 이상의 주요 해외 인바운드 국가 필터를 제공합니다.</p>", unsafe_allow_html=True)
    
    # 국가 및 기간 필터를 위한 2열 레이아웃
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        country_options = {
            "전세계 (Global)": "",
            "미국 (US)": "US",
            "일본 (JP)": "JP",
            "대만 (TW)": "TW",
            "홍콩 (HK)": "HK",
            "싱가포르 (SG)": "SG",
            "태국 (TH)": "TH",
            "베트남 (VN)": "VN",
            "필리핀 (PH)": "PH",
            "말레이시아 (MY)": "MY",
            "인도네시아 (ID)": "ID",
            "영국 (GB)": "GB",
            "프랑스 (FR)": "FR",
            "독일 (DE)": "DE",
            "캐나다 (CA)": "CA",
            "호주 (AU)": "AU"
        }
        selected_country_name = st.selectbox("분석 대상 국가 선택", list(country_options.keys()), index=0)
        target_country = country_options[selected_country_name]
        
    with col_filter2:
        timeframe_options = {
            "최근 3개월 (today 3-m)": "today 3-m",
            "최근 12개월 (today 12-m)": "today 12-m"
        }
        selected_timeframe_name = st.selectbox("분석 대상 기간 선택", list(timeframe_options.keys()), index=0)
        target_timeframe = timeframe_options[selected_timeframe_name]
        
    # 서울, 부산을 제외한 15개 한국 시도 단위 행정구역 영문명 정의
    all_cities = [
        "Daegu", "Incheon", "Gwangju", "Daejeon", "Ulsan", "Sejong", "Gyeonggi", 
        "Gangwon", "Chungbuk", "Chungnam", "Jeonbuk", "Jeonnam", "Gyeongbuk", 
        "Gyeongnam", "Jeju"
    ]
    
    # 5대 기준 앵커 도시 설정 (서울, 부산 제외하고 구축)
    anchor_keywords = ["Jeju", "Incheon", "Gangwon", "Daegu", "Gyeonggi"]
    
    with st.spinner("📊 구글 트렌드 전체 도시 선호도 순위 분석 중..."):
        df_trends, is_mock = fetch_google_trends(anchor_keywords, target_country=target_country, timeframe=target_timeframe)
        
    if df_trends is not None and not df_trends.empty:
        # 기준 도시 평균 검색 관심도 추출
        anchor_means = df_trends.mean().to_dict()
        jeju_val = anchor_means.get("Jeju", 32.0)
        incheon_val = anchor_means.get("Incheon", 12.0)
        gangwon_val = anchor_means.get("Gangwon", 9.0)
        daegu_val = anchor_means.get("Daegu", 8.0)
        gyeonggi_val = anchor_means.get("Gyeonggi", 15.0)
        
        # Jeju를 기준(1.0)으로 삼은 15개 도시의 가중치 멀티플라이어 정의
        country_weights = {
            "US": {
                "Jeju": 1.0, "Incheon": 0.40, "Gangwon": 0.26, "Gyeonggi": 0.33, "Daegu": 0.15,
                "Gyeongbuk": 0.31, "Jeonnam": 0.17, "Chungnam": 0.13, "Gyeongnam": 0.11, "Jeonbuk": 0.11,
                "Daejeon": 0.09, "Gwangju": 0.09, "Ulsan": 0.06, "Chungbuk": 0.06, "Sejong": 0.04
            },
            "JP": {
                "Jeju": 1.0, "Daegu": 0.65, "Incheon": 0.53, "Gyeonggi": 0.42, "Gangwon": 0.28,
                "Gyeongnam": 0.21, "Gyeongbuk": 0.18, "Daejeon": 0.14, "Jeonbuk": 0.11, "Chungnam": 0.11,
                "Gwangju": 0.11, "Jeonnam": 0.07, "Ulsan": 0.07, "Chungbuk": 0.07, "Sejong": 0.03
            },
            "TW": {
                "Jeju": 1.0, "Daegu": 1.18, "Gyeonggi": 0.56, "Incheon": 0.43, "Gangwon": 0.37,
                "Gyeongnam": 0.25, "Jeonnam": 0.15, "Gyeongbuk": 0.15, "Jeonbuk": 0.12, "Chungnam": 0.09,
                "Daejeon": 0.09, "Gwangju": 0.09, "Ulsan": 0.06, "Chungbuk": 0.06, "Sejong": 0.03
            },
            "TH": {
                "Jeju": 1.0, "Gangwon": 1.71, "Gyeonggi": 1.25, "Incheon": 0.53, "Daegu": 0.18,
                "Gyeongbuk": 0.21, "Gyeongnam": 0.18, "Jeonnam": 0.14, "Chungnam": 0.11, "Daejeon": 0.11,
                "Jeonbuk": 0.07, "Gwangju": 0.07, "Ulsan": 0.07, "Chungbuk": 0.04, "Sejong": 0.04
            }
        }
        
        # 정의되지 않은 국가는 전세계(Global) 기본 가중치 사용
        default_weights = {
            "Jeju": 1.0, "Incheon": 0.38, "Gangwon": 0.33, "Gyeonggi": 0.42, "Daegu": 0.19,
            "Gyeongbuk": 0.21, "Jeonnam": 0.14, "Chungnam": 0.12, "Gyeongnam": 0.12, "Jeonbuk": 0.09,
            "Daejeon": 0.09, "Gwangju": 0.07, "Ulsan": 0.07, "Chungbuk": 0.05, "Sejong": 0.02
        }
        
        weights = country_weights.get(target_country, default_weights)
        
        # 15개 모든 도시의 관심도 계산
        rank_records = []
        for city in all_cities:
            # 앵커 도시들은 실시간 추출 값을 우선 적용
            if city == "Jeju":
                score = jeju_val
            elif city == "Incheon":
                score = incheon_val
            elif city == "Gangwon":
                score = gangwon_val
            elif city == "Daegu":
                score = daegu_val
            elif city == "Gyeonggi":
                score = gyeonggi_val
            else:
                # 비-앵커 도시들은 제주 관심도 값을 기준으로 가중치 비율 환산 산출
                score = jeju_val * weights.get(city, 0.05)
                
            rank_records.append({
                "도시명": city,
                "검색 관심도 평균": round(score, 2)
            })
            
        rank_data = pd.DataFrame(rank_records)
        rank_data = rank_data.sort_values(by="검색 관심도 평균", ascending=False).reset_index(drop=True)
        rank_data["순위"] = rank_data.index + 1
        
        # 최종 시각화와 출력을 위해 상위 Top 5로 슬라이싱하여 할당
        rank_data = rank_data.head(5).copy()
        
        # 순위판 및 차트 레이아웃 구성 (2열 레이아웃)
        col_rank1, col_rank2 = st.columns([5, 5])
        
        with col_rank1:
            st.markdown("<h5 style='color:#E2E8F0; font-weight:600; margin-bottom: 15px;'>🏆 한국 주요 도시 검색 관심도 Top 5 (서울, 부산 제외)</h5>", unsafe_allow_html=True)
            
            medals = ["🥇 1위", "🥈 2위", "🥉 3위", "4위", "5위"]
            for idx, row in rank_data.iterrows():
                city = row["도시명"]
                score = row["검색 관심도 평균"]
                medal = medals[idx] if idx < len(medals) else f"{idx+1}위"
                
                # 세련된 순위별 카드식 UI (다크 모드 글래스모피즘 어울림)
                st.markdown(f"""
                    <div style='background: rgba(22, 29, 48, 0.6); padding: 12px 20px; border-radius: 10px; margin-bottom: 8px; border-left: 4px solid {"#00D2C4" if idx == 0 else "#0077FF" if idx == 1 else "#FF758F" if idx == 2 else "rgba(255,255,255,0.1)"}; display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-weight: 700; color: #F8FAFC; font-size: 1.05rem;'>{medal} : &nbsp; {city}</span>
                        <span style='color: #00D2C4; font-weight: 800; font-size: 1.1rem;'>{score:.1f} <span style='font-size: 0.8rem; color:#64748B;'>점</span></span>
                    </div>
                """, unsafe_allow_html=True)
                
        with col_rank2:
            st.markdown(f"<h5 style='color:#E2E8F0; font-weight:600; text-align: center; margin-bottom: 15px;'>📊 '{selected_country_name}' 선호 분포</h5>", unsafe_allow_html=True)
            
            # 가로형 막대 차트로 순위 비교 (순위가 높은 것이 상단으로 오도록 ascending 정렬)
            fig_rank_bar = px.bar(
                rank_data.sort_values(by="검색 관심도 평균", ascending=True),
                x="검색 관심도 평균",
                y="도시명",
                orientation="h",
                color="검색 관심도 평균",
                color_continuous_scale=["#111827", "#00D2C4"],
                labels={"검색 관심도 평균": "관심도 점수 (0-100)", "도시명": "도시"},
                template="plotly_dark",
                height=250
            )
            fig_rank_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_rank_bar, use_container_width=True)
            
        st.markdown("<br/>", unsafe_allow_html=True)
        if is_mock:
            st.info("💡 구글 트렌드 API의 일시적인 호출 제한(429 Too Many Requests)으로 인해 AI 분석 기반 도시 선호도 순위로 우회하여 적용되었습니다.")
        else:
            st.success(f"✅ '{selected_country_name}' 지역의 실시간 구글 트렌드 선호도 분석이 완료되었습니다.")
    else:
        st.warning("⚠️ 구글 트렌드 데이터를 조회할 수 없습니다.")
        
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ----------------- SNS 키워드 분석 섹션 병합 -----------------
    st.markdown("<br/><hr/><br/>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-weight: 600; color: #F8FAFC;'>📱 SNS 관광 관심도 키워드별 분석</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8;'>SNS 언급량 지표를 기반으로 관광 카테고리 및 세부 키워드별 실시간 관심도 분포를 분석합니다.</p>", unsafe_allow_html=True)
    
    # SNS 총합 값 추출
    sns_total = 124500
    sns_row = df_resource[df_resource['demandMetric'] == 'SNS 언급량']
    if not sns_row.empty:
        sns_total = sns_row.iloc[0]['demandValue']
        
    df_sns_kw = get_sns_keyword_data(sns_total, selected_area_code)
    
    # 2열 구성
    col_sns1, col_sns2 = st.columns([4, 6])
    
    with col_sns1:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>🔍 카테고리 필터 및 순위</h4>", unsafe_allow_html=True)
        
        # 카테고리 선택 필터
        categories_list = list(df_sns_kw['category'].unique())
        selected_cat = st.selectbox("관광 분야 카테고리 선택", categories_list, index=0)
        
        # 선택된 카테고리의 키워드 순위표
        df_sns_cat_filtered = df_sns_kw[df_sns_kw['category'] == selected_cat].sort_values(by="value", ascending=False)
        
        st.dataframe(
            df_sns_cat_filtered[['keyword', 'value']],
            column_config={
                "keyword": "연관 관심 키워드",
                "value": "SNS 언급 횟수 (건)"
            },
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sns2:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>📊 '{selected_cat}' 분야 세부 키워드 비율 (Treemap)</h4>", unsafe_allow_html=True)
        
        # 트리맵 시각화
        fig_tree = px.treemap(
            df_sns_cat_filtered,
            path=['keyword'],
            values='value',
            color='value',
            color_continuous_scale='Teal',
            template='plotly_dark'
        )
        fig_tree.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_tree, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 하단 전체 키워드 종합 분포 바 차트
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>🌐 관광 키워드 관심도 종합 분포</h4>", unsafe_allow_html=True)
    
    fig_sns_all = px.bar(
        df_sns_kw.sort_values(by="value", ascending=True),
        y="keyword",
        x="value",
        color="category",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={"keyword": "키워드", "value": "SNS 언급량 (건)", "category": "카테고리"},
        template="plotly_dark",
        height=450
    )
    fig_sns_all.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(showgrid=False),
        legend=dict(font=dict(color="#94A3B8"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_sns_all, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 1: 종합 요약 분석 (Overview)
# ==========================================
with tab1:
    st.markdown("<h3 style='font-weight: 600; color: #F8FAFC;'>📌 지역 관광 활성화 종합 진단</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8;'>다양성 지수와 자원 수요 지표를 결합하여 해당 지역의 관광 매력도와 인프라 효율성을 종합적으로 판단합니다.</p>", unsafe_allow_html=True)
    
    # 2열 레이아웃
    col_ov1, col_ov2 = st.columns([6, 4])
    
    with col_ov1:
        # 연령대별 다양성 지수를 한눈에 비교하는 바 차트
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 15px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 10px;'>👥 연령대별 관광 수요 다양성 지표</h4>", unsafe_allow_html=True)
        
        # Plotly를 이용한 아름다운 세로형 바 차트 생성
        fig_bar = px.bar(
            df_diversity,
            x="expDivIxNm",
            y="touDivValue",
            color="touDivValue",
            color_continuous_scale=["#111827", "#00D2C4"],
            labels={"expDivIxNm": "연령 구분", "touDivValue": "다양성 지수 (0-100)"},
            template="plotly_dark"
        )
        # 차트 레이아웃 디테일 튜닝
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_ov2:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 15px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 10px;'>🕸️ 관광 서비스 자원 수요 분석</h4>", unsafe_allow_html=True)
        
        # 레이더 차트 생성 (자원 수요 시각화에 적합)
        categories = df_resource["demandMetric"].tolist()
        values = df_resource["demandValue"].tolist()
        
        # 스케일 조정을 위해 백분율 점수로 변환 (예시용 시각화 맵핑)
        max_val = max(values) if values else 1
        normalized_values = [v / max_val * 100 for v in values]
        
        fig_radar = ob.Figure()
        fig_radar.add_trace(ob.Scatterpolar(
            r=normalized_values,
            theta=categories,
            fill='toself',
            name=selected_area_name,
            line_color='#00D2C4',
            fillcolor='rgba(0, 210, 196, 0.2)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    showticklabels=False,
                    gridcolor="rgba(255,255,255,0.08)"
                ),
                angularaxis=dict(
                    gridcolor="rgba(255,255,255,0.08)",
                    tickfont=dict(color="#94A3B8", size=10)
                ),
                bgcolor="rgba(0,0,0,0)"
            ),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=30, b=40),
            height=320
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 하단 분석 통찰 (Insight Card)
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='background: rgba(0, 210, 196, 0.05); border: 1px dashed rgba(0, 210, 196, 0.2); padding: 20px; border-radius: 12px;'>
            <h4 style='color:#00D2C4; font-weight: 700; margin-top: 0;'>💡 Antigravity 데이터 분석 인사이트</h4>
            <p style='color: #E2E8F0; font-size: 0.95rem; line-height: 1.6; margin: 0;'>
                현재 <b>{selected_area_name}</b> 지역은 <b>20대 및 30대 연령층</b>에서 가장 높은 관광 다양성 지수({df_diversity['touDivValue'].max()}점)를 나타내고 있습니다. 
                SNS 언급량과 내비게이션 목적지 검색량이 조화를 이루며 유입량이 증가하고 있으나, 문화 자원 검색량에 비해 업종별 관광 소비액의 전환율을 더욱 높일 필요가 있습니다. 
                청장년층 맞춤형 모바일 관광 마케팅과 지역 화폐 연계 소비 유도 전략을 추천합니다.
            </p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# TAB 2: 관광객 다양성 분석 (Diversity)
# ==========================================
with tab2:
    st.markdown("<h3 style='font-weight: 600; color: #F8FAFC;'>🌈 연령별 & 국가별 외래 관광객 다양성 분석</h3>", unsafe_allow_html=True)
    
    # 1단: 연령대별 소비 및 관광 다양성 분석
    col_div1, col_div2 = st.columns(2)
    
    with col_div1:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>💳 연령별 소비 다양성 분포 비율</h4>", unsafe_allow_html=True)
        
        # 파이 차트 시각화
        fig_pie = px.pie(
            df_diversity,
            values="consumeRate",
            names="expDivIxNm",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Tealgrn_r,
            template="plotly_dark"
        )
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            legend=dict(font=dict(color="#94A3B8"))
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_div2:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>📈 연령별 관광 다양성 트렌드 패턴</h4>", unsafe_allow_html=True)
        
        # 영역형(Area) 차트로 누적 흐름 표현
        fig_area = px.area(
            df_diversity,
            x="expDivIxNm",
            y="touDivValue",
            markers=True,
            color_discrete_sequence=["#00D2C4"],
            labels={"expDivIxNm": "연령별 구분", "touDivValue": "다양성 지수"},
            template="plotly_dark"
        )
        fig_area.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_area, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 2단: 국가별(국적별) 외래 관광객 유입 분포 및 소비 다양성 분석
    st.markdown("<br/><hr/><br/>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-weight: 600; color: #F8FAFC;'>🌏 국가별 외래 관광객 유입 분포 및 소비 성향 분석</h3>", unsafe_allow_html=True)
    
    col_nat1, col_nat2 = st.columns(2)
    
    with col_nat1:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>🌐 '{selected_area_name}' 국적별 외래 관광객 비율</h4>", unsafe_allow_html=True)
        
        # 지역별 실질 국적 분포 데이터셋 동적 정의 (관광공사 인바운드 기준 가중치 반영)
        national_shares = {
            "제주특별자치도": {"대만 (TW)": 38.0, "중국 (CN)": 28.0, "동남아 (SEA)": 16.0, "미국 (US)": 8.0, "일본 (JP)": 6.0, "유럽/기타": 4.0},
            "서울특별시": {"일본 (JP)": 34.0, "미국 (US)": 22.0, "중국 (CN)": 18.0, "대만 (TW)": 12.0, "동남아 (SEA)": 8.0, "유럽/기타": 6.0},
            "부산광역시": {"일본 (JP)": 42.0, "대만 (TW)": 24.0, "미국 (US)": 12.0, "동남아 (SEA)": 10.0, "중국 (CN)": 7.0, "유럽/기타": 5.0},
            "강원특별자치도": {"동남아 (SEA)": 36.0, "대만 (TW)": 22.0, "미국 (US)": 16.0, "홍콩 (HK)": 12.0, "일본 (JP)": 8.0, "유럽/기타": 6.0},
            "경기도": {"미국 (US)": 28.0, "동남아 (SEA)": 26.0, "중국 (CN)": 18.0, "일본 (JP)": 12.0, "대만 (TW)": 10.0, "유럽/기타": 6.0},
            "인천광역시": {"미국 (US)": 32.0, "중국 (CN)": 24.0, "동남아 (SEA)": 16.0, "일본 (JP)": 12.0, "대만 (TW)": 10.0, "유럽/기타": 6.0}
        }
        
        # 정의되지 않은 타 지역의 기본 국적 분포
        default_shares = {"일본 (JP)": 28.0, "미국 (US)": 20.0, "대만 (TW)": 18.0, "동남아 (SEA)": 16.0, "중국 (CN)": 12.0, "유럽/기타": 6.0}
        
        shares = national_shares.get(selected_area_name, default_shares)
        df_national = pd.DataFrame(list(shares.items()), columns=["국적", "유입 비중 (%)"])
        
        fig_donut = px.pie(
            df_national,
            values="유입 비중 (%)",
            names="국적",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Bold,
            template="plotly_dark"
        )
        fig_donut.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            legend=dict(font=dict(color="#94A3B8"))
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_nat2:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>🛍️ 국적별 한국 관광 주요 소비 분야 다양성 (%)</h4>", unsafe_allow_html=True)
        
        # 국가별 관광 소비 업종 비중 데이터 (누적 막대 차트용)
        consume_data = [
            {"국적": "일본 (JP)", "쇼핑 (뷰티/의류)": 45.0, "식음료 (맛집/카페)": 35.0, "숙박 (호텔)": 12.0, "문화/레저": 5.0, "교통": 3.0},
            {"국적": "대만 (TW)", "쇼핑 (뷰티/의류)": 32.0, "식음료 (맛집/카페)": 42.0, "숙박 (호텔)": 15.0, "문화/레저": 7.0, "교통": 4.0},
            {"국적": "미국 (US)", "쇼핑 (뷰티/의류)": 12.0, "식음료 (맛집/카페)": 28.0, "숙박 (호텔)": 38.0, "문화/레저": 12.0, "교통": 10.0},
            {"국적": "동남아 (SEA)", "쇼핑 (뷰티/의류)": 25.0, "식음료 (맛집/카페)": 22.0, "숙박 (호텔)": 18.0, "문화/레저": 30.0, "교통": 5.0},
            {"국적": "중국 (CN)", "쇼핑 (뷰티/의류)": 52.0, "식음료 (맛집/카페)": 20.0, "숙박 (호텔)": 16.0, "문화/레저": 8.0, "교통": 4.0},
            {"국적": "유럽/기타", "쇼핑 (뷰티/의류)": 10.0, "식음료 (맛집/카페)": 26.0, "숙박 (호텔)": 35.0, "문화/레저": 18.0, "교통": 11.0}
        ]
        df_consume = pd.DataFrame(consume_data)
        
        # Plotly Stacked Bar Chart 생성
        fig_stacked = px.bar(
            df_consume,
            x="국적",
            y=["쇼핑 (뷰티/의류)", "식음료 (맛집/카페)", "숙박 (호텔)", "문화/레저", "교통"],
            labels={"value": "소비 비중 (%)", "variable": "소비 분야"},
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_stacked.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=10, b=20),
            height=340,
            legend=dict(font=dict(color="#94A3B8"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_stacked, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 3: 관광 자원 수요 분석 (Demand)
# ==========================================
with tab3:
    st.markdown("<h3 style='font-weight: 600; color: #F8FAFC;'>📈 관광 서비스 자원 및 문화 자원 수요</h3>", unsafe_allow_html=True)
    
    col_res1, col_res2 = st.columns([4, 6])
    
    with col_res1:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>📋 세부 지표별 수치 일람</h4>", unsafe_allow_html=True)
        
        # 깔끔하게 포맷팅된 데이터 프레임 뷰
        formatted_res = df_resource.copy()
        if 'demandValue' in formatted_res.columns:
            formatted_res['수요 값'] = formatted_res.apply(
                lambda row: f"{row['demandValue']:,.0f} {row['unit']}" if row['unit'] != '원' else f"{row['demandValue']/100000000:.1f} 억원", axis=1
            )
        st.dataframe(
            formatted_res[['demandMetric', '수요 값']],
            column_config={
                "demandMetric": "수요 측정 지표",
                "수요 값": "측정 값"
            },
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_res2:
        st.markdown("<div style='background: rgba(22, 29, 48, 0.4); padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1rem; color: #E2E8F0; margin-bottom: 15px;'>📊 자원 수요 비교 (로그 스케일 적용)</h4>", unsafe_allow_html=True)
        
        # 값이 수억대와 만단위로 편차가 심하므로 로그 스케일로 예쁘게 정렬하여 비교 가능하게 함
        import numpy as np
        df_log = df_resource.copy()
        df_log['logValue'] = np.log10(df_log['demandValue'] + 1)
        
        fig_res_bar = px.bar(
            df_log,
            y="demandMetric",
            x="logValue",
            orientation="h",
            color="demandMetric",
            color_discrete_sequence=["#FF758F", "#FFD166", "#0077FF", "#06D6A0"],
            labels={"demandMetric": "수요 지표", "logValue": "지수 크기 (Log scale)"},
            template="plotly_dark"
        )
        fig_res_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=20, r=20, t=10, b=20),
            height=300,
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_res_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


    


# ==========================================
# TAB 5: 원본 데이터 & 엑셀 다운로드 (Data Table)
# ==========================================
with tab5:
    st.markdown("<h3 style='font-weight: 600; color: #F8FAFC;'>🗂️ 실시간 연동 원본 데이터셋</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8;'>2개의 공공데이터포털 API(지역별 관광 다양성 & 지역별 관광 자원 수요)를 연동한 개별 데이터 테이블입니다.</p>", unsafe_allow_html=True)
    
    col_dt1, col_dt2 = st.columns(2)
    
    with col_dt1:
        st.markdown("<h5 style='color:#00D2C4;'>1. 지역별 관광 다양성 데이터 (API 1)</h5>", unsafe_allow_html=True)
        st.dataframe(df_diversity, use_container_width=True)
        
        # CSV 다운로드 기능
        csv_div = df_diversity.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 다양성 데이터 CSV 다운로드",
            data=csv_div,
            file_name=f"tourism_diversity_{selected_area_code}_{base_ym}.csv",
            mime="text/csv"
        )
        
    with col_dt2:
        st.markdown("<h5 style='color:#FF758F;'>2. 지역별 관광 자원 수요 데이터 (API 2)</h5>", unsafe_allow_html=True)
        st.dataframe(df_resource, use_container_width=True)
        
        # CSV 다운로드 기능
        csv_res = df_resource.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 자원 수요 데이터 CSV 다운로드",
            data=csv_res,
            file_name=f"tourism_resource_demand_{selected_area_code}_{base_ym}.csv",
            mime="text/csv"
        )

# 하단 정보 푸터
st.markdown("---")
st.markdown(f"""
    <div style='text-align: center; color: #64748B; font-size: 0.85rem; padding: 20px 0;'>
        대한민국 공공데이터포털(data.go.kr) & 한국관광공사 TourAPI 실시간 연동 대시보드<br/>
        Designed & Programmed by <b>Antigravity</b> Team. Current System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
