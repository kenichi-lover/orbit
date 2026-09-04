from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

# Argon2 配置：平衡安全与性能
ph = PasswordHasher()

_DUMMY_HASH: str = ph.hash("dummy-password-for-timing-attack")

def verify_dummy_password(plain_password: str) -> None:
    """
    对不存在的用户执行一次等价耗时的密码验证，防止时序攻击猜解用户名。
    """
    try:
        ph.verify(_DUMMY_HASH, plain_password)
    except (VerifyMismatchError, InvalidHash):
        pass  # 必定失败，目的只是消耗等量时间


def hash_password(password: str) -> str:
    """对明文密码进行 Argon2 哈希。"""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    return ph.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """验证明文密码是否匹配 Argon2 哈希。"""
    if not plain_password or not hashed_password:
        return False
    
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False

def check_needs_rehash(hashed_password: str) -> bool:
    """检查哈希是否需要重新哈希（例如，参数更改）。"""
    return ph.check_needs_rehash(hashed_password)