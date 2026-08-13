# AuditPro FastAPI 后端

当前版本为港审通小程序提供认证、首页、工作台、个人中心、工时打卡、公安备案、耗材采购和安全检查接口。

## 1. 环境要求

- Python 3.11+
- MySQL 8.0+
- 数据库：`audit_pro`

## 2. 配置

复制 `.env.example` 中的配置到服务器环境变量。不要把真实密码、微信 AppSecret 或令牌密钥提交到代码仓库。

必须配置：

- `APP_SECRET`：平台令牌签名密钥。
- `WECHAT_APP_SECRET`：微信小程序 AppSecret。
- `DB_PASSWORD`：MySQL 密码。

开发模式未提供 `WECHAT_APP_SECRET` 时，后端会使用固定测试账号 `DEV_WECHAT_OPENID`，方便本地联调。生产环境不会启用此降级方式。

## 3. 初始化数据库

使用 MySQL 客户端执行：

```bash
mysql -h 59.110.62.226 -P 34409 -u aliyun_zx -p < database/init.sql
```

也可以保留 `AUTO_CREATE_TABLES=true`，由应用首次启动时创建缺失的基础表。

## 4. 启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

开发环境接口文档：`http://127.0.0.1:8000/docs`。

如果远程 MySQL 尚未开放开发机访问，可仅在本地临时启动 SQLite：

```bash
DATABASE_URL=sqlite:///./auditpro_dev.db WECHAT_APP_SECRET= \
  uvicorn app.main:app --host 127.0.0.1 --port 8000
```

该模式只用于小程序开发者工具联调，服务器部署仍使用 `.env` 中的 MySQL 配置。

## 5. 已提供接口

- `POST /api/v1/auth/wechat-login`
- `GET /api/v1/home`
- `GET /api/v1/workbench`
- `GET /api/v1/profile`
- `PATCH /api/v1/profile`
- `GET /api/v1/attendance/today`
- `POST /api/v1/attendance/punch`
- `GET /api/v1/attendance/month?month=YYYY-MM`
- `POST /api/v1/attendance/supplements`
- `GET/POST /api/v1/police-filings`
- `GET /api/v1/police-filings/export`
- `GET/PUT/DELETE /api/v1/police-filings/{id}`
- `GET/POST /api/v1/consumable-purchases`
- `GET /api/v1/consumable-purchases/export`
- `GET/PUT/DELETE /api/v1/consumable-purchases/{id}`
- `GET/POST /api/v1/safety-inspections`
- `GET /api/v1/safety-inspections/rectifications`
- `POST /api/v1/safety-inspections/hazards/{id}/rectify`
- `POST /api/v1/safety-inspections/hazards/{id}/review`
- `POST /api/v1/files/upload`
- `GET /api/v1/files/{id}`
- `GET /health`
