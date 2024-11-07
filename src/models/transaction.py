import sys
import json
from datetime import datetime
from typing import List, Dict

from PySide6.QtCore import Qt, QAbstractTableModel

 # TODO: Change acq.initial_amount to just 'amount'. An acquisition is NOT a lot.

class Transaction():
    """Acquiring or disposing of some of a commodity

    ctor params:
    timestamp: float -- When the transaction occurrred
    asset_price: float --  The market unit price of the commodity at timestamp
    asset_amount: float -- The amount involved. Always positive.
    fees: float -- any fees or taxes or whatever
    comment: str -- as in 'Mike repaying me for lunch'
    """
    # Note that %Z DOES NOT WORK! A tz abbreviation is ignored by strptime
    # you MUST use a numeric offset (which is kinda ugly when displayed)

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z" # "12/27/2016 14:14:00 UTC"

    # DATETIME_FORMAT = "%m/%d/%Y %H:%M:%S %z" # "12/27/2016 14:14:00 +0000"

    def __init__(self, timestamp: float,  asset_amount: float, asset_price: float,
                  fees: float, comment: str = None) -> None:

        self.timestamp = timestamp # posix epoch
        self.asset_price = asset_price
        self.asset_amount = asset_amount
        self.fees = fees
        self.comment = comment
        #TODO: should there be a constant str ID as well? It would need
        # to be created solely from the init data.

