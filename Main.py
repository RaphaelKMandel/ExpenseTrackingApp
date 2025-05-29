import os
import io
import pandas as pd
from zipfile import ZipFile
from MyModels import Model
from MyTabs import BudgetTab, RulesTab, ImportsTab, LedgerTab, DuplicatesTab
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTabWidget, QAction


class MainWindow(QMainWindow):
    file_type = "Zip files (*.zip)"

    def __init__(self):
        super().__init__()
        # Define Variables
        self.name = None
        self.directory = None
        self.file_name = None
        self.model = Model()
        # Main Window
        self.set_title()
        self.setFixedWidth(1600)
        self.setFixedHeight(800)
        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        # Define Actions
        self.load_action = QAction("Load")
        self.save_action = QAction("Save")
        self.save_as_action = QAction("Save As")
        self.save_quit_action = QAction("Save and Quit")
        # Connect Actions
        self.load_action.triggered.connect(self.load)
        self.save_action.triggered.connect(self.save)
        self.save_as_action.triggered.connect(self.save_as)
        self.save_quit_action.triggered.connect(self.save_and_quit)
        # Add Actions
        self.file_menu.addAction(self.load_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addAction(self.save_quit_action)
        # Add Tab Widget
        self.tabs = MyTabWidget(self.model)
        self.setCentralWidget(self.tabs)
        # Show
        self.show()

    def set_title(self):
        self.setWindowTitle(f"Budgeting Application: {self.name}")

    def load(self):
        self.file_dialog("load")
        self.set_title()
        with ZipFile(self.file_name, 'r') as zip_file:
            self.model.budget.df = self.load_dataframe(zip_file, "Budget")
            self.model.rules.df = self.load_dataframe(zip_file, "Rules")
            self.model.ledger.df = self.load_dataframe(zip_file, "Ledger")
        # Update
        self.tabs.update_tabs()

    def save(self):
        if self.name is None:
            self.file_dialog("save")
        self.set_title()
        with ZipFile(self.file_name, 'w') as zip_file:
            self.save_dataframe(zip_file, self.model.budget, "Budget")
            self.save_dataframe(zip_file, self.model.rules, "Rules")
            self.save_dataframe(zip_file, self.model.ledger, "Ledger")

    def save_as(self):
        self.name = None
        self.save()

    def save_and_quit(self):
        self.save()
        self.close()

    def file_dialog(self, mode):
        file_type = "Zip files (*.zip)"
        directory = os.path.dirname(__file__)
        if mode == "load":
            file_name = QFileDialog.getOpenFileName(self, "Select File to Open", directory, file_type)[0]
        elif mode == "save":
            file_name = QFileDialog.getSaveFileName(self, "Name The File", directory, file_type)[0]
        self.file_name = file_name
        self.name = file_name.split('/')[-1].split('.')[0]
        self.directory = '/'.join(file_name.split('/')[:-1])

    @staticmethod
    def load_dataframe(zip_file, name):
        data = zip_file.read(f"{name}.csv").decode()
        data = io.StringIO(data)
        data = pd.read_csv(data, sep=",")
        return data

    @staticmethod
    def save_dataframe(zip_file, data, name):
        zip_file.writestr(f"{name}.csv", data.df.to_csv())


class MyTabWidget(QTabWidget):
    def __init__(self, model):
        super().__init__()
        # Define Variables
        self.model = model
        # GUI
        self.tabs = [BudgetTab(model), RulesTab(model), 
                     ImportsTab(model), LedgerTab(model), DuplicatesTab(model)]
        for tab in self.tabs:
            self.addTab(tab, tab.name)
        self.tabBarClicked.connect(self.update_clicked_tab)

    def update_clicked_tab(self, index):
        self.tabs[index].update_tab()
        
    def update_tabs(self):
        for tab in self.tabs:
            tab.update_tab()


if __name__ == "__main__":
    app = QApplication([])
    app.setQuitOnLastWindowClosed(True)
    result = MainWindow()
    app.exec_()
