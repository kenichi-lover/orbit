# Orbit Gallery

当前版本：V0.1
# Changelog

- 初始化 FastAPI 项目
- 接入 Tailwind CSS
- 完成 Orbit 基础旋转
- 完成咖啡馆背景
- 建立 CSS / JS 模块结构

---

# 技术栈

## Backend

- FastAPI
- Uvicorn
- Jinja2
- SQLModel（后续）
- PostgreSQL（后续）
- Alembic（后续）
- python-multipart（后续）
- pydantic-settings（后续）

---

## Frontend

- HTML5
- CSS3
- Tailwind CSS（基础布局）
- Vanilla JavaScript（ES Modules）

---

# CSS 架构

```
static/css/

input.css
│
├── Tailwind 入口
└── 不直接引用

tailwind.css
│
├── 自动生成
└── 不手工修改

coffee.css
│
├── 背景
├── 灯光
├── 动画
└── 咖啡馆主题

layout.css
│
├── 页面布局
├── Detail Panel
├── Timeline
└── Overlay

orbit.css
│
├── Orbit Stage
├── Orbit Ring
├── Photo Item
└── Orbit Animation
```

---

# JavaScript 架构

```
static/js/

main.js
│
└── 项目入口

orbit.js
│
├── Orbit 初始化
├── 图片创建
├── 自动旋转
└── Hover / Click
```

---

# 动画技术

坚持使用浏览器原生能力。

使用：

- requestAnimationFrame()
- CSS Transform
- translate3d()
- rotate()
- scale()
- CSS Transition
- CSS Variables
- backdrop-filter（Glass Effect）

不使用任何动画框架。

---

# 当前已完成（V0.1）

- FastAPI 项目初始化
- Jinja2 模板系统
- StaticFiles 配置
- Tailwind CSS 编译流程
- 咖啡馆背景
- Orbit 中心发光
- Orbit 自动旋转
- 图片 Hover 暂停
- Detail Panel 基础结构
- Timeline 基础结构

---

# 当前开发计划

## 第一阶段（进行中）

完成静态交互：

- 背景
- Orbit
- Hover
- Detail Panel
- Timeline

---

## 第二阶段

完善交互：

- 鼠标拖拽旋转
- 惯性旋转
- 图片聚焦
- 图片飞向中心
- Timeline 联动

---

## 第三阶段

数据接入：

- PostgreSQL
- 图片数据
- 标签
- 搜索
- 上传

---

# 暂不引入

为了保持项目简单，当前版本暂不使用：

- React
- Vue
- Three.js
- GSAP
- Redis
- Celery

如果后续能够明显降低复杂度，再进行评估。

---

# 项目原则

遵循以下原则：

1. 优先使用浏览器原生能力。
2. Tailwind 仅负责基础布局，不负责复杂动画。
3. JavaScript 负责交互逻辑。
4. CSS 负责视觉表现。
5. 一个文件负责一个职责。
6. 每次迭代只完成一个明确功能，并确保可运行。

保持项目简单、稳定、可维护。
