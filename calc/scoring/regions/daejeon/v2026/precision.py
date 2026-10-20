"""Local calculation precision; each region can change it independently."""
from decimal import Decimal, ROUND_HALF_UP
from calc.scoring.utils import decimal_value

ZERO = Decimal("0")
SIX_PLACES = Decimal("0.000001")

def rounded(value):
    return decimal_value(value).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
