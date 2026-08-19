# Orbit Gallery — 项目进度

> 最后更新：2026-08-19

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Jinja2 + StaticFiles |
| 前端 | 原生 HTML/CSS/JS (ES Module)，无框架 |
| 构建 | Tailwind CSS（`input.css` → `tailwind.css`） |
| 数据库 | SQLModel + asyncpg + PostgreSQL（计划中） |
| ORM 迁移 | Alembic |
| 配置 | pydantic-settings (.env) |

---

## 已完成功能

### 后端

- [x] FastAPI 项目初始化，`main.py` 挂载静态文件和模板
- [x] Jinja2 模板继承体系（`base.html` → `pages/*.html`）
- [x] 静态文件服务 `/static`
- [x] 配置管理（`app/config/settings.py` 读取 .env）
- [x] 异步数据库层（`app/config/database.py`：AsyncEngine + async_sessionmaker + get_session + create_db_and_tables）
- [x] 数据模型定义
  - `app/models/image.py` — Image 表（filename、storage_path、thumbnail_path、title、description、category、tags、user_id、created_at、updated_at）
  - `app/models/user.py` — User 表（username、email、hashed_password、is_active、is_superuser、created_at、updated_at）
- [x] 路由分层（`routers/api/` + `routers/pages/` + `routers/health.py`）

### 前端 — 页面结构

- [x] 咖啡馆主题背景（`background01.webp` + `coffee.css`）
- [x] 顶部导航栏（`nav.css` + `base.html`）
  - 搜索框（展开/收起动画，关闭按钮）
  - 相册 / 叙事 切换按钮
  - 搜索图标、筛选图标、主题切换、用户头像
  - **登录/注册 Modal** — 支持登录/注册切换，注册含邮箱字段
  - 深色/浅色主题完整 CSS 覆盖
  - 移动端响应式（≤768px）
- [x] 轨道舞台（`orbit.css`）
  - 3D perspective + `preserve-3d`
  - 中心核心（咖啡杯发光球体 + glow 光晕）
  - 双层装饰环（outer / inner，不同 Z 轴深度）
  - 照片悬浮动画（`orbitFloat` keyframes）
- [x] 底部缩略图栏（`layout.css`）
- [x] 详情面板（`detail-modal`）— 支持点击缩略图/详情链接触发，含关闭按钮、ESC 键关闭、遮罩点击关闭
- [x] 控制面板（按钮 + 滑块）— 速度滑块、视角滑块
- [x] 轨道示意图（Navigator）— Canvas 俯视轨道环，每帧同步照片位置

### 前端 — JavaScript 交互

- [x] 3D 多层轨道动画（`orbit.js`）
  - 2 层轨道，每层照片数量独立配置（6+4）
  - 每层独立半径（340/260）
  - `requestAnimationFrame` 驱动旋转
  - XZ 平面投影实现真实前后深度
  - 深度驱动 scale + opacity（近大远小、近亮远暗）
  - 照片 hover 暂停自动旋转
  - 点击缩略图触发 `showDetail()` 打开详情面板
- [x] 缩略图栏初始化 + 点击触发 detail panel
- [x] 自动旋转 / 暂停按钮
- [x] 客户端实时搜索
  - 输入框实时匹配（标题、标签、分类）
  - 搜索结果下拉面板（含缩略图 + 元数据）
  - 点击结果高亮对应照片
- [x] 深色/浅色主题切换
  - localStorage 持久化偏好
  - 全量 CSS 覆盖（nav、search results、navigator、buttons）
- [x] 叙事模式（Story Mode）
  - `story-stage` + `story-timeline` DOM 元素，CSS 样式
  - `renderStoryTimeline()` 动态加载图片时间线，支持编辑/删除
  - 权限控制：仅作者或超级管理员可见编辑/删除按钮
  - 用户数据从 DOM `#current-user-data` 读取，避免 ES Module 加载时序问题
  - XSS 防护：所有用户输入通过 `escapeHtml()` 转义

### 后端 — 认证与图片管理

- [x] **注册后自动登录** — `/auth/register` 返回 JWT token + httpOnly cookie
- [x] **图片搜索接口** — `/api/search` 支持关键词(q)、分类(category)、标签(tag)筛选
- [x] **图片上传接口** — `/api/images/upload` 支持 Form 提交 + category/tags，允许匿名上传
- [x] **图片 CRUD** — `GET /api/images`（公开）、`POST /api/images/{id}`（更新）、`DELETE /api/images/{id}`（软删/硬删，需认证）
- [x] **权限控制** — `_ensure_image_access()` 校验作者/管理员权限，匿名图片仅管理员可操作
- [x] **页面路由用户数据注入** — `story.py` 使用 `resolve_user_from_cookie` 从 cookie 解析用户并注入模板，支持前端权限判断

### 前端 — CSS 文件分工

| 文件 | 职责 |
|------|------|
| `input.css` | Tailwind 入口（`@tailwind` 指令，不直接引用） |
| `tailwind.css` | Tailwind 编译产物（不手工修改） |
| `coffee.css` | 背景、咖啡杯核心、蒸汽动画、脉冲 |
| `orbit.css` | 轨道舞台、装饰环、照片卡片、玻璃高光、悬停效果、Detail Panel 样式、Thumbnail Bar 样式、Control Panel 样式、叙事模式样式 |
| `layout.css` | Detail Panel + Thumbnail Bar 补充样式 |
| `nav.css` | 顶部导航栏 + 搜索下拉 + 轨道示意图 |
| `components.css` | Modal 遮罩、通用按钮、组件样式 |

### JavaScript 模块

| 文件 | 职责 |
|------|------|
| `main.js` | 入口：加载 orbit.js + nav.js + filter.js，初始化全局行为 |
| `orbit.js` | 3D 多层轨道动画、缩略图栏、详情面板、主题切换、Navigator 轨道示意图 |
| `nav.js` | 页面切换（相册/叙事）、搜索接口联动、客户端图片过滤 |
| `auth.js` | 登录/注册 Modal 切换、表单提交、JWT 存储、登出 |
| `upload.js` | 图片上传 Modal、FormData 提交、上传结果反馈、分类选项异步加载 |
| `story.js` | 叙事模式渲染、编辑/删除操作、权限校验、XSS 防护 |
| `filter.js` | 筛选面板：分类 chip + 标签 chip（toggle 切换，重置按钮，`/api/categories` 枚举驱动） |
| `profile.js` | 个人中心图片列表渲染 |

---

## 未完成功能

### 优先级 P0 — 交互完善

- [ ] **鼠标拖拽旋转** — 拖拽轨道系统旋转
- [ ] **惯性旋转** — 松开后保持动量衰减
- [ ] **滚动缩放** — 鼠标滚轮改变轨道半径/视角
- [ ] **图片聚焦/飞向中心** — 点击照片后飞入中心并展开 detail panel

### 优先级 P1 — 部署准备

- [ ] **DDL 建表** — 使用 Alembic 迁移替代 `create_all`，在 `main.py` lifespan 中调用 `alembic upgrade head`
- [ ] **生产配置** — `.env.example`、Nginx 反向代理、Gunicorn 启动脚本

### 优先级 P2 — 功能扩展

- [ ] **蒸汽动画** — `initSteam()` 是空函数占位，咖啡杯蒸汽效果待实现
- [ ] **收藏/下载/分享** — Detail Panel 操作按钮（骨架已就绪）
- [ ] **头像上传** — 用户头像自定义

---

## 路由结构

```
app/routers/
├── api/          # API 端点（JSON 响应）
│   ├── auth.py   # 注册、登录、JWT 签发
│   ├── image.py  # 图片 CRUD、搜索、上传、分类枚举
│   └── user.py   # 用户信息读写
├── pages/        # Jinja2 页面渲染（HTML 响应）
│   ├── index.py  # 首页（/）
│   ├── photo.py  # 图片详情（/photo/{id}）
│   ├── profile.py# 个人中心（/profile）
│   └── story.py  # 叙事模式（/story）
└── health.py     # 健康检查（/health）
```

### 认证架构

- `auth.py`（依赖模块）提供三个核心依赖：
  - `get_current_user()` — 强制认证，失败抛 401（用于受保护 API）
  - `resolve_user_from_cookie()` — 可选认证，失败返回 None（用于页面渲染）
  - `require_superuser()` — 额外要求超级管理员权限
- JWT token 通过 `access_token` cookie 存储，fetch 必须携带 `credentials: 'include'`

---

## 编码规范

### 依赖注入 — 统一使用 `Annotated`

路由层所有依赖注入参数必须使用 `Annotated[Type, Depends(...)]` 风格：

```python
from typing import Annotated

@router.get("/items")
async def list_items(
    p: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    ...
```

- **禁止**混用传统 `session: AsyncSession = Depends(get_session)` 写法
- 所有路由文件顶部需显式 `from typing import Annotated`
- auth.py 同样适用（如有新端点）

### Form / File / Query 参数 — `Annotated[Type, Param()]` + `= default`

FastAPI 要求默认值在参数签名上，不能在 `Param()` 内部设：

```python
# ✅ 正确
title: Annotated[str | None, Form()] = None
category: Annotated[Category, Form()] = Category.GALLERY
hard: Annotated[bool, Query()] = False

# ❌ 错误 — Form(None) 会触发 AssertionError
title: Annotated[str | None, Form(None)] = None
```

### 枚举 — 业务分类使用 Python `Enum`

新增业务分类字段时，创建 `app/utils/enums.py` 中的枚举类：

```python
class Category(str, Enum):
    GALLERY = "Gallery"
    TRAVEL = "Travel"
    NATURE = "Nature"
    PORTRAIT = "Portrait"
    ARCHITECTURE = "Architecture"
    ABSTRACT = "Abstract"
```

- Router 层使用枚举类型（`category: Annotated[Category, Form()] = Category.GALLERY`）
- Service 层接收 `.value`（字符串），保持 schema/model 层为 `str`
- 枚举值定义在 `app/utils/enums.py`

---

## 已知问题 / 注意事项

1. `layout.css` 中有缩进不一致问题（部分类名前有 2 空格缩进），不影响功能但影响可读性。
2. `initSteam()` 是空函数占位，蒸汽效果尚未实现。
3. `app/models/user.py` 中 `images` 关系定义缩进错误（在类体外），需修复。
4. **fetch 认证**：所有需要携带登录状态的 `fetch` 调用必须添加 `credentials: 'include'`，否则 cookie 不会发送。
5. **页面路由用户注入**：页面级路由（如 `/story`）应使用 `resolve_user_from_cookie` 而非 `get_current_user`，以支持未登录用户浏览页面内容。
6. **ES Module 加载时序**：`story.js` 作为独立 ES Module 加载，不应依赖 `window.currentUser` 缓存，而应从 DOM `#current-user-data` 读取当前用户信息。
