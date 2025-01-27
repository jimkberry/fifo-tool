import sys
import json
from datetime import datetime
from typing import List, Dict

from PySide6.QtCore import Qt, QAbstractTableModel

class Transaction():
    """Acquiring or disposing of some of a commodity

    ctor params:
    timestamp: float -- When the transaction occurrred
    asset_price: float --  The market unit price of the commodity at timestamp
    asset_amount: float -- The amount involved. Always positive.
    fees: float -- any fees or taxes or whatever
    reference: str -- any tx or order ID
    comment: str -- as in 'Mike repaying me for lunch'
    """
    # Note that %Z DOES NOT WORK! A tz abbreviation is ignored by strptime
    # you MUST use a numeric offset (which is kinda ugly when displayed)

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z" # "12/27/2016 14:14:00 UTC"

    # DATETIME_FORMAT = "%m/%d/%Y %H:%M:%S %z" # "12/27/2016 14:14:00 +0000"

    def __init__(self, timestamp: float, asset: str, asset_amount: float, asset_price: float,
                fees: float, reference: str, comment: str, disabled: bool = False) -> None:
        self.timestamp = timestamp  # floating-point posix epoch
        self.asset = asset
        self.asset_price = asset_price
        self.asset_amount = asset_amount
        self.fees = fees
        self.reference = reference
        self.comment = comment
        self.disabled = disabled # public attribute
        self.update_hash()  # hash

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Invalid timestamp")
        self._timestamp = value

    @property
    def asset(self) -> str:
        return self._asset

    @asset.setter
    def asset(self, value: str) -> None:
        if not isinstance(value, str) or not value:
            raise ValueError("Invalid asset name")
        self._asset = value

    @property
    def asset_price(self) -> float:
        return self._asset_price

    @asset_price.setter
    def asset_price(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Negative asset price")
        self._asset_price = value

    @property
    def asset_amount(self) -> float:
        return self._asset_amount

    @asset_amount.setter
    def asset_amount(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Negative asset amount")
        self._asset_amount = value

    @property
    def fees(self) -> float:
        return self._fees

    @fees.setter
    def fees(self, value: float) -> None:
#        if value < 0:  TODO: put back in
#            raise ValueError("Negative fees")
        self._fees = value

    @property
    def reference(self) -> str:
        return self._reference

    @reference.setter
    def reference(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Reference must be a string")
        self._reference = value

    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Comment must be a string")
        self._comment = value


    @property
    def value(self) -> float:
        return self.asset_amount * self.asset_price

    def update_hash(self) -> None:
        self._hash = hash((self.timestamp, self.asset, self.asset_amount, self.asset_price, self.fees))  # try make dups harder to have

# QT View models
class TxTableModel(QAbstractTableModel):
    """
    Parent mode of both the Acqusition and Disposition table model
    """

    def __init__(self, asset: str, transactions: List[Transaction] = []) -> None:
        super(TxTableModel, self).__init__()
        assert asset is not None
        self.asset = asset
        self.transactionsList = transactions
        self.edit_buff = None
        self.row_under_edit: int = -1 # only a single row can be edited at a time

    # virtuals
    def set_data(self, tx: Transaction, col: int, str_val: str) -> bool:
        raise NotImplementedError("Subclasses must implement this method")

    def fetch_data(self, tx: Transaction, col: int) -> object:
        raise NotImplementedError("Subclasses must implement this method")

    def header_labels(self) -> List[str]:
        raise NotImplementedError("Subclasses must implement this method")

    def editable_columns(self) -> List[int]:
        """return a list of indices for columns that are editable"""
        raise NotImplementedError("Subclasses must implement this method")

    def button_columns(self) -> List[int]:
        """return a list of column indices that are buttons (cancel/accept)"""
        raise NotImplementedError("Subclasses must implement this method")

    # end virtuals

    def money_str_to_float(self, str_val: str) -> float:
        """String may or may not begin with a $"""
        return float(str_val.replace('$', ''))

    def reset_model(self, asset: str, transactions: List[Transaction]) -> None:
        assert asset is not None
        self.asset = asset
        self.beginResetModel()
        self.transactionsList = transactions if transactions else []
        self.endResetModel()

    def is_disabled(self, row: int) -> bool:
        return self.transactionsList[row].disabled

    def toggle_disabled(self, row: int) -> None:
         self.transactionsList[row].disabled = not self.transactionsList[row].disabled

    def edit_row(self, row: int = -1) -> None:
        if self.row_under_edit == -1:
            self.row_under_edit = row
            self.edit_buff = self.transactionsList[row].duplicate()
        else:
            prev_edit_row = self.row_under_edit
            self.cancel_edit()
            if row != prev_edit_row:
                self.row_under_edit = row

    def cancel_edit(self) -> None:
        self.row_under_edit = -1
        self.edit_buff = None

    def accept_edit(self) -> None:
        self.transactionsList[self.row_under_edit] = self.edit_buff.duplicate()
        self.row_under_edit = -1
        self.edit_buff = None

    # overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_labels()[section]

    def flags(self, index):
        if index.row() == self.row_under_edit:
            if index.column() in self.editable_columns():
                return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
            else:
                return Qt.ItemIsEnabled # buttons and computed stuff

        else:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.DisplayRole:
            acq = self.edit_buff if self.row_under_edit == index.row() else self.transactionsList[index.row()]
            return self.fetch_data(acq, index.column())
        if role == Qt.EditRole and index.row() == self.row_under_edit:
            return self.fetch_data(self.edit_buff, index.column())

    def setData(self, index, value, role):
        """This moves edited widget (string) data into the edit_buffer"""
        if role == Qt.EditRole and index.row() == self.row_under_edit:
            return self.set_data(self.edit_buff, index.column(), str(value))

    def rowCount(self, index=None):
        return len(self.transactionsList)

    def columnCount(self, index=None):
        return len(self.header_labels())
