# 部署到 VPS

把 TOTO Analyzer 部署到一台 Ubuntu 22.04 / 24.04 LTS 的 VPS，使用 Docker Compose + Caddy（自动 HTTPS）+ SQLite。整个过程约 15 分钟（不含历史数据回填的 ~30 分钟）。

---

## 0. 准备清单

| 项 | 要求 |
|---|---|
| VPS | ≥ 1 vCPU / 2 GB RAM / 20 GB 磁盘 |
| 系统 | Ubuntu 22.04 或 24.04 LTS（其他发行版同理，自行换 apt 命令）|
| 端口 | 防火墙放行 `80 / 443`；SSH `22` |
| 域名（可选）| 已把 A 记录指向 VPS IP；没有也行（用 IP 访问，无 HTTPS） |
| 镜像大小 | backend 镜像含 Chromium，约 1.2 GB；首次 build/pull 占带宽 |

---

## 1. VPS 上装 Docker

```bash
# 用官方一键脚本（最省事）
curl -fsSL https://get.docker.com | sudo sh

# 把当前用户加到 docker 组（重新登录后生效，可免 sudo）
sudo usermod -aG docker $USER
newgrp docker

# 验证
docker --version
docker compose version
```

---

## 2. clone 代码

```bash
cd ~
git clone https://github.com/qingshan2039/ai_singapore_tools.git
cd ai_singapore_tools
```

> 如果是私有仓库，用 SSH key 或者 PAT：`git clone git@github.com:qingshan2039/ai_singapore_tools.git`

---

## 3. 配置生产环境变量

```bash
cp .env.prod.example .env.prod
nano .env.prod      # 或 vim
```

至少改这几项：

```bash
DOMAIN=toto.your-domain.com                    # 你的真实域名
API_CORS_ORIGINS=["https://toto.your-domain.com"]
JWT_SECRET=$(openssl rand -hex 32)             # 生成一个 32 字节随机串贴进去
```

**没有域名？** 把 `DOMAIN` 留空或写 `:80`，Caddy 只会 listen 80 端口、无 HTTPS。可以暂时直接用 IP 访问。

---

## 4. 本地构建前端

前端是纯静态，要先 build 出 `frontend/dist/`，再被 Caddy serve。

**方案 A（推荐）：在 VPS 上直接 build**

```bash
# 装 Node.js 20（如果还没装）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

cd frontend
npm ci          # 严格按 package-lock.json 安装
npm run build   # 产物在 ./dist
cd ..
```

**方案 B：本地机器 build 完上传**

如果不想在 VPS 上装 Node：本地 `npm run build` 后用 `scp -r frontend/dist user@vps:~/ai_singapore_tools/frontend/`。

---

## 5. 启动服务

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

第一次会拉镜像 + 装 Chromium，慢一点（5-10 分钟）。完成后看一眼：

```bash
docker compose -f docker-compose.prod.yml ps
# backend  Up (healthy)
# caddy    Up
```

健康检查：

```bash
# 容器内的 health 端点
docker compose -f docker-compose.prod.yml exec backend curl -s http://127.0.0.1:8000/health
# 应输出 {"status":"ok"}

# 外网（如果配了域名）
curl -I https://toto.your-domain.com/health
# HTTP/2 200
```

---

## 6. 首次回填历史数据

容器启动时 entrypoint 自动建了空表，但没有数据。手动跑一次 backfill：

```bash
docker compose -f docker-compose.prod.yml exec backend \
    python scripts/backfill.py --start 3873 --end 4185
```

约 30 分钟（313 期 × 6 秒/期）。完成后浏览器打开域名即可看到完整列表。

> 后续每周抓新期：见下方 [自动更新](#9-自动定期抓新期可选)。

---

## 7. 日常运维

### 看日志

```bash
docker compose -f docker-compose.prod.yml logs -f             # 全部 stream
docker compose -f docker-compose.prod.yml logs -f backend     # 只看 backend
docker compose -f docker-compose.prod.yml logs --tail=200 caddy
```

### 重启 / 停 / 起

```bash
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml down                # 停 + 删容器（卷保留）
docker compose -f docker-compose.prod.yml up -d
```

### 进 backend 容器

```bash
docker compose -f docker-compose.prod.yml exec backend bash
# 然后可以直接：
#   sqlite3 /data/toto.db ".tables"
#   python -c "from app.config import settings; print(settings.database_url)"
```

### 备份 SQLite

数据库就是宿主机 `./data/toto.db` 单个文件。直接 cp 就行（SQLite WAL 模式下用 `.backup` 命令更安全）：

```bash
docker compose -f docker-compose.prod.yml exec backend \
    sqlite3 /data/toto.db ".backup /data/toto.$(date +%F).db"

# 拷到本地
scp user@vps:~/ai_singapore_tools/data/toto.2026-05-27.db ~/backups/
```

或者直接停服务后 `cp`：

```bash
docker compose -f docker-compose.prod.yml stop backend
cp data/toto.db backups/toto.$(date +%F).db
docker compose -f docker-compose.prod.yml start backend
```

---

## 8. 更新代码

```bash
cd ~/ai_singapore_tools
git pull

# 前端有变动？重新 build
cd frontend && npm ci && npm run build && cd ..

# 后端有变动？重新构建镜像 + 滚动重启
docker compose -f docker-compose.prod.yml up -d --build backend

# 只动了 Caddyfile？让 caddy reload（不中断）
docker compose -f docker-compose.prod.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

---

## 9. 自动定期抓新期（可选）

新加 cron，每周二、五凌晨 1 点抓最近的期（覆盖 Mon/Thu/Fri 三种开奖日）。

宿主机 crontab：

```bash
crontab -e
```

加一行（端口/路径/compose 文件名按你的环境改；共享 VPS 用 docker-compose.shared.yml）：

```cron
0 1 * * 2,5 cd /opt/ai_singapore_tools && \
    docker compose -f docker-compose.shared.yml exec -T backend \
    python scripts/backfill.py --start 3873 --end 9999 --stop-after-misses 6 \
    >> /var/log/toto-cron.log 2>&1
```

> ⚠️ **务必带 `--stop-after-misses`**。backfill 会跳过已存在的期，但对"还不存在的未来期"
> 会逐个去抓、每个超时重试（极慢）。`--end 9999` + `--stop-after-misses 6` 的含义是：
> "一直抓到连续 6 期都失败为止"——抓完最新几期、撞到未来期就自动停，几十秒内结束。
> 不带这个参数的话 `--end 9999` 会空跑约 5800 个不存在的期，要跑好几个小时。

---

## 10. 切换到 Postgres（可选）

SQLite 单机够用到几百万条记录，没必要早切。但如果想：

1. 启动 Postgres（用项目根目录的开发用 `docker-compose.yml` 或自己加一个 service）
2. 在 `.env.prod` 把 `DATABASE_URL` 改成：
   ```
   DATABASE_URL=postgresql+asyncpg://toto:STRONG_PASSWORD@postgres:5432/toto
   ```
3. 用 `sql/schema.sql` 在 Postgres 里建表（注释里说明了 PG 语法差异，主要是 `TEXT` 换 `JSONB`、`INTEGER DEFAULT 0` 换 `BOOLEAN DEFAULT FALSE`）
4. 重启 backend；初次会拿一个空 DB，需要重抓 backfill

---

## 11. 故障排查

| 症状 | 排查 |
|---|---|
| Caddy 一直 `obtain certificate failed` | DNS 没生效，或防火墙没开 80（Let's Encrypt 用 80 端口 HTTP-01 验证）|
| `https://domain` 转圈 | `docker logs caddy` 看证书申请是否成功；`docker logs backend` 看 API 是否报错 |
| 前端打开但号码不出 | F12 看请求：`/api/toto/draws` 应该是 200。若 502/504 → backend 没起来 |
| `502 Bad Gateway` | backend 容器没起来。`docker compose ps`、`docker logs backend` 看 stack |
| backfill 一半超时 | scraper 已经做了重试和 PlaywrightTimeoutError 兜底，再跑一次会断点续传补缺 |
| 镜像构建在 `playwright install` 报错 | 内存不足。给 swap：`sudo fallocate -l 2G /swap && sudo mkswap /swap && sudo swapon /swap` |
| 容器频繁 OOM | 1 GB RAM 偏紧（Chromium 不算轻量）。要么升 2GB，要么拆爬虫到独立机器仅做 cron |

---

## 12-B. 共享 VPS：宿主已有 nginx，不能让 Caddy 抢 80/443

如果这台 VPS 已经在跑别的网站（宿主机有 nginx / Caddy / Traefik 占着 :80/:443），就**不要**用 `docker-compose.prod.yml` 那套（它的 Caddy 会和宿主反代抢端口）。换 `docker-compose.shared.yml`：后端容器只把 8000 映射到 `127.0.0.1:8001`，公网完全访问不到，由宿主反代转发进来。

### 步骤

```bash
# 1) clone + 配 env
cd ~ && git clone https://github.com/qingshan2039/ai_singapore_tools.git
cd ai_singapore_tools
cp .env.prod.example .env.prod
nano .env.prod
#   API_CORS_ORIGINS=["https://toto.your-domain.com"]
#   JWT_SECRET=<openssl rand -hex 32>
#   BACKEND_PORT=8001         # 选一个宿主没占的端口，可省略，默认 8001

# 2) build 前端
cd frontend && npm ci && npm run build && cd ..

# 3) 起后端容器（不会抢 80/443）
docker compose -f docker-compose.shared.yml up -d --build

# 4) 验证容器健康
curl -sf http://127.0.0.1:8001/health   # 应返回 {"status":"ok"}
```

### 配置宿主 nginx

把模板复制成 vhost 文件，按注释替换占位（域名、绝对路径、端口）：

```bash
sudo cp deploy/nginx.vhost.conf.example \
        /etc/nginx/sites-available/toto.your-domain.com.conf
sudo nano /etc/nginx/sites-available/toto.your-domain.com.conf
# 把里面 toto.your-domain.com / /home/USER/... / 8001 三处占位替换好

sudo ln -s /etc/nginx/sites-available/toto.your-domain.com.conf \
           /etc/nginx/sites-enabled/

sudo nginx -t                # 语法校验，必须 OK 再 reload
sudo systemctl reload nginx
```

### 加 HTTPS（Let's Encrypt via Certbot）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d toto.your-domain.com
# 自动改 vhost 加 listen 443 ssl 段、申请证书、安装 cron 续期任务
```

完成后 `https://toto.your-domain.com` 就通了，跟同 VPS 的其它站点共存。

### 关键差异速查

| | `docker-compose.prod.yml` | `docker-compose.shared.yml` |
|---|---|---|
| 用 Caddy 容器 | ✅ | ❌（宿主反代代替）|
| 占 :80/:443 | ✅ | ❌ |
| 后端端口 | 仅 compose 内部 | `127.0.0.1:8001`（loopback only）|
| 自动 HTTPS | ✅ Caddy 自动 | 自己 `certbot --nginx` |
| 前端 dist 由谁 serve | Caddy 容器 | 宿主 nginx 直读 `frontend/dist` |
| 更新前端 | 重 build 即生效 | 同（nginx 不用 reload）|
| 适合 | 独占 VPS 的新部署 | 多站点共存的老 VPS |

### Traefik / 宿主 Caddy 用户

宿主用 Traefik：删 `docker-compose.shared.yml` 里 `ports:` 段，改 `networks:` 加入 traefik 网络，再加 `labels:` 让 Traefik 发现。

宿主用 Caddy（systemd 版）：和 nginx 同套思路，加段 reverse_proxy：
```
toto.your-domain.com {
    handle /api/* { reverse_proxy 127.0.0.1:8001 }
    handle /docs* { reverse_proxy 127.0.0.1:8001 }
    handle /openapi.json { reverse_proxy 127.0.0.1:8001 }
    handle /health { reverse_proxy 127.0.0.1:8001 }
    handle {
        root * /home/USER/ai_singapore_tools/frontend/dist
        try_files {path} /index.html
        file_server
    }
}
```

---

## 12. 卸载

```bash
docker compose -f docker-compose.prod.yml down -v   # 删容器 + 删 caddy 卷（证书会丢）
rm -rf data/                                         # 删 SQLite
```

镜像还在，要清掉：`docker image prune -a`。

---

## 附：架构示意

```
                ┌──────────────────────────────────────────┐
                │              Caddy :443/:80              │
   外网 ──HTTPS──▶│  ① 静态 → /srv (= frontend/dist)         │
                │  ② /api/* /docs /health  → backend:8000  │
                └────────────────┬─────────────────────────┘
                                 │ (docker bridge network)
                                 ▼
                        ┌──────────────────┐
                        │  backend :8000   │
                        │  FastAPI +       │
                        │  Playwright      │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ SQLite           │
                        │ /data/toto.db    │
                        │ (host bind mount)│
                        └──────────────────┘
```
