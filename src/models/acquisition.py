import sys
import json
from datetime import datetime
from typing import List, Dict

from PySide6.QtCore import Qt, QAbstractTableModel, QDateTime
from PySide6.QtWidgets import  QPushButton, QMessageBox
from PySide6.QtGui import QColor

from models.transaction import Transaction

class Acquisition(Transaction):
    """The receipt of a 'lot' of a commodity. Could be a purchase, a gift, or a payment

    ctor params:
    acq_datetime: datetime -- When the lot was acquired
    asset_amount: float -- The amount when the lot was acquired
    asset_price: float --  The unit cost of the commodity when acqired
    fees: float -- might be zero
    comment: str -- as in 'Mike repaying me for lunch'
    """

    def __str__(self) -> str:
        return 'Acq'

    def __init__(self, acq_datetime: datetime, asset_amount: float,
                 asset_price: float, fees: float, comment: str = None) -> None:
        super().__init__( acq_datetime, asset_amount, asset_price, fees, comment)

    @classmethod
    def duplicate(cls, other: "Acquisition") -> "Acquisition":
        return cls(other.timestamp, other.asset_amount, other.asset_price, other.fees, other.comment)

    @classmethod
    def from_json_dict(cls, jd: Dict) -> "Acquisition":
        """A json-serialized Acquisition is a dict when loaded.

        Like this:
            {
                "timestamp": "12/01/2015 14:19:00",
                "asset_amount": 27.76054701,
                "asset_price": 363.89
                "fees": 0.00,
                "comment": "Some comment"
            }
        """
        return cls(
            datetime.strptime(jd["timestamp"], Transaction.DATETIME_FORMAT),
                jd["asset_amount"],
                jd["asset_price"],
                jd["fees"],
                jd.get("comment", "")
            )

    def to_json_dict(self) -> Dict:
        return  {
            "timestamp": self.timestamp.strftime(Transaction.DATETIME_FORMAT),
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

    def __init__(self, data: List[Acquisition] = []):
        super(AcqTableModel, self).__init__()
        self.acquisitionsList = data  # this is the actual data
        self.edit_buff = None
        self.row_under_edit: int = -1 # only a single row can be edited at a time


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
                acq.timestamp = datetime.strptime(str_val, "%Y-%m-%d %H:%M:%S")
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
            return acq.timestamp.strftime("%Y-%m-%d %H:%M:%S")
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

    # def fetch_data(self, row: int, col: int) -> object:
    #     acq = self.acquisitionsList[row]
    #     if col == AcqTableModel.ACQ_TIMESTAMP_IDX:
    #         return QDateTime(acq.timestamp)
    #     if col == AcqTableModel.ACQ_ASSET_AMOUNT_IDX:
    #         return acq.asset_amount
    #     if col == AcqTableModel.ACQ_ASSET_PRICE_IDX:
    #         return acq.asset_price
    #     if col == AcqTableModel.ACQ_COMMENT_IDX:
    #         return acq.comment


    # overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return AcqTableModel.HEADER_LABELS[section]
        #if orientation == Qt.Vertical and role == Qt.DisplayRole:
        #    return f"{section + 1}"

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