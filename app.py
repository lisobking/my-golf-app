import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data
from datetime import datetime
import os

# 1. 페이지 설정
st.set_page_config(page_title="골프 가성비 비서", page_icon="⛳️", layout="centered")

# [초강력 커스텀 CSS] - 이 코드가 효섭님의 앱을 '상용화' 수준으로 만듭니다.
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    /* 전체 배경: 끊김 없는 부드러운 톤 */
    .stApp {
        background: #F8F9FA;
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    /* 헤더 및 툴바 완전 제거 */
    header {visibility: hidden;}
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    .main .block-container { padding-top: 1rem !important; max-width: 500px !important; }

    /* 상단 캐릭터 & 타이틀 섹션 (가장 중요) */
    .brand-section {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 40px 0 20px 0;
        background: linear-gradient(180deg, #FAE100 0%, #FAE100 70%, #F8F9FA 100%);
        margin: -100px -100px 30px -100px;
        border-radius: 0 0 50px 50px;
        box-shadow: 0 10px 30px rgba(250, 225, 0, 0.3);
    }
    
    .char-profile {
        width: 120px;
        height: 120px;
        background: white;
        border-radius: 40px; /* 캐릭터 하얀 박스를 아예 디자인으로 승화 */
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border: 5px solid white;
        margin-bottom: 15px;
        overflow: hidden;
    }

    .main-title {
        color: #1E1E1E;
        font-size: 1.8rem;
        font-weight: 900;
        margin-top: 10px;
    }

    /* 입력 박스 그룹화 (앱 스타일) */
    div[data-testid="stForm"] {
        background-color: white !important;
        border-radius: 30px !important;
        border: none !important;
        padding: 30px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.05) !important;
    }

    /* 검색 버튼: 상용 앱의 터치감 */
    .stButton>button {
        width: 100%;
        border-radius: 20px !important;
        height: 4.5rem !important;
        background: #1E1E1E !important;
        color: #FAE100 !important;
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        border: none !important;
        margin-top: 10px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton>button:active { transform: scale(0.95); opacity: 0.9; }

    /* 결과 카드 디자인 (Premium) */
    .golf-result-card {
        background: white;
        border-radius: 25px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid #F1F3F5;
        box-shadow: 0 10px 20px rgba(0,0,0,0.02);
    }
    .golf-name { font-size: 1.4rem; font-weight: 900; color: #1E1E1E; }
    .golf-price { font-size: 1.2rem; font-weight: 700; color: #FF4D5A; margin: 10px 0; }
    .golf-meta { color: #868E96; font-size: 0.9rem; }

    /* 예약 버튼(Link) 하이엔드 커스텀 */
    .stLinkButton>a {
        background-color: #F8F9FA !important;
        color: #1E1E1E !important;
        border: 1.5px solid #E9ECEF !important;
        border-radius: 15px !important;
        font-weight: 700 !important;
        padding: 12px !important;
        width: 100% !important;
        display: block;
        text-align: center;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 상단 브랜드 섹션 (이미지 하얀 배경 문제를 디자인으로 해결)
st.markdown("""
    <div class='brand-section'>
        <div class='char-profile'>
            <img src='https://i.imgur.com/your_uploaded_image_id.png' width='100'> 
        </div>
        <div class='main-title'>골프 가성비 비서</div>
        <div style='color: #444; font-size: 0.9rem;'>효섭님을 위한 야간 최저가 서칭</div>
    </div>
""", unsafe_allow_html=True)

# ※ 로컬에서는 st.image('character.png')를 쓰고 싶다면 위 HTML 대신 
# 아래 주석 처리된 코드를 brand-section 안에 적절히 배치해야 합니다.
# st.image('character.png', width=120)

# 3. 입력 폼 (모바일 설정창 스타일)
with st.form("search_form"):
    area_map = {"서울/경기": "1", "강원": "2", "충청": "3", "전라": "4", "경상": "5", "제주": "6"}
    
    st.markdown("<p style='font-weight:700; color:#495057; margin-bottom: -15px;'>어디로 가실까요?</p>", unsafe_allow_html=True)
    selected_areas = st.multiselect("", options=list(area_map.keys()), default=["서울/경기"])
    
    st.markdown("<p style='font-weight:700; color:#495057; margin-bottom: -15px; margin-top: 10px;'>언제 가실까요?</p>", unsafe_allow_html=True)
    selected_date = st.date_input("", value=datetime.now())
    
    date_str = selected_date.strftime("%Y-%m-%d")
    submitted = st.form_submit_button("최저가 검색 시작")

# 4. 결과 출력 섹션
if submitted:
    if not selected_areas:
        st.error("지역을 선택해주세요.")
    else:
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        with st.spinner("⛳️ AI 비서가 최적의 조건을 분석 중..."):
            try:
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                if not df.empty:
                    df_sorted = df.sort_values(by='그린피')
                    st.markdown(f"### 🏆 추천 티타임 {len(df_sorted)}건")
                    
                    for _, row in df_sorted.iterrows():
                        st.markdown(f"""
                            <div class='golf-result-card'>
                                <div class='golf-name'>{row['골프장']}</div>
                                <div class='golf-price'>{row['그린피']:,}원 <span style='font-size:0.8rem; color:#adb5bd;'>부터</span></div>
                                <div class='golf-meta'>⏰ {row['잔여팀']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.link_button("상세 정보 및 예약", 
                                      f"https://www.kakao.golf/tee-time?date={date_str.replace('-','')}&area={area_codes_str}")
                    st.balloons()
                else:
                    st.info("예약 가능한 티타임이 없어요. 😂")
            except:
                st.error("서버 연결 실패")

st.markdown("<br><p style='text-align: center; color: #DEE2E6; font-size: 0.8rem;'>© 2026 효섭's AI Golf Assistant</p>", unsafe_allow_html=True)