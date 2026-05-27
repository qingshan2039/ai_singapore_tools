"""TOTO 开奖数据 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TotoDraw
from app.schemas import TotoDrawListResponse, TotoDrawOut

router = APIRouter(prefix="/api/toto", tags=["toto"])


@router.get("/draws/latest", response_model=TotoDrawOut)
async def get_latest_draw(db: AsyncSession = Depends(get_db)) -> TotoDrawOut:
    """最新一期开奖结果"""
    result = await db.execute(select(TotoDraw).order_by(TotoDraw.draw_no.desc()).limit(1))
    draw = result.scalar_one_or_none()
    if not draw:
        raise HTTPException(status_code=404, detail="No draws in database yet")
    return TotoDrawOut.from_orm(draw)


@router.get("/draws/{draw_no}", response_model=TotoDrawOut)
async def get_draw(draw_no: int, db: AsyncSession = Depends(get_db)) -> TotoDrawOut:
    """单期详情"""
    result = await db.execute(select(TotoDraw).where(TotoDraw.draw_no == draw_no))
    draw = result.scalar_one_or_none()
    if not draw:
        raise HTTPException(status_code=404, detail=f"Draw {draw_no} not found")
    return TotoDrawOut.from_orm(draw)


@router.get("/draws", response_model=TotoDrawListResponse)
async def list_draws(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
    contains_number: int | None = Query(None, ge=1, le=49, description="筛选包含某号码的期"),
    db: AsyncSession = Depends(get_db),
) -> TotoDrawListResponse:
    """历史开奖列表，支持日期 + 号码筛选"""
    stmt = select(TotoDraw)
    count_stmt = select(func.count()).select_from(TotoDraw)

    if date_from:
        stmt = stmt.where(TotoDraw.draw_date >= date_from)
        count_stmt = count_stmt.where(TotoDraw.draw_date >= date_from)
    if date_to:
        stmt = stmt.where(TotoDraw.draw_date <= date_to)
        count_stmt = count_stmt.where(TotoDraw.draw_date <= date_to)
    if contains_number:
        n = contains_number
        cond = (
            (TotoDraw.n1 == n) | (TotoDraw.n2 == n) | (TotoDraw.n3 == n)
            | (TotoDraw.n4 == n) | (TotoDraw.n5 == n) | (TotoDraw.n6 == n)
            | (TotoDraw.additional_no == n)
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(TotoDraw.draw_no.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    draws = result.scalars().all()

    return TotoDrawListResponse(
        items=[TotoDrawOut.from_orm(d) for d in draws],
        total=total,
        page=page,
        page_size=page_size,
    )
