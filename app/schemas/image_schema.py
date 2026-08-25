"""
Image Schema — 分模块优化：

模块 1: 类型修正   → category 绑定 Category 枚举，tags 改为 list[str]
模块 2: 继承优化   → ImagePublic / ImageUpdate 继承 ImageBase，消除重复
模块 3: 响应补全   → ImagePublic 补全 thumbnail_url / file_size / mime_type 等
模块 4: 新增       → ImageCreate（上传时校验元信息）
模块 5: 搜索对齐   → ImageSearchParams.user_name → user_id
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.utils.enums import Category


# ══════════════════════════════════════════════
# 模块 1: 类型修正 + 基础字段
# ══════════════════════════════════════════════

class ImageBase(SQLModel):
    """用户可控的业务字段。

    继承者：ImageCreate / ImageUpdate / ImagePublic
    ⚠️ 不包含 file_name / relative_path 等内部存储字段
    """

    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    alt_text: str | None = Field(default=None, max_length=255)

    # ✅ 模块 1: category 绑定枚举（原来是自由 str）
    category: Category = Field(default=Category.GALLERY)

    # ✅ 模块 1: tags 改为 list[str]（原来是逗号分隔的 str）
    tags: list[str] = Field(default_factory=list)


# ══════════════════════════════════════════════
# 模块 4: 新增 — 创建请求体
# ══════════════════════════════════════════════

class ImageCreate(ImageBase):
    """上传图片时前端传入的元信息。

    文件本身走 multipart/form-data 的 UploadFile，
    这里只校验随文件一起提交的描述性字段。
    """

    # 如果未来需要前端指定分类 / 标签，直接继承 Base 即可
    # 当前 Base 字段已足够，无需额外定义
    pass


# ══════════════════════════════════════════════
# 模块 2 + 3: 公开响应（继承 + 补全）
# ══════════════════════════════════════════════

class ImagePublic(ImageBase):
    """前端可见的图片信息。脱敏、精简。

    ✅ 模块 2: 继承 ImageBase，消除 title/description/tags 重复定义
    ✅ 模块 3: 补全 thumbnail_url / file_size / mime_type / width / height
    ✅ 修正: title 允许 None（与模型层一致）
    """

    id: int

    # ── 存储 URL（由 relative_path 拼接，路由层赋值）──
    url: str
    thumbnail_url: str | None = None

    # ── 文件元数据（只读，服务端计算）──
    original_filename: str
    file_size: int
    mime_type: str
    width: int | None = None
    height: int | None = None

    # ── 关联用户（脱敏：只返回用户名）──
    author_name: str | None = None

    # ── 时间戳 ──
    created_at: datetime
    updated_at: datetime | None = None


# ══════════════════════════════════════════════
# 模块 2: 更新（继承 + 部分更新）
# ══════════════════════════════════════════════

class ImageUpdate(SQLModel):
    """部分更新：所有字段可选，传什么改什么。

    ⚠️ 不继承 ImageBase，因为需要所有字段都是 Optional，
       而 Base 中 category 有默认值、tags 有 default_factory，
       语义不同：
         - Base.tags = []       → 创建时默认空列表
         - Update.tags = None   → 不修改
         - Update.tags = []     → 清空所有标签
    """

    title: str | None = None
    description: str | None = None
    alt_text: str | None = None

    # ✅ 模块 1: 枚举类型
    category: Category | None = None

    # ✅ 模块 1: list[str] 类型
    # None = 不修改, [] = 清空
    tags: list[str] | None = None


# ══════════════════════════════════════════════
# 模块 5: 搜索参数（对齐模型层）
# ══════════════════════════════════════════════

class ImageSearchParams(SQLModel):
    """URL 查询参数（Query 参数）"""

    q: str | None = Field(default=None, max_length=200)

    # ✅ 模块 1: 枚举过滤
    category: Category | None = Field(default=None)

    # ✅ 模块 1: 单标签过滤（模型层 tags 是 JSON list，
    #    查询时用 contains 匹配单个标签即可）
    tag: str | None = Field(default=None, max_length=100)

    # ✅ 模块 5: user_name → user_id（与模型层外键对齐）
    user_id: int | None = Field(default=None, ge=1)

    # ── 分页 ──
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
