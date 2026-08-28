import pyarrow as pa
import pytest

from specklepy.bundle.parquet_table_reader import ParquetTable
from specklepy.bundle.property_table import PropertyTable


def _paths(*names: str) -> ParquetTable:
    return ParquetTable(
        pa.table({"path_index": list(range(len(names))), "path": list(names)})
    )


def _eav(rows: list[tuple]) -> ParquetTable:
    cols = list(zip(*rows, strict=True)) if rows else [[], [], [], [], []]
    return ParquetTable(
        pa.table(
            {
                "object_index": pa.array(cols[0], pa.int32()),
                "path_index": pa.array(cols[1], pa.int32()),
                "value_string": pa.array(cols[2], pa.string()),
                "value_double": pa.array(cols[3], pa.float64()),
                "value_boolean": pa.array(cols[4], pa.bool_()),
            }
        )
    )


PATHS = _paths(
    "name",
    "units",
    "properties.Constraints.Base Offset",
    "properties.Identity Data.Mark",
    "properties.Flag",
    "",
)


@pytest.fixture
def table() -> PropertyTable:
    eav = _eav(
        [
            (1, 3, "W-02", None, None),
            (0, 0, "Basic Wall", None, None),
            (0, 2, None, 0.5, None),
            (0, 3, "W-01", None, None),
            (0, 4, None, None, True),
            (0, 1, "m", None, None),
            (2, 2, None, None, None),  # no value → dropped
            (2, 5, "x", None, None),  # empty path → dropped
            (2, 99, "x", None, None),  # unknown path → dropped
        ]
    )
    return PropertyTable.load(eav, PATHS, "object_index")


def test_load_filters_and_sorts_by_key(table):
    assert table.row_count == 6
    assert table.keys == [0, 1]
    assert not table.contains(2)
    assert table.paths == [p for p in PATHS.strings("path") if p]


def test_typed_lookups_coalesce_bool_double_string(table):
    assert table.try_get(0, "properties.Flag") == (True, True)
    assert table.try_get(0, "properties.Constraints.Base Offset") == (True, 0.5)
    assert table.try_get(0, "name") == (True, "Basic Wall")
    assert table.try_get(0, "nope") == (False, None)
    assert table.get_double(0, "properties.Identity Data.Mark") is None
    assert table.get_string(0, "properties.Identity Data.Mark") == "W-01"


def test_views_strip_prefix_and_compose(table):
    props = table.under(0, "properties")
    assert dict(props) == {
        "Constraints.Base Offset": 0.5,
        "Identity Data.Mark": "W-01",
        "Flag": True,
    }
    assert len(props) == 3 and "Flag" in props and "name" not in props
    assert props.under("Constraints")["Base Offset"] == 0.5
    assert props.under("Constraints").prefix == "properties.Constraints"
    with pytest.raises(KeyError):
        props["missing"]
    assert dict(table.view(0)) == {
        "name": "Basic Wall",
        "properties.Constraints.Base Offset": 0.5,
        "properties.Identity Data.Mark": "W-01",
        "properties.Flag": True,
        "units": "m",
    }
    assert len(table.view(42)) == 0


def test_to_nested(table):
    assert table.under(0, "properties").to_nested() == {
        "Constraints": {"Base Offset": 0.5},
        "Identity Data": {"Mark": "W-01"},
        "Flag": True,
    }


def test_column_scans(table):
    assert list(table.keys_with("properties.Identity Data.Mark")) == [0, 1]
    assert list(table.values_of("properties.Identity Data.Mark")) == [
        (0, "W-01"),
        (1, "W-02"),
    ]
    assert list(table.keys_with("unknown")) == []


def test_missing_eav_gives_path_only_table():
    table = PropertyTable.load(None, PATHS, "object_index")
    assert table.row_count == 0 and table.path_id("name") == 0
