from __future__ import annotations

from pathlib import Path

from infrastructure.scenario.file_finder import ScenarioFileFinder


def test_file_finder_prefers_json(tmp_path: Path) -> None:
    base_dir = tmp_path / "scenarios"
    base_dir.mkdir()
    (base_dir / "sample.yaml").write_text("meta: {}", encoding="utf-8")
    (base_dir / "sample.json").write_text("{}", encoding="utf-8")

    finder = ScenarioFileFinder(base_dir)

    found = finder.find_by_id("sample")

    assert found is not None
    assert found.suffix == ".json"


def test_file_finder_uses_yaml_when_no_json(tmp_path: Path) -> None:
    base_dir = tmp_path / "scenarios"
    base_dir.mkdir()
    (base_dir / "sample.yaml").write_text("meta: {}", encoding="utf-8")

    finder = ScenarioFileFinder(base_dir)

    found = finder.find_by_id("sample")

    assert found is not None
    assert found.suffix == ".yaml"
