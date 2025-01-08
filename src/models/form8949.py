import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QAbstractTableModel
from models.stash import StashState
from models.disposition import Disposition

class Form8949Entry:
    """Represents a single entry in IRS Form 8949"""
    def __init__(self, description: str, date_acquired: float, date_sold: float, proceeds: float, cost_basis: float, adjustment: float, code: str):
        self.description = description
        self.date_acquired = date_acquired
        self.date_sold = date_sold # timestamp
        self.proceeds = proceeds
        self.cost_basis = cost_basis
        self.adjustment = adjustment
        self.code = code
        # not on for 8949
        self.year_sold = datetime.fromtimestamp(date_sold, tz=timezone.utc).year

    @property
    def gain_or_loss(self) -> float:
        return self.proceeds - self.cost_basis + self.adjustment

class Form8949TableModel(QAbstractTableModel):
    """Model for a table containing entries for IRS Form 8949"""

    HEADER_LABELS = ["Description", "Date Sold", "Date Acquired", "Proceeds", "Cost Basis", "Adjustment", "Code", "Gain or Loss"]

    # Define named constants for column indices
    DESCRIPTION_COLUMN = 0
    DATE_SOLD_COLUMN = 1
    DATE_ACQUIRED_COLUMN = 2
    PROCEEDS_COLUMN = 3
    COST_BASIS_COLUMN = 4
    ADJUSTMENT_COLUMN = 5
    CODE_COLUMN = 6
    GAIN_OR_LOSS_COLUMN = 7

    def __init__(self, states: List[StashState]) -> None:
        super(Form8949TableModel, self).__init__()
        self.reset_model(states)

    @property
    def display_years(self) -> List[int]:
        return self._display_years

    @property
    def all_years(self) -> List[int]:
        return self._all_years

    def _generate_entries(self, states: List[StashState]) -> List[Form8949Entry]:
        entries = []
        for state in states:
            if isinstance(state.activity, Disposition):
                entry = Form8949Entry(
                    description=state.activity.asset,
                    date_acquired=state.current_lot().initial_timestamp,
                    date_sold=state.timestamp,
                    proceeds=state.value,
                    cost_basis=state.current_lot().basis_price * state.activity.asset_amount,
                    adjustment=0.0,  # Assuming no adjustments for simplicity
                    code=""  # Assuming no code for simplicity
                )
                entries.append(entry)
        return entries

    def _find_all_years(self) -> None:
        all_years: List[int] = []
        for entry in self.entries_list:
            if not entry.year_sold in all_years:
                all_years.append(entry.year_sold)
        return all_years

    def reset_model(self, states: List[StashState]) -> None:
        self.beginResetModel()
        self.entries_list = self._generate_entries(states)
        self._all_years = self._find_all_years()
        self.set_year_filter([])
        self.endResetModel()

    def set_year_filter(self, years: List[int]) -> None:
        self._display_years = years

    def rowCount(self, index) -> int:
        return len(self.entries_list) if not self._display_years else len([e for e in self.entries_list if e.year_sold in self._display_years])

    def columnCount(self, index) -> int:
        return len(self.HEADER_LABELS)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            entry = self.entries_list[index.row()]
            if entry.year_sold in self._display_years or not self._display_years:
                if index.column() == self.DESCRIPTION_COLUMN:
                    return entry.description
                if index.column() == self.DATE_SOLD_COLUMN:
                    return datetime.fromtimestamp(entry.date_sold, tz=timezone.utc).strftime("%Y-%m-%d")
                if index.column() == self.DATE_ACQUIRED_COLUMN:
                    return datetime.fromtimestamp(entry.date_acquired, tz=timezone.utc).strftime("%Y-%m-%d")
                if index.column() == self.PROCEEDS_COLUMN:
                    return f"${entry.proceeds:.2f}"
                if index.column() == self.COST_BASIS_COLUMN:
                    return f"${entry.cost_basis:.2f}"
                if index.column() == self.ADJUSTMENT_COLUMN:
                    return f"${entry.adjustment:.2f}"
                if index.column() == self.CODE_COLUMN:
                    return entry.code
                if index.column() == self.GAIN_OR_LOSS_COLUMN:
                    return f"${entry.gain_or_loss:.2f}"

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADER_LABELS[section]
