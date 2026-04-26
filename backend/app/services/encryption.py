"""端到端加密服务模块。

提供日记内容的端到端加密能力：
- AES-256-GCM 加密/解密日记内容
- SHA-256 哈希用于内容完整性校验
- 支持客户端加密后上传密文

设计原则：
- 云端同步模式下，客户端上传端到端加密后的密文
- 服务端仅存储密文，无法解密用户日记内容
- 解密密钥由客户端（用户）持有，服务端无法获取
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 密钥长度（256 位 = 32 字节）
KEY_LENGTH = 32

# GCM nonce 长度（推荐 12 字节）
NONCE_LENGTH = 12

# 哈希算法
HASH_ALGORITHM = "sha256"


# ---------------------------------------------------------------------------
# 内容哈希计算
# ---------------------------------------------------------------------------

def compute_content_hash(content: str, salt: str = "") -> str:
    """计算日记内容的哈希值。

    用于内容完整性校验，确保存储/传输过程中内容未被篡改。

    Args:
        content: 原始内容
        salt: 盐值（可选）

    Returns:
        SHA-256 哈希值（64 字符十六进制）
    """
    if not content:
        return ""

    data = f"{salt}:{content}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def verify_content_hash(content: str, expected_hash: str, salt: str = "") -> bool:
    """验证内容哈希值。

    Args:
        content: 原始内容
        expected_hash: 期望的哈希值
        salt: 盐值（可选）

    Returns:
        哈希值是否匹配
    """
    if not expected_hash:
        return True  # 无哈希值时不校验

    computed = compute_content_hash(content, salt)
    return hmac.compare_digest(computed, expected_hash)


# ---------------------------------------------------------------------------
# 端到端加密（客户端模式）
# ---------------------------------------------------------------------------

def encrypt_content_for_storage(content: str, key: bytes) -> str:
    """使用 AES-256-GCM 加密内容。

    此函数用于客户端加密后上传密文到服务端。
    服务端仅存储密文，无法解密。

    返回格式：Base64(nonce || ciphertext || tag)

    Args:
        content: 原始内容
        key: 加密密钥（32 字节）

    Returns:
        Base64 编码的密文（含 nonce）
    """
    if not content:
        return ""

    if len(key) != KEY_LENGTH:
        raise ValueError(f"密钥长度必须为 {KEY_LENGTH} 字节")

    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LENGTH)
    ciphertext = aesgcm.encrypt(nonce, content.encode("utf-8"), None)

    # nonce + ciphertext（tag 已包含在 ciphertext 末尾）
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("ascii")


def decrypt_content_from_storage(ciphertext_b64: str, key: bytes) -> str:
    """使用 AES-256-GCM 解密内容。

    此函数用于客户端从服务端下载密文后解密。
    服务端不调用此函数。

    Args:
        ciphertext_b64: Base64 编码的密文（含 nonce）
        key: 解密密钥（32 字节）

    Returns:
        解密后的原始内容

    Raises:
        ValueError: 解密失败时抛出
    """
    if not ciphertext_b64:
        return ""

    if len(key) != KEY_LENGTH:
        raise ValueError(f"密钥长度必须为 {KEY_LENGTH} 字节")

    aesgcm = AESGCM(key)

    try:
        payload = base64.b64decode(ciphertext_b64)
        nonce = payload[:NONCE_LENGTH]
        ciphertext = payload[NONCE_LENGTH:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as exc:
        logger.error("内容解密失败: %s", exc)
        raise ValueError("内容解密失败，密钥不正确或数据已损坏") from exc


# ---------------------------------------------------------------------------
# 服务端辅助加密（本地模式）
# ---------------------------------------------------------------------------

# 服务端加密密钥（用于本地模式下服务端辅助加密）
# 注意：此密钥仅供本地存储模式使用，云端同步模式下使用客户端密钥
_SERVER_ENCRYPTION_KEY_ENV = "DIARY_SERVER_CRYPTO_KEY"
_SERVER_KEY: bytes | None = None
_ENCRYPTION_INITIALIZED = False


def init_server_encryption(require_key: bool = False) -> None:
    """初始化服务端加密密钥。

    应用启动时应调用此函数，确保加密服务可用。

    Args:
        require_key: 是否强制要求配置密钥（生产环境应为 True）

    Raises:
        RuntimeError: 生产环境未配置密钥时抛出
    """
    global _SERVER_KEY, _ENCRYPTION_INITIALIZED

    if _ENCRYPTION_INITIALIZED:
        return

    env_value = os.getenv(_SERVER_ENCRYPTION_KEY_ENV)

    if env_value:
        try:
            key = base64.b64decode(env_value)
            if len(key) != KEY_LENGTH:
                raise ValueError(f"密钥长度必须为 {KEY_LENGTH} 字节")
            _SERVER_KEY = key
            _ENCRYPTION_INITIALIZED = True
            logger.info("服务端加密密钥已从环境变量加载")
            return
        except Exception as exc:
            logger.error("DIARY_SERVER_CRYPTO_KEY 解析失败: %s", exc)
            if require_key:
                raise RuntimeError(
                    f"DIARY_SERVER_CRYPTO_KEY 解析失败: {exc}"
                ) from exc

    if require_key:
        raise RuntimeError(
            "生产环境必须配置 DIARY_SERVER_CRYPTO_KEY 环境变量！"
            "请生成一个 32 字节的 Base64 编码密钥并配置。"
        )

    # 开发环境自动生成临时密钥
    _SERVER_KEY = AESGCM.generate_key(bit_length=256)
    _ENCRYPTION_INITIALIZED = True
    logger.warning(
        "未配置 DIARY_SERVER_CRYPTO_KEY，已自动生成临时密钥。"
        "服务重启后之前加密的数据将无法解密！生产环境务必配置！"
    )


def _get_server_encryption_key() -> bytes:
    """获取服务端加密密钥。

    用于本地存储模式下的辅助加密。
    云端同步模式下不使用此密钥。

    Returns:
        32 字节 AES-256 密钥
    """
    global _SERVER_KEY

    if _SERVER_KEY is None:
        # 延迟初始化（首次使用时）
        init_server_encryption(require_key=False)

    return _SERVER_KEY


def encrypt_content_server_side(content: str) -> str:
    """服务端辅助加密（用于本地存储模式）。

    Args:
        content: 原始内容

    Returns:
        Base64 编码的密文
    """
    if not content:
        return ""

    key = _get_server_encryption_key()
    return encrypt_content_for_storage(content, key)


def decrypt_content_server_side(ciphertext_b64: str) -> str:
    """服务端辅助解密（用于本地存储模式）。

    Args:
        ciphertext_b64: Base64 编码的密文

    Returns:
        解密后的原始内容
    """
    if not ciphertext_b64:
        return ""

    key = _get_server_encryption_key()
    return decrypt_content_from_storage(ciphertext_b64, key)


# ---------------------------------------------------------------------------
# 密钥生成（供客户端使用）
# ---------------------------------------------------------------------------

def generate_encryption_key() -> str:
    """生成新的端到端加密密钥。

    供客户端使用，服务端不存储此密钥。

    Returns:
        Base64 编码的 32 字节密钥
    """
    key = secrets.token_bytes(KEY_LENGTH)
    return base64.b64encode(key).decode("ascii")


def validate_encryption_key(key_b64: str) -> bool:
    """验证加密密钥格式。

    Args:
        key_b64: Base64 编码的密钥

    Returns:
        密钥是否有效
    """
    try:
        key = base64.b64decode(key_b64)
        return len(key) == KEY_LENGTH
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 密文验证
# ---------------------------------------------------------------------------

def is_encrypted_content(content: str) -> bool:
    """判断内容是否已加密。

    通过检查格式判断：Base64 编码且长度大于 NONCE_LENGTH + auth_tag 长度。

    Args:
        content: 待检测内容

    Returns:
        是否为加密内容
    """
    if not content:
        return False

    try:
        decoded = base64.b64decode(content)
        # 最小长度：nonce(12) + ciphertext(至少1) + tag(16) = 29
        return len(decoded) >= NONCE_LENGTH + 1 + 16
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 数据转换辅助
# ---------------------------------------------------------------------------

def prepare_diary_for_storage(
    content: str,
    *,
    is_cloud_sync: bool = False,
    client_encrypted: bool = False,
    client_key: bytes | None = None,
) -> dict[str, Any]:
    """准备日记内容用于存储。

    根据同步模式决定加密策略：
    - 本地存储模式：使用服务端辅助加密
    - 云端同步模式：
      - 如果客户端已加密：直接存储密文
      - 如果客户端未加密：返回原内容（理论上不应该发生）

    Args:
        content: 原始内容
        is_cloud_sync: 是否云端同步模式
        client_encrypted: 内容是否已由客户端加密
        client_key: 客户端加密密钥（仅用于验证）

    Returns:
        包含加密后内容和元数据的字典
    """
    if not content:
        return {"content": "", "is_encrypted": False, "content_hash": ""}

    # 计算内容哈希（用于完整性校验）
    content_hash = compute_content_hash(content)

    if is_cloud_sync:
        # 云端同步模式
        if client_encrypted:
            # 客户端已加密，直接存储密文
            return {
                "content": content,  # content 此时已经是密文
                "is_encrypted": True,
                "content_hash": content_hash,  # 原始内容的哈希
            }
        else:
            # 云端同步但客户端未加密，这是异常情况
            # 服务端不应加密，应该要求客户端加密
            logger.warning("云端同步模式下收到未加密内容，建议客户端加密")
            return {
                "content": content,
                "is_encrypted": False,
                "content_hash": content_hash,
            }
    else:
        # 本地存储模式，服务端辅助加密
        encrypted = encrypt_content_server_side(content)
        return {
            "content": encrypted,
            "is_encrypted": True,
            "content_hash": content_hash,
        }


def retrieve_diary_content(
    stored_content: str,
    *,
    is_encrypted: bool,
    is_cloud_sync: bool,
    client_key: bytes | None = None,
) -> str:
    """获取日记内容（解密）。

    根据同步模式和加密状态决定解密策略：
    - 本地存储模式且已加密：使用服务端密钥解密
    - 云端同步模式且已加密：无法解密（需客户端解密）

    Args:
        stored_content: 存储的内容（可能是密文）
        is_encrypted: 内容是否已加密
        is_cloud_sync: 是否云端同步模式
        client_key: 客户端解密密钥（云端同步时需要）

    Returns:
        解密后的内容，或原始内容（未加密时）
    """
    if not stored_content:
        return ""

    if not is_encrypted:
        return stored_content

    if is_cloud_sync:
        # 云端同步模式，服务端无法解密
        if client_key:
            # 如果提供了客户端密钥，尝试解密
            return decrypt_content_from_storage(stored_content, client_key)
        else:
            # 无法解密，返回密文（客户端需要自行解密）
            logger.debug("云端同步日记内容已加密，服务端无法解密")
            return stored_content  # 返回密文，客户端自行处理
    else:
        # 本地存储模式，使用服务端密钥解密
        return decrypt_content_server_side(stored_content)