import pytest

from specklepy.bundle.parquet_table_reader import find_files, find_table, read_table
from specklepy.bundle.parquet_table_writer import ParquetTableWriter, schema_of
from specklepy.bundle.spec import BY_TABLE


def test_read_table_spans_row_groups(tmp_path):
    path = str(tmp_path / "fx.eav.paths.parquet")
    with ParquetTableWriter(path, schema_of(BY_TABLE["paths"]), flush_rows=2) as w:
        for i in range(5):
            w.add_row(i, f"p{i}")
    table = read_table(path)
    assert table.row_count == 5
    assert table.ints("path_index") == [0, 1, 2, 3, 4]
    assert table.strings("path") == ["p0", "p1", "p2", "p3", "p4"]
    assert table.has("path") and not table.has("nope")


def test_nullable_columns(tmp_path):
    path = str(tmp_path / "fx.envelope.relations.parquet")
    with ParquetTableWriter(path, schema_of(BY_TABLE["relations"])) as w:
        w.add_row(1, 0, 0, None)
        w.add_row(1, 0, 1, 7)
    table = read_table(path)
    assert table.ints("ord") == [0, 7]
    assert table.nullable_ints("ord") == [None, 7]


def test_find_table_by_suffix(tmp_path):
    path = str(tmp_path / "anything.eav.paths.parquet")
    with ParquetTableWriter(path, schema_of(BY_TABLE["paths"])) as w:
        w.add_row(0, "p")
    assert find_table(str(tmp_path), ".eav.paths.parquet", required=True) is not None
    assert find_table(str(tmp_path), ".eav.model.parquet", required=False) is None
    with pytest.raises(FileNotFoundError):
        find_table(str(tmp_path), ".eav.model.parquet", required=True)
    assert find_files(str(tmp_path), "*.geometries*.parquet") == []
