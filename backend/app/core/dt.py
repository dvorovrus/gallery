"""Хелперы времени.

``datetime.utcnow()`` deprecated начиная с Python 3.12. Чтобы убрать предупреждения
и не плодить смешение naive/aware datetime (которое ломает сравнения), здесь
предоставлен единый помощник, возвращающий naive UTC — эквивалент старого
``datetime.utcnow()`` по поведению, но без использования устаревшего API.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Текущее время в UTC как naive datetime (для совместимости со схемой БД)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
