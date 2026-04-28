import streamlit as st
import pandas as pd

st.set_page_config(page_title="수도권 야간 골프", layout="wide")
st.title("⛳️ 야간 라운드 가성비 리스트")

# 임시 데이터 (나중에 수집 데이터로 바꿀 부분)
data = {
    '골프장': ['테스트 골프장'],
    '시간': ['18:00'],
    '그린피': [130000]
}
st.table(pd.DataFrame(data))
st.success("깃허브 연결을 위한 준비가 완료되었습니다!")