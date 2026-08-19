"""Package import smoke test."""


def test_import_nautolab() -> None:
    import nautolab

    assert nautolab.__version__ == "0.0.0"
