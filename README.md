---

# Orbit Gallery

## Project Blueprint V1.0

> **一个具有生命感的图片探索器（Memory Explorer）**

一个浏览、探索、沉浸式展示图片的 Web Application。

---

# 一、设计理念

```
Memory Explorer

↓

Orbit（轨道）

↓

World（世界）

↓

Story（故事）
```

用户进入网站，

不是"查看图片"，

而是

> **进入一个世界（World）**

例如：

```
☕ Coffee World

🖼 Museum World

🌌 Space World

🌳 Forest World
```

不同 World，

仅仅改变：

* 背景
* 灯光
* 配色
* 音乐（后续）
* Orbit 风格

业务逻辑完全一致。

---

# 二、页面结构

```
┌───────────────────────────────────────────────┐
│                  Navigation                   │
├───────────────────────────────────────────────┤
│                                               │
│               Orbit Gallery                   │
│                                               │
│                     ◎                         │
│                                               │
│                               Detail Panel    │
├───────────────────────────────────────────────┤
│ Navigator               Timeline              │
└───────────────────────────────────────────────┘
```

---

## ① Navigation

保留三个入口。

```
🔍 搜索

📁 相册

📖 故事
```

以后不再增加菜单。

保持极简。

---

## ② Orbit Gallery（核心）

整个网站最重要。

负责：

✔ 图片轨道

✔ Hover 暂停

✔ 点击聚焦

✔ 拖拽旋转

✔ 滚轮缩放

✔ 惯性动画

所有动画：

全部由 JavaScript 完成。

---

## ③ Detail Panel

右侧。

展示：

```
图片

标题

时间

地点

EXIF

标签

故事

```

以后还能加入：

```
评论

收藏

分享
```

---

## ④ Navigator

左下角。

不是菜单。

而是：

Orbit Mini Map。

作用：

```
当前位置

当前 Layer

当前图片

Orbit 导航
```

---

## ⑤ Timeline

底部。

缩略图。

负责：

```
浏览图片

快速切换

时间轴
```

---

# 三、项目结构

```
orbit-gallery/
│
├── app/
│
│   ├── main.py
│   │
│   ├── core/
│   │     config.py
│   │     database.py
│   │
│   ├── routers/
│   │     home.py
│   │     gallery.py
│   │     album.py
│   │     story.py
│   │     search.py
│   │
│   ├── services/
│   │     gallery_service.py
│   │     album_service.py
│   │     story_service.py
│   │
│   ├── repositories/
│   │     gallery_repo.py
│   │     album_repo.py
│   │
│   ├── models/
│   │     photo.py
│   │     album.py
│   │     tag.py
│   │     story.py
│   │
│   ├── schemas/
│   │
│   ├── templates/
│   │     base.html
│   │     index.html
│   │
│   ├── static/
│   │
│   │     css/
│   │     js/
│   │     images/
│   │     icons/
│   │
│   └── worlds/
│         coffee.json
│         museum.json
│         space.json
│
├── uploads/
│
├── migrations/
│
├── requirements.txt
│
└── README.md
```

---

# 四、数据库（SQLModel）

第一版仅保留四个实体。

```
Photo
```

```
id

title

filename

story

album_id

created_at
```

---

```
Album
```

```
id

name

cover

description
```

---

```
Tag
```

```
id

name
```

Photo 与 Tag：

多对多。

---

```
Story
```

```
id

title

content

photo_id
```

这样以后：

图片和故事可以分离。

---

# 五、技术职责

## FastAPI

负责：

```
页面

API

数据库

图片上传

搜索

相册
```

不负责动画。

---

## SQLModel

负责：

```
ORM

数据模型

关系映射

Pydantic
```

全部统一。

---

## PostgreSQL

保存：

```
图片信息

故事

相册

标签
```

图片文件：

仍然放：

```
uploads/
```

数据库：

只保存路径。

---

## JavaScript

整个 Orbit。

包括：

```
轨道

Hover

惯性

缩放

Layer

动画
```

全部交给：

```
orbit.js
```

---

# 六、World（整个项目最大的特色）

## World

```
Coffee World

Museum World

Space World

Forest World
```

每个 World：

只是配置。

例如：

```json
{
    "background":"coffee.jpg",
    "theme":"dark",
    "orbit_speed":0.35,
    "orbit_color":"#8a6cff",
    "ambient_sound":"rain.mp3"
}
```

FastAPI：

启动：

```
load_world("coffee")
```

整个网站立即变成：

夜晚咖啡馆。

以后：

```
load_world("museum")
```

整个网站：

又变成：

现代艺术馆。

无需修改业务代码。

---

# 七、开发路线（建议）


| 阶段   | 目标                    | 是否连接数据库 |
| ---- | --------------------- | ------- |
| V0.1 | 静态 UI（Jinja2 + CSS）   | ❌       |
| V0.2 | Orbit 动画（Vanilla JS）  | ❌       |
| V0.3 | Detail Panel 与交互      | ❌       |
| V0.4 | SQLModel + PostgreSQL | ✅       |
| V0.5 | 图片上传、相册、搜索            | ✅       |
| V0.6 | Story 模块              | ✅       |
| V1.0 | Coffee World（完整体验）    | ✅       |

---

## 最终定位

它的定位应该是一句话就能让人理解：

> **Orbit Gallery —— 一个基于 FastAPI + Jinja2 + SQLModel 构建的沉浸式图片探索器。**

它最大的特点不是功能多，而是**体验有生命感**：图片围绕中心缓慢运行，进入不同的 World 就像走进不同的空间，而故事、照片和时间共同构成一段可以探索的记忆。这也会成为整个项目最鲜明的辨识度。

