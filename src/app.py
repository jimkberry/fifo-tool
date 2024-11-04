import sys
import json
from datetime import datetime, timezone
from typing import List, Dict

from PySide6.QtWidgets import ( QApplication, QMainWindow, QPushButton,QLineEdit,
    QWidget, QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QTableView,
    QMessageBox, QTabWidget, QLabel, QFileDialog, QAbstractItemView, QStyle,
    QAbstractItemDelegate, QStyledItemDelegate)
from PySide6.QtGui import QAction, QPainter, QColor, Qt
from PySide6.QtCore import QRect, Signal, Slot

from models.acquisition import Acquisition, AcqTableModel
from models.disposition import Disposition, DisTableModel
from models.stash import Stash, StatesTableModel, StashState

class BorderHighlightItemDelegate(QStyledItemDelegate):
    def __init__(self) -> None:
        super().__init__()

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.row() == index.model().row_under_edit:
            painter.setPen(QColor(255, 255, 128, 128))
            rect = QRect(option.rect)
            rect.adjust(0,0,-1,-1)
            painter.drawRect(rect)


class AcquisitionsPage(QWidget):

    model_changed_sig = Signal(object, object) # params are: acquisitions, dispositions

    def __init__(self, acquisitions: List[Acquisition]) -> None:
        super().__init__()

        self.table = QTableView()
        self.model = AcqTableModel(acquisitions)
        self.table.setModel(self.model)
        self.table.showGrid()
        self.table.setGridStyle(Qt.SolidLine)
        self.table.resizeColumnsToContents()
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setItemDelegate(BorderHighlightItemDelegate())

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_acquisition)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_acquisition)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_acquisition)
        imp_btn = QPushButton("Import")
        imp_btn.clicked.connect(self.import_file)

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

    def reset_data(self, acquisitions: List[Acquisition]) -> None:
        self.model.reset_model(acquisitions)
        self.table.viewport().update()

    def edit_acquisition(self) -> None:
        sel_model = self.table.selectionModel()
        idx_list =  sel_model.selectedRows()
        if not idx_list:
            button = QMessageBox.warning(self,"Edit","No Acquisition row selected" )
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
            self.model.index(idx_list[0].row(), AcqTableModel.ACQ_CANCEL_BTN_IDX),
            cancel_edit_btn)
        self.table.setIndexWidget(
            self.model.index(idx_list[0].row(), AcqTableModel.ACQ_ACCEPT_BTN_IDX),
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
            self.model_changed_sig.emit(self.model.acquisitionsList, None)  # main window catches this, rebuilds stash, and updates views
            self.disable_edit_gui(edit_row)

    def disable_edit_gui(self, edit_row: int) -> None:
        ''' just removes the buttons and updates the view '''
        self.table.setIndexWidget(
            self.model.index(edit_row, AcqTableModel.ACQ_CANCEL_BTN_IDX), None)
        self.table.setIndexWidget(
            self.model.index(edit_row,AcqTableModel.ACQ_ACCEPT_BTN_IDX), None)
        self.table.viewport().update()

    def add_acquisition(self) -> None:
        new_acq = Acquisition(datetime.timestamp(datetime.now(timezone.utc)), 0, 0, 0, "New Acquisition")
        self.model.acquisitionsList.append(new_acq) # TODO: fix fugliness
        self.model_changed_sig.emit(self.model.acquisitionsList, None) # main window catches this, rebuilds stash, and updates views

    def delete_acquisition(self) -> None:
        sel_model = self.table.selectionModel()
        idx_list =  sel_model.selectedRows()
        if not idx_list:
            button = QMessageBox.warning(self,"Delete Acquisition","No Acquisition row selected" )
            return
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Confirm Delete ")
            dlg.setText("Delete the selected Acquisition?")
            dlg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes )
            dlg.setIcon(QMessageBox.Question)
            button = dlg.exec()
            if button == QMessageBox.Yes:
                del_row = idx_list[0].row()
                del self.model.acquisitionsList[del_row]
                self.model_changed_sig.emit(self.model.acquisitionsList,None )

    def import_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select a File"
        )
        if filename:
            res = []  # This would be your JSON data.
            try:
                with open(filename, 'r') as f:
                    jsonData = json.load(f) # a List of Dicts
                res = sorted( [Acquisition.from_json_dict(acq) for acq in jsonData],  key=lambda acq: acq.timestamp)
            except Exception as ex:
                # TODO: handle this with a popup thingy
                QMessageBox.critical(self, "Oops", str(ex))
            self.model.acquisitionsList = res
            self.model.modelReset.emit()
            self.table.resizeColumnsToContents()

    # def save(self):
    #     with open('BTC_acqs.json', 'w') as f:
    #         data = json.dump(self.model.todos, f)


class DispositionsPage(QWidget):

    model_changed_sig = Signal(object, object) # params are: acquisitions, dispositions

    def __init__(self, dispositions: List[Disposition]) -> None:
        super().__init__()

        self.table = QTableView()
        self.model = DisTableModel(dispositions)
        self.table.setModel(self.model)
        self.table.showGrid()
        self.table.setGridStyle(Qt.SolidLine)
        self.table.resizeColumnsToContents()
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setItemDelegate(BorderHighlightItemDelegate())

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_disposition)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_disposition)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_disposition)
        imp_btn = QPushButton("Import")
        imp_btn.clicked.connect(self.import_file)

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

    def reset_data(self, dispositions: List[Disposition]) -> None:
        self.model.reset_model(dispositions)
        self.table.viewport().update()


    def edit_disposition(self) -> None:
        sel_model = self.table.selectionModel()
        idx_list =  sel_model.selectedRows()
        if not idx_list:
            button = QMessageBox.warning(self,"Edit","No Disposition row selected" )
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
            self.model.index(idx_list[0].row(), DisTableModel.DIS_CANCEL_BTN_IDX),
            cancel_edit_btn)
        self.table.setIndexWidget(
            self.model.index(idx_list[0].row(), DisTableModel.DIS_ACCEPT_BTN_IDX),
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
            self.model_changed_sig.emit(None, self.model.dispositionsList)  # main window catches this, rebuilds stash, and updates views
            self.disable_edit_gui(edit_row)

    def disable_edit_gui(self, edit_row: int) -> None:
        ''' just removes the buttons and updates the view '''
        self.table.setIndexWidget(
            self.model.index(edit_row, DisTableModel.DIS_CANCEL_BTN_IDX), None)
        self.table.setIndexWidget(
            self.model.index(edit_row, DisTableModel.DIS_ACCEPT_BTN_IDX), None)
        self.table.viewport().update()

    def add_disposition(self) -> None:
        new_acq = Disposition(datetime.timestamp(datetime.now(timezone.utc)), 0, 0, 0, "", "New Disposition")
        self.model.dispositionsList.append(new_acq) # TODO: fix fugliness
        self.model_changed_sig.emit(None, self.model.dispositionsList )

    def delete_disposition(self) -> None:
        sel_model = self.table.selectionModel()
        idx_list =  sel_model.selectedRows()
        if not idx_list:
            button = QMessageBox.warning(self,"Delete Disposition","No Disposition row selected" )
            return
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Confirm Delete ")
            dlg.setText("Delete the selected Disposition?")
            dlg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes )
            dlg.setIcon(QMessageBox.Question)
            button = dlg.exec()
            if button == QMessageBox.Yes:
                del_row = idx_list[0].row()
                del self.model.dispositionsList[del_row]
                self.model_changed_sig.emit(None, self.model.dispositionsList )

    def import_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select a File"
        )
        if filename:
            res = []  # This would be your JSON data.
            try:
                with open(filename, 'r') as f:
                    jsonData = json.load(f) # a List of Dicts
                res = sorted( [Disposition.from_json_dict(dis) for dis in jsonData],  key=lambda dis: dis.timestamp)
            except Exception as ex:
                # TODO: handle this with a popup thingy
                QMessageBox.critical(self, "Oops", str(ex))
            self.model.dispositionsList = res
            self.model.modelReset.emit()
            self.table.resizeColumnsToContents()


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

    def reset_data(self, states: List[StashState]) -> None:
        self.model.reset_model(states)
        self.table.viewport().update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.stash = self.load_stash('new_stash.json')
        self.resize(1024, 768)
        self.setWindowTitle(f'{self.stash.currency_name}: {self.stash.title}')
        menu = self.menuBar()

        new_stash_action = QAction("&New Stash", self)
        new_stash_action.triggered.connect(self.new_stash)

        open_stash_action = QAction("&Open Stash", self)
        open_stash_action.triggered.connect(self.open_stash)

        save_stash_action = QAction("&Save Stash", self)
        save_stash_action.triggered.connect(self.save_stash)

        file_menu = menu.addMenu("&File")
        file_menu.addAction(new_stash_action)
        file_menu.addAction(open_stash_action)
        file_menu.addAction(save_stash_action)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.acqPage = AcquisitionsPage(self.stash.acquisitions)
        self.acqPage.model_changed_sig[object, object].connect(self.on_model_changed)
        tabs.addTab(self.acqPage, "Acquisitions")

        self.dispPage = DispositionsPage(self.stash.dispositions)
        self.dispPage.model_changed_sig[object, object].connect(self.on_model_changed)
        tabs.addTab(self.dispPage, "Dispositions")

        self.txPage = TransactionStatesPage(self.stash.states)
        tabs.addTab(self.txPage, "Transactions")

    def new_stash(self):

        class NewDlg(QDialog):
            def __init__(self):
                super().__init__()

                self.setWindowTitle("New Stash!")
                self.currency_edit = QLineEdit("Currency")
                self.title_edit = QLineEdit("Stash Title")

                QBtn = (
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )

                self.buttonBox = QDialogButtonBox(QBtn)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                layout = QVBoxLayout()
                layout.addWidget(self.currency_edit)
                layout.addWidget(self.title_edit)
                layout.addWidget(self.buttonBox)
                self.setLayout(layout)

        dlg = NewDlg()
        if dlg.exec():
            self.stash = Stash( dlg.currency_edit.text(), dlg.title_edit.text() )
            self.setWindowTitle(f'{self.stash.currency_name}: {self.stash.title}')
            self.on_model_changed(None, None) # uses self.whatever if none

    def open_stash(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open file:"
        )
        stash = self.load_stash(filename)
        if stash:
            self.stash = stash
            self.setWindowTitle(f'{self.stash.currency_name}: {self.stash.title}')
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

    @Slot(object, object)
    def on_model_changed(self, new_acqs: List[Acquisition], new_disps:List[Disposition]) -> None:

        if new_acqs != None:
            self.stash.acquisitions = new_acqs
        if new_disps!= None:
            self.stash.dispositions = new_disps

        self.stash.update()  # sorts transactions and builds states
        self.acqPage.reset_data(self.stash.acquisitions)
        self.dispPage.reset_data(self.stash.dispositions)
        self.txPage.reset_data(self.stash.states)
        self.centralWidget().update()

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