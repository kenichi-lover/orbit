"""
集中导入所有 SQLModel 模型。
任何需要使用 ORM 的入口（main.py, scripts, tests）只需：
    import app.models
即可确保所有模型注册到 SQLAlchemy Registry。
"""
from app.models.user import User      # noqa: F401
from app.models.image import Image    # noqa: F401
# 新增模型时只需在此处添加一行
