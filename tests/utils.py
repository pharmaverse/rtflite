import polars as pl


class TestData:
    """Data for testing."""

    @staticmethod
    def df1():
        data = {
            "Column1": ["Data 1.1", "Data 2.1"],
            "Column2": ["Data 1.2", "Data 2.2"],
        }
        return pl.DataFrame(data)
