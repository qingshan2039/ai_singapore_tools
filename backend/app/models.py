"""SQLAlchemy ORM models - 与 sql/schema.sql 对应"""
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TotoDraw(Base):
    """TOTO 单期开奖记录"""

    __tablename__ = "toto_draws"

    draw_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    draw_date: Mapped[str] = mapped_column(String(10))           # 'YYYY-MM-DD'
    draw_day: Mapped[str | None] = mapped_column(String(10))     # 'Mon' / 'Thu'

    n1: Mapped[int]
    n2: Mapped[int]
    n3: Mapped[int]
    n4: Mapped[int]
    n5: Mapped[int]
    n6: Mapped[int]
    additional_no: Mapped[int]

    prize_groups: Mapped[str | None] = mapped_column(Text)        # JSON string
    jackpot_amount: Mapped[float | None]
    total_sales: Mapped[float | None]
    total_payout: Mapped[float | None]                            # Σ(prize × winners) 跨所有奖级
    total_payout_corrected: Mapped[float | None]                  # 仅 Group 1 的 prize × winners
    is_snowball: Mapped[int] = mapped_column(Integer, default=0)
    is_cascade: Mapped[int] = mapped_column(Integer, default=0)
    winning_outlets: Mapped[str | None] = mapped_column(Text)

    raw_html: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None]
    scraped_at: Mapped[str | None]
    updated_at: Mapped[str | None]

    __table_args__ = (
        CheckConstraint("n1 BETWEEN 1 AND 49"),
        CheckConstraint("n2 BETWEEN 1 AND 49"),
        CheckConstraint("additional_no BETWEEN 1 AND 49"),
        Index("idx_toto_draws_date", "draw_date"),
    )

    @property
    def numbers(self) -> list[int]:
        """返回排序后的 6 个中奖号"""
        return sorted([self.n1, self.n2, self.n3, self.n4, self.n5, self.n6])


class TotoDrawFeatures(Base):
    """单期号码特征 - 预计算后存储"""

    __tablename__ = "toto_draw_features"

    draw_no: Mapped[int] = mapped_column(ForeignKey("toto_draws.draw_no"), primary_key=True)
    sum_value: Mapped[int]
    odd_count: Mapped[int]
    even_count: Mapped[int]
    small_count: Mapped[int]
    large_count: Mapped[int]
    span_value: Mapped[int]
    consecutive_count: Mapped[int]
    ac_value: Mapped[int | None]
    computed_at: Mapped[str | None]


class TotoNumberStats(Base):
    """每个号码（1-49）的累计统计"""

    __tablename__ = "toto_number_stats"

    number: Mapped[int] = mapped_column(primary_key=True)
    total_appearances: Mapped[int] = mapped_column(default=0)
    last_appeared_draw: Mapped[int | None]
    last_appeared_date: Mapped[str | None]
    as_additional_count: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[str | None]


class ScrapeLog(Base):
    """爬虫日志"""

    __tablename__ = "scrape_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target: Mapped[str] = mapped_column(String(10))
    draw_no: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None]
    scraped_at: Mapped[str | None]
