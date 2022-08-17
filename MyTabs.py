import os
from matplotlib import pyplot as plt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QFileDialog, QLabel
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QHBoxLayout
from MyHelperClasses import Colors
from MyWidgets import BudgetTable, RulesTable, ImportsTable, LedgerTable, DuplicatesTable
from MyButtons import MoveUpButton, MoveDownButton, DeleteButton, AddRowButton, PrintButton
from MyButtons import YearComboBox, ImportTransactionsButton, AutoCategorizeButton
from MyButtons import AcceptCategorizedButton, ClearImportsButton, ClearDuplicatesButton


plt.ioff()


class FiveButtonTable(QWidget):
    def __init__(self, Table, model):
        super().__init__()
        # Model
        self.model = model
        # Table
        self.table = Table(model)
        # Table Buttons
        self.add_row_btn = AddRowButton(self.table)
        self.move_up_btn = MoveUpButton(self.table)
        self.delete_btn = DeleteButton(self.table)
        self.move_down_btn = MoveDownButton(self.table)
        self.print_btn = PrintButton(self.table)
        # Layout
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.add_row_btn, 0, 0, 1, 1)
        self.layout.addWidget(self.move_up_btn, 1, 0, 1, 1)
        self.layout.addWidget(self.delete_btn, 2, 0, 1, 1)
        self.layout.addWidget(self.move_down_btn, 3, 0, 1, 1)
        self.layout.addWidget(self.print_btn, 4, 0, 1, 1)
        self.layout.addWidget(self.table, 0, 1, 5, 6)


class BudgetTab(QWidget):       
    def __init__(self, model):
        super().__init__()
        # Define Variables
        self.name = "Budget"
        self.model = model
        # Table
        self.table = FiveButtonTable(BudgetTable, model)
        # Drop Down Menu
        self.year_cbox = YearComboBox(self)
        # Graphs
        self.graph1 = QLabel("Graph 1 Will Go Here")
        # Layout
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.year_cbox, 0, 0, 1, 10)
        self.layout.addWidget(self.table, 1, 1, 1, 5)
        self.layout.addWidget(self.graph1, 1, 6, 1, 5)

    def update_tab(self):
        print("Updating Budget Tab")
        self.year_cbox.update_box()
        start, stop = self.year_cbox.get_range()
        self.model.summarize(start, stop)
        self.table.table.update_table()
        #self.plot_graphs()
        
    def plot_graphs(self):
        self.bar_chart()
        pixmap1 = QPixmap("graph1.png")
        self.graph1.setPixmap(pixmap1)

    def bar_chart(self, mode=False):
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        df = self.model.budget.df.copy()
        df["Order"] = 0
        months = df.columns[5:17]
        for row, category in zip(df.index, df.Category):  # For Legend
            ax.bar(0, 0, color=Colors.colors[row], label=category)
        for col, month in enumerate(months):
            col += 5
            df.iloc[:, col] = df.Sign * (df.iloc[:, col] - df.Budget)
            df.Order = df.iloc[:, col].abs()
            df.sort_values(by="Order", ascending=mode, inplace=True)
            y = df.iloc[:, col]
            for row, category in zip(df.index, df.Category):
                ax.bar(month, y[row], color=Colors.colors[row])
        fig.legend(loc=2, ncol=4, mode="expand")
        fig.savefig("graph1.png")


class RulesTab(QWidget):       
    def __init__(self, model):
        super().__init__()
        # Define Variables
        self.name = "Rules"
        self.model = model
        # Table
        self.table = FiveButtonTable(RulesTable, model)
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.table)

    def update_tab(self):
        print("Updating Rules Tab")
        self.table.table.update_table()


class ImportsTab(QWidget):
    def __init__(self, model):
        super().__init__()
        # Define Variables
        self.name = "Imports"
        self.model = model
        # Table
        self.table = FiveButtonTable(ImportsTable, model)
        # Buttons
        self.import_btn = ImportTransactionsButton(self)
        self.autocat_btn = AutoCategorizeButton(self)
        self.accept_btn = AcceptCategorizedButton(self)
        self.clear_btn = ClearImportsButton(self)
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.import_btn)
        self.layout.addWidget(self.autocat_btn)
        self.layout.addWidget(self.accept_btn)
        self.layout.addWidget(self.clear_btn)
        self.layout.addWidget(self.table)

    def import_transactions(self):
        prompt = "Select File to Open"
        file_type = "CSV files (*.csv)"
        directory = os.path.dirname(__file__)
        file_name = QFileDialog.getOpenFileName(self, prompt, directory, file_type)[0]
        self.table.table.data.import_transactions(file_name)
        self.update_tab()

    def auto_categorize(self):
        self.table.table.data.auto_categorize()
        self.update_tab()
        
    def accept_categorized(self):
        self.table.table.data.accept_categorized()
        self.update_tab()
        
    def clear_imports(self):
        self.table.table.data.__init__(self.model)
        self.update_tab()

    def update_tab(self):
        print("Updating Imports Tab")
        self.table.table.update_table()


class LedgerTab(QWidget):       
    def __init__(self, model):
        super().__init__()
        # Define Variables
        self.name = "Ledger"
        self.model = model
        # Table
        self.table = FiveButtonTable(LedgerTable, model)
        # Buttons
        self.autocat_btn = AutoCategorizeButton(self)
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.autocat_btn)
        self.layout.addWidget(self.table)

    def auto_categorize(self):
        self.table.table.data.auto_categorize()
        self.update_tab()

    def update_tab(self):
        print("Updating Ledger Tab")
        self.table.table.update_table()


class DuplicatesTab(QWidget):       
    def __init__(self, model):
        super().__init__()
        # Define Variables
        self.name = "Duplicates"
        self.model = model
        # Table
        self.table = FiveButtonTable(DuplicatesTable, model)
        # Buttons
        self.clear_button = ClearDuplicatesButton(self)
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.table)
        
    def clear_duplicates(self):
        self.table.table.data.__init__(self.model)
        self.update_tab()

    def update_tab(self):
        print("Updating Duplicates Tab")
        self.table.table.update_table()