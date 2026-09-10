from enum import Enum


class Category(str, Enum):
    """图片分类枚举"""

    GALLERY = "画廊"
    TRAVEL = "旅行"
    NATURE = "自然"
    PORTRAIT = "人像"
    ARCHITECTURE = "建筑"
    ABSTRACT = "抽象"

    def __str__(self) -> str:
        return self.value
