import sys
import json
from datetime import datetime,timezone
from typing import List, Dict

from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtWidgets import  QMessageBox

import dateparser

from models.transaction import Transaction, TxTableModel

class Acquisition(Transaction):
    """The receipt of a 'lot' of a commodity. Could be a purchase, a gift, or a payment

    ctor params:
    timestamp: float -- When the lot was acquired
    asset: str -- the type of asset acquired
    asset_amount: float -- The amount when the lot was acquired
    asset_price: float --  The unit cost of the commodity when acqired
    fees: float -- might be zero
    reference: str -- a transaction or order "id" if there is one
    comment: str -- as in 'Mike repaying me for lunch'
    """

    def __str__(self) -> str:
        return 'Acq'

    def __init__(self, timestamp: float, asset: str, asset_amount: float,
                 asset_price: float, fees: float, reference: str, comment: str,
                 disabled: bool = False) -> None:
        super().__init__( timestamp, asset, asset_amount, asset_price, fees, reference, comment, disabled)
        assert asset != None

    def duplicate(self) -> "Acquisition":
        return Acquisition(self.timestamp, self.asset, self.asset_amount, self.asset_price,
                   self.fees, self.reference, self.comment, self.disabled)

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
                "reference: "Tx ID 0xE234490D8"
                "comment": "Some comment"
            }
        """
        return cls(
                jd["timestamp"],
                jd["asset"],
                jd["asset_amount"],
                jd["asset_price"],
                jd["fees"],
                jd["reference"],
                jd["comment"],
                jd.get("disabled", False)
            )

    def to_json_dict(self) -> Dict:
        return  {
            "timestamp": self.timestamp,
            "asset": self.asset,
            "asset_amount": self.asset_amount,
            "asset_price": self.asset_price,
            "fees": self.fees,
            "reference": self.reference,
            "comment": self.comment,
            "disabled": self.disabled
        }



# QT View models

class AcqTableModel(TxTableModel):

    ACQ_TIMESTAMP_IDX = 0
    ACQ_ASSET_AMOUNT_IDX = 1
    ACQ_ASSET_PRICE_IDX = 2
    ACQ_VALUE_IDX = 3
    ACQ_REF_IDX = 4
    ACQ_COMMENT_IDX = 5
    ACQ_CANCEL_BTN_IDX = 6
    ACQ_ACCEPT_BTN_IDX = 7
    ACQ_COLUMN_COUNT = 8

    HEADER_LABELS = ["Date", "Amount", "Price", "Value", "Reference", "Comment", "", ""]

    def __init__(self, asset: str, acquisitions: List[Acquisition] = []) -> None:
         super(AcqTableModel, self).__init__(asset, acquisitions)

    def header_labels(self) -> List[str]:
        return AcqTableModel.HEADER_LABELS

    def button_columns(self) -> List[int]:
        """return a list of column indices that are buttons (cancel/accept)"""
        return [AcqTableModel.ACQ_CANCEL_BTN_IDX, AcqTableModel.ACQ_ACCEPT_BTN_IDX]

    def set_data(self, acq: Acquisition, col: int, str_val: str) -> bool:
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
            # col == AcqTableModel.ACQ_VALUE_IDX - "value" is a computed property
            if col == AcqTableModel.ACQ_REF_IDX:
                acq.reference = str_val
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
            return f"${acq.asset_price:.2f}"
        if col == AcqTableModel.ACQ_VALUE_IDX:
            return f"${acq.value:.2f}"
        if col == AcqTableModel.ACQ_REF_IDX:
            return acq.reference
        if col == AcqTableModel.ACQ_COMMENT_IDX:
            return acq.comment
        if col == AcqTableModel.ACQ_CANCEL_BTN_IDX:
            return None
        if col == AcqTableModel.ACQ_ACCEPT_BTN_IDX:
            return None
