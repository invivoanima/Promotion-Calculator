"""Reserved local optional bonus rules; excluded from inputs and totals."""
from .precision import ZERO
def calculate_record_score(record):
    return ZERO
def calculate_item_score(item_code, records):
    return ZERO
