# Orbit Gallery — 项目进度

> 最后更新：2026-08-01

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
- [x] 配置管理（`app/config/setting.py` 读取 `.env`）
- [x] 异步数据库层（`app/config/database.py`：AsyncEngine + async_sessionmaker + get_session + create_db_and_tables）
- [x] 数据模型定义
  - `app/models/image.py` — Image 表（filename、storage_path、thumbnail_path、title、description、category、tags、user_id、created_at、updated_at）
  - `app/models/user.py` — User 表（username、email、hashed_password、is_active、is_superuser、created_at、updated_at）
- [x] 路由分层（`routers/api/` + `routers/pages/` + `routers/health.py`）

### 前端 — 页面结构

- [x] 咖啡馆主题背景（`background.webp` + `coffee.css`）
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
- [x] 详情面板骨架（`pages/index.html` + `orbit.css`）
- [x] 控制面板骨架（按钮 + 滑块）

### 前端 — JavaScript 交互

- [x] 3D 多层轨道动画（`orbit.js`）
  - 2 层轨道，每层照片数量独立配置（6+4）
  - 每层独立半径（340/260）
  - `requestAnimationFrame` 驱动旋转
  - XZ 平面投影实现真实前后深度
  - 深度驱动 scale + opacity（近大远小、近亮远暗）
  - 照片 hover 暂停自动旋转
- [x] 缩略图栏初始化 + 点击触发 detail panel
- [x] 自动旋转 / 暂停按钮
- [x] 客户端实时搜索
  - 输入框实时匹配（标题、标签、分类）
  - 搜索结果下拉面板（含缩略图 + 元数据）
  - 点击结果高亮对应照片
- [x] 深色/浅色主题切换
  - localStorage 持久化偏好
  - 全量 CSS 覆盖（nav、search results、navigator、buttons）
- [x] 轨道示意图（Navigator）
  - Canvas 绘制俯视轨道环
  - 每帧同步照片实时位置（从 transform 读取）
  - 小圆点标记每张照片，选中时放大

### 后端 — 认证与搜索（新增）

- [x] **注册后自动登录** — `/auth/register` 返回 JWT token + cookie
- [x] **图片搜索接口** — `/api/search` 支持关键词(q)、分类(category)、标签(tag)筛选
- [x] **图片上传接口** — `/api/images/upload` 支持 Form 提交 + category/tags
- [x] **Image 模型扩展** — 新增 `category`、`tags` 字段
- [x] **标签/相册分类** — 数据模型 + 查询
- [x] **前端对接** — nav.js 搜索联动 API，story mode 使用搜索结果渲染
- [x] **叙事模式（Story Mode）** — `story-stage` + `story-timeline` DOM 元素，CSS 样式，`renderStoryMode()` 动态加载图片时间线，支持编辑/删除
- [x] **轨道数据对接修复** — orbit.js 从 `/api/images` 获取数据时改用 `data.items`（匹配新 API 格式）；`showDetail()` 使用 `author_name` 和拆分 tags

### 前端 — CSS 文件分工

| 文件 | 职责 |
|------|------|
| `input.css` | Tailwind 入口（`@tailwind` 指令，不直接引用） |
| `tailwind.css` | Tailwind 编译产物（不手工修改） |
| `coffee.css` | 背景、咖啡杯核心、蒸汽动画、脉冲 |
| `orbit.css` | 轨道舞台、装饰环、照片卡片、玻璃高光、悬停效果、Detail Panel 样式、Thumbnail Bar 样式、Control Panel 样式、**叙事模式样式** |
| `layout.css` | Detail Panel + Thumbnail Bar 补充样式 |
| `nav.css` | 顶部导航栏 + 搜索下拉 + 轨道示意图 |
| `components.css` | Modal 遮罩、通用按钮、组件样式 |

### JavaScript 模块

| 文件 | 职责 |
|------|------|
| `main.js` | 入口：加载 orbit.js + nav.js，初始化全局行为 |
| `orbit.js` | 3D 多层轨道动画、缩略图栏、客户端搜索、主题切换、Navigator 轨道示意图 |
| `nav.js` | 页面切换（相册/叙事）、搜索接口联动、筛选面板触发 |
| `auth.js` | 登录/注册 Modal 切换、表单提交、JWT 存储、登出 |
| `upload.js` | 图片上传 Modal、FormData 提交、上传结果反馈 |

---

## 未完成功能

### 优先级 P0 — 交互完善

- [ ] **鼠标拖拽旋转** — 拖拽轨道系统旋转
- [ ] **惯性旋转** — 松开后保持动量衰减
- [ ] **滚动缩放** — 鼠标滚轮改变轨道半径/视角
- [ ] **图片聚焦/飞向中心** — 点击照片后飞入中心并展开 detail panel
- [x] **速度滑块联动** — `#speed-slider` 控制 `config.rotationSpeed`
- [x] **视角滑块联动** — `#view-slider` 控制 `perspective` 值

### 优先级 P1 — 数据层

- [ ] **DDL 建表** — 在 `main.py` lifespan 中调用 `create_db_and_tables()`

### 优先级 P2 — 功能扩展

- [ ] **筛选功能** — `#nav-filter` 按钮的下拉面板
- [x] **用户系统** — `#nav-avatar` 登录/注册（JWT + bcrypt）—— auth.js + auth API 已实现
- [ ] **收藏/下载/分享** — Detail Panel 操作按钮

---

## 路由结构

```
app/routers/
├── api/          # API 端点（JSON 响应，受 JWT 保护）
│   ├── auth.py   # 注册、登录、JWT 签发
│   ├── image.py  # 图片 CRUD、搜索、上传
│   └── user.py   # 用户信息读写
├── pages/        # Jinja2 页面渲染（HTML 响应）
│   ├── index.py  # 首页（/）
│   ├── photo.py  # 图片详情（/photo/{id}）
│   ├── profile.py# 个人中心（/profile）
│   └── story.py  # 叙事模式（/story）
└── health.py     # 健康检查（/health）
```

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
3. 速度滑块和视角滑块已有 HTML/CSS，但未绑定 JS 事件。
4. `#detail-panel` 的 `showDetail()` 仅做 `display: block` + `console.log`，未与照片数据联动。
5. 照片数据全部硬编码在 `config.imageUrls` 中，暂无后端来源。
6. `app/models/user.py` 中 `images` 关系定义缩进错误（在类体外），需修复。
