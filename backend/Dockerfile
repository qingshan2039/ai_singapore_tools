# 单镜像同时跑 API + 爬虫（含 Chromium ~ +400MB）。
# 想拆小？复制本文件去掉 playwright install 即得纯 API 镜像。
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# sqlite3 用于 entrypoint 初始化数据库；ca-certificates 给 https
RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖描述，利用构建缓存
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e . --no-deps && \
    pip install --no-cache-dir \
        "fastapi>=0.110.0" "uvicorn[standard]>=0.27.0" \
        "pydantic>=2.6.0" "pydantic-settings>=2.2.0" \
        "sqlalchemy>=2.0.0" "aiosqlite>=0.20.0" "asyncpg>=0.29.0" \
        "playwright>=1.41.0" "selectolax>=0.3.20" "httpx>=0.27.0" \
        "apscheduler>=3.10.0" \
        "python-jose[cryptography]>=3.3.0" "google-auth>=2.28.0" \
        "python-dotenv>=1.0.0" "tenacity>=8.2.0" "structlog>=24.1.0"

# 装 Chromium + 系统依赖（playwright 自带安装器会装 ~/ms-playwright 下）
RUN python -m playwright install --with-deps chromium

# 最后再拷源代码，业务文件变动不会让上面层失效
COPY app ./app
COPY sql ./sql
COPY scripts ./scripts
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# entrypoint 用的 DB 路径
ENV DB_PATH=/data/toto.db

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
