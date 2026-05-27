"""分析统计 API - 所有响应都带 disclaimer"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import get_cooccurrence_matrix, get_hot_cold_numbers, get_number_frequencies
from app.database import get_db

router = APIRouter(prefix="/api/toto/analytics", tags=["analytics"])


@router.get("/frequencies")
async def number_frequencies(
    last_n: int | None = Query(None, ge=1, description="只统计最近 N 期；不传则全历史"),
    db: AsyncSession = Depends(get_db),
):
    """1-49 号码出现频率统计"""
    return await get_number_frequencies(db, last_n_draws=last_n)


@router.get("/hot-cold")
async def hot_cold(
    window: int = Query(50, ge=10, le=500),
    top_k: int = Query(10, ge=5, le=20),
    db: AsyncSession = Depends(get_db),
):
    """最近 window 期内的冷热号"""
    return await get_hot_cold_numbers(db, window=window, top_k=top_k)


@router.get("/cooccurrence")
async def cooccurrence(
    last_n: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """49×49 共现矩阵 - 注意前端要做好性能（2401 个数据点）"""
    return await get_cooccurrence_matrix(db, last_n_draws=last_n)
