import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QAbstractTableModel
from models.stash import StashState
from models.disposition import Disposition

class Form8949Entry:
    """Represents a single entry in IRS Form 8949"""
    def __init__(self, description: str, date_acquired: float, date_sold: float, proceeds: float, cost_basis: float, adjustment: float, code: str, is_long_term: bool):
        self.description:str = description
        self.date_acquired: float = date_acquired
        self.date_sold: float = date_sold  # timestamp
        self.proceeds: float = proceeds
        self.cost_basis: float = cost_basis
        self.adjustment: float = adjustment
        self.code: str = code
        # not on for 8949
        self.year_sold: int = datetime.fromtimestamp(date_sold, tz=timezone.utc).year
        self.is_long_term: bool = is_long_term  # Add this line

    @property
    def gain_or_loss(self) -> float:
        return self.proceeds - self.cost_basis + self.adjustment

class Form8949TableModel(QAbstractTableModel):
    """Model for a table containing entries for IRS Form 8949"""

    HEADER_LABELS = ["Description", "Date Sold", "Date Acquired", "Net Proceeds", "Cost Basis", "Adjustment", "Code", "Term", "Gain or Loss"]

    # Define named constants for column indices
    DESCRIPTION_COLUMN = 0
    DATE_SOLD_COLUMN = 1
    DATE_ACQUIRED_COLUMN = 2
    PROCEEDS_COLUMN = 3
    COST_BASIS_COLUMN = 4
    ADJUSTMENT_COLUMN = 5
    CODE_COLUMN = 6
    TERM_COLUMN = 7  # New TERM_COLUMN
    GAIN_OR_LOSS_COLUMN = 8

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
                for lot in state.lots_affected:
                    entry = Form8949Entry(
                        description=f"{-lot.update_amount_delta:.8f} {state.activity.asset}",
                        date_acquired=lot.initial_timestamp,
                        date_sold=state.timestamp,
                        proceeds=lot.sale_proceeds,
                        cost_basis=lot.sale_basis,
                        adjustment=0.0,  # Assuming no adjustments for simplicity
                        code="",  # Assuming no code for simplicityy
                        is_long_term=lot.is_long_term  # Add this line to pass the is_long_term parameter
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
            if index.column() == self.TERM_COLUMN:
                return "L" if entry.is_long_term else "S"  # Display "L" if is_long_term is True, else "S"
            if index.column() == self.GAIN_OR_LOSS_COLUMN:
                return f"${entry.gain_or_loss:.2f}"

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADER_LABELS[section]

    def displayed_adjustments_sum(self, is_long_term: bool) -> float:
        """Sum of adjustments for long-term or short-term transactions"""
        return sum(
            tx.adjustment for tx in self.display_entries
            if tx.is_long_term == is_long_term
        )

    def displayed_proceeds_sum(self, is_long_term: bool) -> float:
        """Sum of proceeds for long term or short-term transactions"""
        return sum(
            tx.proceeds for tx in self.display_entries
            if tx.is_long_term == is_long_term
        )


    def displayed_cost_basis_sum(self, is_long_term: bool) -> float:
        """Sum of cost basis for long-term or short-term transactions"""
        return sum(
            tx.cost_basis for tx in self.display_entries
            if tx.is_long_term == is_long_term
        )

    def displayed_gain_sum(self, is_long_term: bool) -> float:
        """Sum of total gains for long-term or short-term transactions"""
        return sum(
            tx.gain_or_loss for tx in self.display_entries
            if tx.is_long_term == is_long_term
        )
