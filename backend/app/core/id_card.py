import base64
import hashlib
import re
from datetime import date, datetime

from cryptography.fernet import Fernet

from app.core.config import settings


ID_CARD_PATTERN = re.compile(r"^\d{17}[0-9X]$")


def normalize_id_card(value: str) -> str:
    return value.strip().upper()


def is_valid_id_card(value: str) -> bool:
    value = normalize_id_card(value)
    if not ID_CARD_PATTERN.fullmatch(value):
        return False
    try:
        birth_date = datetime.strptime(value[6:14], "%Y%m%d").date()
    except ValueError:
        return False
    if birth_date > date.today():
        return False
    weights = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
    checks = "10X98765432"
    return checks[sum(int(value[i]) * weights[i] for i in range(17)) % 11] == value[-1]


def birth_date_from_id_card(value: str) -> date:
    value = normalize_id_card(value)
    if not is_valid_id_card(value):
        raise ValueError("身份证号格式或校验码不正确")
    return datetime.strptime(value[6:14], "%Y%m%d").date()


def age_from_birth_date(birth_date: date, today: date | None = None) -> int:
    current = today or date.today()
    return current.year - birth_date.year - ((current.month, current.day) < (birth_date.month, birth_date.day))


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.app_secret.encode()).digest())
    return Fernet(key)


def encrypt_id_card(value: str) -> str:
    return _fernet().encrypt(normalize_id_card(value).encode()).decode()


def decrypt_id_card(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def hash_id_card(value: str) -> str:
    return hashlib.sha256(normalize_id_card(value).encode()).hexdigest()


def mask_id_card(value: str) -> str:
    return f"{value[:3]}***********{value[-4:]}"
