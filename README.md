# Orbit Gallery

> **一个基于 FastAPI + Jinja2 + SQLModel 构建的沉浸式图片探索器**
>
> 不是"查看图片"，而是**进入一个世界**。图片围绕中心缓慢旋转，通过点击、搜索与筛选发现记忆。

---

## 快速开始

```bash
# 1. 安装依赖（需要 uv：https://docs.astral.sh/uv/）
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DATABASE_URL、SECRET_KEY 等

# 3. 启动开发服务器（自动重载）
uv run fastapi dev main.py

# 4. 编译 Tailwind CSS（开发时监听变更）
npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --watch
```

访问 http://localhost:8000

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Uvicorn + Jinja2 + StaticFiles |
| ORM | SQLModel + asyncpg + PostgreSQL |
| 迁移 | Alembic |
| 配置 | pydantic-settings (.env) |
| 样式 | Tailwind CSS + 手写主题 CSS |
| 交互 | Vanilla JavaScript (ES Module)，无框架 |
| 安全 | JWT + bcrypt + slowapi 限流 + secure CSP |
| 图片处理 | Pillow（缩略图生成） |

---

## 项目结构

```
orbit/
├── main.py                      # FastAPI 入口：路由注册 + 中间件 + CSP
├── pyproject.toml               # 依赖管理（uv）
├── alembic.ini                  # Alembic 配置
├── tailwind.config.js           # Tailwind 配置
├── .env.example                 # 环境变量模板
│
├── app/
│   ├── config/
│   │   ├── settings.py          # pydantic-settings 读取 .env
│   │   └── database.py          # AsyncEngine + async_sessionmaker + get_session()
│   ├── models/
│   │   ├── image.py             # Image 表模型
│   │   └── user.py              # User 表模型
│   ├── routers/
│   │   ├── api/                 # API 端点（JSON）
│   │   │   ├── auth.py          # 注册 / 登录 / 登出
│   │   │   ├── image.py         # 图片 CRUD、搜索、上传、分类枚举
│   │   │   ├── user.py          # 当前用户信息读写（/users/me）
│   │   │   └── user_admin.py    # 管理员用户管理（/admin/users/*）
│   │   ├── pages/               # Jinja2 页面渲染（HTML）
│   │   │   ├── index.py         # 首页（/）
│   │   │   ├── photo.py         # 图片详情（/photo/{id}）
│   │   │   ├── profile.py       # 个人中心（/profile）
│   │   │   └── story.py         # 叙事模式（/story）
│   │   └── health.py            # 健康检查（/health）
│   ├── services/
│   │   ├── image_service.py     # 图片业务逻辑（CRUD、搜索、缩略图生成）
│   │   ├── user_service.py      # 用户业务逻辑（CRUD）
│   │   └── storage_service.py   # 文件存储服务（头像上传、路径生成、旧文件清理）
│   ├── schemas/
│   │   ├── image_schema.py      # Image DTO（Create/Update/Public）
│   │   └── user_schema.py       # User DTO（Create/Login/Read）
│   └── utils/
│       ├── enums.py             # Category 枚举（6 种分类）
│       ├── jwt.py               # JWT 签发与验证
│       ├── limiter.py           # 请求限流（slowapi）
│       ├── pagination.py        # 分页工具
│       └── security.py          # bcrypt 哈希/校验
│
├── templates/
│   ├── base.html                # 模板继承基座（导航栏、主题切换、Modal）
│   └── pages/
│       ├── index.html           # 首页：轨道舞台 + 控制面板 + 详情面板
│       ├── photo_detail.html    # 图片详情（/photo/{id}）
│       ├── profile.html         # 个人中心（/profile）
│       └── story.html           # 叙事模式（/story）
│
├── static/
│   ├── css/
│   │   ├── input.css            # Tailwind 入口（@tailwind 指令）
│   │   ├── tailwind.css         # Tailwind 编译产物（不手工修改）
│   │   ├── coffee.css           # 咖啡馆主题：背景、咖啡杯核心、蒸汽动画
│   │   ├── orbit.css            # 轨道舞台、照片卡片、玻璃高光、全屏预览
│   │   ├── layout.css           # Detail Panel + Thumbnail Bar 布局
│   │   ├── nav.css              # 顶部导航栏 + 搜索下拉 + 轨道示意图
│   │   └── components.css       # Modal 遮罩、通用按钮、表单样式
│   ├── js/
│   │   ├── main.js              # 入口：模块加载 + 全局初始化
│   │   ├── orbit.js             # 3D 轨道动画、缩略图栏、详情面板、全屏预览
│   │   ├── nav.js               # 页面切换、搜索联动、客户端过滤
│   │   ├── filter.js            # 筛选面板（分类 chip + 标签 chip）
│   │   ├── auth.js              # 登录/注册 Modal + JWT 存储
│   │   ├── upload.js            # 图片上传 Modal + 分类加载
│   │   ├── story.js             # 叙事模式渲染、编辑/删除、XSS 防护
│   │   └── profile.js           # 个人中心图片列表渲染
│   └── images/                  # 内置展示用图片（提交到 Git）
│
└── uploads/                     # 用户上传文件（不提交 Git）
```

---

## API 路由

### 认证

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/auth/register` | POST | 否 | 注册（返回 JWT + httpOnly cookie） |
| `/api/auth/login` | POST | 否 | 登录（返回 JWT + httpOnly cookie） |
| `/api/auth/logout` | POST | 是 | 登出（清除 cookie） |

### 图片

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/categories` | GET | 否 | 返回分类枚举值 |
| `/api/images` | GET | 否 | 图片列表（分页，公开） |
| `/api/search` | GET | 否 | 搜索（关键词 / 分类 / 标签 / 作者） |
| `/api/images/upload` | POST | 是 | 上传图片 |
| `/api/images/{id}` | GET | 否 | 图片详情 |
| `/api/images/{id}` | PUT | 是 | 更新元数据（仅作者或管理员） |
| `/api/images/{id}` | DELETE | 是 | 软删除（仅作者或管理员） |

### 用户

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/users/me` | GET | 是 | 当前用户信息 |
| `/api/users/me` | PATCH | 是 | 更新当前用户 |
| `/api/users/me/avatar` | POST | 是 | 上传头像 |
| `/api/users/me/password` | PATCH | 是 | 修改密码 |

### 管理员（仅超级管理员）

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/admin/users` | GET | 是 + 管理员 | 用户列表 |
| `/api/admin/users/{id}` | GET | 是 + 管理员 | 用户详情 |
| `/api/admin/users/{id}` | PATCH | 是 + 管理员 | 更新用户（禁止撤销自身权限） |
| `/api/admin/users/{id}/password` | PATCH | 是 + 管理员 | 强制重置密码 |
| `/api/admin/users/{id}` | DELETE | 是 + 管理员 | 禁用用户（禁止删除自身） |

### 页面路由

| 路由 | 说明 |
|------|------|
| `/` | 首页（3D 轨道舞台） |
| `/photo/{id}` | 图片详情 |
| `/profile` | 个人中心（需登录） |
| `/story` | 叙事模式 |
| `/health` | 健康检查（无需认证） |

---

## 功能概览

### 已完成 ✅

- 3D 多层轨道动画（双环，深度驱动 scale + opacity）
- 全页咖啡馆主题背景 + 咖啡杯核心 + 脉冲光晕
- 顶部导航栏（搜索、相册/叙事切换、主题切换、头像）
- 底部缩略图栏（分页，点击缩略图触发详情面板）
- 右侧详情面板（标题、描述、标签、作者、日期）
- 全屏图片预览（点击轨道图片，居中展示原尺寸，ESC / 遮罩点击关闭）
- 轨道示意图 Navigator（Canvas 俯视图，实时同步照片位置）
- 速度 / 视角控制滑块
- 客户端实时搜索（标题 / 标签 / 分类匹配）
- 分类 + 标签筛选面板（toggle 切换，RESTful 枚举驱动）
- 深色 / 浅色主题（localStorage 持久化）
- 叙事模式（时间线 + 编辑 / 删除，权限控制 + XSS 防护）
- 完整认证体系（JWT + httpOnly cookie + bcrypt）
- 管理员接口（5 个端点，全部 require_superuser 守卫）
- 头像上传（上传 → 存储 → URL 写入数据库，接口已联调）
- 请求限流（slowapi，基于 IP）
- CSP 安全头（secure 中间件）

### 待完善 🔲

- 鼠标拖拽旋转轨道（P0）
- 惯性旋转（松开后动量衰减，P0）
- 滚轮缩放 / 视角调整（P0）
- 点击照片飞入中心的过渡动画（P0）
- 蒸汽动画 `initSteam()` 占位实现（P2）

---

## 前端架构

### CSS 文件分工

| 文件 | 职责 |
|------|------|
| `input.css` | Tailwind 入口（`@tailwind` 指令） |
| `tailwind.css` | Tailwind 编译产物（不手工修改） |
| `coffee.css` | 咖啡馆主题：背景、咖啡杯核心、蒸汽动画、脉冲光晕 |
| `orbit.css` | 轨道舞台、装饰环、照片卡片、全屏图片预览、控制按钮 |
| `layout.css` | Detail Panel + Thumbnail Bar 布局 |
| `nav.css` | 顶部导航栏 + 搜索下拉 + 轨道示意图 |
| `components.css` | Modal 遮罩、通用按钮、表单样式 |

### JavaScript 模块

| 文件 | 职责 |
|------|------|
| `main.js` | 入口：模块加载 + 全局初始化 |
| `orbit.js` | 3D 轨道动画、缩略图栏、详情面板、全屏预览、主题切换、Navigator |
| `nav.js` | 页面切换（相册/叙事）、搜索接口联动、客户端过滤 |
| `filter.js` | 筛选面板（分类 chip + 标签 chip，toggle 切换，重置） |
| `auth.js` | 登录/注册 Modal 切换、表单提交、JWT 存储、登出 |
| `upload.js` | 图片上传 Modal、FormData 提交、分类选项加载 |
| `story.js` | 叙事模式渲染、编辑/删除操作、权限校验、XSS 防护 |
| `profile.js` | 个人中心图片列表渲染 |

### 动画原则

- 全部使用浏览器原生能力：`requestAnimationFrame`、CSS Transform、CSS Variables
- 不使用任何动画框架（GSAP / Three.js / React 等）
- 深度驱动 scale + opacity（近大远小、近亮远暗）
- XZ 平面投影实现真实前后深度感

---

## 数据库模型

### Image

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| original_filename | str | 原始文件名 |
| file_name | str (unique) | 存储用唯一文件名 |
| relative_path | str | 存储相对路径（从 static/ 起算） |
| thumbnail_relative_path | str \| None | 缩略图路径 |
| file_size | int | 文件大小（字节） |
| mime_type | str | MIME 类型 |
| width | int \| None | 图片宽度 |
| height | int \| None | 图片高度 |
| title | str \| None | 标题 |
| description | str \| None | 描述 |
| alt_text | str \| None | 无障碍 alt 属性 |
| category | `category` ENUM | 分类（GALLERY / TRAVEL / NATURE / PORTRAIT / ARCHITECTURE / ABSTRACT） |
| tags | `text[]` ARRAY | 标签数组（NOT NULL，server_default `'{}'`） |
| author_id | int (FK → users.id) | 上传者用户 ID |
| created_at | datetime (TZ) | 创建时间 |
| updated_at | datetime (TZ) | 更新时间 |
| is_deleted | bool | 软删除标记 |
| deleted_at | datetime \| None | 删除时间 |

### User

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK, auto) | 主键 |
| username | str (unique) | 用户名 |
| email | str (unique) | 邮箱 |
| hashed_password | str | bcrypt 哈希密码 |
| is_active | bool | 激活状态 |
| is_superuser | bool | 超级管理员 |
| avatar_url | str \| None | 头像 URL（持久化到数据库） |
| created_at | datetime (TZ) | 注册时间 |
| updated_at | datetime (TZ) | 更新时间 |

---

## 环境变量

详见 `.env.example`：

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | ✅ | PostgreSQL 连接串，格式 `postgresql+asyncpg://user:pass@host:port/dbname` |
| `SECRET_KEY` | ✅ | JWT 签名密钥，生产环境至少 32 字符的强随机值 |
| `APP_ENV` | ✅ | `development` / `production` / `testing` |
| `DEBUG` | - | 调试模式，生产环境必须为 `False` |
| `UPLOAD_DIR` | - | 上传文件目录（相对于项目根），默认 `uploads` |
| `ASSETS_BASE_URL` | - | 图片 CDN 基础 URL，部署时配置以支持 CDN 分发 |

### 上传与存储

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `STATIC_DIR` | `static` | 静态文件根目录 |
| `IMAGES_DIR` | `static/images` | 用户上传的图片存储目录 |
| `AVATARS_DIR` | `static/avatars` | 用户头像存储目录 |
| `MAX_IMAGE_FILE_SIZE` | 10 MB | 图片上传大小上限 |
| `MAX_AVATAR_SIZE` | 5 MB | 头像上传大小上限 |
| `THUMBNAIL_WIDTH` | 300 | 缩略图宽度（px） |
| `THUMBNAIL_HEIGHT` | 300 | 缩略图高度（px） |

生产环境 `SECRET_KEY` 长度不足 32 位或 `DEBUG=True` 时，应用启动会直接报错退出。

---

## 部署

详见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

### 快速参考

```bash
# 安装系统依赖
sudo apt install postgresql nginx

# 初始化数据库并运行迁移
createdb orbit
uv run alembic upgrade head

# 创建超级管理员账号（首次启动）
# 在数据库中直接插入，或编写初始化脚本

# 生产启动（Gunicorn + Uvicorn workers）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 前台启动（开发 / 调试）
uv run fastapi dev main.py
```

---

## 开发约定

- **依赖注入**：统一使用 `Annotated[Type, Depends(...)]` 风格
- **枚举**：业务分类值定义在 `app/utils/enums.py`，Router 层使用枚举类型校验
- **权限**：受保护 API 使用 `get_current_user`，页面渲染使用 `resolve_user_from_cookie`
- **ES Module 时序**：前端用户数据从 DOM `#current-user-data` 读取，避免模块加载竞态
- **XSS 防护**：所有用户输入通过 `escapeHtml()` 转义后再渲染到 DOM
- **安全头**：CSP 由 `secure` 中间件统一注入，新增路由无需额外配置
