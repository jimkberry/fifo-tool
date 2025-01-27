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
    assert t.value == ASSET_AMOUNT_A * ASSET_PRICE_A

def test_transaction_init_invalid_asset_amount():
    with pytest.raises(ValueError):
        Transaction(TIMESTAMP_A, ASSET_A, -1, ASSET_PRICE_A, FEES_A, REFERENCE_A, COMMENT_A)

def test_transaction_init_invalid_asset_price():
    with pytest.raises(ValueError):
        Transaction(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, -1, FEES_A, REFERENCE_A, COMMENT_A)

def test_transaction_init_invalid_fees():
    with pytest.raises(ValueError):
        Transaction(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, -1, REFERENCE_A, COMMENT_A)

def test_transaction_init_invalid_timestamp():
    with pytest.raises(ValueError):
        Transaction(-1, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, REFERENCE_A, COMMENT_A)

def test_transaction_init_invalid_reference():
    with pytest.raises(ValueError):
        Transaction(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, None, COMMENT_A)

def test_transaction_init_invalid_comment():
    with pytest.raises(ValueError):
        Transaction(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, REFERENCE_A, None)

def test_transaction_value():
    t = Transaction(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, REFERENCE_A, COMMENT_A)
    assert t.value == ASSET_AMOUNT_A * ASSET_PRICE_A

