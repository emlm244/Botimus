from data.lookup_table import LookupTable


def test_find_index_includes_last_value():
    column = [0.0, 1.0, 2.0]
    assert LookupTable.find_index(column, 2.0) == 2
    assert LookupTable.find_index(column, 99.0) == 2


def test_get_rows_reads_csv_data():
    table = LookupTable("acceleration/boost.csv")
    rows = table.get_rows()
    assert rows
    assert "time" in rows[0]
