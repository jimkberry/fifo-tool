import sys
import json
from datetime import datetime,timezone
from typing import List, Dict

from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtWidgets import  QMessageBox

import dateparser

from models.transaction import Transaction

class Acquisition(Transaction):
    """The receipt of a 'lot' of a commodity. Could be a purchase, a gift, or a payment

    ctor params:
    timestamp: float -- When the lot was acquired
    asset_amount: float -- The amount when the lot was acquired
    asset_price: float --  The unit cost of the commodity when acqired
    fees: float -- might be zero
    comment: str -- as in 'Mike repaying me for lunch'
    """

    def __str__(self) -> str:
        return 'Acq'

    def __init__(self, timestamp: float, asset: str, asset_amount: float,
                 asset_price: float, fees: float, comment: str = None) -> None:
        super().__init__( timestamp, asset, asset_amount, asset_price, fees, comment)
        assert asset != None

    @classmethod
    def duplicate(cls, other: "Acquisition") -> "Acquisition":
        # TODO: why doesn;t this (and other methods) let transactuio do the transaction attrs?
        return cls(other.timestamp, other.asset, other.asset_amount, other.asset_price, other.fees, other.comment)

    @classmethod
    def from_json_dict(cls, jd: Dict) -> "Acquisition":
        """A json-serialized Acquisition is a dict when loaded.

        Like this:
            {
                "timestamp": 1493251200.0,
                "asset": "BTC",
                "asset_amount": 27.76054701,
                "asset_price": 363.89
                "fees": 0.00,
                "comment": "Some comment"
            }
        """
        return cls(
                jd["timestamp"],
                jd["asset"],
                jd["asset_amount"],
                jd["asset_price"],
                jd["fees"],
                jd.get("comment", "")
            )

    def to_json_dict(self) -> Dict:
        return  {
            "timestamp": self.timestamp,
            "asset": self.asset,
            "asset_amount": self.asset_amount,
            "asset_price": self.asset_price,
            "fees": self.fees,
            "comment": self.comment
        }



# QT View models
class AcqTableModel(QAbstractTableModel):
    """
    The app internally holds Acquisitions as a list of Acqusition class
    instances, but for display spacing reasons we want to use a QTableView
    to display it rather than a QListView. This model does the translation.
    """
    ACQ_TIMESTAMP_IDX = 0
    ACQ_ASSET_AMOUNT_IDX = 1
    ACQ_ASSET_PRICE_IDX = 2
    ACQ_COMMENT_IDX = 3
    ACQ_CANCEL_BTN_IDX = 4
    ACQ_ACCEPT_BTN_IDX = 5
    ACQ_COLUMN_COUNT = 6

    HEADER_LABELS = ["Date", "Amount", "Price", "Comment", "", ""]

    def __init__(self, asset: str, acquisitions: List[Acquisition] = []) -> None:
        super(AcqTableModel, self).__init__()
        assert asset != None
        self.asset = asset
        self.acquisitionsList = acquisitions
        self.edit_buff = None
        self.row_under_edit: int = -1 # only a single row can be edited at a time

    def reset_model(self, asset: str, acquisitions: List[Acquisition] = []) -> None:
        assert asset != None
        self.asset = asset
        self.beginResetModel()
        self.acquisitionsList = acquisitions if acquisitions else []
        self.endResetModel()

    def edit_row(self, row: int = -1) -> None:
        if self.row_under_edit == -1:
            self.row_under_edit = row
            self.edit_buff = Acquisition.duplicate(self.acquisitionsList[row])
        else:
            prev_edit_row = self.row_under_edit
            self.cancel_edit()
            if row != prev_edit_row:
                self.row_under_edit = row

    def cancel_edit(self) -> None:
        self.row_under_edit = -1
        self.edit_buff = None

    def accept_edit(self) -> None:
        self.acquisitionsList[self.row_under_edit] = Acquisition.duplicate(self.edit_buff)
        self.row_under_edit = -1
        self.edit_buff = None

    def set_acq_data(self, acq: Acquisition, col: int, str_val: str) -> bool:
        try:
            if col == AcqTableModel.ACQ_TIMESTAMP_IDX:
                # Note that strptime() ignores TZ abbreviations, so we have to use the ugly "+0000"
                # dt = datetime.strptime(str_val, Acquisition.DATETIME_FORMAT)
                # if dt.tzinfo == None:
                #     raise ValueError("Invalid date format. Unknown timezone")
                dt = dateparser.parse(str_val, settings={'RETURN_AS_TIMEZONE_AWARE': True})
                acq.timestamp = dt.timestamp()
            if col == AcqTableModel.ACQ_ASSET_AMOUNT_IDX:
                acq.asset_amount = float(str_val)
            if col == AcqTableModel.ACQ_ASSET_PRICE_IDX:
                acq.asset_price = float(str_val)
            if col == AcqTableModel.ACQ_COMMENT_IDX:
                acq.comment = str_val
            return True
        except Exception as ex:
            button = QMessageBox.warning(None,"Edit", str(ex) )
            return False

    def fetch_data(self, acq: Acquisition, col: int) -> object:
        if col == AcqTableModel.ACQ_TIMESTAMP_IDX:
            return datetime.fromtimestamp(acq.timestamp,tz=timezone.utc).strftime(Acquisition.DATETIME_FORMAT)
        if col == AcqTableModel.ACQ_ASSET_AMOUNT_IDX:
            return f"{acq.asset_amount:.8f}"
        if col == AcqTableModel.ACQ_ASSET_PRICE_IDX:
            return f"{acq.asset_price:.8f}"
        if col == AcqTableModel.ACQ_COMMENT_IDX:
            return acq.comment
        if col == AcqTableModel.ACQ_CANCEL_BTN_IDX:
            return None
        if col == AcqTableModel.ACQ_ACCEPT_BTN_IDX:
            return None

    # overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return AcqTableModel.HEADER_LABELS[section]

    def flags(self, index):
        if index.row() == self.row_under_edit:
            if index.column() < AcqTableModel.ACQ_CANCEL_BTN_IDX:
                return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
            else:
                return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.DisplayRole:
            acq = self.edit_buff if self.row_under_edit == index.row() else self.acquisitionsList[index.row()]
            return self.fetch_data(acq, index.column())

        if role == Qt.EditRole and index.row() == self.row_under_edit:
            return self.fetch_data(self.edit_buff, index.column())

    def setData(self, index, value, role):
        """This moves edited widget (string) data into the edit_buffer"""
        if role == Qt.EditRole and index.row() == self.row_under_edit:
            return self.set_acq_data(self.edit_buff, index.column(), str(value))

    def rowCount(self, index):
        return len(self.acquisitionsList)

    def columnCount(self, index):
        return self.ACQ_COLUMN_COUNT