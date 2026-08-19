# ──────────────────────────────────────────────
# 1. 时间戳 Mixin：消除 created_at / updated_at 的重复定义
# ──────────────────────────────────────────────
from datetime import datetime

from sqlmodel import Column, DateTime, Field, SQLModel, func


class TimestampMixin(SQLModel):
    """可复用的时间戳字段，任何需要 created_at / updated_at 的模型继承此类即可。"""

    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            index=True,
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
