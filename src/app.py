import sys
import json
from datetime import datetime, timezone
from typing import List, Dict

from PySide6.QtWidgets import ( QApplication, QMainWindow, QPushButton,QLineEdit,
    QWidget, QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QTableView,
    QMessageBox, QTabWidget, QLabel, QFileDialog, QAbstractItemView, QStyle,
    QAbstractItemDelegate, QStyledItemDelegate, QComboBox)
from PySide6.QtGui import QAction, QPainter, QColor, Qt
from PySide6.QtCore import QRect, Signal, Slot

from models.transaction import Transaction, TxTableModel
from models.acquisition import Acquisition, AcqTableModel
from models.disposition import Disposition, DisTableModel
from models.stash import Stash, StatesTableModel, StashState
from models.form8949 import Form8949TableModel

class BorderHighlightItemDelegate(QStyledItemDelegate):
    def __init__(self) -> None:
        super().__init__()

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.model().is_disabled(index.row()): # do disable first so selection rect is on top
            rect = QRect(option.rect)
            rect.adjust(0,0,-1,-1)
            painter.fillRect(rect,QColor(0, 0, 0, 128))
        if index.row() == index.model().row_under_edit:
            painter.setPen(QColor(255, 255, 128, 128))
            rect = QRect(option.rect)
            rect.adjust(0,0,-1,-1)
            painter.drawRect(rect)

class TxPage(QWidget):

    model_changed_sig = Signal(object) # param is new transactionList

    # virtuals for subclass

    def table_model(self) -> TxTableModel:
        """Table Model Class"""
        raise NotImplementedError

    def new_transaction(self) -> Transaction:
        """Create new Acq/Disp instance"""
        raise NotImplementedError

    # end virtuals

    def __init__(self, asset: str,  transactions: List[Transaction]) -> None:
        super().__init__()
        self.table = QTableView()
        self.model = self.table_model()(asset, transactions)
        self.table.setModel(self.model)
        self.table.showGrid()
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setItemDelegate(BorderHighlightItemDelegate())
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_row)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_row)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_row)
        imp_btn = QPushButton("Toggle Disabled")
        imp_btn.clicked.connect(self.toggle_transaction)

        # layout
        btnsLayout = QHBoxLayout()
        btnsLayout.addWidget(add_btn)
        btnsLayout.addWidget(edit_btn)
        btnsLayout.addWidget(del_btn)
        btnsLayout.addWidget(imp_btn)

        pageLayout = QVBoxLayout()
        pageLayout.addWidget(self.table)
        pageLayout.addLayout(btnsLayout)

        self.setLayout(pageLayout)

    def reset_data(self, asset: str, data: List[Transaction]) -> None:
        self.model.reset_model(asset, data)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.viewport().update()

    def edit_row(self) -> None:
        sel_model = self.table.selectionModel()
        idx_list =  sel_model.selectedRows()
        if not idx_list:
            button = QMessageBox.warning(self,"Edit","No row selected" )
            return

        prev_edit_row = self.model.row_under_edit
        if prev_edit_row != -1:
            # cancel the current edit
            self.cancel_edit()
            if prev_edit_row == idx_list[0].row():
                return # edit was pressed only to cancel the current edit

        self.model.edit_row(idx_list[0].row())

        # TODO: this btn/widget stuff oughta be a func
        cancel_edit_btn = QPushButton(
            icon = self.style().standardIcon(QStyle.SP_DialogCancelButton),
            parent=self)
        cancel_edit_btn.clicked.connect(self.cancel_edit)
        accept_edit_btn = QPushButton(
            icon = self.style().standardIcon(QStyle.SP_DialogOkButton),
            parent=self)
        accept_edit_btn.clicked.connect(self.accept_edit)
        self.table.setIndexWidget(
            self.model.index(idx_list[0].row(), self.model.button_columns()[0]), # TODO: add [cancel|accept]_btn_col() to model
            cancel_edit_btn)
        self.table.setIndexWidget(
            self.model.index(idx_list[0].row(), self.model.button_columns()[1]),
            accept_edit_btn)
        self.table.viewport().update()

    def cancel_edit(self) -> None:
        edit_row = self.model.row_under_edit
        if edit_row != -1:
            self.model.cancel_edit()
            self.disable_edit_gui(edit_row)

    def accept_edit(self) -> None:
        edit_row = self.model.row_under_edit
        if edit_row != -1:
            self.model.accept_edit()
            # TODO: figure this one out
            self.model_changed_sig.emit(self.model.transactionsList)  # main window catches this, rebuilds stash, and updates views
            self.disable_edit_gui(edit_row)

    def disable_edit_gui(self, edit_row: int) -> None:
        ''' just removes the buttons and updates the view '''
        self.table.setIndexWidget(
            self.model.index(edit_row, self.model.button_columns()[0]), None)
        self.table.setIndexWidget(
            self.model.index(edit_row,self.model.button_columns()[1]), None)
        self.table.viewport().update()

    def add_row(self) -> None:
        new_acq = self.new_transaction() # Acquisition(datetime.timestamp(datetime.now(timezone.utc)), self.model.asset, 0, 0, 0, "", "New Acquisition")
        self.model.transactionsList.append(new_acq) # TODO: fix fugliness
        self.model_changed_sig.emit(self.model.transactionsList) # main window catches this, rebuilds stash, and updates views

    def delete_row(self) -> None:
        sel_model = self.table.selectionModel()
        idx_list =  sel_model.selectedRows()
        if not idx_list:
            button = QMessageBox.warning(self,"Delete Row","No row selected" )
            return
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Confirm Delete ")
            dlg.setText("Delete the selected transaction?")
            dlg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes )
            dlg.setIcon(QMessageBox.Question)
            button = dlg.exec()
            if button == QMessageBox.Yes:
                del_row = idx_list[0].row()
                del self.model.transactionsList[del_row]
                self.model_changed_sig.emit(self.model.transactionsList)

    def toggle_transaction(self):
        sel_model = self.table.selectionModel()
        idx_list =  sel_model.selectedRows()
        if not idx_list:
            QMessageBox.warning(self,"Toggle Enable/Disabled","No transaction selected" )
            return
        del_row = idx_list[0].row()
        self.model.toggle_disabled(del_row)
        self.model_changed_sig.emit(self.model.transactionsList)


class AcquisitionsPage(TxPage):

    def __init__(self, asset: str,  acquisitions: List[Acquisition]) -> None:
        super().__init__(asset, acquisitions)

    def stash_tx_list(self) -> List[Transaction]:
        """Data list in the stash"""
        return self.stash.acquisitions

    def table_model(self) -> TxTableModel:
        """Table Model Class"""
        return AcqTableModel

    def new_transaction(self) -> Transaction:
        """Create new Acq/Disp instance"""
        return Acquisition(datetime.timestamp(datetime.now(timezone.utc)), self.model.asset, 0, 0, 0, "", "New Acquisition")


class DispositionsPage(TxPage):

    def __init__(self, asset: str,  dispositions: List[Disposition]) -> None:
        super().__init__(asset, dispositions)

    def stash_tx_list(self) -> List[Transaction]:
        """Data list in the stash"""
        return self.stash.dispositions

    def table_model(self) -> TxTableModel:
        """Table Model Class"""
        return DisTableModel

    def new_transaction(self) -> Transaction:
        """Create new Disp instance"""
        return Disposition(datetime.timestamp(datetime.now(timezone.utc)), self.model.asset, 0, 0, 0, "", "New Disposition")


class TransactionStatesPage(QWidget):
    def __init__(self, states: List[StashState]) -> None:
        super().__init__()

        self.table = QTableView()
        self.model = StatesTableModel(states)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        lotsBtn = QPushButton("Show Lots")

        # layout
        btnsLayout = QHBoxLayout()
        btnsLayout.addWidget(lotsBtn)

        pageLayout = QVBoxLayout()
        pageLayout.addWidget(self.table)
        pageLayout.addLayout(btnsLayout)

        self.setLayout(pageLayout)

    def reset_data(self, asset: str, data: List[Transaction]) -> None:
        self.model.reset_model(asset,data)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.viewport().update()


class Form8949Page(QWidget):
    def __init__(self, states: List[StashState]) -> None:
        super().__init__()

        self.states = states
        self.years_combo = QComboBox()
        self.years_combo.setEditable(True)
        self.years_combo.lineEdit().setPlaceholderText("Enter year(s) separated by commas")
        self.years_combo.currentTextChanged.connect(self.on_years_changed)

        self.table = QTableView()
        self.model = Form8949TableModel(states)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
          # layout
        layout = QVBoxLayout()
        layout.addWidget(self.years_combo)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def on_years_changed(self):
        years_text = self.years_combo.currentText()
        if years_text:
            years = [int(year.strip()) for year in years_text.split(",") if year.strip().isdigit()]
        else:
            years = []
        self.model.set_year_filter(years)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.viewport().update()

    def reset_data(self, data: List[Transaction]) -> None:
        self.model.reset_model(data)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.viewport().update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        #self.stash = self.load_stash('new_stash.json')
        self.stash = Stash('BTC','Default Stash')

        self.resize(1024, 768)
        self.setWindowTitle(f'{self.stash.asset}: {self.stash.title}')
        menu = self.menuBar()

        new_stash_action = QAction("&New Stash", self)
        new_stash_action.triggered.connect(self.new_stash)

        open_stash_action = QAction("&Open Stash", self)
        open_stash_action.triggered.connect(self.open_stash)

        save_stash_action = QAction("&Save Stash", self)
        save_stash_action.triggered.connect(self.save_stash)

        import_stash_action = QAction("&Import Data", self)
        import_stash_action.triggered.connect(self.import_stash)

        file_menu = menu.addMenu("&File")
        file_menu.addAction(new_stash_action)
        file_menu.addAction(open_stash_action)
        file_menu.addAction(save_stash_action)
        file_menu.addAction(import_stash_action)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.acqPage = AcquisitionsPage(self.stash.asset, self.stash.acquisitions)
        self.acqPage.model_changed_sig[object].connect(self.on_acq_model_changed)
        tabs.addTab(self.acqPage, "Acquisitions")

        self.dispPage = DispositionsPage(self.stash.asset, self.stash.dispositions)
        self.dispPage.model_changed_sig[object].connect(self.on_disp_model_changed)
        tabs.addTab(self.dispPage, "Dispositions")

        self.txPage = TransactionStatesPage(self.stash.states)
        tabs.addTab(self.txPage, "TX States")

        self.form8949Page = Form8949Page(self.stash.states)
        tabs.addTab(self.form8949Page, "Form 8949")

    @Slot(object, object)
    def on_acq_model_changed(self, new_acqs: List[Acquisition]) -> None:
        self.on_model_changed(new_acqs, None)

    @Slot(object, object)
    def on_disp_model_changed(self, new_disps:List[Disposition]) -> None:
        self.on_model_changed(None, new_disps)

    def on_model_changed(self, new_acqs: List[Acquisition], new_disps:List[Disposition]) -> None:

        if new_acqs != None:
            self.stash.acquisitions = new_acqs
        if new_disps!= None:
            self.stash.dispositions = new_disps

        self.stash.update()  # sorts transactions and builds states
        self.acqPage.reset_data(self.stash.asset, self.stash.acquisitions)
        self.dispPage.reset_data(self.stash.asset, self.stash.dispositions)
        self.txPage.reset_data(self.stash.asset, self.stash.states)
        self.form8949Page.reset_data(self.stash.states)
        self.centralWidget().update()

    def new_stash(self):

        class NewDlg(QDialog):
            def __init__(self):
                super().__init__()

                self.setWindowTitle("New Stash!")
                self.asset_edit = QLineEdit("Asset Name")
                self.title_edit = QLineEdit("Stash Title")

                QBtn = (
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )

                self.buttonBox = QDialogButtonBox(QBtn)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                layout = QVBoxLayout()
                layout.addWidget(self.asset_edit)
                layout.addWidget(self.title_edit)
                layout.addWidget(self.buttonBox)
                self.setLayout(layout)

        dlg = NewDlg()
        if dlg.exec():
            self.stash = Stash( dlg.asset_edit.text(), dlg.title_edit.text() )
            self.setWindowTitle(f'{self.stash.asset}: {self.stash.title}')
            self.on_model_changed(None, None) # uses self.whatever if none

    def open_stash(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open file:"
        )
        stash = self.load_stash(filename)
        if stash:
            self.stash = stash
            self.setWindowTitle(f'{self.stash.asset}: {self.stash.title}')
            self.on_model_changed(None, None)

    def load_stash(self, filename: str) -> Stash:
        stash = {}

        try:
            with open(filename, 'r') as f:
                jsonData = json.load(f) # a List of Dicts
            stash = Stash.from_json_dict(jsonData)
            stash.update()  # sorts transactions and builds states
        except Exception as ex:
             QMessageBox.critical(self, "Oops", str(ex))
        return stash

    def import_stash(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select a file to import"
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    jsonData = json.load(f) # a stash
                    new_data = Stash.from_json_dict(jsonData)
                    if new_data.asset!= self.stash.asset:
                        raise ValueError(f"Asset mismatch: found {new_data.asset}. Should be {self.stash.asset}")
            except Exception as ex:
                # TODO: handle this with a popup thingy
                QMessageBox.critical(self, "Oops", str(ex))
                return

            self.stash.acquisitions += new_data.acquisitions
            self.stash.dispositions += new_data.dispositions
            self.stash.update()
            self.on_model_changed(self.stash.acquisitions, self.stash.dispositions)

    def save_stash(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save as:"
        )
        if filename:
            res = []  # This would be your JSON data.
            try:
                with open(filename, 'w') as f:
                    jd = self.stash.to_json_dict()
                    data = json.dump(jd, f, indent=2)
            except Exception as ex:
                QMessageBox.critical(self, "Oops", str(ex))


app = QApplication(sys.argv)
# print(app.style().objectName())
# app.setStyle('Windows')

window = MainWindow()
window.show()

app.exec()