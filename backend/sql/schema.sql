-- TOTO Analyzer - Database Schema
-- Compatible with SQLite (dev) and PostgreSQL (prod).
-- For PostgreSQL, replace TEXT with VARCHAR/JSONB where noted in comments.

-- ============================================================
-- TOTO 开奖记录
-- ============================================================
CREATE TABLE IF NOT EXISTS toto_draws (
    draw_no              INTEGER PRIMARY KEY,         -- 期号，如 4117
    draw_date            TEXT NOT NULL,               -- ISO 日期 'YYYY-MM-DD' (PG: DATE)
    draw_day             TEXT,                        -- 'Mon' or 'Thu'

    -- 中奖号码：6 个普通号 + 1 个附加号
    n1                   INTEGER NOT NULL CHECK(n1 BETWEEN 1 AND 49),
    n2                   INTEGER NOT NULL CHECK(n2 BETWEEN 1 AND 49),
    n3                   INTEGER NOT NULL CHECK(n3 BETWEEN 1 AND 49),
    n4                   INTEGER NOT NULL CHECK(n4 BETWEEN 1 AND 49),
    n5                   INTEGER NOT NULL CHECK(n5 BETWEEN 1 AND 49),
    n6                   INTEGER NOT NULL CHECK(n6 BETWEEN 1 AND 49),
    additional_no        INTEGER NOT NULL CHECK(additional_no BETWEEN 1 AND 49),

    -- 派奖与中奖统计 - JSON 字符串存奖金分布（PG 可用 JSONB）
    -- 结构: {"group_1": {"prize": 1234567.89, "winners": 1, "share": 1234567.89}, ...}
    prize_groups         TEXT,
    jackpot_amount       REAL,                        -- Group 1 奖池
    total_sales          REAL,                        -- 总投注额（如有）
    total_payout         REAL,                        -- 总派彩 = Σ(prize × winners) 跨所有奖级
    total_payout_corrected REAL,                      -- 仅 Group 1 的 prize × winners
    is_snowball          INTEGER DEFAULT 0,           -- 是否滚存
    is_cascade           INTEGER DEFAULT 0,           -- 是否级联抽奖

    -- 派奖店铺信息（JSON 数组）
    winning_outlets      TEXT,

    -- 元数据
    raw_html             TEXT,                        -- 原始 HTML 备份，便于回溯解析 bug
    source_url           TEXT,
    scraped_at           TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at           TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_toto_draws_date ON toto_draws(draw_date);

-- ============================================================
-- 派生分析表：单期号码特征（每次入库时计算并存储，避免运行时计算）
-- ============================================================
CREATE TABLE IF NOT EXISTS toto_draw_features (
    draw_no              INTEGER PRIMARY KEY REFERENCES toto_draws(draw_no),
    sum_value            INTEGER NOT NULL,             -- 6 个号的和
    odd_count            INTEGER NOT NULL,             -- 奇数个数
    even_count           INTEGER NOT NULL,             -- 偶数个数
    small_count          INTEGER NOT NULL,             -- ≤24 的个数（小号）
    large_count          INTEGER NOT NULL,             -- ≥25 的个数（大号）
    span_value           INTEGER NOT NULL,             -- max - min
    consecutive_count    INTEGER NOT NULL,             -- 连号对数
    ac_value             INTEGER,                      -- AC值（号码复杂度）
    computed_at          TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 派生分析表：号码出现统计（49 个号，每次入库后增量更新）
-- ============================================================
CREATE TABLE IF NOT EXISTS toto_number_stats (
    number               INTEGER PRIMARY KEY CHECK(number BETWEEN 1 AND 49),
    total_appearances    INTEGER DEFAULT 0,            -- 历史总出现次数
    last_appeared_draw   INTEGER,                      -- 最后出现的期号
    last_appeared_date   TEXT,
    as_additional_count  INTEGER DEFAULT 0,            -- 作为附加号出现的次数
    updated_at           TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 初始化 1-49 号
INSERT OR IGNORE INTO toto_number_stats (number) VALUES
(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),
(11),(12),(13),(14),(15),(16),(17),(18),(19),(20),
(21),(22),(23),(24),(25),(26),(27),(28),(29),(30),
(31),(32),(33),(34),(35),(36),(37),(38),(39),(40),
(41),(42),(43),(44),(45),(46),(47),(48),(49);

-- ============================================================
-- 用户与投注记录（P3 阶段才用，先建表）
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                   TEXT PRIMARY KEY,             -- UUID
    email                TEXT UNIQUE,
    name                 TEXT,
    provider             TEXT NOT NULL,                -- 'google' | 'apple'
    provider_user_id     TEXT NOT NULL,
    created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login_at        TEXT,
    UNIQUE(provider, provider_user_id)
);

CREATE TABLE IF NOT EXISTS user_bets (
    id                   TEXT PRIMARY KEY,             -- UUID
    user_id              TEXT NOT NULL REFERENCES users(id),
    game_type            TEXT NOT NULL,                -- 'TOTO' | '4D'
    draw_no              INTEGER,                      -- 关联期号
    numbers              TEXT NOT NULL,                -- JSON: [3,12,25,33,40,45]
    bet_type             TEXT,                         -- 'Ordinary' | 'System 7' ...
    bet_amount           REAL NOT NULL,
    status               TEXT DEFAULT 'pending',       -- 'pending' | 'checked' | 'won' | 'lost'
    prize_group          INTEGER,                      -- 中奖等级，0 = 未中
    prize_won            REAL DEFAULT 0,
    created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
    checked_at           TEXT
);

CREATE INDEX IF NOT EXISTS idx_user_bets_user ON user_bets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_bets_draw ON user_bets(draw_no);

CREATE TABLE IF NOT EXISTS user_favorites (
    id                   TEXT PRIMARY KEY,
    user_id              TEXT NOT NULL REFERENCES users(id),
    game_type            TEXT NOT NULL,
    numbers              TEXT NOT NULL,                -- JSON
    label                TEXT,                         -- 用户自定义备注，如"生日号"
    created_at           TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 爬虫日志（监控用）
-- ============================================================
CREATE TABLE IF NOT EXISTS scrape_logs (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    target               TEXT NOT NULL,                -- 'toto' | '4d'
    draw_no              INTEGER,
    status               TEXT NOT NULL,                -- 'success' | 'failure'
    error_message        TEXT,
    duration_ms          INTEGER,
    scraped_at           TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scrape_logs_time ON scrape_logs(scraped_at);
