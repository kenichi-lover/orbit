# Orbit Gallery

> **一个基于 FastAPI + Jinja2 + SQLModel 构建的沉浸式图片探索器**
>
> 不是"查看图片"，而是**进入一个世界**。图片围绕中心缓慢旋转，通过拖拽、滚轮、点击与记忆交互。

---

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 复制并配置环境变量
cp .env.example .env
# 编辑 .env，填入 DATABASE_URL、SECRET_KEY 等

# 3. 启动开发服务器
uv run fastapi dev main.py

# 4. 编译 Tailwind CSS（开发时自动监听文件变更）
npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --watch
```

访问 http://localhost:8000

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Uvicorn + Jinja2 |
| ORM | SQLModel + asyncpg + PostgreSQL |
| 迁移 | Alembic |
| 配置 | pydantic-settings (.env) |
| 样式 | Tailwind CSS + 手写主题 CSS |
| 交互 | Vanilla JavaScript (ES Module)，无框架 |
| 安全 | JWT + bcrypt + slowapi 限流 + secure CSP |
| 文件上传 | python-multipart + Pillow (缩略图生成) |

---

## 项目结构

```
orbit/
├── main.py                      # FastAPI 入口：路由注册 + 静态文件挂载
├── pyproject.toml               # 依赖管理（uv）
├── .env                         # 环境变量（不提交 Git）
├── .env.example                 # 环境变量模板
├── alembic.ini                  # Alembic 配置
├── tailwind.config.js           # Tailwind 配置
│
├── app/
│   ├── config/
│   │   ├── settings.py          # pydantic-settings 读取 .env
│   │   └── database.py          # AsyncEngine + async_sessionmaker + get_session()
│   ├── models/
│   │   ├── image.py             # Image 表模型（SQLModel table=True）
│   │   └── user.py              # User 表模型
│   ├── routers/
│   │   ├── api/                 # API 端点（JSON）：auth、image、user
│   │   ├── pages/               # Jinja2 页面渲染：index、photo、profile、story
│   │   └── health.py            # 健康检查
│   ├── services/
│   │   ├── image_service.py     # 图片 CRUD 与搜索
│   │   └── user_service.py      # 用户 CRUD
│   ├── schemas/
│   │   ├── image_schema.py      # Image DTO（Create/Update/Public/SearchParams）
│   │   └── user_schema.py       # User DTO（Create/Login/Read）
│   └── utils/
│       ├── enums.py             # Category 枚举（6 种分类）
│       ├── jwt.py               # JWT 签发与验证
│       ├── limiter.py           # 请求限流
│       ├── pagination.py        # 分页工具
│       └── security.py          # bcrypt 哈希/校验
│
├── templates/
│   ├── base.html                # 模板继承基座（导航栏、主题切换、Modal）
│   └── pages/
│       ├── index.html           # 首页：导航栏 + 轨道舞台 + 详情面板 + 控制面板
│       ├── photo_detail.html    # 图片详情（/photo/{id}）
│       ├── profile.html         # 个人中心（/profile）
│       └── story.html           # 叙事模式（/story）
│
├── static/
│   ├── css/
│   │   ├── input.css            # Tailwind 入口（@tailwind 指令）
│   │   ├── tailwind.css         # Tailwind 编译产物（不手工修改）
│   │   ├── coffee.css           # 咖啡馆主题：背景、咖啡杯核心、蒸汽动画
│   │   ├── orbit.css            # 轨道舞台、装饰环、照片卡片、玻璃高光
│   │   ├── layout.css           # Detail Panel + Thumbnail Bar 布局
│   │   ├── nav.css              # 顶部导航栏 + 搜索下拉 + 轨道示意图
│   │   └── components.css       # Modal 遮罩、通用按钮、表单样式
│   ├── js/
│   │   ├── main.js              # 入口：模块加载 + 全局初始化
│   │   ├── orbit.js             # 3D 轨道动画、缩略图栏、详情面板、主题、Navigator
│   │   ├── nav.js               # 页面切换（相册/叙事）、搜索联动
│   │   ├── filter.js            # 筛选面板（分类 chip + 标签 chip）
│   │   ├── auth.js              # 登录/注册 Modal + JWT 存储
│   │   ├── upload.js            # 图片上传 Modal + 分类加载
│   │   ├── story.js             # 叙事模式渲染 + 编辑/删除
│   │   └── profile.js           # 个人中心渲染
│   └── images/
│       ├── background.webp      # 咖啡馆背景图
│       └── *.webp               # 轨道展示用图片
│
└── uploads/                     # 用户上传文件（.gitignore）
```

### API 路由

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 注册（返回 JWT + cookie） |
| `/api/auth/login` | POST | 登录（返回 JWT + cookie） |
| `/api/auth/logout` | POST | 登出 |
| `/api/categories` | GET | 返回所有分类枚举值 |
| `/api/images` | GET | 图片列表（分页） |
| `/api/images/upload` | POST | 图片上传（支持匿名） |
| `/api/images/{id}` | GET | 图片详情 |
| `/api/images/{id}` | POST | 更新图片元数据 |
| `/api/images/{id}` | DELETE | 删除图片（软删/硬删） |
| `/api/search` | GET | 搜索（关键词 + 分类 + 标签） |
| `/api/me` | GET | 当前用户信息 |
| `/health` | GET | 健康检查 |

### 页面路由

| 路由 | 说明 |
|------|------|
| `/` | 首页（轨道舞台） |
| `/photo/{id}` | 图片详情 |
| `/profile` | 个人中心 |
| `/story` | 叙事模式 |

---

## 前端架构

### CSS 文件分工

| 文件 | 职责 |
|------|------|
| `input.css` | Tailwind 入口（`@tailwind` 指令） |
| `tailwind.css` | Tailwind 编译产物（不手工修改） |
| `coffee.css` | 咖啡馆主题：背景、咖啡杯核心、蒸汽动画、脉冲光晕 |
| `orbit.css` | 轨道舞台、装饰环、照片卡片、玻璃高光、悬停效果、Detail Panel |
| `layout.css` | Detail Panel + Thumbnail Bar 补充布局 |
| `nav.css` | 顶部导航栏 + 搜索下拉 + 轨道示意图 |
| `components.css` | Modal 遮罩、通用按钮、表单样式 |

### JavaScript 模块

| 文件 | 职责 |
|------|------|
| `main.js` | 入口：模块加载 + 全局初始化 |
| `orbit.js` | 3D 轨道动画、缩略图栏、详情面板、主题切换、Navigator 轨道示意图 |
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

## 页面结构

```
┌───────────────────────────────────────────────┐
│                  Navigation                   │
│         搜索 · 相册/叙事 · 主题切换 · 头像      │
├───────────────────────────────────────────────┤
│                                               │
│               Orbit Gallery                   │
│          ◎ 咖啡杯核心 + 双层装饰环              │
│          照片围绕中心旋转                       │
│                                               │
├──────────┬────────────────────────────────────┤
│ Navigator│                Detail Panel         │
│ (Canvas) │         标题 · 时间 · 标签 · 故事    │
├──────────┴────────────────────────────────────┤
│            Thumbnail Bar (Timeline)            │
└───────────────────────────────────────────────┘
```

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
| category | str | 分类（默认 "Gallery"） |
| tags | str \| None | 逗号分隔标签 |
| user_name | str (FK) | 上传者用户名 |
| created_at | datetime (TZ) | 创建时间 |
| updated_at | datetime (TZ) | 更新时间 |
| is_deleted | bool | 软删除标记 |
| deleted_at | datetime \| None | 删除时间 |

### User

| 字段 | 类型 | 说明 |
|------|------|------|
| username | str (PK) | 用户名 |
| email | str (unique) | 邮箱 |
| hashed_password | str | bcrypt 哈希密码 |
| is_active | bool | 激活状态 |
| is_superuser | bool | 超级管理员 |
| created_at | datetime (TZ) | 注册时间 |
| updated_at | datetime (TZ) | 更新时间 |

---

## 已知问题

| 问题 | 影响 | 优先级 |
|------|------|--------|
| `initSteam()` 是空函数占位，蒸汽效果尚未实现 | 视觉体验不完整 | P2 |
| 鼠标拖拽旋转轨道尚未实现 | 交互能力受限 | P0 |
| 惯性旋转（松开后动量衰减）尚未实现 | 交互体验缺失 | P0 |
| 鼠标滚轮缩放尚未实现 | 交互能力受限 | P0 |
| 图片聚焦/飞向中心动画尚未实现 | 视觉动效缺失 | P0 |

---

## 环境变量（.env）

```bash
# 运行环境
APP_ENV=production

# PostgreSQL 连接串
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/orbit

# JWT 密钥（至少 32 字符）
SECRET_KEY=your-super-long-secret-key-at-least-32-bytes

# 调试模式（生产环境设为 False）
DEBUG=False

# 上传文件目录（相对于项目根）
UPLOAD_DIR=uploads

# 图片 CDN/基础 URL（可选，部署时配置）
ASSETS_BASE_URL=
```

---

## 部署

### 生产部署要点

1. 将 `APP_ENV` 设为 `production`，跳过 `create_all` 自动建表
2. 使用 Alembic 进行数据库迁移：
   ```bash
   alembic revision --autogenerate -m "initial schema"
   alembic upgrade head
   ```
3. 配置反向代理（Nginx）+ ASGI 服务器（Uvicorn gunicorn worker）
4. 设置 `ASSETS_BASE_URL` 指向 CDN，便于静态资源分发
5. 使用 `SECRET_KEY` 生成强随机密钥，切勿提交到 Git
6. 将 `uploads/` 目录纳入备份策略

### 推荐部署方式

```bash
# 生产启动（Gunicorn + Uvicorn workers）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 开发约定

- **依赖注入**：统一使用 `Annotated[Type, Depends(...)]` 风格
- **枚举**：业务分类值定义在 `app/utils/enums.py`，Router 层使用枚举类型校验
- **权限**：受保护 API 使用 `get_current_user`，页面渲染使用 `resolve_user_from_cookie`
- **ES Module 时序**：前端用户数据从 DOM `#current-user-data` 读取，避免模块加载竞态
- **XSS 防护**：所有用户输入通过 `escapeHtml()` 转义后再渲染到 DOM
