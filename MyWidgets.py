import numpy as np
from MyButtons import AddRuleButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


class PandasTable(QTableWidget):
    def __init__(self, model, data, buttons=None):
        if buttons is None:
            buttons = dict()
        super().__init__()
        self.model = model
        self.data = data
        self.old_df = data.df.copy()
        self.buttons = buttons
        self.columns = self.data.df.columns.tolist() + list(self.buttons.keys())
        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels(self.columns)
        for col, width in enumerate(self.column_widths):
            self.setColumnWidth(col, width)
        self.connect()
        self.fill_all()

    def connect(self):
        self.cellChanged.connect(self.update_dataframe)
        
    def disconnect(self):
        self.cellChanged.disconnect(self.update_dataframe)
 
    def update_dataframe(self, row, col):
        text = self.item(row, col).text()
        value = self.data.set_value(row, col, text)
        self.item(row, col).setText(value)
        self.update_table()

    def update_record(self):
        self.old_df = self.data.df.copy()

    def update_table(self):
        if len(self.data.df) != len(self.old_df):
            print("Re-filling entire table!")
            self.fill_all()
        else:
            self.fill_changed()

    def fill_all(self):
        self.disconnect()
        self.setRowCount(len(self.data.df))
        for col, column in enumerate(self.columns):
            if column in self.buttons:
                for row in range(self.rowCount()):
                    button = self.buttons[column](self)
                    self.setCellWidget(row, col, button)
            else:
                if column in self.data.disabled:
                    flag = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                else:
                    flag = None
                data = self.data.df.iloc[:, col].apply(str).tolist()
                for row in range(self.rowCount()):
                    text = data[row]
                    item = QTableWidgetItem(text)
                    if flag:
                        item.setFlags(flag)
                    self.format_cell(row, col, item)
                    self.setItem(row, col, item)
        self.connect()
        self.update_record()

    def fill_changed(self):
        rows, cols = np.where(self.data.df != self.old_df)
        self.fill_indexes(rows, cols)

    def fill_row(self, row):
        rows = [row] * self.columnCount()
        cols = range(self.columnCount())
        self.fill_indexes(rows, cols)

    def fill_indexes(self, rows, cols):
        self.disconnect()
        for row, col in zip(rows, cols):
            self.fill_item(row, col)
        self.connect()
        self.update_record()

    def fill_item(self, row, col):
        column = self.columns[col]
        if column in self.data.disabled:
            flag = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            flag = False
        if column not in self.buttons:
            text = str(self.data.df.iloc[row, col])
            item = QTableWidgetItem(text)
            if flag:
                item.setFlags(flag)
            self.format_cell(row, col, item)
            self.setItem(row, col, item)
        
    def add_row(self):
        self.data.insert_blank_row()
        row = self.rowCount()
        self.insertRow(row)
        self.fill_row(row)
        self.selectRow(row)
        
    def delete_row(self):
        row = self.currentRow()
        if self.is_valid_row(row):
            self.data.delete_row(row)
            self.removeRow(row)
        else:
            print(f"Cannot delete row {row}")
            
    def swap_rows(self, offset):
        row1 = self.currentRow()
        row2 = row1 + offset
        if self.is_valid_row(row1) and self.is_valid_row(row2):
            self.data.swap_rows(row1, row2)
            self.fill_row(row1)
            self.fill_row(row2)
            self.selectRow(row2)
            
    def is_valid_row(self, row):
        return 0 <= row < self.rowCount()

    def format_cell(self, row, col, item):
        pass


class BudgetTable(PandasTable):
    def __init__(self, model):
        self.column_widths = [30, 150, *[60] * 16, 50]
        super().__init__(model, model.budget)
        self.setFixedWidth(1200)
        
    def format_cell(self, row, col, item):
        if col in range(3, 17):
            sign = self.data.df.Sign[row]
            value = self.data.df.iloc[row, col]
            if col == 4:
                budget = 0
            else:
                budget = self.data.df.Budget[row]
            color = self.color(value, budget, sign)
            item.setForeground(color)

    @staticmethod
    def color(value, budget, sign, scale=50):
        rgb = sign * (value - budget) / scale
        if rgb > 1:
            rgb = 1
        elif rgb < -1:
            rgb = -1
        if  rgb >= 0:
            return QColor.fromRgb(0, int(255 * rgb), 0)
        else:
            return QColor.fromRgb(int(-255 * rgb), 0, 0)


class RulesTable(PandasTable):
    def __init__(self, model):
        self.column_widths = [200, 150, 100, 30]
        super().__init__(model, model.rules)
        self.setFixedWidth(1400)


class LedgerTable(PandasTable):
    def __init__(self, model):
        self.column_widths = [50, 50, 50, 400, 75, 200, 150, 100, 200, 75]
        buttons = {"Add Rule": AddRuleButton}
        super().__init__(model, model.ledger, buttons=buttons)
        self.setFixedWidth(1400)
    
    def add_rule(self):
        row = self.currentRow()
        keyword = self.data.df.loc[row, "Keyword"]
        category = self.data.df.loc[row, "Category"]
        subcategory = self.data.df.loc[row, "Sub Category"]
        if keyword == "None":  # If keyword is blank, use Memo
            keyword = self.data.df.loc[row, "Memo"]
        if keyword in self.model.rules.df.Keyword.values:
            print(f"Rule {keyword} already exists.")
        elif category not in self.model.budget.df.Category.values:
            print(f"Budget {category} is not defined.")
        else:
            self.data.df.loc[row, "Keyword"] = keyword
            self.fill_row(row)
            self.model.rules.add_rule(keyword, category, subcategory)


class ImportsTable(LedgerTable):
    def __init__(self, model):
        super().__init__(model)
        self.data = self.model.imports
        

class DuplicatesTable(LedgerTable):
    def __init__(self, model):
        super().__init__(model)
        self.data = self.model.duplicates