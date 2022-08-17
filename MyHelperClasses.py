import numpy as np


class Colors:
    colors = ("blue", "green", "orange", "red", "black", "cyan",
              "purple", "pink", "yellow", "magenta", "grey")


class Date:
    month_data = {"Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
                  "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}
    month_names = list(month_data.keys())
    month_days = np.array(list(month_data.values()))
    month_cumulative_days = np.array([0, *month_days[:-1].cumsum()])

    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
        self.value = self.days_from_start()
    
    def days_from_start(self):
        return 365 * (self.year - 2020) + self.month_cumulative_days[self.month-1] + self.day


if __name__ == "__main__":
    d = Date(2020, 12, 31)