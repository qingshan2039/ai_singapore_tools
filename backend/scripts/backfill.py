"""一次性历史数据回填脚本

用法：
    python scripts/backfill.py --start 3700 --end 4117

行为：
- 检查 DB 里已有的 draw_no，自动跳过（断点续传）
- 单期失败不中止整个流程，记录到 scrape_logs
- 每期入库时顺便计算 features 和更新 number_stats
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 让 scripts 目录能 import app.*
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import compute_draw_features
from app.config import settings
from app.database import AsyncSessionLocal, engine
from app.models import TotoDraw, TotoDrawFeatures, TotoNumberStats
from app.scraper import TotoScraper

log = logging.getLogger(__name__)


async def get_existing_draws(db: AsyncSession) -> set[int]:
    """已入库的 draw_no 集合"""
    result = await db.execute(select(TotoDraw.draw_no))
    return {row[0] for row in result.all()}


async def insert_draw(db: AsyncSession, parsed, raw_html: str, source_url: str) -> None:
    """入库一期数据 + 特征 + 更新号码统计"""
    row = parsed.to_db_row(raw_html, source_url)
    draw = TotoDraw(**row)
    db.add(draw)

    # 特征预计算
    feats = compute_draw_features(parsed.numbers)
    db.add(TotoDrawFeatures(
        draw_no=parsed.draw_no,
        **feats,
        computed_at=datetime.utcnow().isoformat(),
    ))

    # 号码累计统计 - 更新 1-49 中本期出现的号
    for n in parsed.numbers:
        result = await db.execute(select(TotoNumberStats).where(TotoNumberStats.number == n))
        stat = result.scalar_one()
        stat.total_appearances += 1
        if stat.last_appeared_draw is None or parsed.draw_no > stat.last_appeared_draw:
            stat.last_appeared_draw = parsed.draw_no
            stat.last_appeared_date = parsed.draw_date
        stat.updated_at = datetime.utcnow().isoformat()

    # 附加号也单独计
    result = await db.execute(select(TotoNumberStats).where(TotoNumberStats.number == parsed.additional_no))
    add_stat = result.scalar_one()
    add_stat.as_additional_count += 1

    await db.commit()


async def main(start: int, end: int, delay: float, force: bool, stop_after_misses: int) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    async with AsyncSessionLocal() as db:
        existing = set() if force else await get_existing_draws(db)
        log.info("Already have %d draws in DB", len(existing))

    targets = [n for n in range(start, end + 1) if n not in existing]
    log.info("Will scrape %d draws (skipping %d existing)", len(targets), len(range(start, end + 1)) - len(targets))

    if not targets:
        log.info("Nothing to do.")
        return

    succeeded, failed = 0, 0
    consecutive_misses = 0
    async with TotoScraper() as scraper:
        for draw_no in targets:
            result = await scraper.scrape(draw_no)
            if result.success and result.data and result.raw_html:
                async with AsyncSessionLocal() as db:
                    try:
                        await insert_draw(db, result.data, result.raw_html, f"draw_no={draw_no}")
                        succeeded += 1
                        consecutive_misses = 0
                        log.info("  ✓ Draw %d saved (%dms)", draw_no, result.duration_ms)
                    except Exception as e:
                        log.exception("  ✗ DB insert failed for draw %d: %s", draw_no, e)
                        failed += 1
                        consecutive_misses += 1
            else:
                failed += 1
                consecutive_misses += 1
                log.warning("  ✗ Draw %d failed: %s", draw_no, result.error)

            # 连续失败太多次 = 大概率已经抓到"还不存在的未来期"，提前停止，
            # 避免 --end 给太大时空跑几千个不存在的期（每个都超时重试，极慢）
            if stop_after_misses and consecutive_misses >= stop_after_misses:
                log.info(
                    "Stopping early: %d consecutive misses (likely past the latest available draw)",
                    consecutive_misses,
                )
                break

            await asyncio.sleep(delay)

    log.info("=" * 50)
    log.info("Backfill complete: %d succeeded, %d failed", succeeded, failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True, help="起始期号")
    parser.add_argument("--end", type=int, required=True, help="结束期号")
    parser.add_argument("--delay", type=float, default=5.0, help="单期间隔秒数")
    parser.add_argument("--force", action="store_true", help="忽略已有，全部重抓")
    parser.add_argument(
        "--stop-after-misses",
        type=int,
        default=0,
        help="连续失败 N 次后提前停止（0=不启用）。配合大的 --end 抓增量时强烈建议设 5~8，"
        "否则会空跑大量不存在的未来期",
    )
    args = parser.parse_args()

    asyncio.run(main(args.start, args.end, args.delay, args.force, args.stop_after_misses))
