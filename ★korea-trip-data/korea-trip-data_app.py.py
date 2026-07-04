import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
import os

# 1. 설정
DATA_DIR = r"C:\Users\user\Downloads\ICB\korea trip data\korea-trip-data\data"
API_KEY = "AIzaSyDwDT-n6c3p40G4SWkpi95AWnprNQIHMgM"
SEARCH_ENGINE_ID = "46042a299e6ba4b30"

st.set_page_config(page_title="외국인 관광 분석 대시보드", layout="wide")
st.title("🌏 외국인 관광 관심도 vs 실제 방문 분석")

# 2. 구글 검색량 데이터 수집 함수
def get_google_search_volume(query):
    service = build("customsearch", "v1", developerKey=API_KEY)
    res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
    # 검색 결과 개수를 관심도 지표로 활용
    return int(res.get('searchInformation', {}).get('totalResults', 0))

# 3. 데이터 로드 (로컬 CSV 파일 + API 결합)
@st.cache_data
def load_data():
    # 로컬 경로에서 파일 읽기 (미리 다운로드한 파일이 있다고 가정)
    file_path = os.path.join(DATA_DIR, "regional_visit_data.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        # 파일이 없을 경우 예시 데이터 생성
        df = pd.DataFrame({
            'Region': ['경주', '강릉', '전주'],
            'Visit': [15000, 12000, 18000]
        })
    
    # API를 통한 실시간 관심도 수집 (샘플링)
    df['Interest'] = df['Region'].apply(lambda x: get_google_search_volume(f"{x} travel Korea"))
    return df

df = load_data()

# 4. 대시보드 디자인 (라이트 모드)
col1, col2 = st.columns(2)

with col1:
    st.subheader("지역별 관심도 (Google Search)")
    fig1 = px.bar(df, x='Region', y='Interest', color='Interest', 
                  color_continuous_scale='Blues', text_auto=True)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("지역별 실 방문수 (공공데이터)")
    fig2 = px.bar(df, x='Region', y='Visit', color='Visit', 
                  color_continuous_scale='Greens', text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

# 5. 인사이트 분석
st.divider()
st.subheader("📊 관심도 대비 방문수 차이 분석")
df['Interest_Norm'] = (df['Interest'] / df['Interest'].max()) * 100
df['Visit_Norm'] = (df['Visit'] / df['Visit'].max()) * 100
df['Gap'] = df['Interest_Norm'] - df['Visit_Norm']

fig3 = px.scatter(df, x='Interest_Norm', y='Visit_Norm', color='Region', 
                  size='Interest', hover_data=['Gap'])
st.plotly_chart(fig3, use_container_width=True)

st.info("💡 분석 팁: 우측 하단에 위치한 지역은 관심도는 높으나 실제 방문이 저조한 곳입니다. 해당 지역의 교통 및 숙박 정보를 추가 분석해 보세요.")