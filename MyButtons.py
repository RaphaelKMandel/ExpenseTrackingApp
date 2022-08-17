from PyQt5.QtWidgets import QPushButton, QComboBox


class YearComboBox(QComboBox):
    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.values = []
        self.update_box()
        self.currentIndexChanged.connect(self.widget.update_tab)
        
    def update_box(self):
        old_values = self.values.copy()
        self.years = self.get_years()
        self.values = self.get_values()
        for value in self.values:
            if value not in old_values:
                self.addItems([value])
        for i, item in enumerate(old_values):
            if item not in self.values:
                self.removeItem(i)
        
    def get_years(self):
        return self.widget.model.ledger.df.Year.unique()
    
    def get_values(self):
        return (["All"] + self.years.astype(str).tolist())

    def get_range(self):
        selection = self.currentText()
        if selection == "All":
            start = [min(self.get_years()), 1, 1]
            stop = [max(self.get_years()), 12, 31]
        else:
            start = [int(selection), 1, 1]
            stop = [int(selection), 12, 31]
        return start, stop


class PushButton(QPushButton):
    def __init__(self, widget, name):
        super().__init__(name)
        self.widget = widget
        self.clicked.connect(self.clicked_function)

    def clicked_function(self):
        pass


class ImportTransactionsButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Import Transactions")

    def clicked_function(self):
        self.widget.import_transactions()


class AutoCategorizeButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Auto Categorize Transactions")

    def clicked_function(self):
        self.widget.auto_categorize()
        
        
class AcceptCategorizedButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Accept Categorized Transactions")

    def clicked_function(self):
        self.widget.accept_categorized()
        

class ClearImportsButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Clear Imports")
        
    def clicked_function(self):
        self.widget.clear_imports()
        

class ClearDuplicatesButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Clear Duplicates")
        
    def clicked_function(self):
        self.widget.clear_duplicates()


class SwapRows(PushButton):
    def __init__(self, widget, name):
        super().__init__(widget, name)
        
    def clicked_function(self):
        self.widget.swap_rows(self.offset)


class MoveUpButton(SwapRows):
    def __init__(self, widget):
        super().__init__(widget, "Move Up")
        self.offset = -1
        

class MoveDownButton(SwapRows):
    def __init__(self, widget):
        super().__init__(widget, "Move Down")
        self.offset = 1
     
        
class DeleteButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Delete Row")

    def clicked_function(self):
        self.widget.delete_row()
        

class AddRowButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Add Blank Row")
        
    def clicked_function(self):
        self.widget.add_row()


class PrintButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Print Data")

    def clicked_function(self):
        print(self.widget.data.df)
        

class AddRuleButton(PushButton):
    def __init__(self, widget):
        super().__init__(widget, "Add Rule")
        
    def clicked_function(self):
        self.widget.add_rule()
