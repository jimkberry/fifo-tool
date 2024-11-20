
import sys
import pytest
from datetime import datetime
from typing import List, Dict, Any
import dateparser
from models.transaction import Transaction


TIMESTAMP_A = dateparser.parse('03/12/2022 12:34:56+0000', settings={'RETURN_AS_TIMEZONE_AWARE': True}).timestamp()
ASSET_A = "ETH"
ASSET_AMOUNT_A = 43.24
ASSET_PRICE_A = 100.0
FEES_A = 1.0
REFERENCE_A = "Reference A"
COMMENT_A = "Mike paid me for lunch"

def test_transaction_init():

    t = Transaction(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, REFERENCE_A, COMMENT_A)
    assert t.timestamp == TIMESTAMP_A
    assert t.asset_price == ASSET_PRICE_A
    assert t.asset_amount == ASSET_AMOUNT_A
    assert t.fees == FEES_A
    assert t.comment == COMMENT_A

