from datetime import date


def validate_date_range(start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise ValueError("end_date must be on or after start_date")


def validate_pagination(offset: int, limit: int, maximum_limit: int = 100) -> tuple[int, int]:
    if offset < 0:
        raise ValueError("offset must be zero or greater")
    if not 1 <= limit <= maximum_limit:
        raise ValueError(f"limit must be between 1 and {maximum_limit}")
    return offset, limit
