# Steam CCU Intelligence

Steam 热门游戏并发在线人数（CCU）实时监控与预测大屏。

**技术栈**：Vue 3 + Vite + Tailwind CSS + ECharts · FastAPI · MongoDB

---

## 数据来源

系统不内置任何模拟数据，所有数据均来自真实接口：

| 数据 | 来源 |
|------|------|
| 实时 CCU | Steam 官方 API `ISteamUserStats/GetNumberOfCurrentPlayers` |
| 历史月度 CCU（2012年至今） | SteamCharts 页面抓取 |
| 游戏详情（标签、好评率） | SteamSpy API |
| 游戏价格、发行日期 | Steam Store API |
| 热门游戏自动发现 | SteamSpy `top100in2weeks` |

首次启动后端时，若数据库为空会自动触发一次完整采集（约60秒）。此后可通过页面右上角 **SYNC DATA** 按钮随时手动更新，或按需定时运行 `python scripts/ingest_steam_data.py`。

---

## 快速启动

```bash
docker run -d --name my-mongodb -p 27017:27017 mongo:7   # 启动数据库
cd backend && python -m uvicorn app.main:app --port 8000  # 启动后端
cd frontend && npm install && npm run dev                  # 启动前端
```

访问 `http://localhost:5173`

> 详细部署步骤（含代理配置、环境变量说明）见 [DEPLOY.md](./DEPLOY.md)

