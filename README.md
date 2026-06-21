# Steam CCU Intelligence

Steam 热门游戏数据分析平台：实时并发在线人数（CCU）监控、历史趋势对比、CS2 饰品市场行情。

**技术栈**：Vue 3 + Vite + ECharts · FastAPI (Python) · MongoDB 7

---

## 功能页面

| 页面 | 路由 | 内容 |
|------|------|------|
| 商店首页 | `/` | Steam 商店风格轮播、推荐、搜索、热门与免费游戏 |
| 总览 Dashboard | `/dashboard` | 30 款游戏实时 CCU 排行榜、系统状态卡片 |
| 游戏详情 | `/game/:id` | 近期 CCU 趋势、月度历史图、CNY 价格走势、月度预测（至 2026 年底） |
| CCU 对比 | `/compare` | 最多同时对比 5 款游戏的历史月度在线人数折线图 |
| CS2 饰品市场 | `/market` | 80 件饰品分类行情，180 天价格历史 + 30 天预测 |

---

## 数据来源

> **没有自动定时爬取。** 所有历史数据通过下方描述的方式一次性采集并存入 `backend/data/`，后端首次启动时自动 seed 进 MongoDB。实时 CCU 由启动时触发的 `ingest_steam_data.py` 采集一次。

| 数据 | 来源 | 说明 |
|------|------|------|
| 历史月度 CCU（2012 年至今） | SteamCharts 页面抓取 | 使用 `playwright-cli` 爬取，存于 `steamcharts_history.json` |
| 实时 CCU 快照 | Steam 官方 API | 后端启动时调用 `ISteamUserStats/GetNumberOfCurrentPlayers` |
| 游戏详情（标签、评价、开发商） | Steam Store API | 调用 `/api/appdetails`，存于 `steam_game_details.json` |
| CS2 饰品列表 + 图片 | Steam Market Search API | 无需登录，含 `icon_url`（CDN 直链） |
| CS2 饰品价格历史 | 合成数据 | 当前价为真实值（Steam Market），180 天历史由 OU 均值回归模型生成 |
| 游戏 CNY 价格 | Steam Store API | 真实当前 CNY 价，历史折扣基于已知 Steam 大促日期生成 |
| 游戏封面图 | Steam CDN | 不存储，运行时按 appid 拼接：`cdn.akamai.steamstatic.com/steam/apps/{id}/header.jpg` |

---

## 数据库结构（MongoDB `steam_hot_games`）

| 集合 | 文档数 | 主要字段 | 说明 |
|------|--------|----------|------|
| `ccu_timeseries` | ~3024 | `appid`, `ts`, `ccu`, `peak_ccu`, `source` | `source=steamcharts_monthly`：月度历史；`source=steam_official`：实时快照 |
| `game_info` | 30 | `appid`, `name`, `current_ccu`, `tags`, `price_usd`, `last_synced_at` | 游戏基础信息 + 最新 CCU，由 ingest 脚本写入 |
| `game_details` | 30 | `appid`, `name`, `tags`, `review_summary`, `developer`, `release_date`, `is_free` | 游戏详情页展示数据，由 Steam Store API 采集 |
| `market_items` | 80 | `name`, `category`, `image_url`, `current_price`, `change_7d`, `change_30d`, `price_history` | CS2 饰品，分 8 类（刀具/手套/AK-47/AWP 等） |
| `price_history` | 17 | `appid`, `name`, `initial_cny`, `all_time_low_cny`, `history[]` | 游戏 CNY 价格走势，覆盖有付费价格的游戏 |

> 所有集合在**后端首次启动时自动从 `backend/data/` 目录 seed**，无需手动导入。

---

## 快速启动

### 1. 启动 MongoDB

```bash
docker run -d --name steamccu-mongo -p 27017:27017 mongo:7
```

### 2. 启动后端

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

首次启动会自动完成：
- 将 `backend/data/` 目录下所有 JSON 文件 seed 进 MongoDB
- 触发一次实时 CCU 采集（后台进行，约 60 秒）

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`（或 Vite 分配的端口）

---

## 环境变量（`backend/.env`）

```env
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB=steam_hot_games

# 需要监控的 AppID，逗号分隔
TARGET_APP_IDS=730,570,578080,271590,...

# 允许的前端跨域地址
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

# HTTP 代理（可选，Steam API 需要能访问国际网络）
HTTP_PROXY=
```

---

## 更新数据

### 更新 SteamCharts 月度 CCU

在项目根目录使用内置 skill：

```
/scrape-steamcharts
```

或参考 `.claude/skills/scrape-steamcharts/SKILL.md` 中的完整说明手动执行。

### 手动重新 seed

```bash
# 删除对应集合，后端重启时自动重新导入
python3 -c "
from pymongo import MongoClient
db = MongoClient('mongodb://127.0.0.1:27017')['steam_hot_games']
db['ccu_timeseries'].delete_many({'source': 'steamcharts_monthly'})
db['market_items'].drop()
db['game_details'].drop()
db['price_history'].drop()
print('Done — restart backend to reseed')
"
```

---

## 项目结构

```
steamccu/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 路由
│   │   ├── database.py       # MongoDB 连接
│   │   ├── config.py         # 环境变量
│   │   ├── schemas.py        # Pydantic 模型
│   │   └── services/
│   │       ├── seed.py       # 首次启动自动 seed
│   │       ├── predictor.py  # CCU 月度预测算法
│   │       └── queries.py    # MongoDB 查询封装
│   ├── data/                 # JSON 种子数据（数据库 seed 来源）
│   │   ├── steamcharts_history.json
│   │   ├── steam_game_details.json
│   │   ├── cs2_market_items.json
│   │   └── steam_price_history.json
│   └── scripts/
│       └── ingest_steam_data.py  # 实时 CCU 采集
├── frontend/
│   ├── src/
│   │   ├── views/            # Dashboard / GameDetail / Compare / Market
│   │   ├── components/       # TrendChart / CompareChart / MarketChart
│   │   ├── router/           # Vue Router
│   │   └── api.js            # 所有后端接口封装
│   └── ...
└── .claude/
    └── skills/
        └── scrape-steamcharts/   # 爬取 SteamCharts 数据的 Claude Skill
```
