# Steam CCU Intelligence — 部署手册

## 前置要求

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Docker | 任意版本 | 运行 MongoDB |
| Python | 3.8+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| curl | 任意 | SteamCharts 数据抓取 |

---

## 1. 启动 MongoDB

```bash
docker run -d --name my-mongodb -p 27017:27017 mongo:7
```

已有容器时直接启动：
```bash
docker start my-mongodb
```

---

## 2. 配置后端环境

```bash
cd backend
cp .env.example .env
```

编辑 `.env`，填入代理地址（访问 Steam/SteamCharts 需要）：

```env
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB=steam_hot_games
TARGET_APP_IDS=730,570,578080,271590,1172470,440,252490,4000
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
HTTP_PROXY=http://127.0.0.1:你的代理端口
```

安装依赖：
```bash
pip install -r requirements.txt
```

---

## 3. 启动后端

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**首次启动时，若数据库为空，后端会自动触发数据采集（约60秒完成）。**

验证：
```bash
curl http://localhost:8000/health
# 返回 {"ok":true}
```

---

## 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

---

## 5. 手动触发数据采集

方式一：点击页面右上角 **SYNC DATA** 按钮（35秒后自动刷新）

方式二：命令行直接运行：
```bash
cd backend
python scripts/ingest_steam_data.py
```

---

## 6. 完整启动顺序（一键参考）

```bash
# 1. MongoDB
docker start my-mongodb

# 2. 后端（新终端）
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 前端（新终端）
cd frontend && npm run dev
```

---

## 常见问题

**Q: 页面没有数据？**
点击 SYNC DATA 按钮，等待约60秒后数据自动刷新。

**Q: Steam API 超时？**
确认 `.env` 中 `HTTP_PROXY` 已填写可用代理地址。

**Q: MongoDB 连接失败？**
运行 `docker ps` 确认 `my-mongodb` 容器状态为 `Up`。

**Q: 预测接口报错 "Not enough historical data"？**
先运行一次数据采集，历史数据写入后预测功能自动可用。
