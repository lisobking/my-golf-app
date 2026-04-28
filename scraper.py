import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import pandas as pd

async def fetch_kakao_golf_data(date: str = None, area_codes: str = "1"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ko-KR"
        )
        page = await context.new_page()

        try:
            # 1. 효섭님이 확인한 진짜 주소 구조 적용
            clean_date = date.replace("-", "") if date else "20260505"
            target_url = f"https://www.kakao.golf/tee-time?date={clean_date}&area={area_codes}"
            
            print(f"🚀 분석된 주소로 접속 시도: {target_url}")
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # 2. 로딩 대기 (골프장 리스트가 뜰 때까지)
            try:
                # 분석 결과 'golf_item' 클래스가 핵심입니다.
                await page.wait_for_selector(".golf_item", timeout=20000)
            except PlaywrightTimeout:
                print("⚠️ 화면에 골프장 정보가 표시되지 않습니다.")
                return pd.DataFrame()

            # 3. 데이터 추출 (분석된 Selector 적용)
            items = await page.query_selector_all(".golf_item")
            data_list = []
            
            for item in items:
                try:
                    # 골프장 이름 (h3.golf_name)
                    name_el = await item.query_selector(".golf_name")
                    name = await name_el.inner_text() if name_el else "이름없음"

                    # 가격 정보 (span.price)
                    price_el = await item.query_selector(".price")
                    price_str = await price_el.inner_text() if price_el else ""
                    
                    # '잔여 티타임이 없어요' 처리
                    if "없어요" in price_str or not price_str:
                        continue
                        
                    # 숫자만 추출 (예: 170,000원~ -> 170000)
                    price = int(''.join(filter(str.isdigit, price_str)))

                    # 잔여 팀수 (span.team_count) - 선택사항
                    team_el = await item.query_selector(".team_count")
                    team_count = await team_el.inner_text() if team_el else "확인불가"

                    data_list.append({
                        "골프장": name.strip(),
                        "그린피": price,
                        "잔여팀": team_count.strip()
                    })
                except Exception as e:
                    continue

            # 4. 결과 정리
            df = pd.DataFrame(data_list).drop_duplicates()
            return df

        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            return pd.DataFrame()
        finally:
            await browser.close()

if __name__ == "__main__":
    # 오늘 알려주신 충청(3) 포함 테스트
    test_date = "2026-05-05"
    df = asyncio.run(fetch_kakao_golf_data(date=test_date, area_codes="1,2,3"))
    
    if not df.empty:
        print("\n✅ 수집 성공! 리스트:")
        print(df.sort_values(by='그린피').to_string(index=False))
    else:
        print("\n❌ 데이터를 찾지 못했습니다.")