import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import pandas as pd

async def fetch_kakao_golf_data(date: str = None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        try:
            # ① 메인 먼저 방문
            await page.goto("https://kakaogolfbooking.com", timeout=30000)
            await page.wait_for_timeout(2000)

            # ② 티타임 페이지 이동
            target_url = "https://kakaogolfbooking.com/reservation/t-time"
            if date:
                target_url += f"?date={date}"
            await page.goto(target_url, wait_until="load", timeout=60000)

            # ③ networkidle 대신 실제 셀렉터 출현을 기다림 (더 안정적)
            #    ← 여기 셀렉터를 개발자도구로 확인한 실제 값으로 교체 필수
            CARD_SELECTOR = ".golf-card-item"
            try:
                await page.wait_for_selector(CARD_SELECTOR, timeout=15000)
            except PlaywrightTimeout:
                # 셀렉터 못 찾으면 HTML 덤프 → 실제 구조 파악용
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print("셀렉터 없음. debug_page.html 열어서 클래스명 확인 필요")
                return pd.DataFrame()

            # ④ 무한스크롤 대응: 새 항목이 없을 때까지 스크롤
            while True:
                prev = len(await page.query_selector_all(CARD_SELECTOR))
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
                curr = len(await page.query_selector_all(CARD_SELECTOR))
                if curr == prev:
                    break

            # ⑤ 데이터 추출
            items = await page.query_selector_all(CARD_SELECTOR)
            data_list = []
            for item in items:
                try:
                    name      = await _text(item, ".name")       # ← 실제 셀렉터로 교체
                    tee_time  = await _text(item, ".time")        # ← 실제 셀렉터로 교체
                    price_str = await _text(item, ".price")       # ← 실제 셀렉터로 교체

                    if not all([name, tee_time, price_str]):
                        continue

                    price = int(price_str.replace(",", "").replace("원", "").strip())
                    data_list.append({"골프장": name, "시간": tee_time, "그린피": price})

                except ValueError:
                    print(f"가격 파싱 실패: {price_str!r}")
                except Exception as e:
                    print(f"항목 처리 오류: {e}")

            return pd.DataFrame(data_list)

        finally:
            await browser.close()  # ⑥ finally로 항상 닫기 (기존엔 누락 가능)


async def _text(el, selector: str) -> str | None:
    node = await el.query_selector(selector)
    return (await node.inner_text()).strip() if node else None


if __name__ == "__main__":
    df = asyncio.run(fetch_kakao_golf_data(date="2025-04-28"))
    print(df.to_string())