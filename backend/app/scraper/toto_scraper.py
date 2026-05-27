"""TOTO 爬虫主模块 - 用 Playwright 处理 JS 渲染。

Singapore Pools 的结果页是 SPA，需要等 JS 执行后 DOM 才有内容。
我们用 Playwright headless Chrome，启动时间约 2 秒，单期抓取约 5 秒。

URL 构造：
    https://www.singaporepools.com.sg/en/product/sr/Pages/toto_results.aspx
        ?sppl=<base64(DrawNumber=XXXX)>

伦理与合规：
    - 单期间隔 ≥ 5 秒（settings.scrape_delay_seconds）
    - User-Agent 标识自己
    - 失败自动重试，但不无限循环
    - 完整 raw_html 落库，便于解析失败时回溯
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime

from playwright.async_api import Browser, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.scraper.parser import ParseError, ParsedTotoDraw, parse_toto_html

log = logging.getLogger(__name__)

BASE_URL = "https://www.singaporepools.com.sg/en/product/sr/Pages/toto_results.aspx"


def build_url(draw_no: int) -> str:
    """期号 -> 完整 URL"""
    encoded = base64.b64encode(f"DrawNumber={draw_no}".encode()).decode()
    return f"{BASE_URL}?sppl={encoded}"


@dataclass
class ScrapeResult:
    draw_no: int
    success: bool
    data: ParsedTotoDraw | None = None
    raw_html: str | None = None
    error: str | None = None
    duration_ms: int = 0


class TotoScraper:
    """单例式爬虫，复用 browser 实例以节省启动开销"""

    def __init__(self) -> None:
        self._browser: Browser | None = None
        self._playwright = None

    async def __aenter__(self) -> "TotoScraper":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, *exc) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        # 必须包括 PlaywrightTimeoutError —— page.wait_for_selector 抛的是它，
        # 不是 builtins.TimeoutError；否则 retry 静默失效
        retry=retry_if_exception_type((TimeoutError, ConnectionError, PlaywrightTimeoutError)),
        reraise=True,
    )
    async def fetch_html(self, draw_no: int) -> str:
        """获取单期 HTML，自动重试"""
        if not self._browser:
            raise RuntimeError("Use `async with TotoScraper() as scraper:`")

        url = build_url(draw_no)
        context = await self._browser.new_context(user_agent=settings.scrape_user_agent)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60_000)
            # 等结果表格出现 - 这是 JS 渲染完成的标志
            await page.wait_for_selector("th.drawDate", timeout=30_000)
            html = await page.content()
            return html
        finally:
            await page.close()
            await context.close()

    async def scrape(self, draw_no: int) -> ScrapeResult:
        """抓取并解析一期。失败不抛异常，返回 ScrapeResult。"""
        start = time.monotonic()
        try:
            html = await self.fetch_html(draw_no)
            data = parse_toto_html(html, draw_no)
            duration_ms = int((time.monotonic() - start) * 1000)
            return ScrapeResult(
                draw_no=draw_no,
                success=True,
                data=data,
                raw_html=html,
                duration_ms=duration_ms,
            )
        except (ParseError, TimeoutError, Exception) as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            log.exception("Scrape failed for draw %d", draw_no)
            return ScrapeResult(
                draw_no=draw_no,
                success=False,
                error=f"{type(e).__name__}: {e}",
                duration_ms=duration_ms,
            )


async def scrape_toto_draw(draw_no: int) -> ScrapeResult:
    """便捷函数：抓一期"""
    async with TotoScraper() as scraper:
        return await scraper.scrape(draw_no)


async def persist_result(result: ScrapeResult) -> None:
    """把抓取结果写入数据库：成功的入 toto_draws，所有尝试都入 scrape_logs。

    使用 session.merge 实现 upsert（按主键 draw_no 覆写），重跑同一期不会冲突。
    """
    # 延迟 import 避免没启服务时也加载 SQLAlchemy
    from app.database import AsyncSessionLocal
    from app.models import ScrapeLog, TotoDraw

    async with AsyncSessionLocal() as session:
        if result.success and result.data:
            row = result.data.to_db_row(
                raw_html=result.raw_html or "",
                source_url=build_url(result.draw_no),
            )
            await session.merge(TotoDraw(**row))

        session.add(
            ScrapeLog(
                target="toto",
                draw_no=result.draw_no,
                status="OK" if result.success else "FAIL",
                error_message=result.error,
                duration_ms=result.duration_ms,
                scraped_at=datetime.utcnow().isoformat(),
            )
        )
        await session.commit()


async def scrape_range(start: int, end: int, delay: float | None = None) -> list[ScrapeResult]:
    """批量抓取 [start, end] 区间，礼貌延迟。"""
    delay = delay if delay is not None else settings.scrape_delay_seconds
    results = []
    async with TotoScraper() as scraper:
        for draw_no in range(start, end + 1):
            result = await scraper.scrape(draw_no)
            results.append(result)
            log.info(
                "Scraped draw %d: %s (%dms)",
                draw_no,
                "OK" if result.success else "FAIL",
                result.duration_ms,
            )
            if draw_no != end:
                await asyncio.sleep(delay)
    return results


# --- CLI -----------------------------------------------------------


def _cli() -> None:
    parser = argparse.ArgumentParser(description="TOTO scraper CLI")
    parser.add_argument("--draw", type=int, help="单期号码")
    parser.add_argument("--start", type=int, help="批量起始期号")
    parser.add_argument("--end", type=int, help="批量结束期号")
    parser.add_argument("--delay", type=float, default=5.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    async def _run_single(draw_no: int) -> None:
        result = await scrape_toto_draw(draw_no)
        if result.success and result.data:
            print(f"Draw {result.data.draw_no} ({result.data.draw_date}, {result.data.draw_day})")
            print(f"  Numbers: {sorted(result.data.numbers)}  Additional: {result.data.additional_no}")
            if result.data.jackpot_amount:
                print(f"  Jackpot:  ${result.data.jackpot_amount:,.2f}")
            else:
                print("  Jackpot: -")
        else:
            print(f"FAILED: {result.error}")
        await persist_result(result)
        print(
            f"  Persisted -> scrape_logs"
            + (" + toto_draws" if result.success else " (no toto_draws row, scrape failed)")
        )

    async def _run_range(start: int, end: int, delay: float) -> None:
        results = await scrape_range(start, end, delay)
        for r in results:
            await persist_result(r)
        ok = sum(1 for r in results if r.success)
        print(f"Done: {ok}/{len(results)} successful (all persisted)")

    if args.draw:
        asyncio.run(_run_single(args.draw))
    elif args.start and args.end:
        asyncio.run(_run_range(args.start, args.end, args.delay))
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
