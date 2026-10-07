# Orbit Gallery — 运维操作清单

> 本文档记录部署所需的外部配置和运维操作，代码本身已全部就绪。

---

## 一、服务器准备（一次性）

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y postgresql nginx certbot python3-certbot-nginx libmagic1

# 创建系统用户（隔离运行权限）
sudo useradd -r -s /usr/sbin/nologin orbit
```

---

## 二、数据库初始化（首次部署）

```bash
# 以 postgres 用户创建数据库和用户
sudo -u postgres psql

CREATE DATABASE orbit;
CREATE USER orbit_user WITH PASSWORD '<强密码>';
ALTER ROLE orbit_user SET client_encoding TO 'utf8';
ALTER ROLE orbit_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE orbit TO orbit_user;
GRANT ALL ON SCHEMA public TO orbit_user;  -- PG15+ 必需，否则 alembic 建表无权限
\q
```

---

## 三、项目部署

```bash
# 克隆并安装
cd /opt
git clone git@github.com:<user>/orbit.git orbit
cd orbit
uv sync
uv add gunicorn  # gunicorn 不在项目依赖中，但 systemd 启动必需（见第四节）

# 配置环境变量
cp .env.example .env
nano .env
# 必填项：APP_ENV=production / DEBUG=False / SECRET_KEY（≥32字符随机值）
#         DATABASE_URL / COOKIE_SECURE=True

# 运行 Alembic 迁移（schema 由迁移文件管理，不执行 create_all）
uv run alembic upgrade head

# 初始超级管理员：项目没有初始化脚本，且 user_admin 路由全部要求已有超管权限
#（鸡生蛋问题），需手动插入。注意 session 工厂导出名为 async_session_factory：
uv run python - <<'EOF'
import asyncio
from sqlmodel import select
from app.config.database import async_session_factory
from app.models.user import User
from app.utils.security import hash_password

async def main():
    async with async_session_factory() as s:
        existing = (await s.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
        if not existing:
            s.add(User(username="admin", email="admin@example.com",
                       hashed_password=hash_password("<强密码>"),
                       is_superuser=True, is_active=True))
            await s.commit()
            print("超级管理员已创建")
        else:
            print("已存在，跳过")

asyncio.run(main())
EOF
```

---

## 四、启动服务

### Systemd 服务

```bash
# 创建服务文件
sudo tee /etc/systemd/system/orbit.service > /dev/null << 'EOF'
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
# 图片写入 static/images、static/avatars（uploads 仅为启动时创建的运行时目录）
ReadWritePaths=/opt/orbit/static /opt/orbit/uploads
EOF

# 启用并启动
sudo systemctl daemon-reload
sudo systemctl enable orbit
sudo systemctl start orbit
sudo systemctl status orbit
```

---

## 五、Nginx 反向代理

```bash
# 创建站点配置
sudo tee /etc/nginx/sites-available/orbit > /dev/null << 'EOF'
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

    # 静态文件由 Nginx 直接服务
    # 业务上传的图片存于 static/images/{年}/{月}/{uuid}.ext、头像存 static/avatars/，
    # 均在此目录下；文件名含 uuid 不可变，可安全使用 immutable
    location /static/ {
        alias /opt/orbit/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/orbit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 六、HTTPS（Let's Encrypt）

```bash
sudo certbot --nginx -d your-domain.com
# 按提示输入邮箱，确认自动续期配置
```

验证：
```bash
curl -I https://your-domain.com/health
# 应返回 HTTP/2 200
```

---

## 七、定时备份

```bash
# 创建备份目录
sudo mkdir -p /backups/orbit
sudo chown orbit:www-data /backups/orbit

# 添加 crontab（每日凌晨 3 点备份）
sudo crontab -u orbit -e

# 输入以下内容：
0 3 * * * pg_dump -U orbit_user orbit | gzip > /backups/orbit_$(date +\%Y\%m\%d).sql.gz
0 4 * * * find /backups/orbit -name "orbit_*.sql.gz" -mtime +7 -delete
```

---

## 八、上线检查清单

```
[ ] .env 已填写，SECRET_KEY ≥ 32 字符随机值
[ ] APP_ENV=production，DEBUG=False
[ ] Alembic 迁移执行成功：uv run alembic upgrade head
[ ] 至少一个超级管理员账号已创建
[ ] systemd 服务运行正常：sudo systemctl status orbit
[ ] Nginx 配置无语法错误：sudo nginx -t
[ ] HTTPS 证书有效：curl -I https://your-domain.com/health
[ ] 备份 cron 任务已配置并测试执行一次
[ ] 防火墙仅开放 80/443 端口
[ ] uploads/ 目录可写：ls -la /opt/orbit/uploads/
```

---

## 九、常见问题排查

| 现象 | 排查命令 |
|------|----------|
| 服务无法启动 | `sudo journalctl -u orbit -n 50` |
| 静态文件 404 | `sudo nginx -t`；确认 alias 路径正确 |
| 图片上传失败 | `ls -la /opt/orbit/uploads/` 权限属主为 orbit |
| 数据库连接失败 | 确认 `DATABASE_URL` 格式正确，PostgreSQL 正在运行 |
| HTTPS 证书过期 | `sudo certbot renew --dry-run` |
| 日志过大 | `sudo journalctl --vacuum-size=100M` |


## 十 项目生产上线优化

原文档方案	实际采用
Nginx 容器 + certbot 签发 HTTPS	❌ 跳过，Cloudflare Tunnel 边缘终结 HTTPS
cloudflared 未涉及	✅ systemd 常驻，配置 /etc/cloudflared/config.yml（或用户级 ~/.cloudflared/），ingress → http://localhost:8000
TCP + 密码连数据库	✅ Unix socket + peer 认证：postgresql+asyncpg:///orbit?host=/var/run/postgresql
ProtectHome=true	⚠️ 必须用 read-only（项目在 /home 下），否则 Status=226
worker 类 uvicorn.workers.UvicornWorker	✅ 新包名 uvicorn_worker.UvicornWorker
gunicorn 4 worker	✅ 2 worker（连接池 = 2 × (10+20) = 60 上限，足够）
ExecStart	加 --no-control-socket 避免 ProtectHome=read-only 下的 control socket 报错


上线清单(全部清零)
✅ 数据库：orbit 库、paul 角色、socket peer 认证、迁移至 ec2f092f4bd5
✅ 依赖：gunicorn 26.2.0 + uvicorn-worker 0.4.0
✅ 配置：.env production 校验通过、SECRET_KEY 强随机
✅ 超管：admin + paul
✅ 应用：orbit.service active，2 worker，/health 200
✅ 隧道：cloudflared systemd 常驻，CONNECTIONS ×2
✅ 域名：https://paul-nebula.online 端到端可达，安全头齐全
🟡 待办：enable orbit、--no-control-socket、备份 cron、DEPLOYMENT.md 更新

