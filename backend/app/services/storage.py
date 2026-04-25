"""文件存储服务模块。

提供文件存储能力，支持本地文件系统、MinIO、阿里云 OSS 三种 Provider。
使用 aiofiles 实现异步文件操作。
"""

from __future__ import annotations

import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Protocol

import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)

# 默认上传目录
DEFAULT_UPLOAD_DIR = Path("./uploads")


# ---------------------------------------------------------------------------
# Protocol 定义 — 文件存储服务接口契约
# ---------------------------------------------------------------------------

class StorageProtocol(Protocol):
    """文件存储服务接口。"""

    async def build_path(self, filename: str) -> str:
        """根据文件名构建存储路径。

        Args:
            filename: 原始文件名

        Returns:
            构建后的存储路径（相对路径）
        """
        ...

    async def save(self, file_bytes: bytes, filename: str) -> str:
        """保存文件，返回可访问的 URL 或路径。

        Args:
            file_bytes: 文件二进制内容
            filename: 原始文件名

        Returns:
            文件的可访问 URL 或路径
        """
        ...

    async def get(self, url: str) -> bytes:
        """根据 URL 或路径获取文件内容。

        Args:
            url: 文件的 URL 或路径

        Returns:
            文件的二进制内容
        """
        ...

    async def delete(self, url: str) -> bool:
        """删除文件。

        Args:
            url: 文件的 URL 或路径

        Returns:
            是否删除成功
        """
        ...


# ---------------------------------------------------------------------------
# Local 实现 — 本地文件系统存储
# ---------------------------------------------------------------------------

class LocalStorage:
    """本地文件系统存储服务。

    文件存储到 ./uploads/ 目录，按日期分子目录存储。
    实际创建目录并写入文件，返回可访问的 URL 路径。
    """

    def __init__(self, upload_dir: Path | str | None = None) -> None:
        self._upload_dir = Path(upload_dir) if upload_dir else DEFAULT_UPLOAD_DIR

    async def _ensure_dir(self, dir_path: Path) -> None:
        """确保目录存在。"""
        await aiofiles.os.makedirs(str(dir_path), exist_ok=True)

    def _generate_unique_filename(self, filename: str) -> str:
        """生成唯一文件名，避免冲突。

        格式: {uuid前8位}_{原始文件名}
        """
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        unique_prefix = uuid.uuid4().hex[:8]
        return f"{unique_prefix}_{stem}{suffix}"

    async def build_path(self, filename: str) -> str:
        """构建存储路径，按日期分子目录。

        格式: YYYY-MM-DD/{unique_prefix}_{filename}
        """
        today = date.today().isoformat()
        unique_name = self._generate_unique_filename(filename)
        return f"{today}/{unique_name}"

    async def save(self, file_bytes: bytes, filename: str) -> str:
        """保存文件到本地文件系统。

        Args:
            file_bytes: 文件二进制内容
            filename: 原始文件名

        Returns:
            文件的相对路径，可用于 URL 访问
        """
        sub_path = await self.build_path(filename)
        full_path = self._upload_dir / sub_path

        # 确保目录存在
        await self._ensure_dir(full_path.parent)

        # 异步写入文件
        async with aiofiles.open(str(full_path), "wb") as f:
            await f.write(file_bytes)

        logger.info("[LocalStorage] 文件已保存: %s (%d bytes)", sub_path, len(file_bytes))
        return f"/static/uploads/{sub_path}"

    async def get(self, url: str) -> bytes:
        """根据 URL 路径获取文件内容。

        Args:
            url: 文件的 URL 路径（如 /static/uploads/2024-01-01/abc_file.jpg）

        Returns:
            文件的二进制内容
        """
        # 从 URL 中提取子路径
        # /static/uploads/2024-01-01/abc_file.jpg -> 2024-01-01/abc_file.jpg
        sub_path = url.replace("/static/uploads/", "")
        full_path = self._upload_dir / sub_path

        if not full_path.exists():
            logger.warning("[LocalStorage] 文件不存在: %s", full_path)
            return b""

        async with aiofiles.open(str(full_path), "rb") as f:
            content = await f.read()

        logger.debug("[LocalStorage] 读取文件: %s (%d bytes)", relative_path, len(content))
        return content

    async def delete(self, url: str) -> bool:
        """删除本地文件。

        Args:
            url: 文件的 URL 路径

        Returns:
            是否删除成功
        """
        sub_path = url.replace("/static/uploads/", "")
        full_path = self._upload_dir / sub_path

        if not full_path.exists():
            logger.warning("[LocalStorage] 文件不存在，无法删除: %s", full_path)
            return False

        await aiofiles.os.remove(str(full_path))
        logger.info("[LocalStorage] 文件已删除: %s", relative_path)
        return True


# ---------------------------------------------------------------------------
# MinIO 存储 — 真实调用占位
# ---------------------------------------------------------------------------

class MinIOStorage:
    """MinIO 对象存储服务（真实调用占位）。

    TODO: 接入 MinIO SDK (minio)
    - 需要配置 endpoint、access_key、secret_key、bucket
    - 支持分片上传大文件
    - 支持预签名 URL 生成
    """

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "",
        secret_key: str = "",
        bucket: str = "echo",
        secure: bool = False,
    ) -> None:
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._secure = secure

    async def build_path(self, filename: str) -> str:
        today = date.today().isoformat()
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        return f"minio://{self._bucket}/{today}/{unique_name}"

    async def save(self, file_bytes: bytes, filename: str) -> str:
        # TODO: 接入 MinIO SDK
        path = await self.build_path(filename)
        logger.warning("[MinIOStorage] MinIO SDK 尚未接入，返回占位路径: %s", path)
        return path

    async def get(self, url: str) -> bytes:
        # TODO: 接入 MinIO SDK
        logger.warning("[MinIOStorage] MinIO SDK 尚未接入，返回空字节")
        return b""

    async def delete(self, url: str) -> bool:
        # TODO: 接入 MinIO SDK
        logger.warning("[MinIOStorage] MinIO SDK 尚未接入，返回 False")
        return False


# ---------------------------------------------------------------------------
# 阿里云 OSS 存储 — 真实调用占位
# ---------------------------------------------------------------------------

class OSSStorage:
    """阿里云 OSS 对象存储服务（真实调用占位）。

    TODO: 接入阿里云 OSS SDK (oss2)
    - 需要配置 AccessKey、SecretKey、Endpoint、Bucket
    - 支持分片上传大文件
    - 支持预签名 URL 生成
    - 支持跨区域复制
    """

    def __init__(
        self,
        access_key_id: str = "",
        access_key_secret: str = "",
        endpoint: str = "oss-cn-hangzhou.aliyuncs.com",
        bucket: str = "echo",
    ) -> None:
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        self._endpoint = endpoint
        self._bucket = bucket

    async def build_path(self, filename: str) -> str:
        today = date.today().isoformat()
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        return f"oss://{self._bucket}/{today}/{unique_name}"

    async def save(self, file_bytes: bytes, filename: str) -> str:
        # TODO: 接入阿里云 OSS SDK
        path = await self.build_path(filename)
        logger.warning("[OSSStorage] 阿里云 OSS SDK 尚未接入，返回占位路径: %s", path)
        return path

    async def get(self, url: str) -> bytes:
        # TODO: 接入阿里云 OSS SDK
        logger.warning("[OSSStorage] 阿里云 OSS SDK 尚未接入，返回空字节")
        return b""

    async def delete(self, url: str) -> bool:
        # TODO: 接入阿里云 OSS SDK
        logger.warning("[OSSStorage] 阿里云 OSS SDK 尚未接入，返回 False")
        return False


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

STORAGE_SERVICES: dict[str, type[LocalStorage | MinIOStorage | OSSStorage]] = {
    "local": LocalStorage,
    "minio": MinIOStorage,
    "oss": OSSStorage,
}


def create_storage_service(
    provider: str = "local",
    **kwargs: Any,
) -> LocalStorage | MinIOStorage | OSSStorage:
    """根据配置创建文件存储服务实例。

    Args:
        provider: 服务提供者名称，可选 local / minio / oss
        **kwargs: 传递给存储服务构造函数的额外参数

    Returns:
        文件存储服务实例

    Raises:
        ValueError: 当 provider 名称不在可用列表中时
    """
    if provider not in STORAGE_SERVICES:
        available = ", ".join(STORAGE_SERVICES.keys())
        raise ValueError(f"未知的存储服务 Provider: {provider}，可用选项: [{available}]")
    return STORAGE_SERVICES[provider](**kwargs)
