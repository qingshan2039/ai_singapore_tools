"""Pydantic v2 schemas - API 输入输出格式"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, computed_field


class TotoDrawOut(BaseModel):
    draw_no: int
    draw_date: str
    draw_day: str | None
    numbers: list[int] = Field(description="6 个中奖号码，已排序")
    additional_no: int
    jackpot_amount: float | None
    total_payout: float | None = Field(
        default=None, description="Σ(prize × winners) 跨所有奖级"
    )
    total_payout_corrected: float | None = Field(
        default=None, description="仅 Group 1 的 prize × winners"
    )
    is_snowball: bool = False
    is_cascade: bool = False
    prize_groups: dict | None = None

    @classmethod
    def from_orm(cls, draw: Any) -> "TotoDrawOut":
        return cls(
            draw_no=draw.draw_no,
            draw_date=draw.draw_date,
            draw_day=draw.draw_day,
            numbers=draw.numbers,
            additional_no=draw.additional_no,
            jackpot_amount=draw.jackpot_amount,
            total_payout=draw.total_payout,
            total_payout_corrected=draw.total_payout_corrected,
            is_snowball=bool(draw.is_snowball),
            is_cascade=bool(draw.is_cascade),
            prize_groups=json.loads(draw.prize_groups) if draw.prize_groups else None,
        )


class TotoDrawListResponse(BaseModel):
    items: list[TotoDrawOut]
    total: int
    page: int
    page_size: int


class NumberFrequencyOut(BaseModel):
    number: int
    count: int
    last_seen_draw: int | None
    last_seen_date: str | None
    draws_ago: int | None


class FrequencyResponse(BaseModel):
    frequencies: list[NumberFrequencyOut]
    total_draws: int
    expected_per_number: float = Field(description="理论期望值，用于对比")
    disclaimer: str

    @computed_field
    @property
    def max_count(self) -> int:
        return max((f.count for f in self.frequencies), default=0)
