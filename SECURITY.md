# Orbit Gallery — 安全说明

---

## 已实施的安全措施

### 认证与授权

| 措施 | 实现位置 | 说明 |
|------|----------|------|
| JWT 签名 | `app/utils/jwt.py` | HS256 算法，密钥来自环境变量 `SECRET_KEY` |
| httpOnly Cookie | `app/routers/api/auth.py` | Token 存储在 `access_token` httpOnly cookie，防止 XSS 窃取 |
| 密码哈希 | `app/utils/security.py` | argon2-cffi 哈希，不可逆 + 时序攻击防护 |
| 角色守卫 | `app/dependencies/auth.py` | `require_superuser` 中间层依赖，5 个管理员端点均已使用 |
| 图片访问控制 | `app/routers/api/image.py` | `_ensure_image_access()` 校验作者 / 管理员权限 |

### 传输安全

| 措施 | 实现位置 | 说明 |
|------|----------|------|
| CSP 头 | `main.py` Secure 中间件 | `default-src 'self'`，限制脚本 / 图片 / 字体来源 |
| 请求限流 | `app/utils/limiter.py` | slowapi 基于 IP 速率限制，防止暴力破解 |
| Cookie 安全属性 | `app/config/settings.py` | `COOKIE_SECURE=True`（仅 HTTPS 发送），`SameSite=Lax` |

### 输入防护

| 措施 | 说明 |
|------|------|
| XSS 转义 | 所有用户输入通过 `escapeHtml()` 转义后渲染到 DOM |
| 参数校验 | SQLModel + Pydantic 严格类型校验，防止 SQL 注入 |
| 文件类型白名单 | `ALLOWED_IMAGE_EXTENSIONS` 限定 jpg/png/gif/webp |
| 文件大小限制 | 默认 10MB，由 `MAX_UPLOAD_SIZE` 控制 |

---

## 已知安全风险与建议

### 🔴 高优先级

| 风险 | 说明 | 修复建议 |
|------|------|----------|
| SECRET_KEY 硬编码风险 | 开发环境 `.env.example` 含示例值，勿提交真实密钥 | 使用 CI/CD 注入环境变量或 secrets manager |
| 无 CSRF 保护 | ~~页面级表单（如故事编辑）未使用 CSRF token~~ | ✅ 已评估豁免：httpOnly Cookie + SameSite=Lax 阻断攻击路径，所有写操作均为 fetch JSON API，无服务端 HTML POST 表单；详见下方决策记录 |

### 🟡 中优先级

| 风险 | 说明 | 修复建议 |
|------|------|----------|
| 无账号锁定 | 登录失败次数无上限，存在暴力破解风险 | 添加失败次数计数 + 临时锁定 |
| 无邮件验证 | 注册无需邮箱确认，可创建虚假账号 | 添加注册邮件确认流程 |
| 软删除数据泄露 | 被删除图片的元数据仍可通过 admin 接口查询 | 确认管理员接口已加权限守卫（✅ 已修复） |

### 🟢 低优先级

| 风险 | 说明 | 修复建议 |
|------|------|----------|
| CORS 未显式配置 | 当前仅允许同源，如有前端分离需更新 CSP | 按部署架构调整 `connect_src` 和 `script_src` |
| 日志敏感信息 | `main.py` 已启用 `RotatingFileHandler`，但日志格式未对密码/token 做脱敏 | 在 auth 相关 handler 中过滤敏感字段，避免明文 token 写入日志 |

---

## 生产环境安全检查清单

部署前逐项确认：

- [ ] `APP_ENV=production`
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` 为至少 32 字符的强随机值
- [ ] PostgreSQL 使用独立用户（非 root），最小权限原则
- [ ] Nginx 已配置 HTTPS（Let's Encrypt / 自有证书）
- [ ] `uploads/` 目录仅应用进程可写，不可直接 URL 访问
- [ ] 数据库备份策略已配置（定时 + 异地）
- [ ] 防火墙仅开放 80/443 端口
- [ ] 管理员账号使用强密码
- [ ] `.env` 已从 `.gitignore` 排除，未提交到 Git

---

## CSRF 保护豁免决策（2026-10）

**结论：** 不引入 CSRF token。

**理由：**
- 认证凭证为 httpOnly Cookie，前端 JS 无法读取，XSS 窃取凭证不可行
- Cookie 设置 SameSite=Lax，浏览器层面已阻断跨站 POST 攻击路径
- 全量排查（grep app/routers/pages/ 与 app/templates/）确认：项目不存在服务端渲染的 `<form method="POST">`，所有写操作均为 fetch 发起的 JSON API
- 未使用跨子域 Cookie，无 SameSite 相关边界场景

**复核条件（任一成立时需重新评估并引入 CSRF token）：**
- 新增服务端渲染的 HTML 表单提交
- Cookie 的 SameSite 属性改为 None
- 出现跨子域共享 Cookie 的需求（如 `a.example.com` 与 `b.example.com`）
