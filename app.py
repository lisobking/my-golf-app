import streamlit as st
import asyncio
import os
from scraper import fetch_kakao_golf_data

# [추가] Streamlit Cloud 환경에서 브라우저가 없을 경우 설치하는 로직
def install_playwright_browsers():
    try:
        # 브라우저가 이미 있는지 체크 (간이 확인)
        import playwright
        os.system("playwright install chromium")
    except Exception as e:
        st.error(f"브라우저 설치 중 오류 발생: {e}")

st.set_page_config(page_title="수도권 야간 골프 최저가", layout="wide")

# 앱 시작 시 한 번 실행
if 'browser_installed' not in st.session_state:
    with st.spinner('시스템 환경을 설정 중입니다... (최초 1회)'):
        install_playwright_browsers()
        st.session_state['browser_installed'] = True

st.title("⛳️ 실시간 야간 라운드 가성비 TOP")

if st.button('실시간 최저가 불러오기'):
    with st.spinner('카카오골프에서 데이터를 수집 중입니다...'):
        try:
            # 스크래핑 실행
            df = asyncio.run(fetch_kakao_golf_data())
            
            if not df.empty:
                # 가격순 정렬
                df_sorted = df.sort_values(by='그린피')
                st.success(f"총 {len(df)}개의 티타임을 발견했습니다!")
                st.dataframe(df_sorted, use_container_width=True)
            else:
                st.warning("현재 수집 가능한 티타임이 없습니다.")
        except Exception as e:
            st.error(f"데이터 수집 중 오류가 발생했습니다: {e}")
            st.info("로그를 확인하거나 잠시 후 다시 시도해주세요.")