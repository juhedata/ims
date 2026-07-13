# IMS — 一物一码库存管理系统

前后端分离的库存管理开源项目。

| 目录 | 说明 |
|------|------|
| `backend/` | FastAPI 后端 API |
| `frontend/` | Vue 3 前端 |

## Docker 一键启动

```bash
cp .env.example .env
# 建议修改 JWT_SECRET_KEY、MYSQL_PASSWORD、ADMIN_PASSWORD

docker compose up -d --build
```

启动后访问：

- 前端：http://localhost:8080
- 后端健康检查：http://localhost:8000/health
- 默认管理员：`admin` / `admin123`（可在 `.env` 中修改）

登录后进入 **系统设置 → 品牌配置**，可自定义项目名称、登录页副标题，并上传 Logo。

停止：

```bash
docker compose down
```

## 本地开发

详见 [backend/README.md](backend/README.md) 与 [frontend/README.md](frontend/README.md)。
