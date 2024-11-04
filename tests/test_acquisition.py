
import sys
import pytest
from datetime import datetime,timezone
from typing import List, Dict, Any

from models.acquisition import Acquisition

TIMESTAMP_FORMAT = '%m/%d/%Y %H:%M:%S%z'
TIMESTAMP_A = datetime.strptime('03/12/2022 12:34:56+0000', TIMESTAMP_FORMAT)
ASSET_AMOUNT_A = 43.24
ASSET_PRICE_A = 100.0
FEES_A = 1.0
COMMENT_A = "Mike paid me for lunch"

ACQ_JSON_A = {
    "timestamp": 1451298900.0,  # "12/28/2015 10:35:00+0000",
    "asset_amount": 23.48877188,
    "asset_price": 425.08,
    "fees": 0.0,
    "comment": "Yahoo!"
}

def test_acquisition_init():
    #default
    a = Acquisition(TIMESTAMP_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, COMMENT_A)
    assert a.timestamp == TIMESTAMP_A
    assert a.asset_price == ASSET_PRICE_A
    assert a.asset_amount == ASSET_AMOUNT_A
    assert a.fees == FEES_A
    assert a.comment == COMMENT_A


def test_acquisition_from_json_dict():
    a = Acquisition.from_json_dict(ACQ_JSON_A)
    assert a.timestamp == datetime.strptime('12/28/2015 10:35:00 +0000', Acquisition.DATETIME_FORMAT).timestamp()
    assert a.asset_price == 425.08
    assert a.asset_amount == 23.48877188
    assert a.fees == 0.0
    assert a.comment == "Yahoo!"


