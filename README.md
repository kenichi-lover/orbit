# Orbit Gallery

> **一个基于 FastAPI + Jinja2 + SQLModel 构建的沉浸式图片探索器**

不是"查看图片"，而是**进入一个世界**。图片围绕中心缓慢旋转，通过拖拽、滚轮、点击与记忆交互。

---

## 快速开始

```bash
# 安装依赖
uv sync

# 配置数据库（.env）
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/orbit_db

# 启动开发服务器
uv run fastapi dev main.py

# 编译 Tailwind CSS（文件变更时自动重新编译）
npx tailwindcss -i static/css/input.css -o static/css/tailwind.css --watch
```

访问 http://localhost:8000

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Uvicorn + Jinja2 |
| ORM | SQLModel + asyncpg |
| 迁移 | Alembic |
| 配置 | pydantic-settings (.env) |
| 样式 | Tailwind CSS + 手写主题 CSS |
| 交互 | Vanilla JavaScript (ES Module)，无框架 |
| 文件上传 | python-multipart |

---

## 项目结构

```
orbit/
├── main.py                      # FastAPI 入口：路由注册 + 静态文件挂载
├── pyproject.toml               # 依赖管理（uv）
├── .env                         # 环境变量（不提交 Git）
├── tailwind.config.js           # Tailwind 配置
│
├── app/
│   ├── config/
│   │   ├── setting.py           # pydantic-settings 读取 .env
│   │   └── database.py          # AsyncEngine + async_sessionmaker + get_session()
│   ├── models/
│   │   ├── image.py             # Image 表模型（SQLModel table=True）
│   │   └── user.py              # User 表模型
│   ├── routers/                 # API 路由（待实现）
│   ├── services/                # 业务逻辑层（待实现）
│   ├── repositories/            # 数据访问层（待实现）
│   └── schemas/                 # Pydantic DTO（待实现）
│
├── templates/
│   ├── base.html                # 模板继承基座
│   └── index.html               # 首页：导航栏 + 轨道舞台 + 详情面板
│
├── static/
│   ├── css/
│   │   ├── input.css            # Tailwind 入口（@tailwind 指令）
│   │   ├── tailwind.css         # 编译产物（不手工修改）
│   │   ├── coffee.css           # 咖啡馆主题：背景、灯光、蒸汽动画
│   │   ├── orbit.css            # 轨道舞台、装饰环、照片卡片、Detail Panel
│   │   ├── layout.css           # Detail Panel + Thumbnail Bar 布局
│   │   └── nav.css              # 顶部导航栏 + 搜索下拉
│   ├── js/
│   │   ├── main.js              # 入口：模块加载 + 初始化
│   │   └── orbit.js             # 核心：3D 轨道动画、缩略图栏、搜索、主题切换
│   └── images/
│       ├── background.webp      # 咖啡馆背景图
│       └── *.webp               # 轨道展示用图片
│
└── uploads/                     # 用户上传文件（.gitignore）
```

---

## 前端架构

### CSS 文件分工

| 文件 | 职责 |
|------|------|
| `tailwind.css` | Tailwind 预飞指令编译产物 |
| `coffee.css` | 背景、咖啡杯核心、蒸汽动画、脉冲光晕 |
| `orbit.css` | 轨道舞台、装饰环、照片卡片、玻璃高光、悬停效果、Detail Panel、Thumbnail Bar |
| `layout.css` | Detail Panel + Thumbnail Bar 补充布局 |
| `nav.css` | 顶部导航栏 + 搜索下拉 + 轨道示意图 |

### JavaScript 模块

| 文件 | 职责 |
|------|------|
| `main.js` | 入口：加载 orbit.js，初始化全局行为 |
| `orbit.js` | 3D 多层轨道动画、缩略图栏、客户端搜索、主题切换、Navigator 轨道示意图 |

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
| filename | str | 原始文件名 |
| storage_path | str | 实际存储路径 |
| thumbnail_path | str \| None | 缩略图路径 |
| title | str \| None | 标题 |
| description | str \| None | 描述 |
| user_id | int (FK) | 上传用户 |
| created_at | datetime (TZ) | 创建时间 |
| updated_at | datetime (TZ) | 更新时间 |

### User

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 主键 |
| username | str (unique) | 用户名 |
| email | str (unique) | 邮箱 |
| hashed_password | str | bcrypt 哈希密码 |
| is_active | bool | 激活状态 |
| is_superuser | bool | 超级管理员 |
| created_at | datetime (TZ) | 注册时间 |
| updated_at | datetime (TZ) | 更新时间 |

---

## World 概念

同一个 Orbit 引擎，不同的视觉主题：

| World | 主题色 | 氛围 |
|-------|--------|------|
| ☕ Coffee World | 暖棕 + 暗调 | 夜晚咖啡馆 |
| 🖼 Museum World | 黑白 + 聚光灯 | 现代艺术馆 |
| 🌌 Space World | 深蓝 + 粒子 | 宇宙深空 |
| 🌳 Forest World | 翠绿 + 柔光 | 森林秘境 |

切换 World 仅改变背景、配色和灯光，业务逻辑完全不变。

---

## 开发路线

| 阶段 | 目标 | 数据库 | 状态 |
|------|------|--------|------|
| V0.1 | FastAPI 初始化 + Tailwind CSS | ❌ | ✅ 完成 |
| V0.2 | 咖啡馆背景 + Orbit 基础旋转 | ❌ | ✅ 完成 |
| V0.3 | 完整轨道动画 + 搜索 + 主题切换 + Navigator | ❌ | ✅ 完成 |
| V0.4 | SQLModel + PostgreSQL + 数据模型 | ✅ | 🚧 模型已定义 |
| V0.5 | 图片上传 + 相册 + 搜索后端化 | ✅ | 🔲 待开发 |
| V0.6 | Story 模块 + Detail Panel 美化 | ✅ | 🔲 待开发 |
| V1.0 | Coffee World 完整体验 | ✅ | 🔲 待开发 |

---

## 未完成任务

### P0 — 交互完善
- [ ] 鼠标拖拽旋转轨道
- [ ] 惯性旋转（松开后动量衰减）
- [ ] 滚动缩放
- [ ] 图片聚焦 / 飞向中心
- [ ] 速度滑块 & 视角滑块联动

### P1 — 数据层
- [ ] PostgreSQL 连接 + DDL 建表（lifespan 中调用）
- [ ] 图片上传（multipart + Pillow WebP 压缩）
- [ ] Router / Service / Schema 分层实现
- [ ] 搜索后端化

### P2 — 功能扩展
- [ ] 叙事模式切换
- [ ] 筛选面板
- [ ] 用户系统（登录 / 注册 / JWT）
- [ ] 收藏 / 下载 / 分享

---

## 已知问题

1. `layout.css` 中存在缩进不一致（部分类名前多 2 空格），不影响功能。
2. `initSteam()` 是空函数占位，蒸汽效果尚未实现。
3. 速度滑块和视角滑块已有 HTML/CSS，但未绑定 JS 事件。
4. `#detail-panel` 的 `showDetail()` 目前仅做显示切换，未与照片数据联动。
5. 照片数据全部硬编码在 `config.imageUrls` 中。
6. `app/models/user.py` 中 `images` 关系定义缩进错误（应在类体内而非类体外）。

---

## 项目原则

1. 优先使用浏览器原生能力，不引入重型框架
2. Tailwind 仅负责基础布局，复杂动画交给手写 CSS + JS
3. 一个文件负责一个职责
4. 每次迭代只完成一个明确功能，并确保可运行
5. 保持简单、稳定、可维护
