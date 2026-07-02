# 当前技术栈（V0.1）

## Backend

- FastAPI
- Uvicorn
- Jinja2
- SQLModel
- PostgreSQL
- Alembic
- python-multipart
- pydantic-settings

## Frontend

- HTML5
- CSS3
- Vanilla JavaScript（ES Modules）

---

# 动画技术（V0.1）

坚持使用浏览器原生能力。

使用：

- Tailwind CSS
- requestAnimationFrame()
- CSS Transform
- translate3d()
- rotate()
- scale()
- CSS Transition
- CSS Variables
- backdrop-filter（Glass Effect）

V0.1 不引入任何动画框架。

---

# 暂不使用

为了保持项目简单，V0.1 不使用：

- React
- Vue
- Three.js
- GSAP
- Redis
- Celery

后续如确有必要，再引入。

---

# 推荐安装依赖

```bash
uv add fastapi
uv add uvicorn
uv add jinja2
uv add sqlmodel
uv add psycopg[binary]
uv add alembic
uv add python-multipart
uv add pydantic-settings
```

整个网站的核心。

负责：

- 图片轨道旋转
- Hover 暂停
- 点击聚焦
- 鼠标拖拽旋转
- 滚轮缩放
- 图片飞向中心（后续）

所有动画全部由 JavaScript 完成。

---

---

# 当前开发目标（V0.1）

目标只有一个。

完成 Orbit Gallery 的静态页面。

包括：

- 夜晚咖啡馆背景
- Orbit 主舞台
- 图片旋转
- Hover 效果
- Detail Panel
- Timeline

暂不接数据库。

暂不实现上传。

暂不实现搜索。

先完成体验，再接入数据。

---

# 项目原则

任何新的第三方依赖，都必须回答两个问题：

1. 浏览器原生能力是否已经可以实现？
2. 引入该依赖是否真正降低复杂度？

如果答案都是否，则不引入。

保持项目简单、清晰、可维护。
