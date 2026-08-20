"""Phase 0 repository contract tests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_critical_directories_exist() -> None:
    required = [
        "src/nautolab",
        "tests/unit",
        "tests/integration",
        "tests/architecture",
        "tests/gui",
        "config",
        "docs/adr",
        "scripts",
    ]

    for relative_path in required:
        assert (ROOT / relative_path).is_dir(), relative_path


def test_critical_documents_exist() -> None:
    required = [
        "README.md",
        "ARCHITECTURE.md",
        "OPEN_ITEMS.md",
        "docs/REFERENCE_ARCHITECTURE.md",
        "docs/V1_REFERENCE_MAP.md",
        "docs/ROADMAP.md",
        "docs/CAPABILITY_MATRIX.md",
        "docs/DEVELOPMENT_RULES.md",
        "docs/BACKUP_STRATEGY.md",
        "docs/adr/0001-general-purpose-lab-platform.md",
        "docs/adr/0002-device-backend-separation.md",
        "docs/adr/0003-workflow-resource-orchestration.md",
        "docs/adr/0004-gui-separated-from-core.md",
        "docs/adr/0005-simulation-before-real-hardware.md",
        "docs/adr/0006-canonical-location-and-occupancy-state.md",
        "docs/adr/0007-station-instance-and-slot-resource-hierarchy.md",
    ]

    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path
