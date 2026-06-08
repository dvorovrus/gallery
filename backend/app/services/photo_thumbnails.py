from __future__ import annotations

import io

from PIL import Image


def generate_thumbnail_bytes(file_content: bytes, width: int = 400) -> bytes:
    with Image.open(io.BytesIO(file_content)) as image:
        image = image.copy()
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        aspect_ratio = image.height / image.width
        new_height = max(1, int(width * aspect_ratio))
        image.thumbnail((width, new_height), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85, optimize=True)
        return buffer.getvalue()
