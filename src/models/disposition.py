import sys
import json
from datetime import datetime, timezone
from typing import List, Dict
from PySide6.QtCore import Qt, QAbstractTableModel

from models.transaction import Transaction
from PySide6.QtWidgets import  QMessageBox

import dateparser

class Disposition(Transaction):
    """The getting-rid-of some of a commodity. Could be a sale, a gift, or a payment

    ctor params:
    timestamp: float -- When the thing happened (posix timestamp)
    asset: str -- the commodity involved
    asset_amount: float -- The amount disposed (negative number)
    asset_price: float --  The unit price of the commodity when disposed
    fees: float -- might be zero
    reference: str -- order or transaction id or whatever
    comment: str -- as in 'Mike repaying me for lunch'
    """

    def __str__(self) -> str:
        return 'Dis'

    def __init__(self, timestamp: float, asset: str, asset_amount: float, asset_price: float,
                 fees: float, reference: str, comment: str):
        super().__init__( timestamp, asset, asset_amount, asset_price, fees, comment)
        self.reference = reference
        assert asset != None

    @classmethod
    def duplicate(cls, other: "Disposition") -> "Disposition":
        return cls(other.timestamp, other.asset, other.asset_amount,
                   other.asset_price, other.fees, other.reference, other.comment)


    @classmethod
    def from_json_dict(cls, jd: Dict) -> "Disposition":
        """A json-serialized Disposition is a dict when loaded.

        Like this:
            {
                "timestamp": 1493251200.0,
                "asset": "ETH",
                "asset_amount": 5,
                "asset_price": 1014.95,
                "fees": 0,
                "comment": "",
                "reference": "fd0858a7-4bdf-4278-8d9a-b4045740a32f"
            }
        """
        return cls(
            jd["timestamp"],
            jd["asset"],
            jd["asset_amount"],
            jd["asset_price"],
            jd["fees"],
            jd["reference"],
            jd["comment"]
        )


    def to_json_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "asset": self.asset,
            "asset_amount": self.asset_amount,
            "asset_price": self.asset_price,
            "fees": self.fees,
            "comment": self.comment,
            "reference": self.reference
        }

# QT View models
class DisTableModel(QAbstractTableModel):
    """
    The app internally holds Dispositions as a time-sorted list of Disposition class
    instances, but for display spacing reasons we want to use a QTableView
    to display it rather than a QListView. This model does the translation.
    """
    DIS_TIMESTAMP_IDX = 0
    DIS_AMOUNT_IDX = 1
    DIS_PRICE_IDX = 2
    DIS_FEES_IDX = 3
    DIS_REFERENCE_IDX = 4
    DIS_COMMENT_IDX = 5
    DIS_CANCEL_BTN_IDX = 6
    DIS_ACCEPT_BTN_IDX = 7
    DIS_COLUMN_COUNT = 8

    HEADER_LABELS = ["Date", "Amount", "Price", "Fees", "Reference", "Comment", "", ""]

    def __init__(self, asset: str, dispositions: List[Disposition]):
        super(DisTableModel, self).__init__()
        assert asset != None
        self.asset = asset
        self.dispositionsList = dispositions
        self.edit_buff = None
        self.row_under_edit: int = -1 # only a single row can be edited at a time

    def reset_model(self, asset: str, dispositions: List[Disposition] = []) -> None:
        assert asset!= None
        self.asset = asset
        self.beginResetModel()
        self.dispositionsList = dispositions if dispositions else []
        self.endResetModel()

    def edit_row(self, row: int = -1) -> None:
        if self.row_under_edit == -1:
            self.row_under_edit = row
            self.edit_buff = Disposition.duplicate(self.dispositionsList[row])
        else:
            prev_edit_row = self.row_under_edit
            self.cancel_edit()
            if row != prev_edit_row:
                self.row_under_edit = row

    def cancel_edit(self) -> None:
        self.row_under_edit = -1
        self.edit_buff = None

    def accept_edit(self) -> None:
        self.dispositionsList[self.row_under_edit] = Disposition.duplicate(self.edit_buff)
        self.row_under_edit = -1
        self.edit_buff = None

    def set_dis_data(self, dis: Disposition, col: int, str_val: str) -> bool:
        try:
            if col == DisTableModel.DIS_TIMESTAMP_IDX:
                # Note that strptime() ignores TZ abbreviations, so we have to use the ugly "+0000"
                dt = dateparser.parse(str_val, settings={'RETURN_AS_TIMEZONE_AWARE': True})
                dis.timestamp = dt.timestamp()
            if col == DisTableModel.DIS_AMOUNT_IDX:
                dis.asset_amount = float(str_val)
            if col == DisTableModel.DIS_PRICE_IDX:
                dis.asset_price = float(str_val)
            if col == DisTableModel.DIS_FEES_IDX:
                dis.fees = float(str_val)
            if col == DisTableModel.DIS_REFERENCE_IDX:
                dis.reference = str_val
            if col == DisTableModel.DIS_COMMENT_IDX:
                dis.comment = str_val
            return True
        except Exception as ex:
            button = QMessageBox.warning(None,"Edit", str(ex) )
            return False

    def fetch_data(self, dis: Disposition, col: int) -> object:
        if col == DisTableModel.DIS_TIMESTAMP_IDX:
           return datetime.fromtimestamp(dis.timestamp,tz=timezone.utc).strftime(Transaction.DATETIME_FORMAT)
        if col == DisTableModel.DIS_AMOUNT_IDX:
            return f"{dis.asset_amount:.8f}"
        if col == DisTableModel.DIS_PRICE_IDX:
            return f"{dis.asset_price:.8f}"
        if col == DisTableModel.DIS_FEES_IDX:
            return f"{dis.fees:.8f}"
        if col == DisTableModel.DIS_REFERENCE_IDX:
            return dis.reference
        if col == DisTableModel.DIS_COMMENT_IDX:
            return dis.comment

    # overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return DisTableModel.HEADER_LABELS[section]

    def flags(self, index):
        if index.row() == self.row_under_edit:
            if index.column() < self.DIS_CANCEL_BTN_IDX:
                return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
            else:
                return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.DisplayRole:
            dis = self.edit_buff if self.row_under_edit == index.row() else self.dispositionsList[index.row()]
            return self.fetch_data(dis, index.column())

        if role == Qt.EditRole and index.row() == self.row_under_edit:
            return self.fetch_data(self.edit_buff, index.column())

    def setData(self, index, value, role):
        """This moves edited widget (string) data into the edit_buffer"""
        if role == Qt.EditRole and index.row() == self.row_under_edit:
            return self.set_dis_data(self.edit_buff, index.column(), str(value))


    def rowCount(self, index):
        return len(self.dispositionsList)

    def columnCount(self, index):
        return self.DIS_COLUMN_COUNT
