import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import pandas as pd

async def fetch_kakao_golf_data(date: str = None, area_codes: str = "1"):
    """
    카카오골프 실시간 티타임을 수집하는 엔진
    - date: "2026-05-04" 형식
    - area_codes: "1" (서울/경기), "1,2" (복수선택) 등
    """
    async with async_playwright() as p:
        # 1. 브라우저 실행 (실제 브라우저와 구분하기 어렵게 설정)
        browser = await p.chromium.launch(headless=True)
        
        # 2. 브라우저 컨텍스트 설정 (맥북 유저로 완벽 위장)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        page = await context.new_page()

        try:
            # 3. 날짜 형식 정리 (2026-05-04 -> 20260504)
            clean_date = date.replace("-", "") if date else ""
            
            # 4. 효섭님이 직접 찾아낸 '성공의 주소' 적용
            # area_codes는 "1", "1,2", "1,2,3" 형태로 들어옵니다.
            target_url = f"https://www.kakao.golf/tee-time?date={clean_date}&area={area_codes}"
            
            print(f"🚀 데이터 수집 시작: {target_url}")
            
            # 페이지 접속 및 로드 대기
            await page.goto(target_url, wait_until="load", timeout=60000)
            
            # 데이터 로딩을 위해 5초간 넉넉히 대기
            await page.wait_for_timeout(5000)

            # 5. 데이터 로딩 확인 (가격 표시인 '원'자가 나타날 때까지 대기)
            try:
                await page.wait_for_selector("text='원'", timeout=15000)
            except PlaywrightTimeout:
                print("⚠️ 데이터를 찾지 못했습니다. 날짜에 티가 없거나 차단되었을 수 있습니다.")
                # 실패 시 분석을 위해 현재 화면 저장
                content = await page.content()
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                return pd.DataFrame()

            # 6. 무한 스크롤 (야간 티타임은 아래쪽에 있으므로 3번 정도 내림)
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

            # 7. 데이터 추출 (가장 튼튼한 '텍스트 덩어리 분석' 방식)
            # 카카오 리스트 아이템의 공통 분모인 'Item' 클래스를 찾음
            items = await page.query_selector_all("div[class*='Item']")
            data_list = []
            
            for item in items:
                try:
                    inner_text = await item.inner_text()
                    lines = [l.strip() for l in inner_text.split('\n') if l.strip()]
                    
                    # '원'이 포함된 줄(가격)이 있는지 확인
                    price_line = next((l for l in lines if "원" in l), None)
                    if price_line:
                        # 숫자만 남겨서 정수로 변환
                        price = int(''.join(filter(str.isdigit, price_line)))
                        # 첫 번째 줄은 보통 골프장 이름
                        name = lines[0]
                        # 콜론(:)이 포함된 줄을 시간으로 인식 (예: 18:30)
                        tee_time = next((l for l in lines if ":" in l), "시간미정")
                        
                        data_list.append({
                            "골프장": name,
                            "시간": tee_time,
                            "그린피": price
                        })
                except Exception:
                    continue

            # 8. 중복 제거 및 결과 반환
            df = pd.DataFrame(data_list).drop_duplicates()
            return df

        except Exception as e:
            print(f"❌ 수집 에러 발생: {e}")
            return pd.DataFrame()
        finally:
            # 브라우저 종료 (안 하면 메모리 부족 에러 발생)
            await browser.close()

# 터미널에서 직접 테스트할 때 사용하는 코드
if __name__ == "__main__":
    # 테스트용: 서울/경기(1), 강원(2), 충청(3) 지역의 오늘로부터 7일 뒤 데이터
    import datetime
    test_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"--- 로컬 테스트 시작 ({test_date}) ---")
    result_df = asyncio.run(fetch_kakao_golf_data(date=test_date, area_codes="1,2,3"))
    
    if not result_df.empty:
        print("\n✅ 수집 성공! (가격 낮은 순 리스트)")
        print(result_df.sort_values(by='그린피').to_string(index=False))
    else:
        print("\n❌ 데이터를 가져오지 못했습니다. debug_page.html을 확인하세요.")