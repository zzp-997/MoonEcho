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
    2. 自动生成临时密钥（仅开发环境使用，每次重启会变化）

    Returns:
        32 字节 AES-256 密钥
    """
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

    # 自动生成临时密钥（仅用于开发环境）
    key = AESGCM.generate_key(bit_length=256)
    logger.warning(
        "未配置 CRYPTO_KEY 环境变量，已自动生成临时密钥。"
        "生产环境务必配置，否则重启后无法解密已有数据！"
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
