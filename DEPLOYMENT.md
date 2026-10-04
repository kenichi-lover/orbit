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

# 配置环境变量
cp .env.example .env
nano .env
# 必填项：APP_ENV=production / DEBUG=False / SECRET_KEY（≥32字符随机值）
#         DATABASE_URL / COOKIE_SECURE=True

# 运行 Alembic 迁移（schema 由迁移文件管理，不执行 create_all）
uv run alembic upgrade head

# 创建初始超级管理员（在数据库中直接插入或使用初始化脚本）
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
ReadWritePaths=/opt/orbit/uploads
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
    location /static/ {
        alias /opt/orbit/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 用户上传的图片（允许浏览器缓存但不过期过久）
    location /uploads/ {
        alias /opt/orbit/uploads/;
        expires 7d;
        add_header Cache-Control "public";
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
