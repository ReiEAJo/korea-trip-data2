# -*- coding: utf-8 -*-
"""
외국인 한국 지역별 관심도 / 방문도 / 관심도 vs 방문도 대시보드
연령대별(청년층 10대~40대 / 중장년층 50대~90대) 비교 분석
데이터 출처: 구글 트랜드, TripAdvisor, Tumblr, KKday, GetYourGuide, Creatrip, KTO (2025.06 ~ 2026.05)
서울특별시, 부산광역시, 제주특별자치도 제외 (내국인 제외)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import sqlite3
import json
import re

# ─────────────────────────────────────────────────────────
# 페이지 기본 설정
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Korea City Trip",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────
# CSS 스타일 — 라이트 모드
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');

/* Pull content up to the top */
div[data-testid="stMainBlockContainer"] {
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
}
[data-testid="stSidebarUserContent"] {
    padding-top: 0.5rem !important;
}
[data-testid="stSidebarHeader"] {
    display: none !important;
}
header[data-testid="stHeader"] {
    display: none !important;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    background-color: #F8FAFC;
    color: #0F172A;
}
.stApp { background-color: #F8FAFC; }

/* ── Header ── */
.dashboard-header {
    background: linear-gradient(90deg, #1D4ED8 0%, #059669 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.5rem;
    letter-spacing: -0.05rem;
    margin-bottom: 0.3rem;
}
.dashboard-sub {
    color: #475569;
    font-size: 1.05rem;
    margin-bottom: 1.5rem;
}

/* ── Age group badges ── */
.badge-young {
    display: inline-block;
    background: linear-gradient(90deg, #1D4ED8, #2563EB);
    color: white;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 4px 14px;
    border-radius: 20px;
    margin-right: 6px;
}
.badge-old {
    display: inline-block;
    background: linear-gradient(90deg, #059669, #10B981);
    color: white;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 4px 14px;
    border-radius: 20px;
    margin-right: 6px;
}

/* ── KPI Cards ── */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    transition: all 0.3s ease;
    margin-bottom: 1rem;
}
.kpi-card:hover {
    transform: translateY(-4px);
    border-color: #CBD5E1;
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.08);
}
.kpi-label { color: #64748B; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; }
.kpi-value { color: #0284C7; font-size: 1.8rem; font-weight: 800; margin-top: 4px; }
.kpi-delta-up { color: #059669; font-size: 0.85rem; margin-top: 2px; }
.kpi-delta-down { color: #DC2626; font-size: 0.85rem; margin-top: 2px; }

/* ── Top Rank Badges ── */
.top-rank-container {
    display: flex;
    justify-content: space-around;
    align-items: center;
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.top-rank-item {
    text-align: center;
    flex: 1;
}
.top-rank-title {
    font-size: 0.9rem;
    color: #64748B;
    font-weight: 600;
}
.top-rank-value {
    font-size: 1.3rem;
    font-weight: 800;
    color: #1D4ED8;
    margin-top: 4px;
}

/* ── Section title ── */
.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1D4ED8;
    margin: 1.5rem 0 0.8rem;
    padding-left: 10px;
    border-left: 4px solid #1D4ED8;
}

/* ── Insight box ── */
.insight-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 12px 0;
    color: #1E40AF;
    font-size: 0.93rem;
    line-height: 1.6;
}
.insight-box strong { color: #1D4ED8; }

/* ── Compare chip ── */
.compare-chip {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 0.88rem;
    color: #334155;
    margin-bottom: 8px;
}

/* ── Tabs ── */
div[data-testid="stTabs"] button[role="tab"] {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #64748B !important;
    transition: all 0.3s ease;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #0284C7 !important;
    border-bottom: 2px solid #0284C7 !important;
}
div[data-testid="stTabs"] button[role="tab"]:hover {
    color: #0F172A !important;
}

/* ── Alert styles ── */
.stAlert {
    background-color: #F1F5F9 !important;
    border: 1px solid #E2E8F0 !important;
    color: #0F172A !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0;
}

.rank-column-card {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-top: 4px solid #1D4ED8 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
    width: 100% !important;
}

.insight-summary-card {
    border-radius: 12px !important;
    padding: 18px 22px !important;
    margin-top: 25px !important;
    margin-bottom: 15px !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02) !important;
}
.insight-interest {
    background-color: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    border-left: 5px solid #1D4ED8 !important;
}
.insight-visit {
    background-color: #ECFDF5 !important;
    border: 1px solid #A7F3D0 !important;
    border-left: 5px solid #059669 !important;
}
.insight-vs {
    background-color: #F5F3FF !important;
    border: 1px solid #DDD6FE !important;
    border-left: 5px solid #8B5CF6 !important;
}
.insight-map {
    background-color: #FEF9C3 !important;
    border: 1px solid #FEF08A !important;
    border-left: 5px solid #EAB308 !important;
}

/* --- Google Chrome Tabs Navigation Styling --- */
.chrome-tab-bar {
    display: flex !important;
    flex-direction: row !important;
    align-items: flex-end !important;
    background-color: #DCE6F2 !important; /* Chrome tab bar background */
    padding: 10px 16px 0px 16px !important;
    border-radius: 12px 12px 0 0 !important;
    border-bottom: 1px solid #B0C4DE !important;
    margin-bottom: 15px !important;
    gap: 4px !important;
    width: 100% !important;
}

.chrome-tab {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    background-color: #C3D1E6 !important; /* Inactive Chrome tab background */
    color: #4A5568 !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 8px 20px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    height: 36px !important;
    transition: background-color 0.2s, color 0.2s !important;
    border: none !important;
}

.chrome-tab:hover {
    background-color: #B0C4DE !important;
    color: #1A202C !important;
    text-decoration: none !important;
}

.chrome-tab.active {
    background-color: #F8FAFC !important; /* Active tab matches content area background */
    color: #1A73E8 !important; /* Active text color */
    font-weight: 700 !important;
    box-shadow: 0 -2px 6px rgba(0,0,0,0.06) !important;
    border-bottom: 2px solid #F8FAFC !important;
    z-index: 10 !important;
    text-decoration: none !important;
}

.chrome-tab-close {
    font-size: 14px !important;
    color: #718096 !important;
    margin-left: 12px !important;
    font-weight: normal !important;
}

.chrome-tab.active .chrome-tab-close {
    color: #1A73E8 !important;
    font-weight: bold !important;
}

.chrome-new-tab {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 26px !important;
    height: 26px !important;
    border-radius: 50% !important;
    background-color: rgba(0, 0, 0, 0.06) !important;
    color: #5F6368 !important;
    font-size: 13px !important;
    font-weight: bold !important;
    margin-left: 8px !important;
    align-self: center !important;
    cursor: pointer !important;
    transition: background-color 0.2s !important;
}

.chrome-new-tab:hover {
    background-color: rgba(0, 0, 0, 0.12) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# 데이터 설정 (서울, 부산, 제주 제외 14개 시도)
# ─────────────────────────────────────────────────────────

REGIONS = [
    "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
    "경기도", "강원특별자치도", "충청북도", "충청남도",
    "전북특별자치도", "전라남도", "경상북도", "경상남도"
]

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
    "전북특별자치도": ["전라북도", "전북", "전주", "익산", "내장사", "내장산"],
    "전라남도": ["전라남도", "전남", "여수", "순천"],
    "경상북도": ["경상북도", "경북", "경주", "안동", "포항", "봉화", "석굴암", "불국사", "첨성대"],
    "경상남도": ["경상남도", "경남", "김해", "창원", "진해", "진주", "산청", "고성", "밀양"]
}

EXCLUDE_KWS = [
    "서울", "명동", "홍대", "인사동", "경복궁", "강남", "창덕궁", "청와대", "롯데월드", 
    "광화문", "동대문", "압구정", "남산", "N서울타워", "광장시장", "여의도", "올림픽 공원", "코엑스", "성수", "청담", "창경", "덕수", "익선", "신촌", "이대", "대학로", "혜화", "잠실", "송파", "북촌",
    "부산", "해운대", "광안리", "감천", "남포", "영도", "자갈치", "오륙도", "다대포", "서면", "용궁사", "동부산", "민락동",
    "제주", "서귀포", "성산", "우도", "한라산"
]

AGE_LABELS  = ["10대", "20대", "30대", "40대", "50대", "60대", "70대+"]
AGE_GROUP_YOUNG = ["10대", "20대", "30대", "40대"]   # 인덱스 0~3
AGE_GROUP_OLD   = ["50대", "60대", "70대+"]           # 인덱스 4~6

GRP_YOUNG_LABEL = "청년층"
GRP_OLD_LABEL   = "중장년층"

GRP_YOUNG_DETAIL = "청년층 (10대~40대)"
GRP_OLD_DETAIL   = "중장년층 (50대~90대)"

COLOR_YOUNG       = "#1D4ED8"   # 파랑
COLOR_OLD         = "#059669"   # 초록
COLOR_YOUNG_LIGHT = "#93C5FD"
COLOR_OLD_LIGHT   = "#6EE7B7"

AGE_COLORS = {
    "10대": "#BFDBFE", "20대": "#60A5FA", "30대": "#2563EB", "40대": "#1D4ED8",
    "50대": "#6EE7B7", "60대": "#10B981", "70대+": "#047857"
}

# 연령대별 분포 가중치 (KTO 방한외래관광객 실태조사 참조)
AGE_INTEREST_RATIO = {
    "대구광역시":      [0.08, 0.20, 0.22, 0.20, 0.16, 0.10, 0.04],
    "인천광역시":      [0.09, 0.22, 0.24, 0.19, 0.15, 0.08, 0.03],
    "광주광역시":      [0.07, 0.18, 0.21, 0.21, 0.18, 0.11, 0.04],
    "대전광역시":      [0.07, 0.18, 0.22, 0.21, 0.17, 0.11, 0.04],
    "울산광역시":      [0.06, 0.15, 0.20, 0.22, 0.20, 0.12, 0.05],
    "세종특별자치시":  [0.06, 0.16, 0.22, 0.22, 0.19, 0.11, 0.04],
    "경기도":          [0.09, 0.21, 0.23, 0.20, 0.16, 0.08, 0.03],
    "강원특별자치도":  [0.11, 0.24, 0.22, 0.18, 0.14, 0.08, 0.03],
    "충청북도":        [0.08, 0.18, 0.21, 0.20, 0.17, 0.11, 0.05],
    "충청남도":        [0.07, 0.17, 0.21, 0.21, 0.18, 0.11, 0.05],
    "전북특별자치도":  [0.07, 0.16, 0.19, 0.21, 0.20, 0.13, 0.04],
    "전라남도":        [0.07, 0.15, 0.18, 0.21, 0.21, 0.13, 0.05],
    "경상북도":        [0.07, 0.16, 0.19, 0.21, 0.20, 0.12, 0.05],
    "경상남도":        [0.07, 0.16, 0.20, 0.21, 0.19, 0.12, 0.05],
}
AGE_VISIT_RATIO = {
    "대구광역시":      [0.07, 0.18, 0.22, 0.21, 0.17, 0.11, 0.04],
    "인천광역시":      [0.08, 0.20, 0.25, 0.20, 0.16, 0.08, 0.03],
    "광주광역시":      [0.06, 0.16, 0.22, 0.22, 0.19, 0.11, 0.04],
    "대전광역시":      [0.06, 0.17, 0.22, 0.22, 0.18, 0.11, 0.04],
    "울산광역시":      [0.05, 0.13, 0.19, 0.23, 0.22, 0.13, 0.05],
    "세종특별자치시":  [0.05, 0.14, 0.22, 0.23, 0.21, 0.11, 0.04],
    "경기도":          [0.08, 0.19, 0.24, 0.21, 0.17, 0.08, 0.03],
    "강원특별자치도":  [0.10, 0.22, 0.23, 0.19, 0.15, 0.08, 0.03],
    "충청북도":        [0.07, 0.16, 0.20, 0.21, 0.19, 0.12, 0.05],
    "충청남도":        [0.06, 0.15, 0.20, 0.22, 0.20, 0.12, 0.05],
    "전북특별자치도":  [0.06, 0.14, 0.18, 0.22, 0.22, 0.13, 0.05],
    "전라남도":        [0.06, 0.13, 0.17, 0.22, 0.23, 0.14, 0.05],
    "경상북도":        [0.06, 0.14, 0.18, 0.22, 0.22, 0.13, 0.05],
    "경상남도":        [0.06, 0.14, 0.19, 0.22, 0.21, 0.13, 0.05],
}

# ─────────────────────────────────────────────────────────
# KTO 방한외래관광객 실태조사 2024 기반
# 청년층(10~40대) vs 중장년층(50대+) 지역별 실제 방문 분포 지수
# 출처: KTO 방한외래관광객 실태조사, DataLab 지역별 방문 분포,
#       KKday·GetYourGuide·Creatrip 연령 메타데이터 분석 종합
# ─────────────────────────────────────────────────────────
# 청년층: 액티비티·나이트라이프·자연체험 중심 → 강원, 경기 강세
YOUNG_VISIT_BASE = {
    "경기도":          82.0,   # 에버랜드, DMZ, 수도권 접근성 → 청년 압도적 1위
    "인천광역시":      68.0,   # 공항 관문, 송도 팝업, 차이나타운
    "강원특별자치도":  63.0,   # 스키·서핑·레저 → 청년 특화 1위권 비수도권
    "대구광역시":      31.0,   # 동성로 쇼핑·야시장
    "경상남도":        27.0,   # 거제 케이블카, 통영 스카이라인
    "충청남도":        24.0,   # 보령 머드, 아산 온양
    "전북특별자치도":  21.0,   # 전주 한옥마을 (청년도 선호하나 중장년보다 낮음)
    "경상북도":        20.0,   # 경주 야간 조명 → 청년 SNS 인기
    "전라남도":        19.0,   # 여수 밤바다 콘텐츠
    "대전광역시":      18.0,   # 성심당, 과학관
    "광주광역시":      16.0,   # 5·18 민주화운동 기념관, 예술
    "충청북도":        14.0,   # 단양 패러글라이딩
    "울산광역시":      12.0,   # 태화강 국가정원
    "세종특별자치시":   8.0,   # 행정 중심 → 관광 비중 낮음
}

# 중장년층: 역사문화·음식·힐링·자연 중심 → 전북, 경북 강세
OLD_VISIT_BASE = {
    "경기도":          38.0,   # 수도권 거주 중장년층 근거리 방문
    "인천광역시":      26.0,   # 관문 도착 후 이동, 차이나타운
    "전북특별자치도":  35.0,   # 전주 한옥마을·음식 → 중장년 압도적 선호
    "경상북도":        33.0,   # 경주·불국사·안동 하회마을 → 중장년 1위권
    "강원특별자치도":  28.0,   # 속초 해물·설악산 힐링
    "전라남도":        27.0,   # 순천만·보성 녹차밭·여수
    "경상남도":        25.0,   # 통영·거제 해안 드라이브
    "충청남도":        22.0,   # 아산 현충사·공주 백제유적
    "대구광역시":      21.0,   # 방천시장·서문시장 음식문화
    "충청북도":        19.0,   # 청주 직지심체요절, 단양
    "대전광역시":      17.0,   # 한밭수목원·유성온천
    "광주광역시":      16.0,   # 5·18 민주화운동 역사 관광
    "울산광역시":      14.0,   # 울산 고래박물관·반구대암각화
    "세종특별자치시":   9.0,   # 세종호수공원·정부청사 방문
}

# ─────────────────────────────────────────────────────────
# 데이터 로드 및 중간값 산출 함수
# ─────────────────────────────────────────────────────────
@st.cache_data
def get_integrated_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "data")):
        data_dir = os.path.join(current_dir, "data")
    elif os.path.exists(os.path.join(os.path.dirname(current_dir), "data")):
        data_dir = os.path.join(os.path.dirname(current_dir), "data")
    else:
        data_dir = os.path.join(current_dir, "★korea-trip-data", "data")
    
    # 1. Google Trends (from regional_google_trends.csv)
    google_trends_data = {
        "인천광역시": 19.58, "대구광역시": 7.04, "광주광역시": 3.81, "대전광역시": 3.34, "울산광역시": 1.02, "세종특별자치시": 0.77,
        "경기도": 3.91, "강원특별자치도": 0.70, "충청북도": 11.45, "충청남도": 16.62, "전북특별자치도": 35.53,
        "전라남도": 5.34, "경상북도": 2.28, "경상남도": 3.77
    }
    
    # 2. TripAdvisor cached values
    ta_ratings = {
        "인천광역시": 4.4, "대구광역시": 4.5, "광주광역시": 4.4, "대전광역시": 4.5, "울산광역시": 4.3, "세종특별자치시": 4.3,
        "경기도": 4.5, "강원특별자치도": 4.6, "충청북도": 4.3, "충청남도": 4.4, "전북특별자치도": 4.6, "전라남도": 4.6,
        "경상북도": 4.7, "경상남도": 4.5
    }
    ta_reviews_count = {
        "경기도": 780, "인천광역시": 540, "강원특별자치도": 650, "경상북도": 560,
        "전북특별자치도": 450, "대구광역시": 380, "충청남도": 310, "경상남도": 490,
        "전라남도": 410, "대전광역시": 340, "광주광역시": 290, "충청북도": 280,
        "울산광역시": 250, "세종특별자치시": 150
    }
    
    # 3. Tumblr scores
    tumblr_scores = {r: 3.0 for r in REGIONS}
    tumblr_scores["인천광역시"] = 4.0
    tumblr_visits_count = {r: 0 for r in REGIONS}
    tumblr_visits_count["인천광역시"] = 1
    
    # Helper to parse text to standard region
    def get_region_from_text(name):
        if not name:
            return None
        for kw in EXCLUDE_KWS:
            if kw in name:
                return "EXCLUDE"
        for r, kw_list in REGIONS_MAP.items():
            for kw in kw_list:
                if kw in name:
                    return r
        return None

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

    # Load Instagram Data
    insta_counts = {r: 0 for r in REGIONS}
    insta_ratings = {r: 3.5 for r in REGIONS}
    insta_path = os.path.join(current_dir, "instagram_korea_local_data.csv")
    if not os.path.exists(insta_path):
        insta_path = "instagram_korea_local_data.csv"
    if os.path.exists(insta_path):
        try:
            df_insta = pd.read_csv(insta_path)
            df_insta['caption'] = df_insta['caption'].fillna('')
            df_insta['inputQuery'] = df_insta['inputQuery'].fillna('')
            
            HASHTAG_TO_REGION = {
                "gyeongju": "경상북도", "gyeongjutrip": "경상북도", "hanokstay": "경상북도",
                "gangneung": "강원특별자치도", "yangyang": "강원특별자치도", "koreasurfing": "강원특별자치도",
                "jeonju": "전북특별자치도", "jeonjuhanokvillage": "전북특별자치도", "koreanfoodtrip": "전북특별자치도",
                "suwon": "경기도", "suwonhwaseongfortress": "경기도", "starfieldsuwon": "경기도"
            }
            df_insta['지역'] = df_insta['inputQuery'].map(HASHTAG_TO_REGION).fillna('기타')
            
            def calculate_sentiment_rating(text):
                if not isinstance(text, str):
                    return 3.5
                rating = 3.5
                pos_words = ["great", "delicious", "good", "nice", "amazing", "wonderful", "perfect", "loved", "friendly", "best", "yummy", "맛있", "최고", "좋", "친절", "superb"]
                text_lower = text.lower()
                for word in pos_words:
                    if word in text_lower:
                        rating += 1.0
                        break
                if len(text) > 50:
                    rating += 0.5
                return min(rating, 5.0)
                
            df_insta['rating'] = df_insta['caption'].apply(calculate_sentiment_rating)
            for r in REGIONS:
                subset = df_insta[df_insta['지역'] == r]
                if not subset.empty:
                    insta_counts[r] = len(subset)
                    insta_ratings[r] = subset['rating'].mean()
        except:
            pass

    # Load CatchTable & Naver Map Data
    catch_counts = {r: 0 for r in REGIONS}
    catch_ratings = {r: 3.5 for r in REGIONS}
    naver_counts = {r: 0 for r in REGIONS}
    naver_ratings = {r: 3.5 for r in REGIONS}
    
    foreign_path = os.path.join(current_dir, "foreign_dashboard_data.csv")
    if not os.path.exists(foreign_path):
        foreign_path = "foreign_dashboard_data.csv"
    if os.path.exists(foreign_path):
        try:
            df_foreign = pd.read_csv(foreign_path)
            
            def calculate_sentiment_rating(text):
                if not isinstance(text, str):
                    return 3.5
                rating = 3.5
                pos_words = ["great", "delicious", "good", "nice", "amazing", "wonderful", "perfect", "loved", "friendly", "best", "yummy", "맛있", "최고", "좋", "친절", "superb"]
                text_lower = text.lower()
                for word in pos_words:
                    if word in text_lower:
                        rating += 1.0
                        break
                if len(text) > 50:
                    rating += 0.5
                return min(rating, 5.0)

            df_foreign['rating'] = df_foreign['review_text'].apply(calculate_sentiment_rating)
            df_foreign['지역'] = df_foreign['city'].apply(get_region_from_text)
            for r in REGIONS:
                c_subset = df_foreign[(df_foreign['지역'] == r) & (df_foreign['source'] == 'CatchTable Global')]
                if not c_subset.empty:
                    catch_counts[r] = len(c_subset)
                    catch_ratings[r] = c_subset['rating'].mean()
                n_subset = df_foreign[(df_foreign['지역'] == r) & (df_foreign['source'] == 'Naver Map')]
                if not n_subset.empty:
                    naver_counts[r] = len(n_subset)
                    naver_ratings[r] = n_subset['rating'].mean()
        except:
            pass

    # 7, 8, 9. KKday, GetYourGuide, Creatrip databases
    ota_data = {r: {"kkday_ratings": [], "kkday_reviews": 0, "gyg_ratings": [], "gyg_reviews": 0, "creatrip_ratings": [], "creatrip_reviews": 0} for r in REGIONS}
    
    kkd_db = os.path.join(data_dir, "kkday_products.db")
    if os.path.exists(kkd_db):
        try:
            conn = sqlite3.connect(kkd_db)
            cursor = conn.cursor()
            cursor.execute("SELECT p.name, p.destinations, d.guide_langs, d.rec_avg_score, d.rec_num FROM kkday_products p LEFT JOIN kkday_product_details d ON p.prod_mid = d.prod_mid")
            for name, destinations_str, guide_langs, score_raw, rec_num_raw in cursor.fetchall():
                region = get_region_from_text(name)
                if region and region != "EXCLUDE":
                    rating = clean_rating(score_raw)
                    reviews = clean_reviews(rec_num_raw)
                    if rating > 0:
                        ota_data[region]["kkday_ratings"].append(rating)
                    ota_data[region]["kkday_reviews"] += reviews
            conn.close()
        except:
            pass

    gyg_db = os.path.join(data_dir, "getyourguide.db")
    if os.path.exists(gyg_db):
        try:
            conn = sqlite3.connect(gyg_db)
            cursor = conn.cursor()
            cursor.execute("SELECT title, rating, reviews, region FROM activities")
            for title, rating_raw, reviews_raw, region_raw in cursor.fetchall():
                region = get_region_from_text(region_raw) or get_region_from_text(title)
                if region and region != "EXCLUDE":
                    rating = clean_rating(rating_raw)
                    reviews = clean_reviews(reviews_raw)
                    if rating > 0:
                        ota_data[region]["gyg_ratings"].append(rating)
                    ota_data[region]["gyg_reviews"] += reviews
            conn.close()
        except:
            pass

    ct_db = os.path.join(data_dir, "creatrip_products.db")
    if os.path.exists(ct_db):
        try:
            conn = sqlite3.connect(ct_db)
            cursor = conn.cursor()
            cursor.execute("SELECT p.name, p.destinations, d.guide_langs, d.rec_avg_score, d.rec_num FROM creatrip_products p LEFT JOIN creatrip_product_details d ON p.prod_mid = d.prod_mid")
            for name, destinations_str, guide_langs, score_raw, rec_num_raw in cursor.fetchall():
                region = get_region_from_text(name)
                if region and region != "EXCLUDE":
                    rating = clean_rating(score_raw)
                    reviews = clean_reviews(rec_num_raw)
                    if rating > 0:
                        ota_data[region]["creatrip_ratings"].append(rating)
                    ota_data[region]["creatrip_reviews"] += reviews
            conn.close()
        except:
            pass

    # 10. KTO visitor counts (excluding Koreans)
    kto_visitor_data = {
        "경기도": 2150000, "인천광역시": 1250000, "강원특별자치도": 540000, "경상북도": 200000,
        "전북특별자치도": 110000, "대구광역시": 90000, "충청남도": 85000, "경상남도": 80000,
        "전라남도": 75000, "대전광역시": 70000, "광주광역시": 50000, "충청북도": 45000,
        "울산광역시": 30000, "세종특별자치시": 10000
    }

    # Consolidated Calculations for General Population
    # 10 Visit Counts
    raw_visit_counts = {}
    for r in REGIONS:
        raw_visit_counts[r] = {
            "insta": insta_counts.get(r, 0),
            "catch": catch_counts.get(r, 0),
            "naver": naver_counts.get(r, 0),
            "trends": google_trends_data.get(r, 0.0), 
            "ta": ta_reviews_count.get(r, 0),
            "tumblr": tumblr_visits_count.get(r, 0),
            "kkd": ota_data[r]["kkday_reviews"],
            "gyg": ota_data[r]["gyg_reviews"],
            "ct": ota_data[r]["creatrip_reviews"],
            "kto": kto_visitor_data.get(r, 0)
        }
        
    keys = ["insta", "catch", "naver", "trends", "ta", "tumblr", "kkd", "gyg", "ct", "kto"]
    max_counts = {k: max(raw_visit_counts[r][k] for r in REGIONS) or 1.0 for k in keys}
    
    results = []
    for r in REGIONS:
        # --- 10 INTEREST SOURCES (scaled to 100) ---
        v1 = (insta_ratings.get(r, 3.5) / 5.0) * 100.0
        v2 = (catch_ratings.get(r, 3.5) / 5.0) * 100.0
        v3 = (naver_ratings.get(r, 3.5) / 5.0) * 100.0
        
        max_trends = max(google_trends_data.values())
        v4 = (google_trends_data.get(r, 0.0) / max_trends) * 100.0
        
        v5 = (ta_ratings.get(r, 3.5) / 5.0) * 100.0
        v6 = (tumblr_scores.get(r, 3.0) / 5.0) * 100.0
        
        kkd_ratings_list = ota_data[r]["kkday_ratings"]
        v7 = (np.mean(kkd_ratings_list) / 5.0) * 100.0 if kkd_ratings_list else 70.0
        
        gyg_ratings_list = ota_data[r]["gyg_ratings"]
        v8 = (np.mean(gyg_ratings_list) / 5.0) * 100.0 if gyg_ratings_list else 70.0
        
        ct_ratings_list = ota_data[r]["creatrip_ratings"]
        v9 = (np.mean(ct_ratings_list) / 5.0) * 100.0 if ct_ratings_list else 70.0
        
        max_kto = max(kto_visitor_data.values())
        v10 = (kto_visitor_data.get(r, 0) / max_kto) * 100.0
        
        interest_scores = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10]
        # Median of non-zero interest scores
        valid_interest = [s for s in interest_scores if s > 0.0]
        interest_median = np.median(valid_interest) if valid_interest else 70.0
        
        # --- 10 VISIT SOURCES (scaled to 100) ---
        visit_scores = []
        for k in keys:
            norm_val = (raw_visit_counts[r][k] / max_counts[k]) * 100.0
            visit_scores.append(norm_val)
            
        # Median of non-zero visit scores
        valid_visit = [s for s in visit_scores if s > 0.0]
        visit_median = np.median(valid_visit) if valid_visit else 0.0
        
        results.append({
            "region": r,
            "interest_median": round(interest_median, 1),
            "visit_median": round(visit_median, 1)
        })
        
    return pd.DataFrame(results)

# Load dynamic calculated values
df_integrated = get_integrated_data()
interest_map = df_integrated.set_index("region")["interest_median"].to_dict()
visit_map = df_integrated.set_index("region")["visit_median"].to_dict()

# ─────────────────────────────────────────────────────────
# 청년층 (10대~40대) 10대 데이터 통합 및 중간값 산출 함수
# ─────────────────────────────────────────────────────────
@st.cache_data
def get_youth_integrated_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "data")):
        data_dir = os.path.join(current_dir, "data")
    elif os.path.exists(os.path.join(os.path.dirname(current_dir), "data")):
        data_dir = os.path.join(os.path.dirname(current_dir), "data")
    else:
        data_dir = os.path.join(current_dir, "★korea-trip-data", "data")
        
    # Helper to parse text to standard region
    def get_region_from_text(name):
        if not name:
            return None
        for kw in EXCLUDE_KWS:
            if kw in name:
                return "EXCLUDE"
        for r, kw_list in REGIONS_MAP.items():
            for kw in kw_list:
                if kw in name:
                    return r
        return None

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

    def calculate_sentiment_rating(text):
        if not isinstance(text, str):
            return 3.5
        rating = 3.5
        pos_words = ["great", "delicious", "good", "nice", "amazing", "wonderful", "perfect", "loved", "friendly", "best", "yummy", "맛있", "최고", "좋", "친절", "superb"]
        text_lower = text.lower()
        for word in pos_words:
            if word in text_lower:
                rating += 1.0
                break
        if len(text) > 50:
            rating += 0.5
        return min(rating, 5.0)

    # 1. Instagram
    insta_path = os.path.join(os.path.dirname(data_dir), "instagram_korea_local_data.csv")
    if not os.path.exists(insta_path):
        insta_path = os.path.join(current_dir, "instagram_korea_local_data.csv")
        
    insta_counts = {r: 0 for r in REGIONS}
    insta_ratings = {r: 3.5 for r in REGIONS}
    if os.path.exists(insta_path):
        try:
            df_insta = pd.read_csv(insta_path)
            df_insta['caption'] = df_insta['caption'].fillna('')
            df_insta['inputQuery'] = df_insta['inputQuery'].fillna('')
            HASHTAG_TO_REGION = {
                "gyeongju": "경상북도", "gyeongjutrip": "경상북도", "hanokstay": "경상북도",
                "gangneung": "강원특별자치도", "yangyang": "강원특별자치도", "koreasurfing": "강원특별자치도",
                "jeonju": "전북특별자치도", "jeonjuhanokvillage": "전북특별자치도", "koreanfoodtrip": "전북특별자치도",
                "suwon": "경기도", "suwonhwaseongfortress": "경기도", "starfieldsuwon": "경기도"
            }
            df_insta['지역'] = df_insta['inputQuery'].map(HASHTAG_TO_REGION).fillna('기타')
            df_insta['rating'] = df_insta['caption'].apply(calculate_sentiment_rating)
            for r in REGIONS:
                subset = df_insta[df_insta['지역'] == r]
                if not subset.empty:
                    insta_counts[r] = len(subset)
                    insta_ratings[r] = subset['rating'].mean()
        except:
            pass

    # 2 & 3. CatchTable & Naver Map
    foreign_path = os.path.join(os.path.dirname(data_dir), "foreign_dashboard_data.csv")
    if not os.path.exists(foreign_path):
        foreign_path = os.path.join(current_dir, "foreign_dashboard_data.csv")
        
    catch_counts = {r: 0 for r in REGIONS}
    catch_ratings = {r: 3.5 for r in REGIONS}
    naver_counts = {r: 0 for r in REGIONS}
    naver_ratings = {r: 3.5 for r in REGIONS}
    if os.path.exists(foreign_path):
        try:
            df_foreign = pd.read_csv(foreign_path)
            df_foreign['rating'] = df_foreign['review_text'].apply(calculate_sentiment_rating)
            df_foreign['지역'] = df_foreign['city'].apply(get_region_from_text)
            for r in REGIONS:
                c_subset = df_foreign[(df_foreign['지역'] == r) & (df_foreign['source'] == 'CatchTable Global')]
                if not c_subset.empty:
                    catch_counts[r] = len(c_subset)
                    catch_ratings[r] = c_subset['rating'].mean()
                n_subset = df_foreign[(df_foreign['지역'] == r) & (df_foreign['source'] == 'Naver Map')]
                if not n_subset.empty:
                    naver_counts[r] = len(n_subset)
                    naver_ratings[r] = n_subset['rating'].mean()
        except:
            pass

    # 4. Google Trends (from regional_google_trends.csv)
    google_trends_data = {
        "인천광역시": 19.58, "대구광역시": 7.04, "광주광역시": 3.81, "대전광역시": 3.34, "울산광역시": 1.02, "세종특별자치시": 0.77,
        "경기도": 3.91, "강원특별자치도": 0.70, "충청북도": 11.45, "충청남도": 16.62, "전북특별자치도": 35.53,
        "전라남도": 5.34, "경상북도": 2.28, "경상남도": 3.77
    }

    # 5. TripAdvisor
    ta_ratings = {
        "인천광역시": 4.4, "대구광역시": 4.5, "광주광역시": 4.4, "대전광역시": 4.5, "울산광역시": 4.3, "세종특별자치시": 4.3,
        "경기도": 4.5, "강원특별자치도": 4.6, "충청북도": 4.3, "충청남도": 4.4, "전북특별자치도": 4.6, "전라남도": 4.6,
        "경상북도": 4.7, "경상남도": 4.5
    }
    ta_reviews_count = {
        "경기도": 780, "인천광역시": 540, "강원특별자치도": 650, "경상북도": 560,
        "전북특별자치도": 450, "대구광역시": 380, "충청남도": 310, "경상남도": 490,
        "전라남도": 410, "대전광역시": 340, "광주광역시": 290, "충청북도": 280,
        "울산광역시": 250, "세종특별자치시": 150
    }

    # 6. Tumblr
    tumblr_scores = {r: 3.0 for r in REGIONS}
    tumblr_scores["인천광역시"] = 4.0
    tumblr_visits_count = {r: 0 for r in REGIONS}
    tumblr_visits_count["인천광역시"] = 1

    # 7, 8, 9. KKday, GetYourGuide, Creatrip
    ota_data = {r: {"kkday_ratings": [], "kkday_reviews": 0, "gyg_ratings": [], "gyg_reviews": 0, "creatrip_ratings": [], "creatrip_reviews": 0} for r in REGIONS}
    
    kkd_db = os.path.join(data_dir, "kkday_products.db")
    if os.path.exists(kkd_db):
        try:
            conn = sqlite3.connect(kkd_db)
            cursor = conn.cursor()
            cursor.execute("SELECT p.name, p.destinations, d.guide_langs, d.rec_avg_score, d.rec_num FROM kkday_products p LEFT JOIN kkday_product_details d ON p.prod_mid = d.prod_mid")
            for name, destinations_str, guide_langs, score_raw, rec_num_raw in cursor.fetchall():
                region = get_region_from_text(name)
                if region and region != "EXCLUDE":
                    rating = clean_rating(score_raw)
                    reviews = clean_reviews(rec_num_raw)
                    if rating > 0:
                        ota_data[region]["kkday_ratings"].append(rating)
                    ota_data[region]["kkday_reviews"] += reviews
            conn.close()
        except:
            pass

    gyg_db = os.path.join(data_dir, "getyourguide.db")
    if os.path.exists(gyg_db):
        try:
            conn = sqlite3.connect(gyg_db)
            cursor = conn.cursor()
            cursor.execute("SELECT title, rating, reviews, region FROM activities")
            for title, rating_raw, reviews_raw, region_raw in cursor.fetchall():
                region = get_region_from_text(region_raw) or get_region_from_text(title)
                if region and region != "EXCLUDE":
                    rating = clean_rating(rating_raw)
                    reviews = clean_reviews(reviews_raw)
                    if rating > 0:
                        ota_data[region]["gyg_ratings"].append(rating)
                    ota_data[region]["gyg_reviews"] += reviews
            conn.close()
        except:
            pass

    ct_db = os.path.join(data_dir, "creatrip_products.db")
    if os.path.exists(ct_db):
        try:
            conn = sqlite3.connect(ct_db)
            cursor = conn.cursor()
            cursor.execute("SELECT p.name, p.destinations, d.guide_langs, d.rec_avg_score, d.rec_num FROM creatrip_products p LEFT JOIN creatrip_product_details d ON p.prod_mid = d.prod_mid")
            for name, destinations_str, guide_langs, score_raw, rec_num_raw in cursor.fetchall():
                region = get_region_from_text(name)
                if region and region != "EXCLUDE":
                    rating = clean_rating(score_raw)
                    reviews = clean_reviews(rec_num_raw)
                    if rating > 0:
                        ota_data[region]["creatrip_ratings"].append(rating)
                    ota_data[region]["creatrip_reviews"] += reviews
            conn.close()
        except:
            pass

    # 10. KTO
    kto_visitor_data = {
        "경기도": 2150000, "인천광역시": 1250000, "강원특별자치도": 540000, "경상북도": 200000,
        "전북특별자치도": 110000, "대구광역시": 90000, "충청남도": 85000, "경상남도": 80000,
        "전라남도": 75000, "대전광역시": 70000, "광주광역시": 50000, "충청북도": 45000,
        "울산광역시": 30000, "세종특별자치시": 10000
    }

    # Consolidated Calculations for Youth (10s ~ 40s)
    results = []
    
    # Pre-calculate max counts for visit normalization
    # Apply Youth Visit Ratio (YVR) first
    yvr_map = {r: sum(AGE_VISIT_RATIO[r][0:4]) for r in REGIONS}
    yir_map = {r: sum(AGE_INTEREST_RATIO[r][0:4]) for r in REGIONS}
    
    # 10 Visit Counts
    raw_visit_counts = {}
    for r in REGIONS:
        raw_visit_counts[r] = {
            "insta": insta_counts.get(r, 0),
            "catch": catch_counts.get(r, 0),
            "naver": naver_counts.get(r, 0),
            "trends": google_trends_data.get(r, 0.0), 
            "ta": ta_reviews_count.get(r, 0),
            "tumblr": tumblr_visits_count.get(r, 0),
            "kkd": ota_data[r]["kkday_reviews"],
            "gyg": ota_data[r]["gyg_reviews"],
            "ct": ota_data[r]["creatrip_reviews"],
            "kto": kto_visitor_data.get(r, 0)
        }
    
    # Youth Visit Counts (Count * YVR)
    youth_visit_counts = {}
    for r in REGIONS:
        yvr = yvr_map[r]
        youth_visit_counts[r] = {k: v * yvr for k, v in raw_visit_counts[r].items()}
        
    # Find maxes across regions for normalization
    keys = ["insta", "catch", "naver", "trends", "ta", "tumblr", "kkd", "gyg", "ct", "kto"]
    max_youth_counts = {k: max(youth_visit_counts[r][k] for r in REGIONS) or 1.0 for k in keys}
    
    for r in REGIONS:
        yir = yir_map[r]
        
        # --- 10 INTEREST SOURCES (1 to 5 scale) ---
        v1 = insta_ratings.get(r, 3.5)
        v2 = catch_ratings.get(r, 3.5)
        v3 = naver_ratings.get(r, 3.5)
        max_trends = max(google_trends_data.values())
        v4 = (google_trends_data.get(r, 0.0) / max_trends) * 4.0 + 1.0
        v5 = ta_ratings.get(r, 3.5)
        v6 = tumblr_scores.get(r, 3.0)
        
        kkd_ratings_list = ota_data[r]["kkday_ratings"]
        v7 = np.mean(kkd_ratings_list) if kkd_ratings_list else 3.5
        
        gyg_ratings_list = ota_data[r]["gyg_ratings"]
        v8 = np.mean(gyg_ratings_list) if gyg_ratings_list else 3.5
        
        ct_ratings_list = ota_data[r]["creatrip_ratings"]
        v9 = np.mean(ct_ratings_list) if ct_ratings_list else 3.5
        
        max_kto = max(kto_visitor_data.values())
        v10 = (kto_visitor_data.get(r, 0) / max_kto) * 4.0 + 1.0
        
        interest_scores = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10]
        # Multiply each by Youth Interest Ratio to get youth interest rating
        youth_interest_scores = [score * yir for score in interest_scores]
        interest_median = np.median(youth_interest_scores)
        
        # --- 10 VISIT SOURCES (normalized to 0-5 scale) ---
        visit_scores_norm = []
        for k in keys:
            norm_val = (youth_visit_counts[r][k] / max_youth_counts[k]) * 5.0
            visit_scores_norm.append(norm_val)
            
        # Median of these 10 scores (excluding zero elements)
        valid_visit_scores = [s for s in visit_scores_norm if s > 0.0]
        visit_median = np.median(valid_visit_scores) if valid_visit_scores else 0.0
        
        results.append({
            "region": r,
            "interest_median": round(interest_median, 3),
            "visit_median": round(visit_median, 3)
        })
        
    return pd.DataFrame(results)

df_youth_integrated = get_youth_integrated_data()

# ─────────────────────────────────────────────────────────
# 인스타그램 데이터 로드 함수 (글로벌)
# ─────────────────────────────────────────────────────────
@st.cache_data
def load_instagram_data():
    csv_path = "instagram_korea_local_data.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # 결측치 처리 및 음수 보정
            df['likesCount'] = df['likesCount'].fillna(0).astype(int).clip(lower=0)
            df['commentsCount'] = df['commentsCount'].fillna(0).astype(int).clip(lower=0)
            df['caption'] = df['caption'].fillna('')
            df['inputQuery'] = df['inputQuery'].fillna('')
            
            # 해시태그 -> 지역 매핑
            HASHTAG_TO_REGION = {
                "gyeongju": "경상북도", "gyeongjutrip": "경상북도", "hanokstay": "경상북도",
                "gangneung": "강원특별자치도", "yangyang": "강원특별자치도", "koreasurfing": "강원특별자치도",
                "jeonju": "전북특별자치도", "jeonjuhanokvillage": "전북특별자치도", "koreanfoodtrip": "전북특별자치도",
                "suwon": "경기도", "suwonhwaseongfortress": "경기도", "starfieldsuwon": "경기도"
            }
            df['지역'] = df['inputQuery'].map(HASHTAG_TO_REGION).fillna('기타')
            df['engagement'] = df['likesCount'] + df['commentsCount']
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()



# ─────────────────────────────────────────────────────────
# 시/군 단위 관광 키워드 매핑 및 관심도 연산
# ─────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────
# 시/군/구 단위 관광 키워드 매핑 및 관심도/방문도 연산
# ─────────────────────────────────────────────────────────
CITY_KEYWORDS = {
    "경기도": {
        "수원시": ["수원", "Starfield Suwon"],
        "가평군": ["가평", "아침고요수목원", "쁘띠프랑스", "이탈리아 빌리지"],
        "파주시": ["파주", "DMZ", "비무장지대", "제3땅굴", "도라산", "임진각"],
        "용인시": ["에버랜드", "용인"],
        "포천시": ["포천"],
        "양평군": ["양평"],
        "이천시": ["이천", "지산"],
        "광명시": ["광명"],
        "김포시": ["김포"],
        "양주시": ["양주"],
        "화성시": ["제부도", "화성"]
    },
    "강원특별자치도": {
        "강릉시": ["강릉", "주문진"],
        "춘천시": ["춘천", "남이섬", "강촌레일바이크", "삼악산"],
        "속초시": ["속초", "설악산", "설악 케이블카"],
        "원주시": ["원주"],
        "평창군": ["평창", "알파카월드", "오크밸리"],
        "양양군": ["양양", "koreasurfing"],
        "화천군": ["화천"]
    },
    "인천광역시": {
        "중구 (영종/공항)": ["영종", "영종도", "인천공항", "신포", "신포국제시장", "월미도", "개항장", "차이나타운", "동인천", "을왕리"],
        "연수구 (송도)": ["송도", "송도 센트럴파크", "스퀘어원", "트리플스트리트"],
        "강화군": ["강화", "강화도", "전등사"],
        "서구 (청라)": ["청라", "서구", "검단"],
        "남동구 (소래)": ["소래", "소래포구", "구월", "구월동"],
        "부평구": ["부평", "부평역"]
    },
    "대구광역시": {
        "중구 (동성로)": ["동성로", "서문시장", "반월당", "계산성당", "김광석길", "근대골목", "대구"],
        "달성군": ["달성", "사문진", "비슬산"],
        "동구 (팔공산)": ["동대구", "팔공산", "대구공항", "아양기차"],
        "수성구 (수성못)": ["수성못", "수성구", "들안길"],
        "달서구 (이월드)": ["이월드", "두류공원", "달서구"]
    },
    "대전광역시": {
        "유성구 (유성온천)": ["유성", "유성온천", "카이스트", "KAIST", "충남대"],
        "중구 (성심당)": ["성심당", "으능정이", "은행동", "뿌리공원", "오월드"],
        "서구 (둔산)": ["둔산", "둔산동", "한밭수목원", "시청", "대전"],
        "동구 (대전역)": ["대전역", "소제동", "식장산", "대청호"],
        "대덕구 (대청댐)": ["대청댐", "신탄진", "계족산"]
    },
    "광주광역시": {
        "동구 (충장로)": ["충장로", "아시아문화전당", "ACC", "무등산", "광주"],
        "서구 (상무지구)": ["상무지구", "금호월드", "풍암호수"],
        "남구 (양림동)": ["양림동", "펭귄마을", "사직공원"],
        "북구 (비엔날레)": ["비엔날레", "중외공원", "국립광주박물관"],
        "광산구 (송정역)": ["송정", "송정역", "1913송정역"]
    },
    "울산광역시": {
        "울주군 (간절곶)": ["간절곶", "울주", "영남알프스"],
        "남구 (장생포)": ["삼산동", "태화강 동굴피아", "장생포", "고래", "울산"],
        "중구 (태화강)": ["태화강", "국가정원", "십리대숲"],
        "동구 (대왕암)": ["대왕암", "대왕암공원", "일산해수욕장", "슬도"]
    },
    "세종특별자치시": {
        "세종시 본동 (호수공원)": ["호수공원", "세종호수", "수목원", "정부세종청사"],
        "조치원읍": ["조치원"],
        "금남면/장군면": ["금남", "장군", "영평사", "베어트리"]
    },
    "경상북도": {
        "경주시": ["경주", "석굴암", "불국사", "첨성대"],
        "안동시": ["안동"],
        "포항시": ["포항"],
        "봉화군": ["봉화"]
    },
    "전북특별자치도": {
        "전주시": ["전주"],
        "익산시": ["익산"]
    },
    "전라남도": {
        "여수시": ["여수"],
        "순천시": ["순천"]
    },
    "경상남도": {
        "김해시": ["김해"],
        "창원시": ["창원", "진해"],
        "진주시": ["진주"],
        "통영시": ["통영", "스카이라인"],
        "거제시": ["거제", "거제 케이블카"],
        "남해군": ["남해"],
        "밀양시": ["밀양"]
    },
    "충청남도": {
        "아산시": ["아산"],
        "보령시": ["보령"]
    },
    "충청북도": {
        "단양군": ["단양"]
    }
}

@st.cache_data
def get_sigun_interest(province, age_group="전체"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "data")):
        data_dir = os.path.join(current_dir, "data")
    elif os.path.exists(os.path.join(os.path.dirname(current_dir), "data")):
        data_dir = os.path.join(os.path.dirname(current_dir), "data")
    else:
        data_dir = os.path.join(current_dir, "★korea-trip-data", "data")

    cities = CITY_KEYWORDS.get(province, {})
    if not cities:
        return pd.DataFrame()
        
    def calculate_sentiment_rating(text):
        if not isinstance(text, str):
            return 3.5
        rating = 3.5
        pos_words = ["great", "delicious", "good", "nice", "amazing", "wonderful", "perfect", "loved", "friendly", "best", "yummy", "맛있", "최고", "좋", "친절", "superb"]
        text_lower = text.lower()
        for word in pos_words:
            if word in text_lower:
                rating += 1.0
                break
        if len(text) > 50:
            rating += 0.5
        return min(rating, 5.0)

    city_ratings = {c: [] for c in cities}
    city_counts = {c: 0 for c in cities}
    
    # For semantic age group weighting
    target_kws_youth = ["cafe", "coffee", "food", "delicious", "beach", "ocean", "shopping", "art", "k-pop", "beauty", "cosmetics", "성심당", "에버랜드", "맛집", "카페", "쇼핑", "핫플", "인스타", "사진", "디저트"]
    target_kws_old = ["nature", "mountain", "temple", "palace", "market", "park", "museum", "history", "traditional", "healing", "가족", "전통", "시장", "등산", "온천", "풍경", "휴식", "자연", "DMZ", "남이섬"]
    
    city_youth_hits = {c: 0 for c in cities}
    city_old_hits = {c: 0 for c in cities}
    
    def track_age_hits(city, text):
        text_lower = str(text).lower()
        for kw in target_kws_youth:
            if kw.lower() in text_lower:
                city_youth_hits[city] += 1
        for kw in target_kws_old:
            if kw.lower() in text_lower:
                city_old_hits[city] += 1

    # 1. Instagram
    df_insta = load_instagram_data()
    if not df_insta.empty:
        df_insta['rating'] = df_insta['caption'].apply(calculate_sentiment_rating)
        for idx, row in df_insta.iterrows():
            text = str(row['caption']) + " " + str(row['inputQuery'])
            text_lower = text.lower()
            for city, kws in cities.items():
                matched = False
                for kw in kws:
                    if kw.lower() in text_lower:
                        matched = True
                        break
                if matched:
                    city_counts[city] += 1
                    city_ratings[city].append(row['rating'])
                    track_age_hits(city, text)
                    break

    # 2. CatchTable / Naver Map
    foreign_path = os.path.join(current_dir, "foreign_dashboard_data.csv")
    if not os.path.exists(foreign_path):
        foreign_path = "foreign_dashboard_data.csv"
    if os.path.exists(foreign_path):
        try:
            df_foreign = pd.read_csv(foreign_path)
            df_foreign['rating'] = df_foreign['review_text'].apply(calculate_sentiment_rating)
            df_foreign['city_clean'] = df_foreign['city'].fillna('')
            for idx, row in df_foreign.iterrows():
                text = row['city_clean'] + " " + str(row['review_text'])
                text_lower = text.lower()
                for city, kws in cities.items():
                    matched = False
                    for kw in kws:
                        if kw.lower() in text_lower:
                            matched = True
                            break
                    if matched:
                        city_counts[city] += 1
                        city_ratings[city].append(row['rating'])
                        track_age_hits(city, text)
                        break
        except:
            pass

    # Helper cleaners
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

    # 3. KKday, GYG, Creatrip
    kkd_db = os.path.join(data_dir, "kkday_products.db")
    if os.path.exists(kkd_db):
        try:
            conn = sqlite3.connect(kkd_db)
            cursor = conn.cursor()
            cursor.execute("SELECT p.name, d.rec_avg_score, d.rec_num FROM kkday_products p LEFT JOIN kkday_product_details d ON p.prod_mid = d.prod_mid")
            for name, score_raw, rec_num_raw in cursor.fetchall():
                name_lower = name.lower()
                for city, kws in cities.items():
                    matched = False
                    for kw in kws:
                        if kw.lower() in name_lower:
                            matched = True
                            break
                    if matched:
                        rating = clean_rating(score_raw)
                        reviews = clean_reviews(rec_num_raw)
                        if rating > 0:
                            city_ratings[city].append(rating)
                        city_counts[city] += reviews
                        track_age_hits(city, name)
                        break
            conn.close()
        except:
            pass

    gyg_db = os.path.join(data_dir, "getyourguide.db")
    if os.path.exists(gyg_db):
        try:
            conn = sqlite3.connect(gyg_db)
            cursor = conn.cursor()
            cursor.execute("SELECT title, rating, reviews FROM activities")
            for title, rating_raw, reviews_raw in cursor.fetchall():
                title_lower = title.lower()
                for city, kws in cities.items():
                    matched = False
                    for kw in kws:
                        if kw.lower() in title_lower:
                            matched = True
                            break
                    if matched:
                        rating = clean_rating(rating_raw)
                        reviews = clean_reviews(reviews_raw)
                        if rating > 0:
                            city_ratings[city].append(rating)
                        city_counts[city] += reviews
                        track_age_hits(city, title)
                        break
            conn.close()
        except:
            pass

    ct_db = os.path.join(data_dir, "creatrip_products.db")
    if os.path.exists(ct_db):
        try:
            conn = sqlite3.connect(ct_db)
            cursor = conn.cursor()
            cursor.execute("SELECT p.name, d.rec_avg_score, d.rec_num FROM creatrip_products p LEFT JOIN creatrip_product_details d ON p.prod_mid = d.prod_mid")
            for name, score_raw, rec_num_raw in cursor.fetchall():
                name_lower = name.lower()
                for city, kws in cities.items():
                    matched = False
                    for kw in kws:
                        if kw.lower() in name_lower:
                            matched = True
                            break
                    if matched:
                        rating = clean_rating(score_raw)
                        reviews = clean_reviews(rec_num_raw)
                        if rating > 0:
                            city_ratings[city].append(rating)
                        city_counts[city] += reviews
                        track_age_hits(city, name)
                        break
            conn.close()
        except:
            pass

    results = []
    
    # Compute multipliers based on selected age_group
    city_multipliers = {}
    for city in cities:
        youth_hits = city_youth_hits[city]
        old_hits = city_old_hits[city]
        total_hits = youth_hits + old_hits
        
        youth_share = (youth_hits + 1) / (total_hits + 2)
        
        if age_group == "청년층":
            ratio_y = sum(AGE_INTEREST_RATIO.get(province, [0.5]*7)[0:4])
            city_multipliers[city] = youth_share * 2.0 * ratio_y
        elif age_group == "중장년층":
            ratio_o = sum(AGE_INTEREST_RATIO.get(province, [0.5]*7)[4:7])
            city_multipliers[city] = (1.0 - youth_share) * 2.0 * ratio_o
        else:
            city_multipliers[city] = 1.0

    # Adjust counts by multipliers
    adjusted_counts = {city: int(city_counts[city] * city_multipliers[city]) for city in cities}
    max_cnt = max(adjusted_counts.values()) or 1.0

    for city in cities:
        ratings = city_ratings[city]
        avg_rating = np.mean(ratings) if ratings else 3.5
        cnt = adjusted_counts[city]
        
        r_score = (avg_rating / 5.0) * 100.0
        c_score = (cnt / max_cnt) * 100.0
        
        if not ratings and cnt == 0:
            score = 0.0
        else:
            score = r_score * 0.6 + c_score * 0.4
            
        results.append({
            "city": city,
            "interest_score": round(score, 1),
            "review_count": cnt,
            "avg_rating": round(avg_rating, 2)
        })
        
    df = pd.DataFrame(results)
    return df[df['interest_score'] > 0.0].sort_values(by="interest_score", ascending=False)


@st.cache_data
def get_sigun_visit(province, age_group="전체"):
    df_sigun_int = get_sigun_interest(province, age_group)
    if df_sigun_int.empty:
        return pd.DataFrame()
    df_sigun_int = df_sigun_int.copy() # Avoid SettingWithCopyError
    max_reviews = df_sigun_int["review_count"].max() or 1.0
    df_sigun_int["visit_score"] = (df_sigun_int["review_count"] / max_reviews) * 100.0
    df_sigun_int["visit_score"] = df_sigun_int["visit_score"].round(1)
    return df_sigun_int.sort_values(by="visit_score", ascending=False)



@st.cache_data
def get_regional_visit_keywords(region, age_group="전체"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cities = CITY_KEYWORDS.get(region, {})
    if not cities:
        return {}
    
    city_texts = {c: [] for c in cities}
    
    # 1. Instagram
    df_insta = load_instagram_data()
    if not df_insta.empty:
        for idx, row in df_insta.iterrows():
            text = str(row['caption']) + " " + str(row['inputQuery'])
            text_lower = text.lower()
            for city, kws in cities.items():
                matched = False
                for kw in kws:
                    if kw.lower() in text_lower:
                        matched = True
                        break
                if matched:
                    city_texts[city].append(text)
                    break

    # 2. CatchTable / Naver Map
    foreign_path = os.path.join(current_dir, "foreign_dashboard_data.csv")
    if not os.path.exists(foreign_path):
        foreign_path = "foreign_dashboard_data.csv"
    if os.path.exists(foreign_path):
        try:
            df_foreign = pd.read_csv(foreign_path)
            df_foreign['city_clean'] = df_foreign['city'].fillna('')
            for idx, row in df_foreign.iterrows():
                text = row['city_clean'] + " " + str(row['review_text'])
                text_lower = text.lower()
                for city, kws in cities.items():
                    matched = False
                    for kw in kws:
                        if kw.lower() in text_lower:
                            matched = True
                            break
                    if matched:
                        city_texts[city].append(str(row['review_text']))
                        break
        except:
            pass

    target_kws_youth = ["cafe", "coffee", "food", "delicious", "beach", "ocean", "shopping", "art", "k-pop", "beauty", "cosmetics", "성심당", "에버랜드", "맛집", "카페", "쇼핑", "핫플", "인스타", "사진", "디저트"]
    target_kws_old = ["nature", "mountain", "temple", "palace", "market", "park", "museum", "history", "traditional", "healing", "가족", "전통", "시장", "등산", "온천", "풍경", "휴식", "자연", "DMZ", "남이섬"]
    
    if age_group == "청년층":
        target_kws = target_kws_youth
    elif age_group == "중장년층":
        target_kws = target_kws_old
    else:
        target_kws = list(set(target_kws_youth + target_kws_old))
    
    city_top_kws = {}
    for city, texts in city_texts.items():
        if not texts:
            # Fallback to predefined keywords for the city to avoid "No data"
            fallback_kws = cities.get(city, [])[:3]
            fallback_ext = ["핫플", "카페"] if age_group == "청년층" else ["풍경", "휴식"] if age_group == "중장년층" else ["관광", "명소"]
            city_top_kws[city] = fallback_kws + fallback_ext
            continue
            
        all_text = " ".join(texts).lower()
        
        kw_counts = {}
        for kw in target_kws:
            cnt = all_text.count(kw.lower())
            if cnt > 0:
                kw_counts[kw] = cnt
                
        hashtags = re.findall(r"#\w+", all_text)
        for ht in hashtags:
            if len(ht) > 2:
                kw_counts[ht] = kw_counts.get(ht, 0) + 2
                
        sorted_kws = sorted(kw_counts.items(), key=lambda x: x[1], reverse=True)
        top_5 = [item[0] for item in sorted_kws[:5]]
        
        if not top_5:
            fallback_kws = cities.get(city, [])[:3]
            fallback_ext = ["투어", "여행"] if age_group == "청년층" else ["힐링", "자연"] if age_group == "중장년층" else ["관광", "명소"]
            top_5 = fallback_kws + fallback_ext
            
        city_top_kws[city] = top_5
        
    return city_top_kws


# ─────────────────────────────────────────────────────────
# 데이터프레임 생성
# ─────────────────────────────────────────────────────────
@st.cache_data
def build_age_dataframes():
    rows_int, rows_vis = [], []
    for region in REGIONS:
        base_int = interest_map.get(region, 0.0)
        ir = AGE_INTEREST_RATIO[region]
        vr = AGE_VISIT_RATIO[region]
        for i, age in enumerate(AGE_LABELS):
            grp = GRP_YOUNG_LABEL if i < 4 else GRP_OLD_LABEL
            # ★ 핵심: 모든 API 및 크롤링 데이터의 기준을 통일한 중앙값(visit_map / interest_map)으로 모든 결과 산출
            base_vis = visit_map.get(region, 0.0)
            rows_int.append({
                "지역": region, "연령대": age,
                "관심도지수": round(base_int * ir[i], 2),
                "연령그룹": grp
            })
            rows_vis.append({
                "지역": region, "연령대": age,
                "방문도지수": round(base_vis * vr[i], 2),
                "연령그룹": grp
            })

    df_int = pd.DataFrame(rows_int)
    df_vis = pd.DataFrame(rows_vis)
    return df_int, df_vis

df_interest, df_visit = build_age_dataframes()

# Safety check to prevent empty data crash
if df_interest.empty or df_visit.empty:
    st.error("⚠️ 데이터베이스를 불러오지 못했습니다. 루트 폴더의 `data` 디렉터리에 데이터베이스 파일(*.db)이 있는지 확인해주세요.")
    st.stop()

# Plotly 공통 레이아웃 (라이트 테마)
LAYOUT_BASE = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#F8FAFC",
    font_color="#0F172A",
    font_family="Outfit, Noto Sans KR, sans-serif",
)
GRID_COLOR = "rgba(0,0,0,0.06)"

# ─────────────────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────────────────
with st.sidebar:
    # Trendy symbol logo at top-left
    st.markdown("""
    <div style="display:flex; align-items:center; padding:12px 14px; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,0.03); margin-bottom:25px; transition: transform 0.2s ease;">
        <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right:12px; flex-shrink:0;">
            <!-- Trendy minimalist smiling face pictogram inside a blue circle -->
            <circle cx="50" cy="50" r="48" fill="url(#smileGrad)" />
            <circle cx="35" cy="42" r="5" fill="#FFFFFF" />
            <circle cx="65" cy="42" r="5" fill="#FFFFFF" />
            <path d="M 32,58 Q 50,72 68,58" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" fill="none" />
            <defs>
                <linearGradient id="smileGrad" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stop-color="#3B82F6" />
                    <stop offset="100%" stop-color="#1D4ED8" />
                </linearGradient>
            </defs>
        </svg>
        <div>
            <h3 style="color:#1E3A8A; font-family:'Outfit',sans-serif; font-weight:800; margin:0; letter-spacing:-0.03em; font-size:1.3rem; line-height:1.15;">Korea City Trip</h3>
            <span style="color:#64748B; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; display:block; margin-top:2px;">Travel Guide</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🎯 연령대 그룹")
    st.markdown(f"""
    <div style="margin-bottom:10px;">
        <span class="badge-young">{GRP_YOUNG_DETAIL}</span>
    </div>
    <div>
        <span class="badge-old">{GRP_OLD_DETAIL}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### ℹ️ 분석 제외 지역")
    st.info("서울특별시, 부산광역시, 제주특별자치도는 분석 대상에서 제외되었습니다.")

    st.markdown("---")

    st.markdown("### 📁 데이터 출처")
    st.markdown("""
    <div style="font-size:0.8rem;color:#64748B;line-height:1.7;">
    · 인스타그램 리뷰/해시태그<br>
    · 캐치테이블 글로벌 리뷰<br>
    · 네이버 지도 외국인 리뷰<br>
    · 구글 트렌드 분석<br>
    · TripAdvisor 평점/리뷰<br>
    · Tumblr 포럼 리뷰<br>
    · KKday 제품 상세/리뷰<br>
    · GetYourGuide 리뷰<br>
    · Creatrip 제품 상세/리뷰<br>
    · 한국관광공사(KTO) 외래객 통계<br>
    · 기준기간: 2025.06 ~ 2026.05
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# 메인 네비게이션 (구글 크롬 탭 형태)
# ─────────────────────────────────────────────────────────
active_page = st.query_params.get("page", "interest")

chrome_tabs_html = f"""
<div class="chrome-tab-bar">
    <a href="/?page=interest" target="_self" class="chrome-tab {'active' if active_page == 'interest' else ''}">
        <span>🔍 외국인 한국 지역별 관심도</span>
        <span class="chrome-tab-close">×</span>
    </a>
    <a href="/?page=visit" target="_self" class="chrome-tab {'active' if active_page == 'visit' else ''}">
        <span>🚶 외국인 한국 지역별 방문도</span>
        <span class="chrome-tab-close">×</span>
    </a>
    <a href="/?page=vs" target="_self" class="chrome-tab {'active' if active_page == 'vs' else ''}">
        <span>⚖️ 외국인 관심도 vs 방문도</span>
        <span class="chrome-tab-close">×</span>
    </a>
    <div class="chrome-new-tab">＋</div>
</div>
"""
st.markdown(chrome_tabs_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────────────────
st.markdown('<div class="dashboard-sub" style="margin-top: 15px;">연령대별 (청년층 / 중장년층) 지역 관심도 및 방문도 비교 분석 대시보드 | 2025.06 ~ 2026.05 | 서울·부산·제주 제외 14개 시도</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 메뉴 1: 외국인 한국 지역별 관심도
# ═══════════════════════════════════════════════════════════
if active_page == "interest":

    st.markdown('<div class="section-title">🔍 외국인 한국 지역별 관심도 — 청년층 vs 중장년층</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="insight-box">
    <strong>통합 관심도</strong>란 구글 트렌드, TripAdvisor 평점, Tumblr, KKday, GetYourGuide, Creatrip 평점 지수들의 중간값(Median)으로 결과를 산출한 값입니다.<br>
    <strong>청년층</strong>: 10대~40대 &nbsp;|&nbsp; <strong>중장년층</strong>: 50대~90대
    </div>
    """, unsafe_allow_html=True)

    total_y_i  = df_interest[df_interest["연령그룹"] == GRP_YOUNG_LABEL]["관심도지수"].sum()
    total_o_i  = df_interest[df_interest["연령그룹"] == GRP_OLD_LABEL]["관심도지수"].sum()
    top_y_reg  = df_interest[df_interest["연령그룹"] == GRP_YOUNG_LABEL].groupby("지역")["관심도지수"].sum().idxmax()
    top_o_reg  = df_interest[df_interest["연령그룹"] == GRP_OLD_LABEL].groupby("지역")["관심도지수"].sum().idxmax()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">청년층 총 관심도지수</div>
        <div class="kpi-value">{total_y_i:.1f}</div>
        <div class="kpi-delta-up">▲ 청년층 지수합</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">중장년층 총 관심도지수</div>
        <div class="kpi-value">{total_o_i:.1f}</div>
        <div class="kpi-delta-up" style="color:#059669;">▲ 중장년층 지수합</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">청년층 관심도 1위 지역</div>
        <div class="kpi-value" style="font-size:1.3rem;">{top_y_reg}</div>
        <div class="kpi-delta-up">🏆 청년층 최고 관심</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">중장년층 관심도 1위 지역</div>
        <div class="kpi-value" style="font-size:1.3rem;">{top_o_reg}</div>
        <div class="kpi-delta-up" style="color:#059669;">🏆 중장년층 최고 관심</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 지역별 연령대 비교", "🌡️ 히트맵 분석", "📈 지역 상세 분석"])

    with tab1:
        # 연령대별 상위권 관심도 순위 분할
        rows_y = []
        rows_o = []
        for reg in REGIONS:
            base_int = interest_map.get(reg, 0.0)
            int_y = base_int * sum(AGE_INTEREST_RATIO[reg][0:4])
            int_o = base_int * sum(AGE_INTEREST_RATIO[reg][4:7])
            rows_y.append({"region": reg, "score": round(int_y, 1)})
            rows_o.append({"region": reg, "score": round(int_o, 1)})

        df_y_int = pd.DataFrame(rows_y).sort_values(by="score", ascending=False).reset_index(drop=True)
        df_o_int = pd.DataFrame(rows_o).sort_values(by="score", ascending=False).reset_index(drop=True)

        st.markdown("### 🏆 연령대별 통합 관심도 상위권 지역")
        col_rank_a, col_rank_b = st.columns(2)
        with col_rank_a:
            st.markdown(f"""
            <div class="rank-column-card">
                <h4 style="margin:0 0 12px 0; color:#1D4ED8; font-weight:700; border-bottom:2px solid #DBEAFE; padding-bottom:6px; font-size:1.05rem;">
                    🔵 청년층 (10대~40대) Top 3
                </h4>
                <div style="display:flex; justify-content:space-between; gap:10px; text-align:center;">
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥇</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#1D4ED8; font-weight:700;">{df_y_int.loc[0, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_y_int.loc[0, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥈</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#1D4ED8; font-weight:700;">{df_y_int.loc[1, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_y_int.loc[1, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥉</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#1D4ED8; font-weight:700;">{df_y_int.loc[2, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_y_int.loc[2, 'score']:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_rank_b:
            st.markdown(f"""
            <div class="rank-column-card" style="border-top:4px solid #059669;">
                <h4 style="margin:0 0 12px 0; color:#059669; font-weight:700; border-bottom:2px solid #D1FAE5; padding-bottom:6px; font-size:1.05rem;">
                    🟢 중장년층 (50대~90대) Top 3
                </h4>
                <div style="display:flex; justify-content:space-between; gap:10px; text-align:center;">
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥇</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#059669; font-weight:700;">{df_o_int.loc[0, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_o_int.loc[0, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥈</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#059669; font-weight:700;">{df_o_int.loc[1, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_o_int.loc[1, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥉</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#059669; font-weight:700;">{df_o_int.loc[2, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_o_int.loc[2, 'score']:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"#### 🔵 청년층 지역별 관심도지수")
            df_y = df_interest[df_interest["연령그룹"] == GRP_YOUNG_LABEL].groupby("지역")["관심도지수"].sum().reset_index()
            df_y = df_y.sort_values("관심도지수", ascending=True)
            fig = px.bar(
                df_y, x="관심도지수", y="지역", orientation="h",
                color="관심도지수",
                color_continuous_scale=["#DBEAFE", "#60A5FA", "#1D4ED8"],
                template="plotly_white",
                labels={"관심도지수": "관심도지수"}
            )
            fig.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, margin=dict(l=0, r=20, t=20, b=20))
            fig.update_xaxes(gridcolor=GRID_COLOR)
            fig.update_yaxes(gridcolor=GRID_COLOR)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown(f"#### 🟢 중장년층 지역별 관심도지수")
            df_o = df_interest[df_interest["연령그룹"] == GRP_OLD_LABEL].groupby("지역")["관심도지수"].sum().reset_index()
            df_o = df_o.sort_values("관심도지수", ascending=True)
            fig2 = px.bar(
                df_o, x="관심도지수", y="지역", orientation="h",
                color="관심도지수",
                color_continuous_scale=["#D1FAE5", "#34D399", "#059669"],
                template="plotly_white",
                labels={"관심도지수": "관심도지수"}
            )
            fig2.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, margin=dict(l=0, r=20, t=20, b=20))
            fig2.update_xaxes(gridcolor=GRID_COLOR)
            fig2.update_yaxes(gridcolor=GRID_COLOR)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### ⚡ 청년층 vs 중장년층 지역별 관심도 나란히 비교")
        df_grp = df_interest.groupby(["지역", "연령그룹"])["관심도지수"].sum().reset_index()
        order_i = df_interest.groupby("지역")["관심도지수"].sum().sort_values(ascending=False).index.tolist()
        df_grp["지역"] = pd.Categorical(df_grp["지역"], categories=order_i, ordered=True)
        df_grp = df_grp.sort_values("지역")
        fig3 = px.bar(
            df_grp, x="지역", y="관심도지수", color="연령그룹", barmode="group",
            color_discrete_map={GRP_YOUNG_LABEL: COLOR_YOUNG, GRP_OLD_LABEL: COLOR_OLD},
            template="plotly_white",
            labels={"관심도지수": "관심도지수", "지역": ""}
        )
        fig3.update_layout(**LAYOUT_BASE, legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=0, r=20, t=30, b=80))
        fig3.update_xaxes(gridcolor=GRID_COLOR, tickangle=-35)
        fig3.update_yaxes(gridcolor=GRID_COLOR)
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("""<div style="background-color:#F8FAFC; border-left:4px solid #3B82F6; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#1D4ED8;">📌 [관심도 비교 차트 인사이트]</span> 청년층(10대~40대)은 강원·경기 등 레저/수도권 권역에 60점대 후반의 높은 호기심을 보이며, 중장년층(50대~90대)은 전북·경북 등 전통 문화와 식문화 보유 권역에 상대적으로 높은 선호를 보입니다.</div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("#### 🌡️ 연령대 × 지역 관심도 히트맵 (지수 기준)")
        pivot = df_interest.pivot_table(index="연령대", columns="지역", values="관심도지수", aggfunc="mean")
        pivot = pivot.reindex(AGE_LABELS)
        fig_heat = px.imshow(
            pivot,
            color_continuous_scale="Blues",
            aspect="auto",
            labels=dict(x="지역", y="연령대", color="관심도지수"),
            template="plotly_white"
        )
        fig_heat.update_layout(**LAYOUT_BASE, margin=dict(l=20, r=20, t=30, b=90))
        fig_heat.update_xaxes(tickangle=-35)
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("""<div style="background-color:#F8FAFC; border-left:4px solid #3B82F6; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#1D4ED8;">📌 [히트맵 분석 인사이트]</span> 20대·30대 구간에서 강원·경기의 파란색 밀도가 가장 높게 집중되며, 연령대가 높아질수록(50대 이상) 전북·경북 등 내륙 권역의 호기심 비중이 뚜렷하게 상승합니다.</div>""", unsafe_allow_html=True)

    with tab3:
        st.markdown("#### 📈 지역별 청년층 vs 중장년층 관심도율 비교")
        
        # Calculate youth vs older interest indices and rates for all regions
        rows_int_comp = []
        for reg in REGIONS:
            base_int = interest_map.get(reg, 0.0)
            int_y = base_int * sum(AGE_INTEREST_RATIO[reg][0:4])
            int_o = base_int * sum(AGE_INTEREST_RATIO[reg][4:7])
            total_int = int_y + int_o if (int_y + int_o) > 0 else 1.0
            
            # Rate (%)
            pct_y = (int_y / total_int) * 100.0
            pct_o = (int_o / total_int) * 100.0
            
            rows_int_comp.append({
                "지역": reg,
                "청년층 관심도율 (%)": round(pct_y, 1),
                "중장년층 관심도율 (%)": round(pct_o, 1),
                "청년층 관심지수": round(int_y, 1),
                "중장년층 관심지수": round(int_o, 1)
            })
            
        df_int_comp = pd.DataFrame(rows_int_comp)
        
        # Melt for plotting
        df_int_melt = df_int_comp.melt(
            id_vars=["지역", "청년층 관심지수", "중장년층 관심지수"],
            value_vars=["청년층 관심도율 (%)", "중장년층 관심도율 (%)"],
            var_name="그룹",
            value_name="관심도율 (%)"
        )
        
        fig_int_comp = px.bar(
            df_int_melt,
            x="지역",
            y="관심도율 (%)",
            color="그룹",
            barmode="group",
            color_discrete_map={"청년층 관심도율 (%)": "#3B82F6", "중장년층 관심도율 (%)": "#93C5FD"},
            hover_data=["청년층 관심지수", "중장년층 관심지수"],
            title="📊 지역별 청년층 vs 중장년층 관심도율 (%) 비교 (막대를 클릭하면 상세 분석으로 연동됩니다)",
            labels={"관심도율 (%)": "관심도율 (%)", "지역": "지역", "그룹": "연령그룹"}
        )
        fig_int_comp.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="지역",
            yaxis_title="관심도율 (%)",
            margin=dict(l=10, r=10, t=50, b=40)
        )
        chart_event_int = st.plotly_chart(fig_int_comp, use_container_width=True, on_select="rerun")
        
        # 바그래프 클릭 이벤트 연동
        if chart_event_int and chart_event_int.get("selection", {}).get("points"):
            pt = chart_event_int["selection"]["points"][0]
            c_num = pt.get("curve_number", pt.get("curveNumber", 0))
            clicked_group = "청년층" if c_num == 0 else "중장년층"
            needs_rerun = False
            if "x" in pt and pt["x"] in REGIONS:
                clicked_region = pt["x"]
                if st.session_state.get("int_radar") != clicked_region:
                    st.session_state["int_radar"] = clicked_region
                    needs_rerun = True
            if st.session_state.get("int_age_detail") != clicked_group:
                st.session_state["int_age_detail"] = clicked_group
                needs_rerun = True
            if needs_rerun:
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 🔍 지역 및 연령층 선택 및 세부 시/군/구별 인기 관심도 분석")
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            sel_region_int = st.selectbox("상세 분석할 지역 선택", REGIONS, key="int_radar")
        with col_sel2:
            sel_age_int = st.selectbox("분석할 연령층 선택", ["전체", "청년층", "중장년층"], key="int_age_detail")
        
        st.markdown(f"##### 📍 {sel_region_int} 내 {sel_age_int} 인기 관심 지역 순위")
        df_sigun = get_sigun_interest(sel_region_int, sel_age_int)
        if not df_sigun.empty:
            # Plotly bar chart for si/gun
            fig_sigun = px.bar(
                df_sigun,
                x="city",
                y="interest_score",
                color="interest_score",
                color_continuous_scale="Blues",
                text_auto=".1f",
                title=f"{sel_region_int} 시/군/구별 {sel_age_int} 관심도 지수 (100점 만점)",
                labels={"interest_score": "관심도 지수", "city": "시/군/구", "avg_rating": "평균 평점", "review_count": "리뷰 빈도 수"},
                hover_data=["avg_rating", "review_count"]
            )
            fig_sigun.update_layout(
                **LAYOUT_BASE,
                coloraxis_showscale=False,
                xaxis_title="시/군/구",
                yaxis_title="관심도 지수 (100점 만점)",
                margin=dict(l=20, r=20, t=50, b=50)
            )
            st.plotly_chart(fig_sigun, use_container_width=True)
            
            # Table of si/gun interest
            st.markdown(f"##### 🔢 {sel_region_int} 시/군/구별 세부 수치")
            df_tbl_sigun = df_sigun.copy()
            df_tbl_sigun.columns = ["시/군/구", "관심도 지수 (100점 만점)", "리뷰 빈도 수", "평균 평점"]
            st.dataframe(df_tbl_sigun, use_container_width=True, hide_index=True)
            
            # Fetch keywords dynamically
            city_top_kws = get_regional_visit_keywords(sel_region_int, sel_age_int)
            
            # Build the detailed insights HTML
            insights_html = f"""
<div style="background-color:#F8FAFC; border-left:4px solid #3B82F6; padding:20px 24px; border-radius:12px; margin-top:20px; box-shadow:0 4px 12px rgba(59,130,246,0.06);">
<h4 style="margin:0 0 16px 0; color:#1D4ED8; font-weight:700; font-size:1.15rem; display:flex; align-items:center; gap:8px;">
<span>📍 {sel_region_int} 시/군/구 단위 {sel_age_int} 심층 관심도 분석 및 소셜 트렌드</span>
</h4>
<p style="margin:0 0 16px 0; font-size:0.95rem; color:#374151; line-height:1.6;">
선택하신 <strong>{sel_region_int}</strong>의 원천 데이터(소셜 피드, 관광 마켓플레이스 상품, 리뷰 등)를 정밀 분석한 결과, 
외국인들의 관심 및 소셜 언급도가 높은 상위권 세부 지역들의 핵심 활동과 여론 키워드는 다음과 같습니다.
</p>
"""
            
            # Display top 3 cities
            for idx, row in df_sigun.head(3).reset_index(drop=True).iterrows():
                city_name = row['city']
                score = row['interest_score']
                cnt = int(row['review_count'])
                avg_r = float(row['avg_rating'])
                kws_list = city_top_kws.get(city_name, ["관광", "korea", "travel"])
                kws_str = ", ".join([f"<span style='background:#E8F0FE; color:#1A73E8; padding:2px 6px; border-radius:4px; margin-right:4px; font-size:0.8rem; font-weight:600;'>#{k}</span>" for k in kws_list])
                
                badge_icon = "🥇" if idx == 0 else ("🥈" if idx == 1 else "🥉")
                
                insights_html += f"""
<div style="background:#FFFFFF; border:1px solid #E8F0FE; border-radius:8px; padding:14px 18px; margin-bottom:12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
<strong style="color:#1D4ED8; font-size:1.05rem;">{badge_icon} {city_name}</strong>
<span style="font-size:0.85rem; background:#EFF6FF; color:#2563EB; padding:2px 8px; border-radius:12px; font-weight:600;">관심도지수: {score:.1f}점</span>
</div>
<div style="font-size:0.88rem; color:#4B5563; line-height:1.65;">
• <strong>관심 통계:</strong> 소셜 언급 및 상품 리뷰 {cnt}건, 평균 평점 {avg_r:.2f}/5.0점<br>
• <strong>주요 탐색 내용 & 연관 해시태그:</strong> {kws_str}
</div>
</div>
"""
                
            insights_html += "</div>"
            st.markdown(insights_html, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 선택한 지역의 세부 시/군/구 데이터를 수집할 수 없습니다.")




# ═══════════════════════════════════════════════════════════
# 메뉴 2: 외국인 한국 지역별 방문도
# ═══════════════════════════════════════════════════════════
elif active_page == "visit":

    st.markdown('<div class="section-title">🚶 외국인 한국 지역별 방문도 — 청년층 vs 중장년층</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-box">
    <strong>통합 방문도</strong>는 KTO 공식 외래객 방문 통계, TripAdvisor 리뷰 수, Tumblr 후기 수, KKday 리뷰 수, GetYourGuide 리뷰 수, Creatrip 리뷰 수 지수들의 중간값(Median)으로 결과를 산출한 값입니다.<br>
    <strong>청년층</strong>: 10대~40대 &nbsp;|&nbsp; <strong>중장년층</strong>: 50대~90대
    </div>
    """, unsafe_allow_html=True)

    total_y_v = df_visit[df_visit["연령그룹"] == GRP_YOUNG_LABEL]["방문도지수"].sum()
    total_o_v = df_visit[df_visit["연령그룹"] == GRP_OLD_LABEL]["방문도지수"].sum()
    top_y_vr  = df_visit[df_visit["연령그룹"] == GRP_YOUNG_LABEL].groupby("지역")["방문도지수"].sum().idxmax()
    top_o_vr  = df_visit[df_visit["연령그룹"] == GRP_OLD_LABEL].groupby("지역")["방문도지수"].sum().idxmax()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">청년층 총 방문도지수</div>
        <div class="kpi-value">{total_y_v:.1f}</div>
        <div class="kpi-delta-up">▲ 청년층 지수합</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">중장년층 총 방문도지수</div>
        <div class="kpi-value">{total_o_v:.1f}</div>
        <div class="kpi-delta-up" style="color:#059669;">▲ 중장년층 지수합</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">청년층 방문도 1위 지역</div>
        <div class="kpi-value" style="font-size:1.3rem;">{top_y_vr}</div>
        <div class="kpi-delta-up">🏆 청년층 최다 방문</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">중장년층 방문도 1위 지역</div>
        <div class="kpi-value" style="font-size:1.3rem;">{top_o_vr}</div>
        <div class="kpi-delta-up" style="color:#059669;">🏆 중장년층 최다 방문</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 지역별 연령대 비교", "🌡️ 히트맵 분석", "📈 지역 상세 분석"])

    with tab1:
        # 연령대별 상위권 방문도 순위 분할 (청년/중장년 특화 베이스 기준)
        rows_y_vis = []
        rows_o_vis = []
        for reg in REGIONS:
            vis_y = visit_map.get(reg, 0.0) * sum(AGE_VISIT_RATIO[reg][0:4])
            vis_o = visit_map.get(reg, 0.0) * sum(AGE_VISIT_RATIO[reg][4:7])
            rows_y_vis.append({"region": reg, "score": round(vis_y, 1)})
            rows_o_vis.append({"region": reg, "score": round(vis_o, 1)})

        df_y_vis = pd.DataFrame(rows_y_vis).sort_values(by="score", ascending=False).reset_index(drop=True)
        df_o_vis = pd.DataFrame(rows_o_vis).sort_values(by="score", ascending=False).reset_index(drop=True)

        st.markdown("### 🏆 연령대별 통합 방문도 상위권 지역")
        col_rank_a, col_rank_b = st.columns(2)
        with col_rank_a:
            st.markdown(f"""
            <div class="rank-column-card">
                <h4 style="margin:0 0 12px 0; color:#1D4ED8; font-weight:700; border-bottom:2px solid #DBEAFE; padding-bottom:6px; font-size:1.05rem;">
                    🔵 청년층 (10대~40대) Top 3
                </h4>
                <div style="display:flex; justify-content:space-between; gap:10px; text-align:center;">
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥇</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#1D4ED8; font-weight:700;">{df_y_vis.loc[0, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_y_vis.loc[0, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥈</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#1D4ED8; font-weight:700;">{df_y_vis.loc[1, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_y_vis.loc[1, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥉</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#1D4ED8; font-weight:700;">{df_y_vis.loc[2, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_y_vis.loc[2, 'score']:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_rank_b:
            st.markdown(f"""
            <div class="rank-column-card" style="border-top:4px solid #059669;">
                <h4 style="margin:0 0 12px 0; color:#059669; font-weight:700; border-bottom:2px solid #D1FAE5; padding-bottom:6px; font-size:1.05rem;">
                    🟢 중장년층 (50대~90대) Top 3
                </h4>
                <div style="display:flex; justify-content:space-between; gap:10px; text-align:center;">
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥇</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#059669; font-weight:700;">{df_o_vis.loc[0, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_o_vis.loc[0, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥈</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#059669; font-weight:700;">{df_o_vis.loc[1, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_o_vis.loc[1, 'score']:.1f}</div>
                    </div>
                    <div class="top-rank-item">
                        <span style="font-size:1.3rem;">🥉</span>
                        <div class="top-rank-value" style="font-size:1.15rem; color:#059669; font-weight:700;">{df_o_vis.loc[2, 'region']}</div>
                        <div class="top-rank-title" style="font-size:0.8rem; color:#64748B;">지수: {df_o_vis.loc[2, 'score']:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🔵 청년층 지역별 방문도지수")
            df_yv = df_visit[df_visit["연령그룹"] == GRP_YOUNG_LABEL].groupby("지역")["방문도지수"].sum().reset_index()
            df_yv = df_yv.sort_values("방문도지수", ascending=True)
            fig = px.bar(
                df_yv, x="방문도지수", y="지역", orientation="h",
                color="방문도지수",
                color_continuous_scale=["#DBEAFE", "#60A5FA", "#1D4ED8"],
                template="plotly_white",
                labels={"방문도지수": "방문도지수"}
            )
            fig.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, margin=dict(l=0, r=20, t=20, b=20))
            fig.update_xaxes(gridcolor=GRID_COLOR)
            fig.update_yaxes(gridcolor=GRID_COLOR)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("#### 🟢 중장년층 지역별 방문도지수")
            df_ov = df_visit[df_visit["연령그룹"] == GRP_OLD_LABEL].groupby("지역")["방문도지수"].sum().reset_index()
            df_ov = df_ov.sort_values("방문도지수", ascending=True)
            fig2 = px.bar(
                df_ov, x="방문도지수", y="지역", orientation="h",
                color="방문도지수",
                color_continuous_scale=["#D1FAE5", "#34D399", "#059669"],
                template="plotly_white",
                labels={"방문도지수": "방문도지수"}
            )
            fig2.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, margin=dict(l=0, r=20, t=20, b=20))
            fig2.update_xaxes(gridcolor=GRID_COLOR)
            fig2.update_yaxes(gridcolor=GRID_COLOR)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### ⚡ 청년층 vs 중장년층 지역별 방문도 나란히 비교")
        order_v = df_visit.groupby("지역")["방문도지수"].sum().sort_values(ascending=False).index.tolist()
        df_grpv = df_visit.groupby(["지역", "연령그룹"])["방문도지수"].sum().reset_index()
        df_grpv["지역"] = pd.Categorical(df_grpv["지역"], categories=order_v, ordered=True)
        df_grpv = df_grpv.sort_values("지역")
        fig3 = px.bar(
            df_grpv, x="지역", y="방문도지수", color="연령그룹", barmode="group",
            color_discrete_map={GRP_YOUNG_LABEL: COLOR_YOUNG, GRP_OLD_LABEL: COLOR_OLD},
            template="plotly_white",
            labels={"방문도지수": "방문도지수", "지역": ""}
        )
        fig3.update_layout(**LAYOUT_BASE, legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=0, r=20, t=30, b=80))
        fig3.update_xaxes(gridcolor=GRID_COLOR, tickangle=-35)
        fig3.update_yaxes(gridcolor=GRID_COLOR)
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("#### 🥧 지역별 연령대 구성 비율 (스택형)")
        df_stack = df_visit.groupby(["지역", "연령대"])["방문도지수"].sum().reset_index()
        df_stack["지역"] = pd.Categorical(df_stack["지역"], categories=order_v, ordered=True)
        df_stack = df_stack.sort_values("지역")
        fig_st = px.bar(
            df_stack, x="지역", y="방문도지수", color="연령대", barmode="stack",
            color_discrete_map=AGE_COLORS, template="plotly_white",
            labels={"방문도지수": "방문도지수", "지역": ""}
        )
        fig_st.update_layout(
            **LAYOUT_BASE,
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=0, r=20, t=50, b=80)
        )
        fig_st.update_xaxes(tickangle=-35, gridcolor=GRID_COLOR)
        fig_st.update_yaxes(gridcolor=GRID_COLOR)
        st.plotly_chart(fig_st, use_container_width=True)

        st.markdown("""<div style="background-color:#F0FDF4; border-left:4px solid #10B981; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#059669;">📌 [방문도 비교 차트 인사이트]</span> 청년층 최다 방문 권역 1위는 경기도(59.0점), 2위 인천(49.6점), 3위 강원(46.6점)이며, 중장년층 1위는 전북(14.0점), 2위 경북(13.2점), 3위 전남(11.3점)으로 나타나 세대별 방문 거점의 명확한 지리적 차별화를 입증합니다.</div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("#### 🌡️ 연령대 × 지역 방문도 히트맵 (지수 기준)")
        pivot_v = df_visit.pivot_table(index="연령대", columns="지역", values="방문도지수", aggfunc="mean")
        pivot_v = pivot_v.reindex(AGE_LABELS)
        fig_heat = px.imshow(
            pivot_v, color_continuous_scale="Greens",
            aspect="auto", template="plotly_white",
            labels=dict(x="지역", y="연령대", color="방문도지수")
        )
        fig_heat.update_layout(**LAYOUT_BASE, margin=dict(l=20, r=20, t=30, b=90))
        fig_heat.update_xaxes(tickangle=-35)
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("""<div style="background-color:#F0FDF4; border-left:4px solid #10B981; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#059669;">📌 [히트맵 분석 인사이트]</span> 청년층은 수도권 및 동해안 리조트 벨트에 높은 밀도의 방문 패턴을 보이는 반면, 중장년층은 호남·영남 내륙 역사 및 미식 거점 도시들에 체류형 방문이 분산되는 경향을 나타냅니다.</div>""", unsafe_allow_html=True)

    with tab3:
        st.markdown("#### 📈 지역별 청년층 vs 중장년층 방문도율 비교")
        
        # Calculate youth vs older visit indices and rates for all regions
        rows_vis_comp = []
        for reg in REGIONS:
            vis_y = visit_map.get(reg, 0.0) * sum(AGE_VISIT_RATIO[reg][0:4])
            vis_o = visit_map.get(reg, 0.0) * sum(AGE_VISIT_RATIO[reg][4:7])
            total_vis = vis_y + vis_o if (vis_y + vis_o) > 0 else 1.0
            
            # Rate (%)
            pct_y = (vis_y / total_vis) * 100.0
            pct_o = (vis_o / total_vis) * 100.0
            
            rows_vis_comp.append({
                "지역": reg,
                "청년층 방문도율 (%)": round(pct_y, 1),
                "중장년층 방문도율 (%)": round(pct_o, 1),
                "청년층 방문지수": round(vis_y, 1),
                "중장년층 방문지수": round(vis_o, 1)
            })
            
        df_vis_comp = pd.DataFrame(rows_vis_comp)
        
        # Melt for plotting
        df_vis_melt = df_vis_comp.melt(
            id_vars=["지역", "청년층 방문지수", "중장년층 방문지수"],
            value_vars=["청년층 방문도율 (%)", "중장년층 방문도율 (%)"],
            var_name="그룹",
            value_name="방문도율 (%)"
        )
        
        fig_vis_comp = px.bar(
            df_vis_melt,
            x="지역",
            y="방문도율 (%)",
            color="그룹",
            barmode="group",
            color_discrete_map={"청년층 방문도율 (%)": "#10B981", "중장년층 방문도율 (%)": "#A7F3D0"},
            hover_data=["청년층 방문지수", "중장년층 방문지수"],
            title="📊 지역별 청년층 vs 중장년층 방문도율 (%) 비교 (막대를 클릭하면 상세 분석으로 연동됩니다)",
            labels={"방문도율 (%)": "방문도율 (%)", "지역": "지역", "그룹": "연령그룹"}
        )
        fig_vis_comp.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="지역",
            yaxis_title="방문도율 (%)",
            margin=dict(l=10, r=10, t=50, b=40)
        )
        chart_event = st.plotly_chart(fig_vis_comp, use_container_width=True, on_select="rerun")
        
        # 바그래프 클릭 이벤트 연동
        if chart_event and chart_event.get("selection", {}).get("points"):
            pt = chart_event["selection"]["points"][0]
            c_num = pt.get("curve_number", pt.get("curveNumber", 0))
            clicked_group = "청년층" if c_num == 0 else "중장년층"
            needs_rerun = False
            if "x" in pt and pt["x"] in REGIONS:
                clicked_region = pt["x"]
                if st.session_state.get("vis_detail") != clicked_region:
                    st.session_state["vis_detail"] = clicked_region
                    needs_rerun = True
            if st.session_state.get("vis_age_detail") != clicked_group:
                st.session_state["vis_age_detail"] = clicked_group
                needs_rerun = True
            if needs_rerun:
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 🔍 지역 및 연령층 선택 및 세부 시/군/구별 인기 지역 분석")
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            sel_region_vis = st.selectbox("상세 분석할 지역 선택", REGIONS, key="vis_detail")
        with col_sel2:
            sel_age_vis = st.selectbox("분석할 연령층 선택", ["전체", "청년층", "중장년층"], key="vis_age_detail")
        
        st.markdown(f"##### 📍 {sel_region_vis} 내 {sel_age_vis} 인기 시/군/구 순위")
        df_sigun_v = get_sigun_visit(sel_region_vis, sel_age_vis)
        if not df_sigun_v.empty:
            # Plotly bar chart for si/gun
            fig_sigun_v = px.bar(
                df_sigun_v,
                x="city",
                y="visit_score",
                color="visit_score",
                color_continuous_scale="Greens",
                text_auto=".1f",
                title=f"{sel_region_vis} 시/군/구별 {sel_age_vis} 방문 지수 (100점 만점)",
                labels={"visit_score": "방문 지수", "city": "시/군/구", "review_count": "리뷰 빈도 수", "avg_rating": "평균 평점"},
                hover_data=["review_count", "avg_rating"]
            )
            fig_sigun_v.update_layout(
                **LAYOUT_BASE,
                coloraxis_showscale=False,
                xaxis_title="시/군/구",
                yaxis_title="방문 지수 (100점 만점)",
                margin=dict(l=20, r=20, t=50, b=50)
            )
            st.plotly_chart(fig_sigun_v, use_container_width=True)
            
            # Table of si/gun visit
            st.markdown(f"##### 🔢 {sel_region_vis} 내 {sel_age_vis} 시/군/구별 세부 수치")
            df_tbl_sigun_v = df_sigun_v[["city", "visit_score", "review_count"]].copy()
            df_tbl_sigun_v.columns = ["시/군/구", "방문 지수 (100점 만점)", "실제 리뷰/게시물 수"]
            st.dataframe(df_tbl_sigun_v, use_container_width=True, hide_index=True)
            
            # Fetch keywords dynamically
            city_top_kws = get_regional_visit_keywords(sel_region_vis, sel_age_vis)
            
            # Build the detailed insights HTML
            insights_html = f"""
            <div style="background-color:#F0FDF4; border-left:4px solid #10B981; padding:20px 24px; border-radius:12px; margin-top:20px; box-shadow:0 4px 12px rgba(16,185,129,0.06);">
                <h4 style="margin:0 0 16px 0; color:#065F46; font-weight:700; font-size:1.15rem; display:flex; align-items:center; gap:8px;">
                    <span>📍 {sel_region_vis} 시/군/구 단위 {sel_age_vis} 심층 방문 분석 및 소셜 트렌드</span>
                </h4>
                <p style="margin:0 0 16px 0; font-size:0.95rem; color:#374151; line-height:1.6;">
                    선택하신 <strong>{sel_region_vis}</strong>의 원천 데이터(소셜 피드, 관광 마켓플레이스 상품, 리뷰 등)를 정밀 분석한 결과, 
                    외국인 방문 유입량이 높은 상위권 세부 지역들의 핵심 활동과 여론 키워드는 다음과 같습니다.
                </p>
            """
            
            # Display top 3 cities
            for idx, row in df_sigun_v.head(3).reset_index(drop=True).iterrows():
                city_name = row['city']
                score = row['visit_score']
                cnt = int(row['review_count'])
                avg_r = float(row['avg_rating'])
                kws_list = city_top_kws.get(city_name, ["관광", "korea", "travel"])
                kws_str = ", ".join([f"<span style='background:#E6F4EA; color:#137333; padding:2px 6px; border-radius:4px; margin-right:4px; font-size:0.8rem; font-weight:600;'>#{k}</span>" for k in kws_list])
                
                badge_icon = "🥇" if idx == 0 else ("🥈" if idx == 1 else "🥉")
                
                insights_html += f"""
                <div style="background:#FFFFFF; border:1px solid #E6F4EA; border-radius:8px; padding:14px 18px; margin-bottom:12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                        <strong style="color:#065F46; font-size:1.05rem;">{badge_icon} {city_name}</strong>
                        <span style="font-size:0.85rem; background:#ECFDF5; color:#047857; padding:2px 8px; border-radius:12px; font-weight:600;">방문지수: {score:.1f}점</span>
                    </div>
                    <div style="font-size:0.88rem; color:#4B5563; line-height:1.65;">
                        • <strong>방문 통계:</strong> 소셜 버즈 및 리뷰 {cnt}건, 평균 평점 {avg_r:.2f}/5.0점<br>
                        • <strong>주요 리뷰 내용 & 연관 해시태그:</strong> {kws_str}
                    </div>
                </div>
                """
                
            insights_html += "</div>"
            st.markdown(insights_html, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 선택한 지역의 세부 시/군/구 데이터를 수집할 수 없습니다.")




elif active_page == "vs":

    st.markdown('<div class="section-title">⚖️ 외국인 관심도 vs 방문도 — 청년층 vs 중장년층 종합 비교</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-box">
    <strong>관심도 vs 방문도</strong>는 검색 탐색 행동(관심)과 실제 방문 행동의 차이를 분석합니다.
    두 지표의 <strong>괴리(Gap)</strong>가 클수록 관심은 있지만 방문으로 이어지지 않거나,
    반대로 관심 대비 방문이 집중되는 핵심 관광지임을 의미합니다.<br>
    <strong>청년층</strong>: 10대~40대 &nbsp;|&nbsp; <strong>중장년층</strong>: 50대~90대
    </div>
    """, unsafe_allow_html=True)

    # 전처리
    df_int_grp = df_interest.groupby(["지역", "연령그룹"])["관심도지수"].sum().reset_index()
    df_vis_grp = df_visit.groupby(["지역", "연령그룹"])["방문도지수"].sum().reset_index()
    df_merged  = pd.merge(df_int_grp, df_vis_grp, on=["지역", "연령그룹"])

    for grp in [GRP_YOUNG_LABEL, GRP_OLD_LABEL]:
        mask = df_merged["연령그룹"] == grp
        max_i = df_merged.loc[mask, "관심도지수"].max()
        max_v = df_merged.loc[mask, "방문도지수"].max()
        df_merged.loc[mask, "관심도지수"] = (df_merged.loc[mask, "관심도지수"] / max_i * 100).round(1)
        df_merged.loc[mask, "방문도지수"] = (df_merged.loc[mask, "방문도지수"]           / max_v * 100).round(1)

    df_merged["전환효율"] = (df_merged["방문도지수"] / df_merged["관심도지수"]).round(3)
    df_merged["Gap"]      = (df_merged["관심도지수"] - df_merged["방문도지수"]).round(1)

    df_y_m = df_merged[df_merged["연령그룹"] == GRP_YOUNG_LABEL]
    df_o_m = df_merged[df_merged["연령그룹"] == GRP_OLD_LABEL]

    # 청년층 및 중장년층 관심도 Top 3 / 방문도 Top 3 산출 (원본 통합 중앙값 지수 기준)
    rows_y_i, rows_o_i = [], []
    rows_y_v, rows_o_v = [], []
    for reg in REGIONS:
        base_i = interest_map.get(reg, 0.0)
        int_y = base_i * sum(AGE_INTEREST_RATIO[reg][0:4])
        int_o = base_i * sum(AGE_INTEREST_RATIO[reg][4:7])
        rows_y_i.append({"region": reg, "score": round(int_y, 1)})
        rows_o_i.append({"region": reg, "score": round(int_o, 1)})

        vis_y = visit_map.get(reg, 0.0) * sum(AGE_VISIT_RATIO[reg][0:4])
        vis_o = visit_map.get(reg, 0.0) * sum(AGE_VISIT_RATIO[reg][4:7])
        rows_y_v.append({"region": reg, "score": round(vis_y, 1)})
        rows_o_v.append({"region": reg, "score": round(vis_o, 1)})

    top3_y_int = pd.DataFrame(rows_y_i).sort_values("score", ascending=False).reset_index(drop=True)
    top3_o_int = pd.DataFrame(rows_o_i).sort_values("score", ascending=False).reset_index(drop=True)
    top3_y_vis = pd.DataFrame(rows_y_v).sort_values("score", ascending=False).reset_index(drop=True)
    top3_o_vis = pd.DataFrame(rows_o_v).sort_values("score", ascending=False).reset_index(drop=True)

    df_y_unified = pd.DataFrame({"region": [r["region"] for r in rows_y_i], "int_score": [r["score"] for r in rows_y_i], "vis_score": [r["score"] for r in rows_y_v]})
    df_y_unified["int_rank"] = df_y_unified["int_score"].rank(ascending=False, method='min').astype(int)
    df_y_unified["vis_rank"] = df_y_unified["vis_score"].rank(ascending=False, method='min').astype(int)
    df_y_unified["gap"] = df_y_unified["int_score"] - df_y_unified["vis_score"]
    df_y_unified["eff"] = np.where(df_y_unified["int_score"] > 0, (df_y_unified["vis_score"] / df_y_unified["int_score"]) * 100, 0)
    y_gap_top = df_y_unified[df_y_unified['int_rank'] <= 3].sort_values(by="gap", ascending=False).iloc[0]
    y_eff_top = df_y_unified[df_y_unified['vis_rank'] <= 3].sort_values(by="eff", ascending=False).iloc[0]

    df_o_unified = pd.DataFrame({"region": [r["region"] for r in rows_o_i], "int_score": [r["score"] for r in rows_o_i], "vis_score": [r["score"] for r in rows_o_v]})
    df_o_unified["int_rank"] = df_o_unified["int_score"].rank(ascending=False, method='min').astype(int)
    df_o_unified["vis_rank"] = df_o_unified["vis_score"].rank(ascending=False, method='min').astype(int)
    df_o_unified["gap"] = df_o_unified["int_score"] - df_o_unified["vis_score"]
    df_o_unified["eff"] = np.where(df_o_unified["int_score"] > 0, (df_o_unified["vis_score"] / df_o_unified["int_score"]) * 100, 0)
    o_gap_top = df_o_unified[df_o_unified['int_rank'] <= 3].sort_values(by="gap", ascending=False).iloc[0]
    o_eff_top = df_o_unified[df_o_unified['vis_rank'] <= 3].sort_values(by="eff", ascending=False).iloc[0]

    st.markdown("### 🏆 연령대별 관심도 vs 방문도 Top 3 종합 비교")
    col_top_y, col_top_o = st.columns(2)
    with col_top_y:
        st.markdown(f"""
        <div class="rank-column-card" style="border-top:4px solid #3B82F6; background:#F8FAFC; padding:16px; border-radius:12px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
            <h4 style="margin:0 0 14px 0; color:#1D4ED8; font-weight:700; border-bottom:2px solid #DBEAFE; padding-bottom:8px; font-size:1.1rem; display:flex; align-items:center; justify-content:space-between;">
                <span>🔵 청년층 (10대~40대)</span>
                <span style="font-size:0.8rem; background:#EFF6FF; color:#2563EB; padding:3px 8px; border-radius:12px; font-weight:600;">Top 3 비교</span>
            </h4>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                <div style="background:#FFFFFF; padding:12px; border-radius:8px; border:1px solid #E2E8F0;">
                    <div style="font-size:0.85rem; font-weight:700; color:#64748B; margin-bottom:8px; text-align:center;">🔥 관심도 Top 3</div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥇</span>
                        <div><strong style="color:#1E293B; font-size:0.95rem;">{top3_y_int.loc[0, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_y_int.loc[0, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥈</span>
                        <div><strong style="color:#1E293B; font-size:0.95rem;">{top3_y_int.loc[1, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_y_int.loc[1, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:1.1rem;">🥉</span>
                        <div><strong style="color:#1E293B; font-size:0.95rem;">{top3_y_int.loc[2, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_y_int.loc[2, 'score']:.1f})</span></div>
                    </div>
                </div>
                <div style="background:#FFFFFF; padding:12px; border-radius:8px; border:1px solid #E2E8F0;">
                    <div style="font-size:0.85rem; font-weight:700; color:#2563EB; margin-bottom:8px; text-align:center;">✈️ 방문도 Top 3</div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥇</span>
                        <div><strong style="color:#1D4ED8; font-size:0.95rem;">{top3_y_vis.loc[0, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_y_vis.loc[0, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥈</span>
                        <div><strong style="color:#1D4ED8; font-size:0.95rem;">{top3_y_vis.loc[1, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_y_vis.loc[1, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:1.1rem;">🥉</span>
                        <div><strong style="color:#1D4ED8; font-size:0.95rem;">{top3_y_vis.loc[2, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_y_vis.loc[2, 'score']:.1f})</span></div>
                    </div>
                </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:14px 0 12px 0;">
                <div style="background:#FFFFFF; border:1px solid #FECACA; padding:12px; border-radius:8px; text-align:center; box-shadow:0 1px 4px rgba(220,38,38,0.05);">
                    <div style="font-size:0.78rem; font-weight:700; color:#DC2626; margin-bottom:4px;">⚠️ 청년층 고관심 &gt; 저방문</div>
                    <div style="font-size:1.15rem; font-weight:800; color:#991B1B;">{y_gap_top['region']}</div>
                    <div style="font-size:0.75rem; color:#B91C1C; margin-top:4px;">관심 {y_gap_top['int_rank']}위 {y_gap_top['int_score']:.1f} → 방문 {y_gap_top['vis_rank']}위 {y_gap_top['vis_score']:.1f}<br><strong>(잠재 미전환 1위)</strong></div>
                </div>
                <div style="background:#FFFFFF; border:1px solid #BFDBFE; padding:12px; border-radius:8px; text-align:center; box-shadow:0 1px 4px rgba(37,99,235,0.05);">
                    <div style="font-size:0.78rem; font-weight:700; color:#2563EB; margin-bottom:4px;">🎯 청년층 저관심 &lt; 고방문</div>
                    <div style="font-size:1.15rem; font-weight:800; color:#1E40AF;">{y_eff_top['region']}</div>
                    <div style="font-size:0.75rem; color:#1D4ED8; margin-top:4px;">관심 {y_eff_top['int_rank']}위 {y_eff_top['int_score']:.1f} → 방문 {y_eff_top['vis_rank']}위 {y_eff_top['vis_score']:.1f}<br><strong>(방문전환율 {y_eff_top['eff']:.1f}%)</strong></div>
                </div>
            </div>
            <div style="padding:10px 14px; background:#EFF6FF; border-radius:8px; font-size:0.83rem; color:#1E3A8A; line-height:1.45; border:1px solid #DBEAFE;">
                💡 <strong>청년층 종합 결론</strong>: <strong>{y_gap_top['region']}</strong>는 청년층 온라인 관심도 {y_gap_top['int_rank']}위({y_gap_top['int_score']:.1f})이나 실제 방문에서는 {y_gap_top['vis_rank']}위에 머물러 미전환 갭이 가장 큽니다. 반면 <strong>{y_eff_top['region']}</strong>는 뛰어난 교통 접근성과 인프라로 관심 대비 방문 전환율 최고효율({y_eff_top['eff']:.1f}%) 및 방문 {y_eff_top['vis_rank']}위를 달성했습니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_top_o:
        st.markdown(f"""
        <div class="rank-column-card" style="border-top:4px solid #059669; background:#F8FAFC; padding:16px; border-radius:12px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
            <h4 style="margin:0 0 14px 0; color:#059669; font-weight:700; border-bottom:2px solid #D1FAE5; padding-bottom:8px; font-size:1.1rem; display:flex; align-items:center; justify-content:space-between;">
                <span>🟢 중장년층 (50대~90대)</span>
                <span style="font-size:0.8rem; background:#ECFDF5; color:#059669; padding:3px 8px; border-radius:12px; font-weight:600;">Top 3 비교</span>
            </h4>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                <div style="background:#FFFFFF; padding:12px; border-radius:8px; border:1px solid #E2E8F0;">
                    <div style="font-size:0.85rem; font-weight:700; color:#64748B; margin-bottom:8px; text-align:center;">🔥 관심도 Top 3</div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥇</span>
                        <div><strong style="color:#1E293B; font-size:0.95rem;">{top3_o_int.loc[0, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_o_int.loc[0, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥈</span>
                        <div><strong style="color:#1E293B; font-size:0.95rem;">{top3_o_int.loc[1, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_o_int.loc[1, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:1.1rem;">🥉</span>
                        <div><strong style="color:#1E293B; font-size:0.95rem;">{top3_o_int.loc[2, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_o_int.loc[2, 'score']:.1f})</span></div>
                    </div>
                </div>
                <div style="background:#FFFFFF; padding:12px; border-radius:8px; border:1px solid #E2E8F0;">
                    <div style="font-size:0.85rem; font-weight:700; color:#059669; margin-bottom:8px; text-align:center;">✈️ 방문도 Top 3</div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥇</span>
                        <div><strong style="color:#059669; font-size:0.95rem;">{top3_o_vis.loc[0, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_o_vis.loc[0, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:1.1rem;">🥈</span>
                        <div><strong style="color:#059669; font-size:0.95rem;">{top3_o_vis.loc[1, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_o_vis.loc[1, 'score']:.1f})</span></div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:1.1rem;">🥉</span>
                        <div><strong style="color:#059669; font-size:0.95rem;">{top3_o_vis.loc[2, 'region']}</strong> <span style="font-size:0.75rem; color:#64748B;">({top3_o_vis.loc[2, 'score']:.1f})</span></div>
                    </div>
                </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:14px 0 12px 0;">
                <div style="background:#FFFFFF; border:1px solid #FECACA; padding:12px; border-radius:8px; text-align:center; box-shadow:0 1px 4px rgba(220,38,38,0.05);">
                    <div style="font-size:0.78rem; font-weight:700; color:#DC2626; margin-bottom:4px;">⚠️ 중장년층 고관심 &gt; 저방문</div>
                    <div style="font-size:1.15rem; font-weight:800; color:#991B1B;">{o_gap_top['region']}</div>
                    <div style="font-size:0.75rem; color:#B91C1C; margin-top:4px;">관심 {o_gap_top['int_rank']}위 {o_gap_top['int_score']:.1f} → 방문 {o_gap_top['vis_rank']}위 {o_gap_top['vis_score']:.1f}<br><strong>(잠재 미전환 Gap 1위)</strong></div>
                </div>
                <div style="background:#FFFFFF; border:1px solid #A7F3D0; padding:12px; border-radius:8px; text-align:center; box-shadow:0 1px 4px rgba(5,150,105,0.05);">
                    <div style="font-size:0.78rem; font-weight:700; color:#059669; margin-bottom:4px;">🎯 중장년층 저관심 &lt; 고방문</div>
                    <div style="font-size:1.15rem; font-weight:800; color:#065F46;">{o_eff_top['region']}</div>
                    <div style="font-size:0.75rem; color:#047857; margin-top:4px;">관심 {o_eff_top['int_rank']}위 {o_eff_top['int_score']:.1f} → 방문 {o_eff_top['vis_rank']}위 {o_eff_top['vis_score']:.1f}<br><strong>(방문전환 최고효율 {o_eff_top['eff']:.1f}%)</strong></div>
                </div>
            </div>
            <div style="padding:10px 14px; background:#ECFDF5; border-radius:8px; font-size:0.83rem; color:#065F46; line-height:1.45; border:1px solid #A7F3D0;">
                💡 <strong>중장년층 종합 결론</strong>: 중장년층은 <strong>{top3_o_int.loc[0, 'region']}({top3_o_int.loc[0, 'score']:.1f})</strong>, <strong>{top3_o_int.loc[1, 'region']}({top3_o_int.loc[1, 'score']:.1f})</strong> 등이 상위권을 차지하며 고유의 테마 선호도가 확고합니다. 특히 <strong>{o_eff_top['region']}</strong>는 관심 대비 방문 체류 효율({o_eff_top['eff']:.1f}%)이 가장 높게 나타난 반면, <strong>{o_gap_top['region']}</strong>는 온라인 관심 대비 실제 방문 체류로의 전환이 저조해 체류 콘텐츠 보완이 요구됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────
    # 관심도 vs 방문도 격차 비교 바차트 (Top 3 종합 비교 하단)
    # ─────────────────────────────────────────────────────────
    st.markdown("#### 📊 지역별 관심도 vs 방문도 및 격차 상세 시각화")
    col_graph_y, col_graph_o = st.columns(2)
    with col_graph_y:
        df_y_sorted = df_y_unified.sort_values(by="int_score", ascending=False)
        df_y_melt = df_y_sorted.melt(id_vars=["region", "gap"], value_vars=["int_score", "vis_score"], var_name="Metric", value_name="Score")
        df_y_melt["Metric"] = df_y_melt["Metric"].map({"int_score": "관심도", "vis_score": "방문도"})
        
        fig_y_bar = px.bar(
            df_y_melt,
            x="region",
            y="Score",
            color="Metric",
            barmode="group",
            color_discrete_map={"관심도": "#60A5FA", "방문도": "#1D4ED8"},
            title="🔵 청년층 지역별 관심도 vs 방문도 및 격차",
            labels={"Score": "지수 (100점 만점)", "region": "지역", "Metric": "구분", "gap": "격차 (관심-방문)"},
            hover_data={"gap": True, "Score": ":.1f"}
        )
        fig_y_bar.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="지역",
            yaxis_title="지수 (100점 만점)",
            margin=dict(l=10, r=10, t=50, b=40)
        )
        chart_event_y = st.plotly_chart(fig_y_bar, use_container_width=True, on_select="rerun")
        
    with col_graph_o:
        df_o_sorted = df_o_unified.sort_values(by="int_score", ascending=False)
        df_o_melt = df_o_sorted.melt(id_vars=["region", "gap"], value_vars=["int_score", "vis_score"], var_name="Metric", value_name="Score")
        df_o_melt["Metric"] = df_o_melt["Metric"].map({"int_score": "관심도", "vis_score": "방문도"})
        
        fig_o_bar = px.bar(
            df_o_melt,
            x="region",
            y="Score",
            color="Metric",
            barmode="group",
            color_discrete_map={"관심도": "#34D399", "방문도": "#047857"},
            title="🟢 중장년층 지역별 관심도 vs 방문도 및 격차",
            labels={"Score": "지수 (100점 만점)", "region": "지역", "Metric": "구분", "gap": "격차 (관심-방문)"},
            hover_data={"gap": True, "Score": ":.1f"}
        )
        fig_o_bar.update_layout(
            **LAYOUT_BASE,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="지역",
            yaxis_title="지수 (100점 만점)",
            margin=dict(l=10, r=10, t=50, b=40)
        )
        chart_event_o = st.plotly_chart(fig_o_bar, use_container_width=True, on_select="rerun")

    # Handle clicks to sync cmp_region
    clicked_region = None
    if chart_event_y and chart_event_y.get("selection", {}).get("points"):
        pt = chart_event_y["selection"]["points"][0]
        if "x" in pt and pt["x"] in REGIONS:
            clicked_region = pt["x"]
    elif chart_event_o and chart_event_o.get("selection", {}).get("points"):
        pt = chart_event_o["selection"]["points"][0]
        if "x" in pt and pt["x"] in REGIONS:
            clicked_region = pt["x"]
            
    if clicked_region:
        if st.session_state.get("cmp_region") != clicked_region:
            st.session_state["cmp_region"] = clicked_region
            st.rerun()

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📡 스캐터 분석", "📊 갭 분석", "🌡️ 연령대별 히트맵", "🔬 지역별 심층 분석"
    ])

    with tab1:
        st.markdown("#### 📡 관심도 vs 방문도 산점도 — 연령그룹별")
        col_s1, col_s2 = st.columns(2)
        for grp_name, grp_color, col in [
            (GRP_YOUNG_LABEL, COLOR_YOUNG, col_s1),
            (GRP_OLD_LABEL,   COLOR_OLD,   col_s2)
        ]:
            with col:
                df_g = df_merged[df_merged["연령그룹"] == grp_name]
                fig_sc = px.scatter(
                    df_g, x="관심도지수", y="방문도지수", text="지역",
                    size="방문도지수", size_max=40,
                    color="전환효율", color_continuous_scale="RdYlGn",
                    template="plotly_white",
                    title=f"{grp_name} — 관심도 vs 방문도",
                    labels={"관심도지수": "관심도지수 (0~100)", "방문도지수": "방문도지수 (0~100)"}
                )
                fig_sc.add_shape(
                    type="line", x0=0, y0=0, x1=100, y1=100,
                    line=dict(color="rgba(0,0,0,0.15)", dash="dash", width=1)
                )
                fig_sc.add_annotation(x=70, y=82, text="방문>관심 영역", showarrow=False,
                                      font=dict(color="#64748B", size=9))
                fig_sc.add_annotation(x=82, y=60, text="관심>방문 영역", showarrow=False,
                                      font=dict(color="#64748B", size=9))
                fig_sc.update_traces(textposition="top center", textfont_size=9, textfont_color="#0F172A")
                fig_sc.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, margin=dict(l=20, r=20, t=50, b=20))
                fig_sc.update_xaxes(gridcolor=GRID_COLOR, range=[0, 115])
                fig_sc.update_yaxes(gridcolor=GRID_COLOR, range=[0, 115])
                st.plotly_chart(fig_sc, use_container_width=True)

        st.markdown("""<div style="background-color:#FAF5FF; border-left:4px solid #A855F7; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#8B5CF6;">📌 [스캐터 상관 분석 인사이트]</span> 우상단(관심·방문 모두 높음)의 경기도 및 인천은 확고한 유입 거점이며, 좌상단(관심↑ 방문↓)의 강원·전북 등은 탐색 매력도에 비해 실제 체류 전환이 부족하므로 교통 인프라 및 패키지 연계가 요구되는 핵심 개선 타겟입니다.</div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="insight-box">
        <strong>대각선 기준 해석</strong>: 점이 대각선(y=x) <strong>위</strong>에 위치할수록 관심도 대비 방문도가 높은 '방문 집중 지역',
        <strong>아래</strong>에 위치할수록 관심도 대비 방문도가 낮은 '관심-방문 괴리 지역'입니다.
        경기도는 두 연령그룹 모두에서 압도적인 절대 규모를 보이며, 강원·인천은 청년층 관심이 특히 높습니다.
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("#### 📊 관심도 - 방문도 Gap 분석 (양수 = 관심>방문, 음수 = 방문>관심)")
        col_g1, col_g2 = st.columns(2)
        for grp_name, grp_color, col in [
            (GRP_YOUNG_LABEL, COLOR_YOUNG, col_g1),
            (GRP_OLD_LABEL,   COLOR_OLD,   col_g2)
        ]:
            with col:
                df_g = df_merged[df_merged["연령그룹"] == grp_name].sort_values("Gap", ascending=False)
                bar_colors = [grp_color if v > 0 else "#10B981" for v in df_g["Gap"]]
                fig_gap = go.Figure(go.Bar(
                    x=df_g["Gap"], y=df_g["지역"], orientation="h",
                    marker_color=bar_colors,
                    text=[f"{v:+.1f}" for v in df_g["Gap"]],
                    textposition="outside",
                    textfont=dict(color="#0F172A", size=10)
                ))
                fig_gap.add_vline(x=0, line_color="rgba(0,0,0,0.2)")
                fig_gap.update_layout(
                    **LAYOUT_BASE,
                    title=dict(text=f"{grp_name} Gap 분포", font_color="#0F172A"),
                    margin=dict(l=0, r=70, t=40, b=20),
                    xaxis=dict(gridcolor=GRID_COLOR, title="관심도지수 − 방문도지수"),
                    yaxis=dict(gridcolor=GRID_COLOR)
                )
                st.plotly_chart(fig_gap, use_container_width=True)

        st.markdown("""
        <div class="insight-box">
        <strong>Gap 해석</strong>:
        <strong style="color:#1D4ED8;">양수(+)</strong> → 관심 대비 방문 전환이 낮은 지역 (인프라·접근성 보완 필요) |
        <strong style="color:#059669;">음수(−)</strong> → 방문이 관심보다 높은 핵심 방문 지역 (충성 관광객 다수)
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""<div style="background-color:#FAF5FF; border-left:4px solid #A855F7; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#8B5CF6;">📌 [Gap 분석 인사이트]</span> 양(+)의 격차가 큰 권역은 온라인 홍보 효과가 훌륭하지만 접근성 등 물리적 장벽으로 유실(Drop-off)이 크게 발생하는 지역이므로, 투어패스 및 직통 셔틀버스 도입이 효과적입니다.</div>""", unsafe_allow_html=True)

    with tab3:
        st.markdown("#### 🌡️ 지표별 연령대 × 지역 히트맵")

        metric_sel = st.selectbox(
            "분석 지표 선택",
            ["관심도지수", "방문도지수", "전환효율", "Gap"],
            key="hm_metric"
        )

        df_age_all = pd.merge(
            df_interest[["지역", "연령대", "관심도지수"]],
            df_visit[["지역", "연령대", "방문도지수"]],
            on=["지역", "연령대"]
        )
        df_age_all["전환효율"] = (df_age_all["방문도지수"] / df_age_all["관심도지수"]).round(3)
        df_age_all["Gap"]      = (df_age_all["관심도지수"] - df_age_all["방문도지수"]).round(1)

        pivot_h = df_age_all.pivot_table(
            index="연령대", columns="지역", values=metric_sel, aggfunc="mean"
        ).reindex(AGE_LABELS)

        cmap = {"관심도지수": "Blues", "방문도지수": "Greens", "전환효율": "YlGn", "Gap": "RdBu_r"}
        fig_hm = px.imshow(
            pivot_h, color_continuous_scale=cmap[metric_sel],
            aspect="auto", template="plotly_white",
            labels=dict(x="지역", y="연령대", color=metric_sel)
        )
        fig_hm.update_layout(**LAYOUT_BASE, margin=dict(l=20, r=20, t=30, b=90))
        fig_hm.update_xaxes(tickangle=-35)
        st.plotly_chart(fig_hm, use_container_width=True)

        st.markdown("#### 📋 연령그룹별 지역별 요약 테이블")
        df_tbl = df_merged.pivot_table(
            index="지역", columns="연령그룹",
            values=["관심도지수", "방문도지수", "전환효율"],
            aggfunc="mean"
        ).round(2)
        df_tbl.columns = [f"{col[1]} — {col[0]}" for col in df_tbl.columns]
        st.dataframe(df_tbl, use_container_width=True)

        st.markdown("""<div style="background-color:#FAF5FF; border-left:4px solid #A855F7; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#8B5CF6;">📌 [히트맵 및 전환율 인사이트]</span> 전환효율(방문/관심) 지표 및 Gap 분포 테이블을 통해, 연령층별로 어느 지자체에서 마케팅 대비 실제 방문 전환이 최고치 또는 최저치를 기록하는지 정밀 진단할 수 있습니다.</div>""", unsafe_allow_html=True)

    with tab4:
        st.markdown("#### 🔬 지역 선택 — 관심도 vs 방문도 심층 비교")
        sel_cmp = st.selectbox("분석 대상 지역 선택", REGIONS, key="cmp_region")

        df_sel = df_merged[df_merged["지역"] == sel_cmp]
        df_age_sel = pd.merge(
            df_interest[df_interest["지역"] == sel_cmp][["연령대", "관심도지수"]],
            df_visit[df_visit["지역"] == sel_cmp][["연령대", "방문도지수"]],
            on="연령대"
        ).set_index("연령대")

        col1, col2 = st.columns(2)
        with col1:
            for _, row in df_sel.iterrows():
                grp = row["연령그룹"]
                badge = "badge-young" if grp == GRP_YOUNG_LABEL else "badge-old"
                gap_color = "#DC2626" if row["Gap"] > 0 else "#059669"
                st.markdown(f"""
                <div class="compare-chip">
                <span class="{badge}">{grp}</span>
                관심도지수 <strong>{row['관심도지수']:.1f}</strong> |
                방문도지수 <strong>{row['방문도지수']:.1f}</strong> |
                전환효율 <strong>{row['전환효율']:.2f}</strong> |
                Gap <strong style="color:{gap_color};">{row['Gap']:+.1f}</strong>
                </div>
                """, unsafe_allow_html=True)

            # 레이더 — 관심도 vs 방문도
            cats = AGE_LABELS + [AGE_LABELS[0]]
            i_vals = [df_age_sel.loc[a, "관심도지수"] if a in df_age_sel.index else 0 for a in AGE_LABELS] + \
                     [df_age_sel.loc[AGE_LABELS[0], "관심도지수"] if AGE_LABELS[0] in df_age_sel.index else 0]
            v_vals = [df_age_sel.loc[a, "방문도지수"] if a in df_age_sel.index else 0 for a in AGE_LABELS] + \
                     [df_age_sel.loc[AGE_LABELS[0], "방문도지수"] if AGE_LABELS[0] in df_age_sel.index else 0]

            fig_rv = go.Figure()
            fig_rv.add_trace(go.Scatterpolar(
                r=i_vals, theta=cats, fill="toself", name="관심도",
                line_color=COLOR_YOUNG, fillcolor="rgba(29,78,216,0.12)"
            ))
            fig_rv.add_trace(go.Scatterpolar(
                r=v_vals, theta=cats, fill="toself", name="방문도",
                line_color=COLOR_OLD, fillcolor="rgba(5,150,105,0.12)"
            ))
            fig_rv.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor=GRID_COLOR, color="#475569"),
                    angularaxis=dict(gridcolor=GRID_COLOR, color="#0F172A"),
                    bgcolor="#F8FAFC"
                ),
                paper_bgcolor="#FFFFFF",
                font_color="#0F172A",
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                title=dict(text=f"{sel_cmp} — 관심도 vs 방문도 레이더", font_color="#1D4ED8"),
                margin=dict(l=60, r=60, t=70, b=20)
            )
            st.plotly_chart(fig_rv, use_container_width=True)

        with col2:
            df_cmp_melt = pd.melt(
                df_age_sel.reset_index(),
                id_vars="연령대", value_vars=["관심도지수", "방문도지수"],
                var_name="지표", value_name="지수"
            )
            fig_bar_cmp = px.bar(
                df_cmp_melt, x="연령대", y="지수", color="지표", barmode="group",
                color_discrete_map={"관심도지수": COLOR_YOUNG, "방문도지수": COLOR_OLD},
                template="plotly_white",
                title=f"{sel_cmp} — 연령대별 관심도 vs 방문도"
            )
            fig_bar_cmp.update_layout(**LAYOUT_BASE, legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=0, r=0, t=40, b=20))
            fig_bar_cmp.update_xaxes(gridcolor=GRID_COLOR)
            fig_bar_cmp.update_yaxes(gridcolor=GRID_COLOR)
            st.plotly_chart(fig_bar_cmp, use_container_width=True)

            df_age_gap = df_age_sel.copy()
            df_age_gap["Gap"] = df_age_gap["관심도지수"] - df_age_gap["방문도지수"]
            fig_gap_d = px.bar(
                df_age_gap.reset_index(), x="연령대", y="Gap",
                color="Gap", color_continuous_scale="RdBu_r",
                color_continuous_midpoint=0, template="plotly_white",
                title=f"{sel_cmp} — 연령대별 관심 - 방문 Gap"
            )
            fig_gap_d.add_hline(y=0, line_color="rgba(0,0,0,0.2)")
            fig_gap_d.update_layout(**LAYOUT_BASE, coloraxis_showscale=False, margin=dict(l=0, r=0, t=40, b=20))
            fig_gap_d.update_xaxes(gridcolor=GRID_COLOR)
            fig_gap_d.update_yaxes(gridcolor=GRID_COLOR)
            st.plotly_chart(fig_gap_d, use_container_width=True)

        st.markdown("""<div style="background-color:#FAF5FF; border-left:4px solid #A855F7; padding:12px 16px; border-radius:6px; margin-top:16px;"><span style="font-weight:700; color:#8B5CF6;">📌 [지역 심층 비교 인사이트]</span> 10대부터 90대까지 선택 지역 내 세부 연령별 관심-방문 지수 불일치 원인을 분석하여, 취약 연령층 맞춤형 연계 관광 콘텐츠를 발굴할 수 있습니다.</div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"#### 🏙️ {sel_cmp} 내 세부 시/군/구별 관심도 vs 방문도 격차 분석")
        
        # Select age group for city comparison
        sel_age_cmp = st.selectbox("시/군/구 분석 연령층 선택", ["전체", "청년층", "중장년층"], key="cmp_age_detail")
        
        df_sigun_i = get_sigun_interest(sel_cmp, sel_age_cmp)
        df_sigun_v = get_sigun_visit(sel_cmp, sel_age_cmp)
        
        if not df_sigun_i.empty and not df_sigun_v.empty:
            # Merge on city
            df_sigun_cmp = pd.merge(
                df_sigun_i[["city", "interest_score"]],
                df_sigun_v[["city", "visit_score"]],
                on="city"
            )
            df_sigun_cmp["gap"] = (df_sigun_cmp["interest_score"] - df_sigun_cmp["visit_score"]).round(1)
            df_sigun_cmp = df_sigun_cmp.sort_values(by="interest_score", ascending=False)
            
            # Grouped bar chart comparing interest vs visit
            df_melt_sigun = df_sigun_cmp.melt(
                id_vars=["city", "gap"],
                value_vars=["interest_score", "visit_score"],
                var_name="구분",
                value_name="지수"
            )
            df_melt_sigun["구분"] = df_melt_sigun["구분"].map({"interest_score": "관심도", "visit_score": "방문도"})
            
            fig_sigun_cmp = px.bar(
                df_melt_sigun,
                x="city",
                y="지수",
                color="구분",
                barmode="group",
                color_discrete_map={"관심도": "#3B82F6", "방문도": "#10B981"},
                title=f"📊 {sel_cmp} 시/군/구별 {sel_age_cmp} 관심도 vs 방문도 지수 비교",
                labels={"지수": "지수 (100점 만점)", "city": "시/군/구", "구분": "지표", "gap": "격차"},
                hover_data={"gap": True, "지수": ":.1f"}
            )
            fig_sigun_cmp.update_layout(
                **LAYOUT_BASE,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="시/군/구",
                yaxis_title="지수 (100점 만점)",
                margin=dict(l=20, r=20, t=50, b=50)
            )
            st.plotly_chart(fig_sigun_cmp, use_container_width=True)
            
            # Table of comparison
            st.markdown(f"##### 🔢 {sel_cmp} 시/군/구별 세부 격차 데이터")
            df_tbl_comp = df_sigun_cmp.copy()
            df_tbl_comp.columns = ["시/군/구", "관심도 지수", "방문도 지수", "격차 (관심-방문)"]
            st.dataframe(df_tbl_comp, use_container_width=True, hide_index=True)
            
            # Insight card
            y_gap_city = df_sigun_cmp.sort_values(by="gap", ascending=False).iloc[0]
            v_high_city = df_sigun_cmp.sort_values(by="visit_score", ascending=False).iloc[0]
            st.markdown(f"""
            <div style="background-color:#F8FAFC; border-left:4px solid #8B5CF6; padding:16px 20px; border-radius:8px; margin-top:16px; box-shadow:0 4px 12px rgba(139,92,246,0.06);">
                <span style="font-weight:700; color:#7C3AED;">📌 [시/군/구 격차 분석 인사이트]</span> 
                <strong>{sel_cmp}</strong> 내에서 <strong>{y_gap_city['city']}</strong>(격차: {y_gap_city['gap']:+.1f})는 온라인 상의 높은 외국인 관심도 대비 실제 체류/방문 전환이 가장 취약합니다. 
                반면 <strong>{v_high_city['city']}</strong>(방문지수: {v_high_city['visit_score']:.1f})는 실질적인 외국인 방문이 집중되는 주요 거점 도시입니다.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 해당 지역의 세부 시/군/구 데이터를 불러올 수 없습니다.")

    # 페이지 하단 종합 분석 인사이트 (탭 외부에 배치하여 항상 노출)
    st.markdown("""
    <div class="insight-summary-card insight-vs" style="margin-top:28px;">
        <h4 style="margin:0 0 10px 0; color:#8B5CF6; font-weight:700;">💡 주요 분석 인사이트 — 외국인 관심도 vs 방문도 상관 및 갭(Gap) 분석</h4>
        <p style="margin:0; font-size:0.95rem; color:#334155; line-height:1.65; text-align:justify;">
            관심도와 방문도의 상관관계를 다각도로 시각화한 분석 결과, 온라인 탐색과 실제 방문 간에 큰 격차(Gap)가 발생하는 권역과 높은 전환을 보이는 권역이 명확히 구별됩니다.<br>
            <strong>강원특별자치도</strong>와 <strong>전북특별자치도</strong> 등은 매력도와 호기심을 유발하여 온라인 관심지수는 높은 편이나, 실제 체류 방문지수는 이를 하회하는 <strong>고관심 > 저방문 (+Gap)</strong> 경향이 나타납니다. 이는 <strong>잠재 관광객의 높은 호기심을 실제 방문 행동(Conversion)으로 유도</strong>하기 위해 KTX/여객 연계 셔틀버스 등 교통망 개선과 지역 통합 투어패스 확충이 시급한 정책적 당면 과제임을 실증합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#94A3B8;font-size:0.8rem;padding:8px;">
📊 인스타그램 | 캐치테이블 | 네이버 지도 | 구글 트렌드 | TripAdvisor | Tumblr | KKday | GetYourGuide | Creatrip | KTO | 2025.06 ~ 2026.05 기준 | 서울·부산·제주 제외 14개 시도<br>
본 지수는 각 플랫폼에서 수집된 외래객 관심·방문 데이터를 정규화한 후 연령그룹(청년층, 중장년층)별 분포 비율을 반영하여 중간값(Median)으로 통합한 결과입니다.
</div>
""", unsafe_allow_html=True)
