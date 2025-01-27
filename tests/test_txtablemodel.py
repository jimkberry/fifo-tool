import sys
import json
import pytest
from datetime import datetime
import pytest

from datetime import datetime, timezone

from typing import List, Dict

from PySide6.QtCore import Qt, QAbstractTableModel

from src.models.transaction import Transaction, TxTableModel

from dateparser import parse

TIMESTAMP_A = parse('2022-01-01 00:00:00+0000', settings={'RETURN_AS_TIMEZONE_AWARE': True}).timestamp()
ASSET_A = "ETH"
ASSET_AMOUNT_A = 1.0
ASSET_PRICE_A = 3000.0
FEES_A = 0.0
REFERENCE_A = "TX1234567890"
COMMENT_A = "Initial deposit"

TIMESTAMP_B = parse('2022-01-02 00:00:00+0000', settings={'RETURN_AS_TIMEZONE_AWARE': True}).timestamp()
ASSET_B = "ETH"
ASSET_AMOUNT_B = 2.0
ASSET_PRICE_B = 3500.0
FEES_B = 50.0
REFERENCE_B = "TX2345678901"
COMMENT_B = "Second deposit"

class TestTxTableModel(TxTableModel):
    TIMESTAMP_IDX = 0
    ASSET_IDX = 1
    ASSET_AMOUNT_IDX = 2
    ASSET_PRICE_IDX = 3
    FEES_IDX = 4
    REFERENCE_IDX = 5
    COMMENT_IDX = 6

    def __init__(self, asset: str, transactions: List[Transaction] = []) -> None:
        super(TestTxTableModel, self).__init__(asset, transactions)

    def set_data(self, tx: Transaction, col: int, str_val: str) -> bool:
        if col == self.TIMESTAMP_IDX:
            tx.timestamp = float(str_val)
        elif col == self.ASSET_IDX:
            tx.asset = str_val
        elif col == self.ASSET_AMOUNT_IDX:
            tx.asset_amount = float(str_val)
        elif col == self.ASSET_PRICE_IDX:
            tx.asset_price = float(str_val)
        elif col == self.FEES_IDX:
            tx.fees = float(str_val)
        elif col == self.REFERENCE_IDX:
            tx.reference = str_val
        elif col == self.COMMENT_IDX:
            tx.comment = str_val
        return True

    def fetch_data(self, tx: Transaction, col: int) -> object:
        if col == self.TIMESTAMP_IDX:
            return datetime.fromtimestamp(tx.timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        elif col == self.ASSET_IDX:
            return tx.asset
        elif col == self.ASSET_AMOUNT_IDX:
            return  f"{tx.asset_amount:.8f}"
        elif col == self.ASSET_PRICE_IDX:
            return f"{tx.asset_price:.2f}"
        elif col == self.FEES_IDX:
            return f"{tx.fees:.2f}"
        elif col == self.REFERENCE_IDX:
            return tx.reference
        elif col == self.COMMENT_IDX:
            return tx.comment
        return None

    def header_labels(self) -> List[str]:
        return ["Timestamp", "Asset", "Asset Amount", "Asset Price", "Fees", "Reference", "Comment"]

    def editable_columns(self) -> List[int]:
        return [self.ASSET_IDX, self.ASSET_AMOUNT_IDX, self.ASSET_PRICE_IDX, self.FEES_IDX, self.REFERENCE_IDX, self.COMMENT_IDX]

    def button_columns(self) -> List[int]:
        return []

@pytest.fixture
def test_table_model():
    transactions = [
        Transaction(TIMESTAMP_A, ASSET_A, ASSET_AMOUNT_A, ASSET_PRICE_A, FEES_A, REFERENCE_A, COMMENT_A),
        Transaction(TIMESTAMP_B, ASSET_B, ASSET_AMOUNT_B, ASSET_PRICE_B, FEES_B, REFERENCE_B, COMMENT_B)
    ]
    return TestTxTableModel(ASSET_A, transactions)

def test_model_creation(test_table_model):
    assert test_table_model.rowCount() == 2
    assert test_table_model.columnCount() == 7
    assert test_table_model.header_labels() == ["Timestamp", "Asset", "Asset Amount", "Asset Price", "Fees", "Reference", "Comment"]

def test_model_data(test_table_model):
    assert test_table_model.data(test_table_model.index(0, 0),Qt.DisplayRole) == "2022-01-01 00:00:00"
    assert test_table_model.data(test_table_model.index(0, 1),Qt.DisplayRole) == "ETH"
    assert test_table_model.data(test_table_model.index(0, 2), Qt.DisplayRole) == "1.00000000"
    assert test_table_model.data(test_table_model.index(0, 3), Qt.DisplayRole) == "3000.00"
    assert test_table_model.data(test_table_model.index(0, 4), Qt.DisplayRole) == "0.00"
    assert test_table_model.data(test_table_model.index(0, 5), Qt.DisplayRole) == "TX1234567890"
    assert test_table_model.data(test_table_model.index(0, 6), Qt.DisplayRole) == "Initial deposit"

    assert test_table_model.data(test_table_model.index(1, 0), Qt.DisplayRole) == "2022-01-02 00:00:00"
    assert test_table_model.data(test_table_model.index(1, 1), Qt.DisplayRole) == "ETH"
    assert test_table_model.data(test_table_model.index(1, 2), Qt.DisplayRole) == "2.00000000"
    assert test_table_model.data(test_table_model.index(1, 3), Qt.DisplayRole) == "3500.00"
    assert test_table_model.data(test_table_model.index(1, 4), Qt.DisplayRole) == "50.00"
    assert test_table_model.data(test_table_model.index(1, 5), Qt.DisplayRole) == "TX2345678901"
    assert test_table_model.data(test_table_model.index(1, 6), Qt.DisplayRole) == "Second deposit"

def test_model_toggle_disabled(test_table_model):
    pass


