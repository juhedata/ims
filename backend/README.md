# IMS 后端

IMS（一物一码库存管理系统）的后端 API 服务，基于 FastAPI 构建，提供入库、出库、库存、商品 SKU、往来单位等业务能力。

## 技术架构

| 层级 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | REST API，自动生成 Swagger 文档（`DEBUG=true` 时） |
| ORM | SQLAlchemy 2.0 | 声明式模型，类型注解 `Mapped[]` |
| 数据库 | MySQL + PyMySQL | 连接串由 `.env` 配置 |
| 迁移 | Alembic | 版本化数据库变更，支持启动时自动迁移 |
| 鉴权 | JWT（python-jose）+ bcrypt | 登录签发 token，接口通过 Bearer 鉴权 |
| 定时任务 | APScheduler | 每月 1 日 00:00 自动快照库存单品 |
| 日志 | Loguru | 按日滚动，输出到 `logs/` |
| 依赖管理 | uv | Python 3.12+，虚拟环境在 `.venv/` |

### 目录结构

```
backend/
├── alembic/              # 数据库迁移脚本
├── app/
│   ├── api/              # 路由层（HTTP 入口）
│   ├── core/             # 配置、鉴权、日志、定时任务
│   ├── db/               # 数据库连接与 Base
│   ├── models/           # SQLAlchemy ORM 模型
│   ├── schemas/          # Pydantic 请求/响应模型
│   ├── service/          # 业务逻辑层
│   └── utils/            # 工具（SN 生成、单号生成等）
├── scripts/              # 运维脚本（如初始化管理员）
├── logs/                 # 运行日志（自动生成）
├── main.py               # 应用入口
├── alembic.ini
├── pyproject.toml
└── .env                  # 环境变量（不提交 Git）
```

### API 模块

所有接口前缀为 `/api/v1`：

| 模块 | 路径前缀 | 功能 |
|------|----------|------|
| 认证 | `/auth` | 登录、token |
| 用户 | `/users` | 员工账号管理 |
| 首页 | `/dashboard` | 待审核统计、库存汇总 |
| 库存 | `/inventory` | 单品查询、可用库存、变动轨迹 |
| 商品 | `/products` | 分类、SKU 管理 |
| 往来单位 | `/partners` | 单位分组与单位 |
| 入库 | `/inbound` | 采购/非采购入库、审核 |
| 出库 | `/outbound` | 出库单、审核 |
| 系统设置 | `/settings` | 品牌配置（名称/副标题/Logo） |
| 快照 | `/snapshots` | 月度库存快照查询 |

---

## 快速启动

### 环境要求

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) 包管理器
- MySQL 5.7+ / 8.0+

### 1. 安装依赖

```bash
cd backend
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少配置数据库与 JWT 密钥：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=ims

JWT_SECRET_KEY=change-me-to-a-long-random-string
```

### 3. 创建数据库

```sql
CREATE DATABASE ims CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 执行数据库迁移

**方式 A：启动时自动迁移**（适合本地开发）

```env
AUTO_MIGRATE=true
```

**方式 B：手动迁移**（适合生产环境）

```bash
uv run python -m alembic upgrade head
```

### 5. 初始化管理员账号

```bash
uv run python scripts/init_admin.py
# 自定义账号密码：
uv run python scripts/init_admin.py --username admin --password admin123 --nickname 管理员
```

### 6. 启动服务

```bash
uv run python -m uvicorn main:app --reload
```

> 请使用 `python -m uvicorn` 启动，确保使用项目虚拟环境（`.venv`）中的 Python，避免与系统 Python 冲突。

启动成功后：

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000/health | 健康检查 |
| http://127.0.0.1:8000/docs | Swagger 文档（`DEBUG=true` 时） |

### 启动流程说明

应用启动时会依次执行：

1. 初始化日志系统
2. 检查数据库连接
3. 若 `AUTO_MIGRATE=true`，自动执行 `alembic upgrade head`
4. 初始化系统枚举配置（`stock_status`、`operation_status` 等）
5. 启动定时任务（月度库存快照）

---

## Item SN 自动生成规则

系统采用**一物一码**，每件商品对应唯一 Item SN（如 `S00001-001-002`）。SN 在**采购入库**时录入或自动生成。

### SN 格式

```
{前缀}-{批次序号3位}-{单品序号3位}
```

示例：`S00001-001-002`

| 段 | 规则 | 示例 |
|----|------|------|
| 前缀 | 由 SKU 条码推导：将 `NO` 替换为 `S`；无法解析时用 `S{sku_id:05d}` | `NO00001` → `S00001` |
| 批次序号 | 该 SKU 已完成入库单明细行数 + 1 | 第 1 批 → `001` |
| 单品序号 | 同一入库明细行内，从 1 递增到 `quantity` | 第 2 件 → `002` |

### 前缀推导示例

| SKU 条码 | SKU ID | 生成前缀 |
|----------|--------|----------|
| `NO00001` | 1 | `S00001` |
| `NO00123` | 5 | `S00123` |
| `ABC-999`（无法解析） | 7 | `S00007` |

### 批次序号计算

批次序号 = 该 SKU 在**已完成**（`operation_status = COMPLETED`）入库单中的明细行总数 + 1。

同一入库单、同一 SKU 的多件商品共享同一批次序号，单品序号在行内递增。

**示例**：SKU `NO00001` 已有 2 条已完成入库明细，本次采购入库 3 件，则生成：

```
S00001-003-001
S00001-003-002
S00001-003-003
```

### 录入方式

采购入库支持两种方式，也可混合使用：

| 方式 | 触发条件 | `sn_source` 标记 |
|------|----------|------------------|
| 人工导入 | 请求中提供 `item_sns` 列表 | `MANUAL` |
| 系统生成 | 未提供 `item_sns`，或数量不足时自动补齐 | `AUTO` |

规则要点：

- `item_sns` 数量必须与 `quantity` 一致；不足时系统自动按规则补齐剩余 SN
- 全新商品入库前会校验 SN 唯一性（库存已有 + 其他未完成入库单中已录入）
- 非采购入库（退货/归还）复用原出库单上的 Item SN，不重新生成

### SKU 的 SN 模式

每个 SKU 可配置 `sn_mode` 字段，表示该商品支持的 SN 录入方式：

| 值 | 含义 |
|----|------|
| `MANUAL` | 仅支持人工录入 |
| `AUTO` | 仅支持系统生成 |
| `BOTH` | 两者均可（默认） |

### 相关代码

- SN 生成逻辑：`app/utils/sn_generator.py`
- 采购入库绑定 SN：`app/service/inbound_service.py` → `_build_procurement_items()`
- SN 唯一性校验接口：`POST /api/v1/inbound/validate-sns`

---

## 常用命令

```bash
# 安装依赖
uv sync

# 启动开发服务
uv run python -m uvicorn main:app --reload

# 手动数据库迁移
uv run python -m alembic upgrade head

# 生成迁移脚本（模型变更后）
uv run python -m alembic revision --autogenerate -m "描述"

# 初始化管理员
uv run python scripts/init_admin.py
```

## 环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `APP_NAME` | 否 | `IMS` | 应用名称（Swagger/健康检查；前端展示名以 sys_config 为准） |
| `DEBUG` | 否 | `false` | 调试模式，控制 Swagger 是否暴露 |
| `MYSQL_HOST` | 是 | — | MySQL 主机 |
| `MYSQL_PORT` | 否 | `3306` | MySQL 端口 |
| `MYSQL_USER` | 是 | — | 数据库用户名 |
| `MYSQL_PASSWORD` | 是 | — | 数据库密码 |
| `MYSQL_DB` | 是 | — | 数据库名 |
| `JWT_SECRET_KEY` | 是 | — | JWT 签名密钥 |
| `JWT_ALGORITHM` | 否 | `HS256` | JWT 算法 |
| `JWT_EXPIRE_MINUTES` | 否 | `1440` | Token 有效期（分钟） |
| `AUTO_MIGRATE` | 否 | `false` | 启动时是否自动执行数据库迁移 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `CORS_ORIGINS` | 否 | `http://localhost:5173` | 跨域白名单，逗号分隔 |
| `UPLOAD_DIR` | 否 | `uploads` | 上传文件目录 |
| `UPLOAD_URL_PREFIX` | 否 | `/uploads` | 上传文件 URL 前缀 |
| `MAX_LOGO_SIZE` | 否 | `2097152` | Logo 最大字节数（默认 2MB） |
