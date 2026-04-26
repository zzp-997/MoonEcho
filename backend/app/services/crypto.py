"""加密服务模块。

提供手机号加密存储能力：
- AES-256-GCM 加密/解密手机号（phone 字段存储密文）
- SHA-256 哈希手机号（phone_hash 字段用于唯一索引查询）

密钥从环境变量 CRYPTO_KEY 读取，要求 32 字节（256 位）的
Base64 编码字符串。若未配置则启动时自动生成并打印警告。
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 密钥管理
# ---------------------------------------------------------------------------

_CRYPTO_KEY_ENV = "CRYPTO_KEY"
_FALLBACK_KEY: bytes | None = None


def _load_or_generate_key() -> bytes:
    """加载或生成 AES-256 密钥。

    优先级：
    1. 环境变量 CRYPTO_KEY（Base64 编码的 32 字节密钥）
    2. 自动生成临时密钥（仅开发/测试环境使用，每次重启会变化）

    生产环境强制要求配置 CRYPTO_KEY，否则启动时抛出异常。
    这是为了防止重启后无法解密已有数据，同时避免攻击者通过临时密钥解密窃取的数据。

    Returns:
        32 字节 AES-256 密钥

    Raises:
        RuntimeError: 生产环境未配置 CRYPTO_KEY 时抛出
    """
    from app.core.config import _environment_name

    env_value = os.getenv(_CRYPTO_KEY_ENV)
    if env_value:
        try:
            key = base64.b64decode(env_value)
            if len(key) != 32:
                raise ValueError(f"密钥长度必须为 32 字节，当前为 {len(key)} 字节")
            return key
        except Exception as exc:
            logger.error("CRYPTO_KEY 环境变量解析失败: %s", exc)
            raise

    # 检查是否为生产环境
    env = _environment_name()
    if env == "production":
        raise RuntimeError(
            "生产环境必须配置 CRYPTO_KEY 环境变量！"
            "请生成一个 32 字节的随机密钥，使用 Base64 编码后配置到环境变量中。"
            "示例（Python）: import os; import base64; print(base64.b64encode(os.urandom(32)).decode())"
        )

    # 自动生成临时密钥（仅用于开发/测试环境）
    key = AESGCM.generate_key(bit_length=256)
    logger.warning(
        "未配置 CRYPTO_KEY 环境变量，已自动生成临时密钥。"
        "此密钥仅用于开发/测试环境，重启后无法解密已有数据。"
        "生产环境务必配置，否则将导致数据永久丢失！"
    )
    return key


def _get_key() -> bytes:
    """获取当前加密密钥（单例模式）。"""
    global _FALLBACK_KEY
    if _FALLBACK_KEY is None:
        _FALLBACK_KEY = _load_or_generate_key()
    return _FALLBACK_KEY


# ---------------------------------------------------------------------------
# AES-256-GCM 加密 / 解密
# ---------------------------------------------------------------------------


def encrypt_phone(plaintext: str) -> str:
    """使用 AES-256-GCM 加密手机号。

    返回格式：Base64(nonce || ciphertext || tag)，其中 nonce 为 12 字节随机值。

    Args:
        plaintext: 明文手机号

    Returns:
        Base64 编码的密文（含 nonce）
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # GCM 推荐 12 字节 nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # nonce + ciphertext(tag 已包含在 ciphertext 末尾)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("ascii")


def decrypt_phone(ciphertext_b64: str) -> str:
    """使用 AES-256-GCM 解密手机号。

    Args:
        ciphertext_b64: Base64 编码的密文（含 nonce）

    Returns:
        明文手机号

    Raises:
        ValueError: 解密失败时抛出
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    try:
        payload = base64.b64decode(ciphertext_b64)
        nonce = payload[:12]
        ciphertext = payload[12:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as exc:
        logger.error("手机号解密失败: %s", exc)
        raise ValueError("手机号解密失败") from exc


# ---------------------------------------------------------------------------
# SHA-256 哈希
# ---------------------------------------------------------------------------

# 哈希盐值，从环境变量读取，若未配置则使用默认值
_HASH_SALT_ENV = "PHONE_HASH_SALT"
_DEFAULT_SALT = "echo_phone_hash_salt_2024"


def phone_hash(plaintext: str) -> str:
    """计算手机号的 SHA-256 哈希值（带盐）。

    哈希结果用于 phone_hash 字段，支持唯一索引查询。
    盐值增强安全性，防止彩虹表攻击。

    Args:
        plaintext: 明文手机号

    Returns:
        64 字符十六进制 SHA-256 哈希值
    """
    salt = os.getenv(_HASH_SALT_ENV, _DEFAULT_SALT)
    data = f"{salt}:{plaintext}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# 通用数据加密 / 解密
# ---------------------------------------------------------------------------


def encrypt_data(plaintext: str, key: str | None = None) -> str:
    """使用 AES-256-GCM 加密任意字符串数据。

    用于加密敏感数据如匿名身份映射关系。

    Args:
        plaintext: 明文数据
        key: 加密密钥（可选，默认使用全局密钥）

    Returns:
        Base64 编码的密文（含 nonce）
    """
    aes_key = _get_key() if key is None else _derive_key(key)
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("ascii")


def decrypt_data(ciphertext_b64: str, key: str | None = None) -> str:
    """使用 AES-256-GCM 解密数据。

    Args:
        ciphertext_b64: Base64 编码的密文（含 nonce）
        key: 解密密钥（可选，默认使用全局密钥）

    Returns:
        明文数据

    Raises:
        ValueError: 解密失败时抛出
    """
    aes_key = _get_key() if key is None else _derive_key(key)
    aesgcm = AESGCM(aes_key)
    try:
        payload = base64.b64decode(ciphertext_b64)
        nonce = payload[:12]
        ciphertext = payload[12:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as exc:
        logger.error("数据解密失败: %s", exc)
        raise ValueError("数据解密失败") from exc


def _derive_key(key: str) -> bytes:
    """从字符串密钥派生 32 字节 AES 密钥。

    Args:
        key: 字符串密钥

    Returns:
        32 字节密钥
    """
    # 使用 SHA-256 派生固定长度密钥
    return hashlib.sha256(key.encode("utf-8")).digest()


# ---------------------------------------------------------------------------
# 内容哈希
# ---------------------------------------------------------------------------


def compute_content_hash(content: str) -> str:
    """计算内容哈希值，用于完整性校验。

    Args:
        content: 内容字符串

    Returns:
        SHA-256 哈希值
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
