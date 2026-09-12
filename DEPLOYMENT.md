# Orbit Gallery — 生产部署指南

---

## 前置要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.14 | 运行时 |
| PostgreSQL | ≥ 14 | 数据库 |
| uv | 最新 | 包管理器 |
| Nginx | ≥ 1.18 | 反向代理（可选但推荐） |
| Gunicorn | ≥ 22 | 生产 ASGI 进程管理 |

---

## 1. 服务器准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y postgresql nginx python3-pip

# 创建系统用户（可选，用于隔离运行权限）
sudo useradd -r -s /usr/sbin/nologin orbit
```

---

## 2. 克隆与依赖安装

```bash
cd /opt
git clone <repo-url> orbit
cd orbit

# 创建并激活虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv sync
```

---

## 3. 数据库初始化

```bash
# 创建数据库和用户
sudo -u postgres psql

CREATE DATABASE orbit;
CREATE USER orbit_user WITH PASSWORD '<strong-password>';
ALTER ROLE orbit_user SET client_encoding TO 'utf8';
ALTER ROLE orbit_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE orbit TO orbit_user;
\q

# 运行 Alembic 迁移
export DATABASE_URL="postgresql+asyncpg://orbit_user:<strong-password>@localhost:5432/orbit"
uv run alembic upgrade head
```

---

## 4. 环境变量配置

```bash
cp .env.example .env
nano .env
```

生产环境必需填写的变量：

```bash
APP_ENV=production
DEBUG=False
SECRET_KEY=<至少32字符的强随机字符串>
DATABASE_URL=postgresql+asyncpg://orbit_user:password@localhost:5432/orbit
ASSETS_BASE_URL=https://cdn.yourdomain.com   # 如有 CDN 则填写
```

生成强随机密钥：

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. 数据库迁移

首次部署必须执行：

```bash
uv run alembic upgrade head
```

后续有模型变更时：

```bash
# 自动生成迁移文件
uv run alembic revision --autogenerate -m "description"

# 应用迁移
uv run alembic upgrade head
```

---

## 6. Nginx 反向代理

创建 `/etc/nginx/sites-available/orbit`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # 静态文件由 Nginx 直接服务（提升性能）
    location /static/ {
        alias /opt/orbit/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 用户上传的图片
    location /uploads/ {
        alias /opt/orbit/uploads/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

启用站点并重载 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/orbit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

如需 HTTPS，使用 Certbot：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 7. Systemd 服务

创建 `/etc/systemd/system/orbit.service`：

```ini
[Unit]
Description=Orbit Gallery
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=orbit
Group=www-data
WorkingDirectory=/opt/orbit
Environment="PATH=/opt/orbit/.venv/bin"
ExecStart=/opt/orbit/.venv/bin/gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile -
Restart=always
RestartSec=5

# 安全加固
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/orbit/uploads

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable orbit
sudo systemctl start orbit
sudo systemctl status orbit
```

---

## 8. 验证部署

```bash
# 服务状态
sudo systemctl status orbit

# 健康检查
curl https://your-domain.com/health

# 查看日志
sudo journalctl -u orbit -f
```

---

## 9. 备份策略

```bash
# 数据库备份
pg_dump orbit -U orbit_user > /backups/orbit_$(date +%Y%m%d).sql

# 上传文件备份（rsync）
rsync -avz /opt/orbit/uploads/ /backups/orbit-uploads/
```

建议配置 cron 定时备份：

```cron
# 每日凌晨 3 点备份数据库
0 3 * * * pg_dump orbit -U orbit_user | gzip > /backups/orbit_$(date +\%Y\%m\%d).sql.gz
```

---

## 10. 常见问题

| 问题 | 排查方向 |
|------|----------|
| 启动报错 `SECRET_KEY` 过短 | 检查 `.env` 中 SECRET_KEY 至少 32 字符 |
| 启动报错 `DEBUG=True` | 生产环境不允许 DEBUG，改为 `False` |
| 数据库连接失败 | 检查 `DATABASE_URL` 格式和 PostgreSQL 是否运行 |
| 静态文件 404 | 确认 Nginx `alias` 路径正确，文件权限为 `www-data` |
| 图片上传失败 | 检查 `uploads/` 目录权限，systemd 配置了 `ReadWritePaths` |
| 跨域请求被拒 | 检查 CSP 配置，如有前端分离需添加 `connect_src` |
