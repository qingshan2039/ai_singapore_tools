# TOTO Analyzer

Singapore TOTO & 4D 历史数据分析平台。**仅供娱乐参考**，不构成任何投注建议。

> 彩票每期开奖在数学上是独立事件。本应用提供的所有"频率"、"冷热号"、"共现"等分析仅为数据娱乐用途，不能预测未来号码。

## 项目结构

```
toto-analyzer/
├── PRD.md              # 产品需求
├── ROADMAP.md          # 13 周开发路线图
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── main.py     # 应用入口
│   │   ├── scraper/    # 爬虫模块
│   │   ├── routes/     # API 路由
│   │   └── analytics/  # 统计分析
│   ├── sql/schema.sql  # 数据库 DDL
│   └── scripts/        # 一次性脚本（如历史回填）
└── flutter_app/        # Flutter 前端（后续阶段）
```

## 快速开始（10 分钟）

### 1. 环境准备

```bash
# Python 3.11+
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium  # 爬虫需要
```

### 2. 初始化数据库（默认 SQLite，零配置）

```bash
sqlite3 toto.db < sql/schema.sql
```

### 3. 拉取一期测试数据

```bash
python -m app.scraper.toto_scraper --draw 4117
```

### 4. 启动 API 服务

```bash
uvicorn app.main:app --reload
# 打开 http://localhost:8000/docs 看接口文档
```

### 5. 回填近 5 年历史数据

```bash
python scripts/backfill.py --start 3873 --end 4185
# 每期间隔 5 秒，礼貌爬取
```

## 切换到 PostgreSQL（生产）

1. `docker compose up -d` 启动 Postgres + Redis
2. 改 `.env` 里的 `DATABASE_URL`
3. 用同一份 `sql/schema.sql`（兼容两种数据库的语法已注释）

## 法律与伦理

- 爬虫遵守 robots.txt，单请求间隔 ≥ 5 秒
- User-Agent 标识自己（非伪装浏览器）
- 仅供个人学习和娱乐，不商业化
- 如官方要求停止，立即停止
