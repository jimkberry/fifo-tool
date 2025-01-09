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
        self.all_entries: List[Form8949Entry] = []
        self.all_years: List[int] = []
        self.displayed_years: List[int] = []
        self.display_entries: List[Form8949Entry] = []
        self.reset_model(states)

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

    def _find_all_years(self, entries: List[Form8949Entry]) -> None:
        all_years: List[int] = []
        for entry in entries:
            if not entry.year_sold in all_years:
                all_years.append(entry.year_sold)
        return all_years

    def _filter_entries_by_year(self, entries: List[Form8949Entry],  years: List[int]) -> None:
        self.displayed_years = years
        return entries if not years else [e for e in entries if e.year_sold in years]

    def reset_model(self, states: List[StashState]) -> None:
        self.beginResetModel()
        self.all_entries = self._generate_entries(states)
        self.all_years = self._find_all_years(self.all_entries)
        self.display_entries = self._filter_entries_by_year(self.all_entries, [])
        self.endResetModel()

    def filter_model_by_year(self, years: List[int]) -> None:
        self.beginResetModel()
        self.display_entries = self._filter_entries_by_year(self.all_entries, years)
        self.endResetModel()

    def rowCount(self, index) -> int:
        return len(self.display_entries)

    def columnCount(self, index) -> int:
        return len(self.HEADER_LABELS)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            entry = self.display_entries[index.row()]
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
