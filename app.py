import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data
from datetime import datetime
import os

# 1. 페이지 및 테마 설정
st.set_page_config(
    page_title="골프 가성비 비서", 
    page_icon="🏌️‍♂️", 
    layout="centered"
)

# 캐릭터 이미지 경로 설정
CHARACTER_IMG = 'character.png' # 효섭님이 생성한 AI 캐릭터 이미지 파일명

# [핵심] 카카오 테마 감성을 위한 강력한 커스텀 CSS
st.markdown("""
    <style>
    /* 기본 배경: 카카오 회색 */
    .stApp { background-color: #F2F2F2; }
    
    /* 헤더: 카카오 노란색 */
    header[data-testid="stHeader"] { background-color: #FAE100 !important; }
    
    /* 제목 및 캡션 폰트 */
    h1, h2, h3, p, span { font-family: 'Noto Sans KR', sans-serif !important; }
    h1 { color: #1E1E1E; font-weight: 900 !important; }

    /* 메인 컨테이너 영역 */
    div.block-container { padding-top: 2rem !important; }

    /* 검색 조건 설정 섹션 */
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 15px !important;
        border: 1px solid #E0E0E0 !important;
        margin-bottom: 15px !important;
    }

    /* 하단 버튼 스타일: 카카오 블랙 */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5rem;
        background-color: #1E1E1E !important;
        color: #FAE100 !important;
        font-size: 1.2rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #333333 !important; }
    
    /* 상단 지표(Metric) 카드 */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #E0E0E0;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
    }
    div[data-testid="stMetricValue"] { color: #1E1E1E !important; font-weight: 800; }

    /* [핵심 UX] 결과 리스트 말풍선 스타일 */
    .golf-card {
        background-color: #FAE100; /* 말풍선 노란색 */
        border-radius: 15px 15px 15px 0px; /* 말풍선 모양 */
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #E6D000;
        color: #1E1E1E;
    }
    .golf-card-header { font-size: 1.1rem; font-weight: 800; margin-bottom: 5px; }
    .golf-card-body { font-size: 0.9rem; color: #444; }
    </style>
    """, unsafe_allow_html=True)

# 2. 헤더 및 캐릭터 배치
col_head1, col_head2 = st.columns([1, 4])
with col_head1:
    if os.path.exists(CHARACTER_IMG):
        st.image(CHARACTER_IMG, width=80) # 캐릭터 배치
    else:
        st.text("🏌️‍♂️")
with col_head2:
    st.title("가성비 비서")
    st.markdown("<p style='color: #444; margin-top: -15px;'>실시간 야간 최저가 추천</p>", unsafe_allow_html=True)

# 3. 검색 조건 설정 (사이드바 대신 메인에 깔끔하게)
area_map = {
    "서울/경기": "1", "강원": "2", "충청": "3", 
    "전라": "4", "경상": "5", "제주": "6"
}

st.markdown("### 🔍 어디로 가실까요?")
col1, col2 = st.columns(2)
with col1:
    selected_areas = st.multiselect(
        "지역 선택",
        options=list(area_map.keys()),
        default=["서울/경기"],
        label_visibility="collapsed"
    )
with col2:
    selected_date = st.date_input(
        "날짜 선택", 
        value=datetime.now(),
        min_value=datetime.now(),
        label_visibility="collapsed"
    )
date_str = selected_date.strftime("%Y-%m-%d")

search_btn = st.button("🚀 최저가 티타임 찾기")

# 4. 데이터 표시 및 상세 정보 로직
if search_btn:
    if not selected_areas:
        st.warning("지역을 선택해 주세요.")
    else:
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        # 귀여운 로딩화면
        with st.spinner("⛳️ '가성비 곰'이 티타임을 찾고 있어요..."):
            try:
                # 데이터 수집 (기존 scraper.py 활용)
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                
                if not df.empty:
                    df_sorted = df.sort_values(by='그린피')
                    
                    # 요약 지표 리포트 (카카오 스타일 카드)
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("오늘의 최저가", f"{df_sorted['그린피'].min():,}원")
                    col_m2.metric("검색된 골프장", f"{len(df_sorted)}곳")
                    
                    st.divider()
                    st.markdown("### 🏆 추천 리스트")
                    
                    # [핵심 UX] 카카오톡 말풍선 스타일 리스트
                    for _, row in df_sorted.iterrows():
                        # 말풍선 HTML 구성
                        st.markdown(f"""
                            <div class='golf-card'>
                                <div class='golf-card-header'>{row['골프장']}</div>
                                <div class='golf-card-body'>
                                    💰 <b>{row['그린피']:,}원 부터</b><br>
                                    ⏰ {row['잔여팀']}<br>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 예약 버튼은 말풍선 아래에 깔끔하게
                        st.link_button(f"🔗 {row['골프장']} 예약하기", 
                                      f"https://www.kakao.golf/tee-time?date={date_str.replace('-','')}&area={area_codes_str}")
                        st.markdown("<br>", unsafe_allow_html=True)

                    st.balloons()
                else:
                    # 결과 없음 화면에도 캐릭터 활용
                    col_none1, col_none2 = st.columns([1, 3])
                    with col_none1:
                        if os.path.exists(CHARACTER_IMG):
                            st.image(CHARACTER_IMG, width=100)
                    with col_none2:
                        st.info("현재 예약 가능한 티타임이 없습니다. 다른 날짜를 검색해 보세요! 😂")
                        
            except Exception as e:
                st.error("데이터 수집 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

st.markdown("<br><p style='text-align: center; color: #bdc3c7; font-size: 0.8rem;'>© 2026 효섭's AI Golf Assistant</p>", unsafe_allow_html=True)