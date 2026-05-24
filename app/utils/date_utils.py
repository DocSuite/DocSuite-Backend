from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def format_date(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")
