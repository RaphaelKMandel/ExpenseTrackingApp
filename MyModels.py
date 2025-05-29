import re
import numpy as np
import pandas as pd
from MyHelperClasses import Date


class Model:
    def __init__(self, budget=None, rules=None, imports=None, ledger=None, duplicates=None):
        self.budget = BudgetData(self, budget)
        self.rules = RulesData(self, rules)
        self.imports = ImportData(self, imports)
        self.ledger = LedgerData(self, ledger)
        self.duplicates = DuplicateData(self, duplicates)
        self.tables = [self.budget, self.rules, self.imports, self.ledger, self.duplicates]
        self.summary = SummaryTable(self)
        
    def summarize(self, start, stop):
        self.budget.df = self.summary.summarize(start, stop)
        
    def elaborate(self):
        pass
        
    def rename_budget_category(self, old_category, new_category):
        for table in self.tables:
            table.rename_budget_category(old_category, new_category)
            
    def rename_keyword(self, old_keyword, new_keyword):
        for table in self.tables:
            table.rename_keyword(old_keyword, new_keyword)
            
    def recategorize_keyword(self, keyword, new_category):
        for table in self.tables:
            table.recategorize_keyword(keyword, new_category)
    
    def resubcategorize_keyword(self, keyword, new_subcategory):
        for table in self.tables:
            table.resubcategorize_keyword(keyword, new_subcategory)


class DataFrame:        
    def __init__(self, model, data, name):
        self.model = model
        self.df = pd.DataFrame(data, columns=self.columns)
        self.name = name
        
    def set_nothing(self, row, col, text):
        return text

    def set_value(self, row, col, text):
        function = self.functions[col]
        value = function(row, col, text)
        return value
    
    def swap_rows(self, row1, row2):
        temp = self.df.iloc[row1, :].copy()
        self.df.iloc[row1, :] = self.df.iloc[row2, :].copy()
        self.df.iloc[row2, :] = temp

    def insert_blank_row(self):
        N = len(self.df)
        self.df.loc[N] = dict(zip(self.columns, self.defaults))
        print(f"{self.name} row added (blank).")

    def delete_row(self, row):
        self.df.drop(row, inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        print(f"{self.name} {row} deleted.")

    def rename_budget_category(self, old_category, new_category):
        if "Category" in self.columns:
            index = self.df.Category == old_category
            self.df.loc[index, "Category"] = new_category
            
    def rename_keyword(self, old_keyword, new_keyword):
        # TODO: Check/Redo this logic
        if isinstance(self, LedgerData):
            ledger_indexes = np.where(self.df.Keyword == old_keyword)[0]
            for ledger_index in ledger_indexes:
                memo = self.df.loc[ledger_index, "Memo"]
                result = re.search(new_keyword, memo, re.I)
                if isinstance(result, re.Match):
                    self.df.loc[ledger_index, "Keyword"] = new_keyword
                else:
                    print(f"{memo} does not contain new keyword {new_keyword}")
                    rule_index = np.where(self.model.rules.df.Keyword == old_keyword)[0]
                    self.assign(ledger_index, rule_index, "None", "None", "None")
            
    def recategorize_keyword(self, keyword, new_category):
        if "Keyword" in self.columns:
            index = self.df.Keyword == keyword
            self.df.loc[index, "Category"] = new_category
    
    def resubcategorize_keyword(self, keyword, new_subcategory):
        if "Keyword" in self.columns:
            index = self.df.Keyword == keyword
            self.df.loc[index, "Sub Category"] = new_subcategory


class BudgetData(DataFrame):
    columns = ["Sign", "Category", "Budget", 
                        "Average", "Net", *Date.month_names, "Total"]
    defaults = [-1, "N/A", 0, *15 * [0]]
    disabled = columns[3:].copy()
    
    def __init__(self, model, data=None, name="Budget"):
        if data is None:
            data = {"Sign": [1, -1],
                    "Category": ["INCOME", "GROCERIES"],
                    "Budget": [10000, 1000],
                    "Average": [0, 0],
                    "Net": [0, 0],
                    **dict(zip(Date.month_names, 12 *[2 * [0]])),
                    "Total": [0, 0]}
        self.functions = (self.set_sign, 
                          self.set_category,
                          self.set_budget,
                          *15 * (self.set_nothing,))
        super().__init__(model, data, name)

    def set_sign(self, row, col, text):
        try:
            value = int(text)
            if value in [-1, 1]:
                self.df.iloc[row, col] = value
            else:
                print(f"Sign {value} must be -1 or 1.")
                value = self.df.iloc[row, col] 
        except ValueError:
            print(f"Failed to convert Sign '{text}' to {int}")
            value = self.df.iloc[row, col]
        return str(value)
        
    def set_category(self, row, col, text):
        new_category = text.upper()
        old_category = self.df.iloc[row, col]
        if new_category not in self.df.Category.values:
            self.df.iloc[row, col] = new_category
            self.model.rename_budget_category(old_category, new_category)
            return new_category
        else:
            print(f"Category {text} already exists.")
            return old_category

    def set_budget(self, row, col, text):
        try:
            value = abs(int(text))
            self.df.iloc[row, col] = value
        except ValueError:
            print(f"Failed to convert Budget '{text}' to {int}")
            value = self.df.iloc[row, col]
        return str(value)


class RulesData(DataFrame):
    columns = ("Keyword", "Category", "Sub Category", "Count")
    defaults = ("N/A", "", "", 0)
    disabled = ("Count", )
    
    def __init__(self, model, data=None, name="Rules"):
        if data is None:
            data = {"Keyword": ["Trader Joes", "CVS", "GOOGLE"],
                    "Category": ["GROCERIES", "GROCERIES", "INCOME"],
                    "Sub Category": ["Trader Joe's", "CVS/PHARMACY", "Person 1"],
                    "Count": [0, 0, 0]}
        self.functions = (self.set_keyword, self.set_category,
                          self.set_subcategory, self.set_nothing)
        super().__init__(model, data, name)
        
    def set_keyword(self, row, col, new_keyword):
        old_keyword = self.df.iloc[row, col]
        if new_keyword not in self.df.Keyword.values:
            self.df.Count[row] = 0
            self.model.rename_keyword(old_keyword, new_keyword)
            self.df.iloc[row, col] = new_keyword
            return new_keyword
        else:
            print(f"Rule {new_keyword} already exists.")
            return old_keyword

    def set_category(self, row, col, text):
        value = text.upper()
        if value in self.model.budget.df.Category.values:
            keyword = self.df.loc[row, "Keyword"]
            self.df.iloc[row, col] = value
            self.model.recategorize_keyword(keyword, value)
            return value
        else:
            print(f"Budget {value} does not exist.")
            return self.df.iloc[row, col]
        
    def set_subcategory(self, row, col, text):
        keyword = self.df.loc[row, "Keyword"]
        self.df.iloc[row, col] = text
        self.model.resubcategorize_keyword(keyword, text)
        return text     

    def add_rule(self, keyword, category, subcategory):
        col = 0
        row = len(self.df)
        self.insert_blank_row()
        self.set_keyword(row, col, keyword)
        self.set_category(row, col + 1, category)
        self.set_subcategory(row, col + 2, subcategory)
        

class TransactionData(DataFrame):
    columns = ("Year", "Month", "Day", "Memo", "Amount",
               "Keyword", "Category", "Sub Category", "ID")
    defaults = (2020, 1, 1, "", 0, "None", "None", "None", "None")
    disabled = ("Memo", "Amount")
    
    def __init__(self, model, data=None, name=None):
        self.functions = (self.set_year, self.set_month, self.set_day, 
                          self.set_nothing, self.set_nothing, 
                          self.set_keyword, self.set_category, self.set_subcategory)
        super().__init__(model, data, name)
        
    def empty_data(self):
        data = dict(zip(self.columns, [len(self.columns) * []]))
        return data

    def set_year(self, row, col, text):
        try:
            value = int(text)
            if value > 2000:
                self.df.iloc[row, col] = value
                return str(value)
            else:
                raise ValueError
        except ValueError:
            print(f"Year {text} is not valid.")
            return str(self.df.iloc[row, col])
        
    def set_month(self, row, col, text):
        try:
            value = int(text)
            if 1 <= value <= 12:
                self.df.iloc[row, col] = value
                return str(value)
            else:
                raise ValueError
        except ValueError:
            print(f"Month {text} is not valid.")
            return str(self.df.iloc[row, col])
        
    def set_day(self, row, col, text):
        try:
            value = int(text)
            if 1 <= value <= 31:
                self.df.iloc[row, col] = value
                return str(value)
            else:
                raise ValueError
        except ValueError:
            print(f"Day {text} is not valid.")
            return str(self.df.iloc[row, col])
        
    def set_keyword(self, row, col, text):
        if text not in self.df.Keyword.values:
            old_text = self.df.iloc[row, col]
            if old_text != "None":
                rule_index = np.where(self.model.rules.df.Keyword == old_text)[0]
                self.model.rules.df.Count[rule_index] -= 1
            self.df.iloc[row, col] = text
            return text
        else:
            print(f"Rule {text} already exists.")
            return self.df.iloc[row, col]

    def set_category(self, row, col, text):
        value = text.upper()
        if value in self.model.budget.df.Category.values:
            self.df.iloc[row, col] = value
            return value
        else:
            print(f"Budget {value} does not exist.")
            return self.df.iloc[row, col]
        
    def set_subcategory(self, row, col, text):
        self.df.iloc[row, col] = text
        return text


class LedgerData(TransactionData):
    def __init__(self, model, data=None, name="Ledger"):
        if data is None:
            data = {"Year": [2019, 2019, 2020, 2020],
                    "Month": [1, 2, 3, 4],
                    "Day": [1, 1, 1, 1],
                    "Memo": ["Trader Joes", "CVS", "CVS Trader Joes", "STATE OF MD"],
                    "Amount": [-100.0, -50.25, -23.2, 1000.0],
                    "Keyword": ["None", "None", "None", "None"],
                    "Category": ["None", "None", "None", "None"],
                    "Sub Category": ["None", "None", "None", "None"],
                    "ID": ["1", "2", "3", "4"]}
        super().__init__(model, data, name)
    
    def auto_categorize(self):
        # Extract Uncategorized Data
        data_indexes = np.where(self.df.Keyword == "None")[0]
        data = self.df.Memo[data_indexes]
        # Find All Rule Matches
        rule_indexes = []
        ledger_indexes = []
        keywords = self.model.rules.df.Keyword
        for k, keyword in enumerate(keywords):
            index = data.str.contains(keyword, flags=re.I, regex=True)
            index = list(np.where(index)[0])
            rule_indexes += [k] * len(index)
            ledger_indexes += data_indexes[index].tolist()
        # Find Duplicate Matches
        columns = ["Rule", "Ledger"]
        duplicates = pd.DataFrame(zip(rule_indexes, ledger_indexes), columns=columns)
        duplicates = duplicates.groupby(by="Ledger")
        duplicates = duplicates["Rule"].apply(list)
        # Find Missing by Taking Set Difference
        missing = np.setdiff1d(data.index, duplicates.index).tolist()
        # Assign Categories
        for ledger_index, rule_index in zip(duplicates.index, duplicates.values):
            if len(rule_index) == 1:  # Assign Only Match
                keyword = keywords[rule_index[0]]
                category = self.model.rules.df.loc[rule_index, "Category"].values
                subcategory = self.model.rules.df.loc[rule_index, "Sub Category"].values
                self.assign(ledger_index, rule_index, keyword, category, subcategory)
            elif len(rule_index) > 1:
                memo = self.df.Memo[ledger_index]
                keyword1, keyword2 = keywords[rule_index[0]], keywords[rule_index[1]]
                print(f"{memo} is {keyword1} and {keyword2}!")
        return missing

    def assign(self, ledger_index, rule_index, keyword, category, subcategory):
        self.model.rules.df.loc[rule_index, "Count"] += 1
        old_keyword = self.df.loc[ledger_index, "Keyword"]
        if old_keyword != "None":
            old_ledger_index = np.where(self.model.rules.df.Keyword == old_keyword)[0]
            self.model.rules.df.loc[old_ledger_index, "Count"] -= 1
        self.df.loc[ledger_index, "Keyword"] = keyword
        self.df.loc[ledger_index, "Category"] = category
        self.df.loc[ledger_index, "Sub Category"] = subcategory

    def add_transactions(self, new_data):
        self.df = pd.concat([self.df, new_data])
        self.df.reset_index(drop=True, inplace=True)
        if not isinstance(self, DuplicateData):
            duplicate_indexes = self.df.duplicated(subset="ID", keep="first")
            duplicates = self.df[duplicate_indexes]
            self.model.duplicates.add_transactions(duplicates)
            self.df.drop(np.where(duplicate_indexes)[0], inplace=True)


class ImportData(LedgerData):
    def __init__(self, model, data=None, name="Import"):
        if data is None:
            data = self.empty_data()
        super().__init__(model, data, name)
        
    def import_transactions(self, file_name):
        def get_ID(year, month, day, memo, amount):
            dl = "|"
            if isinstance(year, int):
                ID = dl.join([str(year), str(month), str(day), memo, str(amount)])
            else:
                year, month, day, amount = (year.apply(str), month.apply(str),
                                            day.apply(str), amount.apply(str))
                ID = year + dl + month + dl + day + dl + memo + dl + amount
            return ID
        # Parse File
        with open(file_name) as file:
            for n, line in enumerate(file):
                if "" not in line.split(","):  # Find First Complete Line
                    break
            else:
                print(f"Could not Parse {file_name}.")
                return None
        # Read Data
        df = pd.read_csv(file_name, skiprows=n)
        # Extract Data
        labels = set(df.columns)
        for column in ["Trans. Date", "Transaction Date", "Date"]:
            if column in labels:
                date = pd.to_datetime(df[column])
                day = date.dt.day
                month = date.dt.month
                year = date.dt.year
                break
        memo = df["Description"].replace("[-,.*#&']", "", regex=True)  # RegEx
        df.fillna(0.0, inplace=True)  # Fill in Missing Zeros
        if "Credit" in labels:
            credit = df.Credit.replace(r"[$,]", "", regex=True).astype(float)
            debit = df.Debit.replace(r"[$,]", "", regex=True).astype(float)
            amount = credit - debit
        elif "Amount" in labels:
            amount = df.Amount.replace(r"[$,]", "", regex=True).astype(float)
        ID = get_ID(year, month, day, memo, amount)
        N = len(df)
        keyword = ["None"] * N
        category = ["None"] * N
        subcategory = ["None"] * N
        # New DataFrame
        data = zip(year, month, day, memo, amount, 
                   keyword, category, subcategory, ID)
        self.df = pd.DataFrame(data, columns=self.columns)
        self.auto_categorize()

    def accept_categorized(self):
        index = self.df.Category == "None"
        new_data = self.df[~index]
        self.model.ledger.add_transactions(new_data)
        self.df = self.df[index]
        self.df.reset_index(drop=True, inplace=True)


class DuplicateData(LedgerData):
    def __init__(self, model, data=None, name="Duplicates"):
        if data is None:
            data = self.empty_data()
        super().__init__(model, data, name)
        self.disabled = self.columns


class PlaceholderData(TransactionData):
    def __init__(self):
        values = []
        for value, column in zip(self.defaults, self.columns):
            if column == "Month":  # Set Months 1-12
                values.append(range(1, 13))
            else:
                values.append(12 * [value])
        data = dict(zip(self.columns, values))
        self.df = pd.DataFrame(data)


class SummaryTable:
    def __init__(self, model):
        self.model = model
        self.budget = model.budget
        self.ledger = model.ledger
        self.placeholder = PlaceholderData()
        self.table = pd.DataFrame()
        
    def summarize(self, start, stop):
        year = self.ledger.df.Year
        month = self.ledger.df.Month
        day = self.ledger.df.Day
        months = len(month.unique())
        num_days = Date(year, month, day).value
        start_days = Date(*start).value
        end_days = Date(*stop).value
        index = np.all([start_days <= num_days, num_days <= end_days], axis=0)
        table = self.ledger.df[index].copy()
        table = pd.concat([self.placeholder.df, table])
        table = pd.pivot_table(table, values="Amount", 
                               index="Category", columns="Month", aggfunc=sum)
        table = table.reindex(self.budget.df.Category)
        table.columns = Date.month_names
        table.fillna(0.0, inplace=True)
        sign = self.budget.df.Sign.tolist()
        table["Total"] = sign * table.sum(axis=1)
        table["Average"] = (table.Total / months).round(0)
        table["Budget"] = self.budget.df.Budget.tolist()
        table["Net"] = sign * (table["Average"] - table["Budget"])
        table["Sign"] = sign
        table.reset_index(drop=False, inplace=True)
        table = table.reindex(columns=self.budget.columns)
        return table
