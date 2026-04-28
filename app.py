import streamlit as st
import asyncio
import pandas as pd
from scraper import fetch_kakao_golf_data
from datetime import datetime
import os

# 1. 페이지 설정
st.set_page_config(page_title="골프 가성비 비서", page_icon="⛳️", layout="centered")

# [강력한 UI 커스텀 CSS] - 이 부분이 앱의 생명입니다.
st.markdown("""
    <style>
    /* 기본 배경 및 폰트 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .stApp {
        background: linear-gradient(180deg, #FAE100 0%, #F2F2F2 30%, #F2F2F2 100%);
    }
    
    html, body, [class*="css"]  {
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 헤더 및 툴바 제거 */
    header {visibility: hidden;}
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    .main .block-container { padding-top: 2rem !important; }

    /* 캐릭터 섹션 디자인 */
    .char-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 10px;
    }
    
    /* 캐릭터를 감싸는 둥근 원형 배경 (흰 배경 해결책) */
    .char-img-wrapper {
        background-color: white;
        border-radius: 50%;
        padding: 10px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        border: 4px solid #FAE100;
        margin-bottom: -40px;
        z-index: 99;
    }

    /* 카카오톡 스타일 말풍선 */
    .bubble {
        background-color: white;
        padding: 25px 20px 15px 20px;
        border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        width: 90%;
        margin-top: 20px;
    }
    .bubble b { color: #1E1E1E; font-size: 1.2rem; font-weight: 900; }

    /* 입력 박스 카드 디자인 */
    div[data-testid="stForm"] {
        background-color: white !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 25px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        margin-top: 20px;
    }

    /* 위젯 글씨 크기 조정 */
    label p { font-weight: 700 !important; color: #555 !important; }

    /* 전용 검색 버튼 */
    .stButton>button {
        width: 100%;
        border-radius: 18px !important;
        height: 4.5rem !important;
        background-color: #1E1E1E !important;
        color: #FAE100 !important;
        font-size: 1.4rem !important;
        font-weight: 900 !important;
        border: none !important;
        transition: transform 0.2s ease;
        margin-top: 15px;
    }
    .stButton>button:active { transform: scale(0.98); }

    /* 결과 리스트 카드 스타일 */
    .result-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #eee;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .res-name { font-size: 1.3rem; font-weight: 900; color: #1E1E1E; margin-bottom: 5px; }
    .res-price { font-size: 1.2rem; font-weight: 700; color: #FF4D5A; }
    .res-tag { display: inline-block; background: #F2F2F2; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; color: #777; margin-top: 8px; }
    
    /* 예약 버튼(Link) 커스텀 */
    .stLinkButton>a {
        background-color: #FAE100 !important;
        color: #1E1E1E !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        border: none !important;
        width: 100% !important;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 메인 배너 섹션 (캐릭터 일체화)
st.markdown("<div class='char-box'>", unsafe_allow_html=True)
if os.path.exists('character.png'):
    st.markdown("<div class='char-img-wrapper'>", unsafe_allow_html=True)
    st.image('character.png', width=120)
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""
    <div class='bubble'>
        <b>효섭님, 최저가 티타임입니다!</b><br>
        <span style='color:#777; font-size:0.9rem;'>오늘도 즐거운 라운드 되세요 ⛳️</span>
    </div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# 3. 검색 조건 설정 (앱 설정창 스타일)
with st.form("search_form"):
    area_map = {"서울/경기": "1", "강원": "2", "충청": "3", "전라": "4", "경상": "5", "제주": "6"}
    
    selected_areas = st.multiselect("📍 검색 지역", options=list(area_map.keys()), default=["서울/경기"])
    selected_date = st.date_input("📅 라운드 날짜", value=datetime.now())
    
    date_str = selected_date.strftime("%Y-%m-%d")
    submitted = st.form_submit_button("🚀 최저가 검색 시작")

# 4. 결과 출력
if submitted:
    if not selected_areas:
        st.error("지역을 하나 이상 골라주세요!")
    else:
        codes = [area_map[name] for name in selected_areas]
        area_codes_str = ",".join(codes)
        
        with st.spinner("⛳️ AI 비서가 데이터를 분석 중입니다..."):
            try:
                # scraper.py의 함수 호출
                df = asyncio.run(fetch_kakao_golf_data(date=date_str, area_codes=area_codes_str))
                
                if not df.empty:
                    df_sorted = df.sort_values(by='그린피')
                    st.markdown(f"### 🏆 검색 결과 {len(df_sorted)}건")
                    
                    for _, row in df_sorted.iterrows():
                        # 리스트 카드 형태
                        st.markdown(f"""
                            <div class='result-card'>
                                <div class='res-name'>{row['골프장']}</div>
                                <div class='res-price'>{row['그린피']:,}원 <span style='font-size:0.8rem; color:#999;'>부터</span></div>
                                <div class='res-tag'>⏰ 잔여팀: {row['잔여팀']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.link_button(f"👉 {row['골프장']} 바로 예약하기", 
                                      f"https://www.kakao.golf/tee-time?date={date_str.replace('-','')}&area={area_codes_str}")
                    
                    st.balloons()
                else:
                    st.warning("예약 가능한 티타임이 없네요. 날짜를 조정해 보세요!")
            except Exception:
                st.error("서버 접속이 원활하지 않습니다.")

st.markdown("<br><p style='text-align: center; color: #bdc3c7; font-size: 0.8rem;'>© 2026 효섭's AI Golf Assistant</p>", unsafe_allow_html=True)