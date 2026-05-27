"""统计分析模块 - 为前端图表提供数据。

设计原则：
1. 所有"频率分析"都必须在 API 响应里加 disclaimer 字段，提醒前端展示
2. 计算可以批量缓存（materialized view 思路），不每次都现算
3. 函数纯净，输入 DB session 输出 dict，便于测试

数学免责声明：
彩票每期是独立事件。下方所有统计仅描述历史，无预测能力。
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TotoDraw

DISCLAIMER = (
    "彩票每期开奖在数学上是独立事件。以下统计仅描述历史频率，"
    "不能用于预测下期号码。仅供娱乐参考。"
)


@dataclass
class NumberFrequency:
    number: int
    count: int
    last_seen_draw: int | None
    last_seen_date: str | None
    draws_ago: int | None    # 距离最近一期多少期前


async def get_number_frequencies(
    db: AsyncSession,
    last_n_draws: int | None = None,
) -> dict:
    """每个号码（1-49）的出现频率。

    Args:
        last_n_draws: 只统计最近 N 期；None 表示全历史
    """
    # 拉所有期，按 draw_no 倒序
    stmt = select(TotoDraw).order_by(TotoDraw.draw_no.desc())
    if last_n_draws:
        stmt = stmt.limit(last_n_draws)
    result = await db.execute(stmt)
    draws = result.scalars().all()

    if not draws:
        return {"frequencies": [], "disclaimer": DISCLAIMER, "total_draws": 0}

    latest_draw_no = draws[0].draw_no
    counter: Counter[int] = Counter()
    last_seen: dict[int, TotoDraw] = {}

    for d in draws:
        for n in d.numbers:
            counter[n] += 1
            if n not in last_seen or d.draw_no > last_seen[n].draw_no:
                last_seen[n] = d

    frequencies = []
    for n in range(1, 50):
        last = last_seen.get(n)
        frequencies.append(NumberFrequency(
            number=n,
            count=counter[n],
            last_seen_draw=last.draw_no if last else None,
            last_seen_date=last.draw_date if last else None,
            draws_ago=(latest_draw_no - last.draw_no) if last else None,
        ))

    return {
        "frequencies": [f.__dict__ for f in frequencies],
        "total_draws": len(draws),
        "expected_per_number": len(draws) * 6 / 49,
        "disclaimer": DISCLAIMER,
    }


async def get_hot_cold_numbers(
    db: AsyncSession,
    window: int = 50,
    top_k: int = 10,
) -> dict:
    """冷热号：最近 window 期内最常出现 / 最少出现。"""
    freq_data = await get_number_frequencies(db, last_n_draws=window)
    freqs = sorted(freq_data["frequencies"], key=lambda f: f["count"], reverse=True)

    return {
        "window_draws": window,
        "hot": freqs[:top_k],
        "cold": list(reversed(freqs[-top_k:])),
        "disclaimer": DISCLAIMER,
    }


async def get_cooccurrence_matrix(
    db: AsyncSession,
    last_n_draws: int | None = None,
) -> dict:
    """49×49 共现矩阵：每对号码在历史中一起出现的次数。"""
    stmt = select(TotoDraw).order_by(TotoDraw.draw_no.desc())
    if last_n_draws:
        stmt = stmt.limit(last_n_draws)
    result = await db.execute(stmt)
    draws = result.scalars().all()

    # 用 defaultdict(int)，key 是 (i, j) where i < j
    pairs: dict[tuple[int, int], int] = defaultdict(int)
    for d in draws:
        nums = sorted(d.numbers)
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pairs[(nums[i], nums[j])] += 1

    # 转成 49×49 矩阵
    matrix = [[0] * 49 for _ in range(49)]
    for (a, b), count in pairs.items():
        matrix[a - 1][b - 1] = count
        matrix[b - 1][a - 1] = count

    return {
        "matrix": matrix,
        "total_draws": len(draws),
        "disclaimer": DISCLAIMER,
    }


def compute_draw_features(numbers: list[int]) -> dict:
    """单期号码特征。用于 toto_draw_features 表的入库。"""
    nums = sorted(numbers)
    odd = sum(1 for n in nums if n % 2 == 1)
    small = sum(1 for n in nums if n <= 24)
    consecutive = sum(1 for i in range(len(nums) - 1) if nums[i + 1] - nums[i] == 1)

    return {
        "sum_value": sum(nums),
        "odd_count": odd,
        "even_count": len(nums) - odd,
        "small_count": small,
        "large_count": len(nums) - small,
        "span_value": nums[-1] - nums[0],
        "consecutive_count": consecutive,
        "ac_value": _ac_value(nums),
    }


def _ac_value(nums: list[int]) -> int:
    """AC值（算术复杂度）：所有正差值去重后的个数 - (n - 1)。

    彩票圈常用指标。值越大表示号码越"散"。
    """
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(abs(nums[j] - nums[i]))
    return len(diffs) - (len(nums) - 1)
