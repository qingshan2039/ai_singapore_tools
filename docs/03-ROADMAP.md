# Roadmap - 13 周 MVP 计划

按业余时间每周 8-10 小时估算。

## P0 - 数据底座（第 1-2 周）

> **目标**：能稳定拉到数据，能自动追增量。这是命根子，必须扎实。

### Week 1：爬虫与解析
- [ ] 用 Playwright 写 TOTO 爬虫，能拉单期
- [ ] 解析中奖号码、附加号、日期、各奖级奖金
- [ ] 单元测试：固定 HTML fixture，验证解析正确
- [ ] 建好 SQLite 数据库，schema.sql 跑通

### Week 2：回填与调度
- [ ] 写 backfill 脚本，把近 5 年（约 500 期）全量入库
- [ ] APScheduler 配置：每周一/四 19:00 自动跑（开奖后 30 分钟）
- [ ] 失败重试 + 邮件/Telegram 告警
- [ ] 部署到云主机（DO / Hetzner $4-6 一个月）

**P0 完成标准**：连续 2 个开奖周期，数据自动入库且数据正确。

---

## P1 - MVP 后端 + 简易前端（第 3-6 周）

> **目标**：自己能用上的最小可用版本。

### Week 3：后端 API
- [ ] FastAPI 项目结构搭好
- [ ] `GET /api/toto/draws` 列表（分页、日期筛选）
- [ ] `GET /api/toto/draws/{draw_no}` 单期详情
- [ ] `GET /api/toto/draws/latest` 最新一期
- [ ] OpenAPI 文档可访问

### Week 4：Flutter 项目搭建
- [ ] Flutter 项目初始化，配好 routing（go_router）
- [ ] 用 openapi-generator 生成 API client
- [ ] 状态管理选型：Riverpod
- [ ] 主题、配色定下来

### Week 5：核心三屏
- [ ] 首页：最新一期 + 历史列表入口
- [ ] 历史列表页：可滚动、可筛选
- [ ] 单期详情页

### Week 6：发布 v0.1
- [ ] Flutter Web 部署（用 Cloudflare Pages，免费）
- [ ] 域名 + HTTPS
- [ ] 自己用一周，记录所有坑

---

## P2 - 数据爱好者功能（第 7-10 周）

> **目标**：差异化卖点，让数据爱好者爱不释手。

### Week 7：分析后端
- [ ] 频率统计 API
- [ ] 冷热号 API（参数：最近 N 期）
- [ ] 共现矩阵 API
- [ ] 奇偶比、和值等单期特征 API
- [ ] 这些都计算成 materialized view，每天更新

### Week 8：Flutter 图表
- [ ] 引入 fl_chart 或 syncfusion_flutter_charts
- [ ] 频率热力图（49 个格子的彩色矩阵）
- [ ] 冷热号榜单
- [ ] 时间序列折线图（和值趋势）

### Week 9：高级可视化
- [ ] 共现矩阵热力图（49×49）
- [ ] 雷达图（单期号码特征）
- [ ] 钻取交互：点击号码看历史详情

### Week 10：选号助手
- [ ] 机选 API
- [ ] 条件选号（前端 form + 后端逻辑）
- [ ] 收藏号码组合（本地存储）

---

## P3 - 用户系统 + 投注记录（第 11-13 周）

### Week 11：账号系统
- [ ] Google 一键登录（google_sign_in package）
- [ ] Apple 一键登录（sign_in_with_apple package）
- [ ] FastAPI 校验 OAuth token，签发 JWT
- [ ] users 表 + 数据迁移

### Week 12：投注记录
- [ ] 录入投注 UI（号码、金额、期号）
- [ ] 开奖后自动对奖（后台 job）
- [ ] 历史投注统计（总投入、总中奖、回报率）

### Week 13：通知与收尾
- [ ] FCM 推送（开奖结果、中奖提醒）
- [ ] 全应用文案打磨（每个分析图都加免责声明）
- [ ] 上架 TestFlight + Play Console 内测

---

## 维护期（13 周后）

- 4D 模块（约 2-3 周复用现有架构）
- 用户反馈迭代
- 监控告警完善

## 砍功能预案

如果时间紧，按以下顺序砍：
1. 砍 P3 全部（账号/投注记录/推送）→ 留个纯查询工具
2. 砍 Week 9 高级可视化 → 留基础图表
3. 砍 Week 10 选号助手 → 数据爱好者用筛选也够
4. **绝对不能砍 P0 + Week 3-6**：没数据没 API 就没产品
