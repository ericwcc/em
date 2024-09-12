from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

def increment_by_hour(dt: datetime, hours: int = 1) -> datetime:
    return dt + timedelta(hours=hours)

def round_decimal(number: Decimal, decimal_places: int = 3):
    return number.quantize(Decimal(10) ** (-1 * decimal_places), ROUND_HALF_UP)