import streamlit as st
import asyncio
from scraper import fetch_kakao_golf_data

st.set_page_config(page_title="수도권 야간 골프 최저가", layout="wide")

st.title("⛳️ 실시간 야간 라운드 가성비 TOP")

if st.button('실시간 최저가 불러오기'):
    with st.spinner('카카오골프에서 데이터를 수집 중입니다...'):
        # 스크래핑 실행
        df = asyncio.run(fetch_kakao_golf_data())
        
        if not df.empty:
            # 가격순 정렬
            df_sorted = df.sort_values(by='그린피')
            
            st.success(f"총 {len(df)}개의 티타임을 발견했습니다!")
            
            # 보기 좋게 표로 출력
            st.dataframe(df_sorted, use_container_width=True)
        else:
            st.warning("데이터를 가져오지 못했습니다. 잠시 후 다시 시도해주세요.")