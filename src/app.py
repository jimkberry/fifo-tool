import sys
import json
from datetime import datetime
from typing import List, Dict

from PySide6.QtWidgets import ( QApplication, QMainWindow, QPushButton,
    QWidget, QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QTableView,
    QMessageBox, QTabWidget, QLabel, QFileDialog, QAbstractItemView, QStyle,
    QAbstractItemDelegate, QStyledItemDelegate)
from PySide6.QtGui import QAction, QPainter, QColor, Qt
from PySide6.QtCore import QRect

from models.acquisition import Acquisition, AcqTableModel
from models.disposition import Disposition, DisTableModel
from models.stash import Stash, StatesTableModel


class AcquisitionItemDelegate(QStyledItemDelegate):
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
    def __init__(self, acq_dict: List[Acquisition] = []) -> None:
        super().__init__()

        # QTableView::item properties that work:
        # :selected
        # :focus
        # :hover
        # :enabled / :disabled

        # self.setStyleSheet('''
        #     QTableView::item[ItemIsEditable="true"] {
        #         background-color: red;
        #         border-top: 2px solid yellow;
        #         border-bottom: 2px solid yellow;
        #     }
        # ''')

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_acquisition)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_acquisition)
        del_btn = QPushButton("Delete")
        imp_btn = QPushButton("Import")
        imp_btn.clicked.connect(self.import_file)


        self.table = QTableView()
        self.model = AcqTableModel(acq_dict)
        self.table.setModel(self.model)
        self.table.showGrid()
        self.table.setGridStyle(Qt.SolidLine)
        self.table.resizeColumnsToContents()
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setItemDelegate(AcquisitionItemDelegate())

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
            self.disable_edit_gui(edit_row)

    def disable_edit_gui(self, edit_row: int) -> None:
        ''' just removes the buttones and updates the view '''
        self.table.setIndexWidget(
            self.model.index(edit_row, AcqTableModel.ACQ_CANCEL_BTN_IDX), None)
        self.table.setIndexWidget(
            self.model.index(edit_row,AcqTableModel.ACQ_ACCEPT_BTN_IDX), None)
        self.table.viewport().update()

    def add_acquisition(self) -> List[Acquisition]:
        pass

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
    def __init__(self, dis_dict: List[Disposition] = []) -> None:
        super().__init__()

        addBtn = QPushButton("Add")
        delBtn = QPushButton("Delete")
        impBtn = QPushButton("Import")
        impBtn.clicked.connect(self.import_file)

        self.table = QTableView()
        self.model = DisTableModel(dis_dict)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)


        # layout
        btnsLayout = QHBoxLayout()
        btnsLayout.addWidget(addBtn)
        btnsLayout.addWidget(delBtn)
        btnsLayout.addWidget(impBtn)

        pageLayout = QVBoxLayout()
        pageLayout.addWidget(self.table)
        pageLayout.addLayout(btnsLayout)

        self.setLayout(pageLayout)

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
    def __init__(self, states_list: List[Acquisition|Disposition] = []) -> None:
        super().__init__()

        lotsBtn = QPushButton("Show Lots")

        self.table = QTableView()
        self.model = StatesTableModel(states_list)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # layout
        btnsLayout = QHBoxLayout()
        btnsLayout.addWidget(lotsBtn)

        pageLayout = QVBoxLayout()
        pageLayout.addWidget(self.table)
        pageLayout.addLayout(btnsLayout)

        self.setLayout(pageLayout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.stash = self.load_stash()
        self.resize(1024, 768)
        self.setWindowTitle("My App")

        menu = self.menuBar()

        save_stash_action = QAction("&Save Stash", self)
        save_stash_action.triggered.connect(self.save_stash)

        file_menu = menu.addMenu("&File")
        file_menu.addAction(save_stash_action)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        acqPage = AcquisitionsPage(self.stash.acquisitions)
        tabs.addTab(acqPage, "Acquisitions")

        dispPage = DispositionsPage(self.stash.dispositions)
        tabs.addTab(dispPage, "Dispositions")

        txPage = TransactionStatesPage(self.stash.states)
        tabs.addTab(txPage, "Transactions")

    def load_stash(self):
        stash = {}
        try:
            with open('stash.json', 'r') as f:
                jsonData = json.load(f) # a List of Dicts
                stash = Stash.from_json_dict(jsonData)
        except Exception as ex:
             QMessageBox.critical(self, "Oops", str(ex))

        stash.generate_states()
        return stash


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