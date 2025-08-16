import pandas as pd


class Process_data:

    def __init__(self, data):
        self.data = pd.read_csv(data)

    def get_df(self):
        return self.data

    def get_columns(self):
        return self.data.columns.to_list()

    def get_bar_data(self):
        return self.data

    def get_mean(self, col_name):
        series = self._coerce_to_numeric(self.data[col_name])
        if series.notna().sum() == 0:
            return None
        return float(series.mean())

    def describe_data(self):
        return self.data.describe()

    def get_numeric_columns(self):
        numeric_columns = []
        for column_name in self.data.columns:
            series = self._coerce_to_numeric(self.data[column_name])
            if series.notna().sum() > 0:
                numeric_columns.append(column_name)
        return numeric_columns

    def _coerce_to_numeric(self, series: pd.Series) -> pd.Series:
        # If already numeric dtype, return as-is
        if pd.api.types.is_numeric_dtype(series):
            return series
        s = series.astype(str).str.strip()
        # Handle parentheses negatives: (123) => -123
        s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
        # Remove common non-numeric chars (currency, spaces, commas, percent)
        s = s.str.replace('$', '', regex=False)
        s = s.str.replace('₹', '', regex=False)
        s = s.str.replace(',', '', regex=False)
        s = s.str.replace('%', '', regex=False)
        # Keep digits, minus, and dot; others -> remove
        s = s.str.replace(r"[^0-9\.-]", '', regex=True)
        cleaned = pd.to_numeric(s, errors='coerce')
        return cleaned