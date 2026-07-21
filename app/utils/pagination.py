from math import ceil
from typing import TypeVar, Generic, Sequence

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    路由中直接作为依赖注入：
        @router.get("/items")
        async def list_items(p: PaginationParams = Depends()):
            ...
    """
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)  # 限制最大 100，防拖库

    @property
    def page(self) -> int:
        """兼容前端用 page 传参的场景"""
        return self.skip // self.limit + 1 if self.limit > 0 else 1


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    skip: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        skip: int,
        limit: int,
    ) -> "PaginatedResponse[T]":
        # 防御除零
        safe_limit = limit if limit > 0 else 1
        total_pages = ceil(total / safe_limit) if total > 0 else 0

        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            total_pages=total_pages,
            has_next=(skip + len(items)) < total,
            has_prev=skip > 0,
        )