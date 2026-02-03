from __future__ import annotations

from pathlib import Path

from infrastructure.scenario.file_finder import ScenarioFileFinder
from infrastructure.scenario.yaml_loader import YamlScenarioLoader
from domain.steps.http import HttpStep
from domain.steps.result import ResultStep


def test_find_yaml_scenario_file(tmp_path: Path) -> None:
    base_dir = tmp_path / "scenarios"
    base_dir.mkdir()
    scenario_path = base_dir / "sample.yaml"
    scenario_path.write_text("meta: {id: 1, name: sample, version: 1}\nsteps: []\n", encoding="utf-8")

    finder = ScenarioFileFinder(base_dir)

    assert finder.find_by_id("sample") == scenario_path


def test_find_yml_scenario_file(tmp_path: Path) -> None:
    base_dir = tmp_path / "scenarios"
    nested_dir = base_dir / "nested"
    nested_dir.mkdir(parents=True)
    scenario_path = nested_dir / "sample.yml"
    scenario_path.write_text("meta: {id: 1, name: sample, version: 1}\nsteps: []\n", encoding="utf-8")

    finder = ScenarioFileFinder(base_dir)

    assert finder.find_by_id("sample") == scenario_path


def test_find_json_scenario_file(tmp_path: Path) -> None:
    base_dir = tmp_path / "scenarios"
    base_dir.mkdir()
    scenario_path = base_dir / "sample.json"
    scenario_path.write_text('{"meta": {"id": 1, "name": "sample", "version": 1}, "steps": []}', encoding="utf-8")

    finder = ScenarioFileFinder(base_dir)

    assert finder.find_by_id("sample") == scenario_path


def test_yaml_loader_parses_steps(tmp_path: Path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
meta:
  id: 1
  name: sample
  version: 2
defaults:
  http:
    base_url: https://example.com
steps:
  - id: request
    type: http
    request:
      method: POST
      url: /submit
      form_list:
        - [foo, bar]
  - id: done
    type: result
    fields:
      status: ok
""".lstrip(),
        encoding="utf-8",
    )

    loader = YamlScenarioLoader()
    scenario = loader.load_from_file(str(scenario_path))

    assert scenario.meta.name == "sample"
    assert scenario.meta.version == 2
    assert scenario.defaults.http is not None
    assert scenario.defaults.http.base_url == "https://example.com"
    assert len(scenario.steps) == 2
    assert isinstance(scenario.steps[0], HttpStep)
    assert scenario.steps[0].request.form_list == [("foo", "bar")]
    assert isinstance(scenario.steps[1], ResultStep)
