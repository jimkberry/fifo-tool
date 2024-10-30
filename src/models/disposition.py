import sys
import json
from datetime import datetime
from typing import List, Dict
from PySide6.QtCore import Qt, QAbstractTableModel

from models.transaction import Transaction

class Disposition(Transaction):
    """The getting-rid-of some of a commodity. Could be a sale, a gift, or a payment

    ctor params:
    timestamp: datetime -- When the thing happened
    asset_amount: float -- The amount disposed (negative number)
    asset_price: float --  The unit price of the commodity when disposed
    fees: float -- might be zero
    reference: str -- order or transaction id or whatever
    comment: str -- as in 'Mike repaying me for lunch'
    """

    def __str__(self) -> str:
        return 'Dis'

    def __init__(self, timestamp: datetime, asset_amount: float, asset_price: float,
                 fees: float, reference: str, comment: str):

        super().__init__( timestamp, asset_amount, asset_price, fees, comment)
        self.reference = reference

    @classmethod
    def from_json_dict(cls, jd: Dict) -> "Disposition":
        """A json-serialized Disposition is a dict when loaded.

        Like this:
            {
                "timestamp": "02/03/2017 02:09:50",
                "asset_amount": 5,
                "asset_price": 1014.95,
                "fees": 0,
                "comment": "",
                "reference": "fd0858a7-4bdf-4278-8d9a-b4045740a32f"
            }
        """
        return cls(
            datetime.strptime(jd["timestamp"], Transaction.DATETIME_FORMAT),
            jd["asset_amount"],
            jd["asset_price"],
            jd["fees"],
            jd["reference"],
            jd["comment"]
        )


    def to_json_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.strftime(Transaction.DATETIME_FORMAT),
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
    DIS_COLUMN_COUNT = 6

    HEADER_LABELS = ["Date", "Amount", "Price", "Fees", "reference", "Comment"]

    def __init__(self, data: List[Disposition] = []):
        super(DisTableModel, self).__init__()
        self.dispositionsList = data

    def fetch_data_str(self, row: int, col: int) -> str:
        dis = self.dispositionsList[row]
        if col == DisTableModel.DIS_TIMESTAMP_IDX:
            return dis.timestamp.strftime("%Y-%m-%d %H:%M:%S")
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
        #if orientation == Qt.Vertical and role == Qt.DisplayRole:
        #    return f"{section + 1}"

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.fetch_data_str(index.row(), index.column())

    def rowCount(self, index):
        return len(self.dispositionsList)

    def columnCount(self, index):
        return self.DIS_COLUMN_COUNT
