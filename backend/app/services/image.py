"""图片处理服务模块。

提供图片压缩、缩略图生成、格式校验等能力。
基于 Pillow 库实现，支持异步操作。
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Protocol

from PIL import Image

logger = logging.getLogger(__name__)

# 允许的图片格式
ALLOWED_FORMATS: set[str] = {"jpg", "jpeg", "png", "webp"}

# MIME 类型映射
FORMAT_MIME_MAP: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}

# 格式与 Pillow 保存格式映射
FORMAT_PIL_MAP: dict[str, str] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
}

# 默认压缩参数
DEFAULT_MAX_WIDTH = 1080
DEFAULT_THUMBNAIL_SIZE = (200, 200)
DEFAULT_QUALITY = 85
DEFAULT_WEBP_QUALITY = 80


# ---------------------------------------------------------------------------
# Protocol 定义 — 图片处理服务接口契约
# ---------------------------------------------------------------------------

class ImageServiceProtocol(Protocol):
    """图片处理服务接口。"""

    async def validate_format(self, filename: str) -> bool:
        """校验图片格式是否允许。

        Args:
            filename: 文件名（含扩展名）

        Returns:
            格式是否合法
        """
        ...

    async def compress(
        self,
        file_bytes: bytes,
        max_width: int = DEFAULT_MAX_WIDTH,
        quality: int = DEFAULT_QUALITY,
        output_format: str | None = None,
    ) -> bytes:
        """压缩图片，限制最大宽度并调整质量。

        Args:
            file_bytes: 原始图片二进制内容
            max_width: 最大宽度，超过则等比缩放
            quality: 压缩质量 (1-100)
            output_format: 输出格式，None 表示保持原格式

        Returns:
            压缩后的图片二进制内容
        """
        ...

    async def generate_thumbnail(
        self,
        file_bytes: bytes,
        size: tuple[int, int] = DEFAULT_THUMBNAIL_SIZE,
        output_format: str = "webp",
    ) -> bytes:
        """生成缩略图。

        Args:
            file_bytes: 原始图片二进制内容
            size: 缩略图尺寸 (宽, 高)
            output_format: 输出格式，默认 webp 以节省空间

        Returns:
            缩略图的二进制内容
        """
        ...

    async def get_image_info(self, file_bytes: bytes) -> dict[str, int | str]:
        """获取图片基本信息。

        Args:
            file_bytes: 图片二进制内容

        Returns:
            {"width": int, "height": int, "format": str, "size_bytes": int}
        """
        ...


# ---------------------------------------------------------------------------
# Pillow 图片处理实现
# ---------------------------------------------------------------------------

class PillowImageService:
    """基于 Pillow 的图片处理服务。

    支持：
    - 格式校验（仅允许 jpg/png/webp）
    - 图片压缩（最大宽度限制 + 质量调整）
    - 缩略图生成
    - 图片信息读取
    """

    async def validate_format(self, filename: str) -> bool:
        """校验文件扩展名是否在允许列表中。"""
        ext = Path(filename).suffix.lstrip(".").lower()
        is_valid = ext in ALLOWED_FORMATS
        if not is_valid:
            logger.warning(
                "[ImageService] 不支持的图片格式: %s，允许: %s",
                ext, ", ".join(ALLOWED_FORMATS),
            )
        return is_valid

    async def compress(
        self,
        file_bytes: bytes,
        max_width: int = DEFAULT_MAX_WIDTH,
        quality: int = DEFAULT_QUALITY,
        output_format: str | None = None,
    ) -> bytes:
        """压缩图片。

        处理流程：
        1. 加载图片
        2. 如果宽度超过 max_width，等比缩放
        3. 转换为目标格式（如果指定）
        4. 调整质量参数压缩输出
        """
        img = Image.open(io.BytesIO(file_bytes))
        original_size = img.size

        # 确定输出格式
        if output_format:
            pil_format = FORMAT_PIL_MAP.get(output_format.lower(), "JPEG")
        else:
            # 保持原格式
            pil_format = img.format or "JPEG"

        # 等比缩放
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            logger.info(
                "[ImageService] 图片缩放: %s -> %s",
                original_size, img.size,
            )

        # 处理 RGBA 模式（PNG 转 JPEG 时需要转换）
        if img.mode == "RGBA" and pil_format == "JPEG":
            # 创建白色背景
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # 使用 alpha 通道作为 mask
            img = background
        elif img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")

        # 压缩输出
        output_buffer = io.BytesIO()
        save_kwargs: dict = {"format": pil_format}

        if pil_format == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif pil_format == "WEBP":
            save_kwargs["quality"] = min(quality, DEFAULT_WEBP_QUALITY)
            save_kwargs["method"] = 4  # 压缩方法，4 为较好的平衡
        elif pil_format == "PNG":
            save_kwargs["optimize"] = True

        img.save(output_buffer, **save_kwargs)
        compressed = output_buffer.getvalue()

        compression_ratio = len(compressed) / len(file_bytes) * 100
        logger.info(
            "[ImageService] 图片压缩完成: %d -> %d 字节 (%.1f%%), 格式: %s",
            len(file_bytes), len(compressed), compression_ratio, pil_format,
        )

        return compressed

    async def generate_thumbnail(
        self,
        file_bytes: bytes,
        size: tuple[int, int] = DEFAULT_THUMBNAIL_SIZE,
        output_format: str = "webp",
    ) -> bytes:
        """生成缩略图。

        使用 Thumbnail 方法保持宽高比，图片不会超过指定尺寸。
        """
        img = Image.open(io.BytesIO(file_bytes))

        # 生成缩略图（保持宽高比）
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # 处理 RGBA 模式
        if img.mode == "RGBA" and output_format.lower() in ("jpg", "jpeg"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")

        # 输出
        pil_format = FORMAT_PIL_MAP.get(output_format.lower(), "WEBP")
        output_buffer = io.BytesIO()

        save_kwargs: dict = {"format": pil_format}
        if pil_format == "JPEG":
            save_kwargs["quality"] = 75
            save_kwargs["optimize"] = True
        elif pil_format == "WEBP":
            save_kwargs["quality"] = 70
            save_kwargs["method"] = 4
        elif pil_format == "PNG":
            save_kwargs["optimize"] = True

        img.save(output_buffer, **save_kwargs)
        thumbnail = output_buffer.getvalue()

        logger.info(
            "[ImageService] 缩略图生成: %s -> %s, 格式: %s, 大小: %d 字节",
            size, img.size, pil_format, len(thumbnail),
        )

        return thumbnail

    async def get_image_info(self, file_bytes: bytes) -> dict[str, int | str]:
        """获取图片基本信息。"""
        img = Image.open(io.BytesIO(file_bytes))
        img_format = img.format or "UNKNOWN"
        # 将 Pillow 格式名转为小写扩展名
        format_lower = img_format.lower()
        if format_lower == "jpeg":
            format_lower = "jpg"

        info = {
            "width": img.width,
            "height": img.height,
            "format": format_lower,
            "size_bytes": len(file_bytes),
        }
        logger.debug("[ImageService] 图片信息: %s", info)
        return info


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_image_service() -> PillowImageService:
    """创建图片处理服务实例。

    Returns:
        PillowImageService 实例
    """
    return PillowImageService()
