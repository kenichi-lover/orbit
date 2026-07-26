from enum import Enum


class Category(str, Enum):
    """图片分类枚举"""

    GALLERY = "Gallery"
    TRAVEL = "Travel"
    NATURE = "Nature"
    PORTRAIT = "Portrait"
    ARCHITECTURE = "Architecture"
    ABSTRACT = "Abstract"
