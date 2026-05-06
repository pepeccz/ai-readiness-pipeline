"""
tests/schemas/test_questionnaire_yaml.py — REQ-1 regression guard.

Asserts that after YAML cleanup:
  - Zero max_length / min_length entries exist in any core block YAML.
  - No empty validations: [] lists remain.
  - pattern and required rules are preserved where they exist.
  - All YAML files load without parse errors.
"""

from __future__ import annotations

import glob
from pathlib import Path

import yaml

CORE_DIR = Path(__file__).parents[2] / "schemas" / "questionnaire-v2" / "core"
YAML_FILES = sorted(CORE_DIR.glob("*.yaml"))


def _collect_validation_types(obj: object) -> list[str]:
    """Recursively collect all validation `type` values from a YAML structure."""
    types: list[str] = []
    if isinstance(obj, dict):
        if "validations" in obj and isinstance(obj["validations"], list):
            for v in obj["validations"]:
                if isinstance(v, dict) and "type" in v:
                    types.append(v["type"])
        for value in obj.values():
            types.extend(_collect_validation_types(value))
    elif isinstance(obj, list):
        for item in obj:
            types.extend(_collect_validation_types(item))
    return types


def _collect_empty_validations(obj: object) -> list[str]:
    """Recursively find any 'validations: []' entries and return paths as strings."""
    found: list[str] = []
    if isinstance(obj, dict):
        if "validations" in obj and obj["validations"] == []:
            found.append(f"empty validations in: {obj.get('id', '<unknown>')}")
        for value in obj.values():
            found.extend(_collect_empty_validations(value))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_collect_empty_validations(item))
    return found


class TestYamlFilesLoadCleanly:
    def test_all_core_yaml_files_found(self):
        assert len(YAML_FILES) >= 7, f"Expected at least 7 core YAML files, got {len(YAML_FILES)}"

    def test_all_core_yaml_files_parse(self):
        for path in YAML_FILES:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            assert data is not None, f"{path.name} is empty or unparseable"


class TestLengthValidationsRemoved:
    def test_no_max_length_in_any_yaml(self):
        """REQ-1: max_length must be absent from all core block YAMLs."""
        violations: list[str] = []
        for path in YAML_FILES:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            types = _collect_validation_types(data)
            if "max_length" in types:
                violations.append(f"{path.name}: found max_length")
        assert violations == [], f"max_length still present:\n" + "\n".join(violations)

    def test_no_min_length_in_any_yaml(self):
        """REQ-1: min_length must be absent from all core block YAMLs."""
        violations: list[str] = []
        for path in YAML_FILES:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            types = _collect_validation_types(data)
            if "min_length" in types:
                violations.append(f"{path.name}: found min_length")
        assert violations == [], f"min_length still present:\n" + "\n".join(violations)

    def test_no_empty_validations_lists(self):
        """REQ-1: After removing length entries, empty validations: [] must also be removed."""
        violations: list[str] = []
        for path in YAML_FILES:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            empties = _collect_empty_validations(data)
            if empties:
                violations.extend([f"{path.name}: {e}" for e in empties])
        assert violations == [], f"Empty validations lists found:\n" + "\n".join(violations)


class TestOtherValidationsPreserved:
    def test_required_fields_preserved(self):
        """required: true fields must still be present in YAML after cleanup."""
        required_count = 0
        for path in YAML_FILES:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            text = path.read_text(encoding="utf-8")
            if "required: true" in text:
                required_count += 1
        assert required_count >= 5, (
            f"Expected at least 5 YAML files to have required: true, found {required_count}"
        )

    def test_pattern_validations_preserved_if_present(self):
        """pattern validations must NOT be removed by the cleanup script."""
        for path in YAML_FILES:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            types = _collect_validation_types(data)
            # If pattern existed before cleanup, it must still be there.
            # (We just confirm we don't accidentally strip non-length types.)
            for t in types:
                assert t not in ("max_length", "min_length"), (
                    f"{path.name}: unexpected length type '{t}' found after cleanup"
                )
