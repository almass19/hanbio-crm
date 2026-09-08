"""Валидация и нормализация пользовательского ввода."""

from __future__ import annotations

import re

_DIGITS_RE = re.compile(r"\D+")
_NAME_ALLOWED_RE = re.compile(r"^[А-Яа-яЁёA-Za-z\- ]+$")

_NAME_MIN_LEN = 3
_NAME_MAX_LEN = 100
_NAME_MIN_WORDS = 2


def normalize_phone(raw: str) -> str | None:
    """Привести номер к виду ``+7XXXXXXXXXX`` (Казахстан).

    Принимает ``8XXXXXXXXXX``, ``+7XXXXXXXXXX``, ``7XXXXXXXXXX`` и 10 цифр без кода.
    Возвращает ``None``, если номер не распознан.
    """
    digits = _DIGITS_RE.sub("", raw or "")

    if len(digits) == 11 and digits[0] in {"7", "8"}:
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    return None


def validate_full_name(raw: str) -> str | None:
    """Проверить ФИО: минимум 2 слова, только буквы/дефис/пробел, длина 3–100.

    Возвращает очищенное значение (схлопнутые пробелы) либо ``None``.
    """
    cleaned = " ".join((raw or "").split())

    if not (_NAME_MIN_LEN <= len(cleaned) <= _NAME_MAX_LEN):
        return None
    if len(cleaned.split()) < _NAME_MIN_WORDS:
        return None
    if not _NAME_ALLOWED_RE.match(cleaned):
        return None
    return cleaned
