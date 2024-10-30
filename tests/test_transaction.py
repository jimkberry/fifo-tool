
import sys
import pytest
from datetime import datetime
from typing import List, Dict, Any

from models.transaction import Transaction

TIMESTAMP_FORMAT = '%m/%d/%Y %H:%M:%S%z'
TIMESTAMP_A = datetime.strptime('03/12/2022 12:34:56+0000', TIMESTAMP_FORMAT)
ASSET_AMOUNT_A = 43.24
ASSET_PRICE_A = 100.0
FEES_A = 1.0
COMMENT_A = "Mike paid me for lunch"

def test_transaction_init():

    t = Transaction(TIMESTAMP_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, COMMENT_A)
    assert t.timestamp == TIMESTAMP_A
    assert t.asset_price == ASSET_PRICE_A
    assert t.asset_amount == ASSET_AMOUNT_A
    assert t.fees == FEES_A
    assert t.comment == COMMENT_A

