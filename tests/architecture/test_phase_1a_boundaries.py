"""Architecture guardrails for the completed Phase 1 scope."""

import ast
from pathlib import Path

from nautolab.core import Action, Recipe


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "nautolab"


def test_domain_and_resources_do_not_import_gui_or_hardware_libraries() -> None:
    forbidden_prefixes = (
        "PyQt",
        "PySide",
        "serial",
        "pyvisa",
        "cv2",
        "pyrealsense",
    )
    for package_name in ("core", "resources", "workflow", "simulation", "safety"):
        for path in (SOURCE_ROOT / package_name).glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            assert not any(name.startswith(forbidden_prefixes) for name in imports), path


def test_action_and_recipe_have_no_execution_entrypoint() -> None:
    assert "execute" not in Action.__dict__
    assert "run" not in Action.__dict__
    assert "execute" not in Recipe.__dict__
    assert "run" not in Recipe.__dict__


def test_core_has_no_material_specific_class_names() -> None:
    forbidden = ("PerovskiteSample", "PerovskiteRecipe", "PerovskiteStationMap")
    core_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (SOURCE_ROOT / "core").glob("*.py")
    )
    assert all(name not in core_text for name in forbidden)


def test_runtime_layers_do_not_import_gui() -> None:
    for package_name in ("core", "resources", "workflow", "simulation", "safety", "application"):
        for path in (SOURCE_ROOT / package_name).glob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "nautolab.gui" not in source, path
            assert "PySide6" not in source, path


def test_parent_station_has_no_mutable_occupancy_state() -> None:
    station_source = (SOURCE_ROOT / "core" / "station.py").read_text(encoding="utf-8")
    assert "_occupant_ids" not in station_source
    assert "_add_occupant" not in station_source


def test_core_does_not_encode_gui_station_abbreviations() -> None:
    core_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (SOURCE_ROOT / "core").glob("*.py")
    )
    assert "HP01" not in core_text
    assert "SC01" not in core_text
    assert "ST01" not in core_text
