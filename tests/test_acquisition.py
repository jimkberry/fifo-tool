
import sys
import pytest
from datetime import datetime,timezone
from typing import List, Dict, Any

import dateparser

from models.acquisition import Acquisition

TIMESTAMP_A = dateparser.parse('03/12/2022 12:34:56+0000', settings={'RETURN_AS_TIMEZONE_AWARE': True}).timestamp()
ASSET_A = "BTC"
ASSET_AMOUNT_A = 43.24
ASSET_PRICE_A = 100.0
FEES_A = 1.0
REFERENCE_A = "Reference A"
COMMENT_A = "Mike paid me for lunch"

ACQ_JSON_A = {
    "timestamp": 1451298900.0,  # "12/28/2015 10:35:00+0000",
    "asset": "BTC",
    "asset_amount": 23.48877188,
    "asset_price": 425.08,
    "fees": 0.0,
    "reference": "The ref",
    "comment": "Yahoo!"
}

ACQ_JSON_B = {
    "timestamp": 1451298900.0,  # "12/28/2015 10:35:00+0000",
    "asset": "BTC",
    "asset_amount": 23.48877188,
    "asset_price": 425.08,
    "fees": 0.0,
    "reference": "The ref",
    "comment": "Yahoo!",
    "disabled": True
}

def test_acquisition_init():
    #default
    a = Acquisition(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, REFERENCE_A, COMMENT_A)
    assert a.timestamp == TIMESTAMP_A
    assert a.asset == ASSET_A
    assert a.asset_price == ASSET_PRICE_A
    assert a.asset_amount == ASSET_AMOUNT_A
    assert a.fees == FEES_A
    assert a.reference == REFERENCE_A
    assert a.comment == COMMENT_A
    assert a.disabled == False

    b = Acquisition(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, REFERENCE_A, COMMENT_A, True)
    assert b.disabled == True

def test_acquisition_from_json_dict():
    a = Acquisition.from_json_dict(ACQ_JSON_A)
    assert a.timestamp == 1451298900.0
    assert a.asset == "BTC"
    assert a.asset_price == 425.08
    assert a.asset_amount == 23.48877188
    assert a.fees == 0.0
    assert a.reference == "The ref"
    assert a.comment == "Yahoo!"
    assert a.disabled == False

    b = Acquisition.from_json_dict(ACQ_JSON_B)
    assert b.disabled == True


