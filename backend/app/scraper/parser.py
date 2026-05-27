"""TOTO 结果页 HTML 解析器

设计原则：解析逻辑独立于网络请求，便于用 fixture 单元测试。
所有 selector 都基于 ccie48715/Toto_Singapore 的实测结果。
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime

from selectolax.parser import HTMLParser


@dataclass
class ParsedTotoDraw:
    """解析后的单期数据 - 中间产物，不直接落库"""

    draw_no: int
    draw_date: str            # ISO 'YYYY-MM-DD'
    draw_day: str             # 'Mon' / 'Thu'
    numbers: list[int]        # 6 个普通号
    additional_no: int        # 附加号
    prize_groups: dict        # {'group_1': {'prize': ..., 'winners': ..., 'share': ...}}
    jackpot_amount: float | None
    is_snowball: bool
    is_cascade: bool
    winning_outlets: list[dict]  # [{'group': 1, 'outlet': '...', 'address': '...', 'bet_type': '...'}]

    @property
    def total_payout(self) -> float:
        """所有奖级 prize × winners 之和（总派彩）"""
        return sum(
            (g.get("prize") or 0) * (g.get("winners") or 0)
            for g in self.prize_groups.values()
        )

    @property
    def total_payout_corrected(self) -> float:
        """仅 Group 1 的 prize × winners"""
        g1 = self.prize_groups.get("group_1") or {}
        return (g1.get("prize") or 0) * (g1.get("winners") or 0)

    def to_db_row(self, raw_html: str, source_url: str) -> dict:
        """转成可以直接 insert 进 toto_draws 表的 dict"""
        nums = sorted(self.numbers)
        return {
            "draw_no": self.draw_no,
            "draw_date": self.draw_date,
            "draw_day": self.draw_day,
            "n1": nums[0], "n2": nums[1], "n3": nums[2],
            "n4": nums[3], "n5": nums[4], "n6": nums[5],
            "additional_no": self.additional_no,
            "prize_groups": json.dumps(self.prize_groups),
            "jackpot_amount": self.jackpot_amount,
            "total_payout": self.total_payout,
            "total_payout_corrected": self.total_payout_corrected,
            "is_snowball": int(self.is_snowball),
            "is_cascade": int(self.is_cascade),
            "winning_outlets": json.dumps(self.winning_outlets),
            "raw_html": raw_html,
            "source_url": source_url,
            "scraped_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }


# --- 解析辅助 -----------------------------------------------------------------


def _parse_date(text: str) -> tuple[str, str]:
    """解析 'Mon, 18 Oct 2021' -> ('Mon', '2021-10-18')"""
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 2:
        raise ValueError(f"Unexpected date format: {text!r}")
    day = parts[0]
    iso_date = datetime.strptime(parts[1], "%d %b %Y").strftime("%Y-%m-%d")
    return day, iso_date


def _parse_amount(text: str) -> float | None:
    """'$1,234,567.89' -> 1234567.89; '-' -> None"""
    if not text or text.strip() in {"-", "", "TBA"}:
        return None
    cleaned = re.sub(r"[^\d.]", "", text)
    return float(cleaned) if cleaned else None


def _parse_int(text: str) -> int:
    cleaned = re.sub(r"[^\d]", "", text)
    return int(cleaned) if cleaned else 0


# --- 主解析函数 ---------------------------------------------------------------


def parse_toto_html(html: str, draw_no: int) -> ParsedTotoDraw:
    """从 Singapore Pools TOTO 结果页 HTML 解析出结构化数据。

    Selectors 来源：实地验证 + 参考 ccie48715/Toto_Singapore。
    如果 SG Pools 改版导致解析失败，先看 raw_html 字段对比 selector。
    """
    tree = HTMLParser(html)

    # --- 日期 ---
    date_node = tree.css_first("th.drawDate")
    if not date_node:
        raise ParseError(f"Cannot find th.drawDate for draw {draw_no}")
    draw_day, draw_date = _parse_date(date_node.text(strip=True))

    # --- 中奖号码：6 个 td[width="16%"]，第 7 个开始可能是其它信息 ---
    number_nodes = tree.css('td[width="16%"]')
    numbers = []
    for node in number_nodes[:6]:
        txt = node.text(strip=True)
        if txt.isdigit():
            numbers.append(int(txt))
    if len(numbers) != 6:
        raise ParseError(f"Expected 6 winning numbers, got {len(numbers)} for draw {draw_no}")

    # --- 附加号 ---
    additional_node = tree.css_first("td.additional")
    if not additional_node:
        raise ParseError(f"Cannot find td.additional for draw {draw_no}")
    additional_no = int(additional_node.text(strip=True))

    # --- 奖级 (Group 1-7) ---
    # 通常是一个表格，每行：Group X | Prize Amount | Number of Winners | Prize per Winner
    # 我们用类名/位置定位，做容错
    prize_groups = _parse_prize_groups(tree)
    jackpot_amount = prize_groups.get("group_1", {}).get("prize")

    # --- 滚存 / 级联 ---
    page_text = tree.text().lower()
    is_snowball = "snowball" in page_text
    is_cascade = "cascade" in page_text

    # --- 中奖店铺 ---
    winning_outlets = _parse_winning_outlets(html)

    return ParsedTotoDraw(
        draw_no=draw_no,
        draw_date=draw_date,
        draw_day=draw_day,
        numbers=numbers,
        additional_no=additional_no,
        prize_groups=prize_groups,
        jackpot_amount=jackpot_amount,
        is_snowball=is_snowball,
        is_cascade=is_cascade,
        winning_outlets=winning_outlets,
    )


def _parse_prize_groups(tree: HTMLParser) -> dict:
    """解析 7 个奖级的奖金 + 中奖人数。

    页面上通常是个 prize table。每个 group 一行。
    用宽松匹配：找到含 'Group 1' / 'Group 2' 文本的行，提取相邻 td。
    """
    groups: dict[str, dict] = {}
    # 找所有 td 元素，按文本扫描
    rows = tree.css("tr")
    for row in rows:
        text = row.text(strip=True)
        m = re.match(r"Group\s+(\d)", text)
        if not m:
            continue
        group_no = int(m.group(1))
        tds = row.css("td")
        if len(tds) < 3:
            continue
        # 典型结构: [Group X label][Prize per Share][Number of Winners] 或类似
        # 跳过 "Group N" 标签列（它本身含数字 N，否则会被误当奖金）
        amounts = []
        for td in tds:
            t = td.text(strip=True)
            if re.match(r"^Group\s+\d", t, re.IGNORECASE):
                continue
            if any(c.isdigit() for c in t):
                amounts.append(t)
        if not amounts:
            continue
        groups[f"group_{group_no}"] = {
            "prize": _parse_amount(amounts[0]),
            "winners": _parse_int(amounts[1]) if len(amounts) > 1 else 0,
            "share": _parse_amount(amounts[2]) if len(amounts) > 2 else None,
            "raw": amounts,  # 保留原始字符串，调试用
        }
    return groups


def _parse_winning_outlets(html: str) -> list[dict]:
    """解析 Group 1 / 2 派奖店铺。

    页面上结构: <li>店铺名 - 地址 ( 1 QuickPick Ordinary Entry )</li>
    """
    tree = HTMLParser(html)
    outlets = []

    # 只截取 Group 2 之前的部分，避免误抓 Group 2 的店铺当成 Group 1
    g1_idx = html.find("Group 1 winning tickets sold at")
    g2_idx = html.find("Group 2 winning tickets sold at")

    if g1_idx == -1:
        return []

    g1_section = html[g1_idx : g2_idx if g2_idx > 0 else len(html)]
    g1_tree = HTMLParser(g1_section)

    for li in g1_tree.css("li"):
        text = li.text(strip=True)
        # 格式: "店铺名 - 地址 ( 1 QuickPick Ordinary Entry )"
        m = re.match(r"(.+?)\s*-\s*(.+?)\s*\(\s*(.+?)\s*\)", text)
        if not m:
            continue
        outlet, address, bet_info = m.groups()
        outlets.append({
            "group": 1,
            "outlet": outlet.strip(),
            "address": address.strip(),
            "bet_type": bet_info.strip(),
        })

    return outlets


class ParseError(Exception):
    """解析失败 - raw_html 会保留以便调试"""
