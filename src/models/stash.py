import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QAbstractTableModel

from models.acquisition import Acquisition
from models.disposition import Disposition

class LotState:
    """State of stuff acquired at the same timne
    """

    ONE_YEAR_SECS = 24 * 60 * 60 * 365.0

    def __init__(self, lot_num: int):
        # constant across activities
        self.lot_num: int = lot_num
        self.initial_timestamp: float = 0
        self.initial_balance: float = 0
        self.basis_price: float = 0
        # "update" means last activity that modified the lot
        self.update_timestamp: float = 0
        self.update_amount_delta: float = 0
        self.update_asset_price: float = 0
        self.update_fees: float = 0
        self.balance: float = 0

    # computed stuff
    @property
    def sale_basis(self) -> float: # IRS 8949 basis total. Not basis price. Should include acqusition fees? Nah.
        return self.basis_price * (-self.update_amount_delta) # delta is < 0 for a disp

    @property
    def sale_proceeds(self) -> float: #net sale proceeds
        return self.update_asset_price * (-self.update_amount_delta) - self.update_fees

    @property
    def cap_gains(self) -> float:
        return self.sale_proceeds - self.sale_basis

    @property
    def is_long_term(self) -> bool:
        return (self.update_timestamp - self.initial_timestamp) > LotState.ONE_YEAR_SECS

    @classmethod
    def copy(cls, src: "LotState") -> "LotState":
        """ Makes an exact copy, INCLUDING -previous-activity-specific data.

            returns copy.
        """
        dst = cls(src.lot_num)
        # constants
        dst.initial_timestamp = src.initial_timestamp
        dst.initial_balance = src.initial_balance
        dst.basis_price = src.basis_price
        # carry this forward
        dst.balance = src.balance

        #leave all update* attributes zero
        return dst

    def acquire(self, timestamp: float, initital_balance: float, basis_price: float, fees: float):
        # constant for all state of this lot
        self.initial_timestamp: float = timestamp
        self.initial_balance: float = initital_balance
        self.basis_price: float = basis_price
        # values from the most recent update
        self.update_timestamp: float = timestamp
        self.update_amount_delta = initital_balance
        self.update_asset_price = basis_price
        self.update_fees = fees
        # current state value
        self.balance: float = initital_balance


    def dispose(self, timestamp: float, amount: float, price: float, fees: float ) -> float:
        ''' subtract amount from lot balance and update vars

            returns overdraw amount > 0 if amount > lot balance

        '''
        assert amount >= 0, f"LotState.dispose() - Amount must be positive, got {amount}"
        self.update_timestamp = timestamp
        self.update_asset_price = price
        self.update_fees = fees

        overdraw: float = amount - self.balance
        if overdraw > 0:
            self.update_amount_delta = -self.balance
            self.balance = 0 # TODO: maybe set this to -overdraw and track negative balances?
            return overdraw
        else:
            self.update_amount_delta = -amount
            self.balance -= amount
            return 0

    def to_json_dict(self) -> Dict:
        return {
            "initial_timestamp": self.initial_timestamp,
            "initial_balance": self.initial_balance,
            "basis_price": self.basis_price,
            "update_timestamp": self.update_timestamp,
            "update_amount_delta": self.update_amount_delta,
            "update_asset_price": self.update_asset_price,
            "update_fees": self.update_fees,
            "balance": self.balance
        }


class StashState:
    """State of the stash after an activity is applied

       An acquisition will add a new lots entry, but lots will never go away -
       they just have their balance reduced until it's zero.

    """
    def __init__(self):
        self.activity: Acquisition | Disposition = None
        self.lots : list[LotState] = []

    @classmethod
    def copy(cls, src: "StashState") -> "StashState":
        dst = StashState()
        dst.activity = src.activity
        dst.lots = [LotState.copy(l) for l in src.lots]
        return dst

    @property
    def tx_type(self) -> Acquisition|Disposition:
        return type(self.activity)

    # TX/Acq properties
    @property
    def timestamp(self) -> float:
        return self.activity.timestamp

    @property
    def asset_price(self) -> float:
        return self.activity.asset_price

    @property
    def asset_amount(self) -> float:
        return self.activity.asset_amount

    @property
    def value(self) -> float:
        return self.activity.asset_value

    @property
    def fees(self) -> float:
        return self.activity.fees

    @property
    def comment(self) -> str:
        return self.activity.comment

    # Disp properties
    @property
    def reference(self) -> str:
        return self.activity.reference if hasattr(self.activity, "reference") else ""

    # computed state stuff
    @property
    def balance(self) -> float:
        return sum(l.balance for l in self.lots)

    @property
    def lots_affected(self) -> List[LotState]:
        return [l for l in self.lots if l.update_amount_delta != 0]


    @property
    def cap_gains(self) -> Dict[str, float]:
        """ returns a Dict potentially containing:
            {"L": sum_of_long_term_cap_gains (only if there are any),
            "S": sum_of_short_term_cap_gains (only if there are any)}
            or None if there are no cap gains at all
        """
        long_term_gains = [l.cap_gains for l in self.lots_affected if l.is_long_term]
        short_term_gains = [l.cap_gains for l in self.lots_affected if not l.is_long_term]
        gains_dict: Dict[str, float] = {}
        if long_term_gains:
            gains_dict["L"] = sum(long_term_gains)
        if short_term_gains:
            gains_dict["S"] = sum(short_term_gains)
        return gains_dict if gains_dict else None

    # TODO: property? method? Make up your (my) mind on these

    def current_lot(self) -> LotState:
        return next((l for l in self.lots if l.balance > 0), None)

    def current_lot_idx(self) -> int:
        return next((idx for idx,l in enumerate(self.lots) if l.balance > 0), -1)

    def to_json_dict(self) -> Dict:
        return  {
            "activity": self.activity.to_json_dict() if self.activity else None,
            "lots": [lot.to_json_dict() for lot in self.lots],
            "balance": self.balance
        }

    def apply_activity(self, activity_idx: int, activity: Acquisition | Disposition) -> "StashState":
        """state machine applies an activity to a state and returns a new state"""
        new_state = StashState.copy(self)
        new_state.activity = activity

        if isinstance(activity, Acquisition):
            new_lot = LotState(len(self.lots))  # this is where lots get their sequence numbers
            new_lot.acquire(activity.timestamp, activity.asset_amount, activity.asset_price, activity.fees)
            new_state.lots.append(new_lot)

        elif isinstance(activity, Disposition):
            amount_left = activity.asset_amount
            while new_state.current_lot() and amount_left > 0:
                amount_left = new_state.current_lot().dispose(activity.timestamp, amount_left, activity.asset_price, activity.fees)
            # should be an assert?
            if amount_left != 0:
                print(f"Error! Activity #{activity_idx} Disposition {activity.timestamp} overdrawn {amount_left}")
        return new_state


class Stash:
    """The container object for an asset/commodity

    """
    def __init__(self, asset: str = "", title: str = "",
                 acqs: List[Acquisition] = [],
                 disps: List[Disposition] = []) -> None:
        self.asset = asset
        self.title = title
        self.acquisitions: List[Acquisition] = acqs
        self.dispositions: List[Disposition] = disps
        self.states: List[StashState] = []

    def update(self) -> None:
        """Rebuild after load or edit of transactions

            Re-sorts transaction types lists and rebuilds states
        """
        self.acquisitions = sorted( self.acquisitions,  key=lambda a: a.timestamp)
        self.dispositions = sorted( self.dispositions,  key=lambda d: d.timestamp)
        self.generate_states()

    def generate_states(self):
        activities: List[Any] =  [act for act in (self.acquisitions + self.dispositions) if not act.disabled]
        sortedActivities: List[Any] =  sorted(activities,  key=lambda a: a.timestamp)

        state: StashState = StashState()
        # this state, before anything at all has happened, does not go into the states list
        self.states = []
        for idx, act in enumerate(sortedActivities):
            state = state.apply_activity(idx, act)
            self.states.append(state)
        pass

    @classmethod
    def from_json_dict(cls, jd: Dict) -> "Stash":
        """A json-serialized Acquisition is a dict when loaded.

        Looks like this:

            {
                "asset": "BTC",
                "title: "My Bitcoin Stash",
                "acquisitions": [Acq1, Acq2...],
                "dispositions": [Disp1, Disp2...]
            }

        This should be called inside a try block
        """
        stash = Stash(jd["asset"], jd["title"])
        # Sort and filter out any wrong-commodity stuff
        stash.acquisitions = sorted( [Acquisition.from_json_dict(acq) for acq in jd["acquisitions"] ],  key=lambda a: a.timestamp)
        stash.dispositions = sorted( [Disposition.from_json_dict(dis) for dis in jd["dispositions"]], key=lambda d: d.timestamp)
        return stash

    def to_json_dict(self) -> Dict:
        """Serialize to a json dict
        """
        return {
            "asset": self.asset,
            "title": self.title,
            "acquisitions": [acq.to_json_dict() for acq in self.acquisitions],
            "dispositions": [dis.to_json_dict() for dis in self.dispositions]
        }

# QT View models

class StatesTableModel(QAbstractTableModel):
    """
    Model for a table containing all of the post-activity states for the stash
    """

    TIMESTAMP_IDX = 0 # tx/acq
    TX_TYPE_IDX = 1 # tx/acq
    ASSET_AMOUNT_IDX = 2 # tx/acq
    ASSET_PRICE_IDX = 3 # tx/acq
    VALUE_IDX = 4 # tx/acq
    FEES_IDX = 5 # tx/acq
    BALANCE_IDX = 6 # state
    LOTS_AFFECTED_IDX = 7 # state
    CAP_GAINS_IDX = 8 # state
    REFERENCE_IDX = 9 # disp
    COMMENT_IDX = 10 # tx/acq
    COLUMN_COUNT = 11

    HEADER_LABELS = ["Date", "Type", "Amount", "Price", "Value", "Fees", "Balance", "Lots Affected", "Cap Gains", "Reference", "Comment"]

    def __init__(self, stashStates: List[StashState] = []) -> None:
        super(StatesTableModel, self).__init__()
        self.states_list = stashStates

    def reset_model(self, asset: str, stashStates: List[StashState]) -> None:
        self.beginResetModel()
        self.states_list = stashStates if stashStates else []
        self.endResetModel()


    def fetch_data_str(self, row: int, col: int) -> str:
        state = self.states_list[row]
        if col == StatesTableModel.TIMESTAMP_IDX:
            return datetime.fromtimestamp(state.timestamp,tz=timezone.utc).strftime(Acquisition.DATETIME_FORMAT)
        if col == StatesTableModel.TX_TYPE_IDX:
            return str(state.activity)
        if col == StatesTableModel.ASSET_AMOUNT_IDX:
            return f"{state.asset_amount:.8f}"
        if col == StatesTableModel.ASSET_PRICE_IDX:
            return f"${state.asset_price:.2f}"
        if col == StatesTableModel.VALUE_IDX:
            return f"${state.value:.2f}"
        if col == StatesTableModel.FEES_IDX:
            return f"{state.fees:.2f}"
        if col == StatesTableModel.BALANCE_IDX:
            return f"{state.balance:.8f}"
        if col == StatesTableModel.LOTS_AFFECTED_IDX:
            strs = [f"{l.lot_num}: {l.update_amount_delta:+.8f}" for l in state.lots_affected]
            return "\n".join(strs)
        if col == StatesTableModel.CAP_GAINS_IDX:
            if isinstance(state.activity, Disposition):
                gains = state.cap_gains
                if gains:
                    strs = [f"{cg[0]}: ${cg[1]:.2f}" for cg in gains.items()]
                    return "\n".join(strs)
            return ""

        if col == StatesTableModel.REFERENCE_IDX:
            return state.reference
        if col == StatesTableModel.COMMENT_IDX:
            return state.comment


    # overrides
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return StatesTableModel.HEADER_LABELS[section]
        #if orientation == Qt.Vertical and role == Qt.DisplayRole:
        #    return f"{section + 1}"

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.fetch_data_str(index.row(), index.column())

    def rowCount(self, index):
        return len(self.states_list)

    def columnCount(self, index):
        return self.COLUMN_COUNT

