from datetime import datetime, timezone

from sqlalchemy import DateTime

from typing import cast

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """返回 UTC 时间（timezone-aware）。"""
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    """时间戳 Mixin。

    ✅ 关键：使用 sa_column_kwargs 而非直接 Field()，
       确保每个继承者获得独立的 Column 实例。
    ✅ 优化点：
    1. 使用 sa_column 显式指定 DateTime(timezone=True)。
    2. 通过 type_ 参数指定 DateTime(timezone=True)。
    """

    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=cast(type, DateTime(timezone=True)),
        sa_column_kwargs={
            "nullable": False
        },
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=cast(type, DateTime(timezone=True)),
        sa_column_kwargs={
            "nullable": True,
            "onupdate": _utcnow
        },
    )
