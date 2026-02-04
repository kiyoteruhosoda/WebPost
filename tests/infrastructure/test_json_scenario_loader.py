from __future__ import annotations

from pathlib import Path

from infrastructure.scenario.json_loader import JsonScenarioLoader
from domain.steps.http import HttpStep
from domain.steps.result import ResultStep
from domain.steps.log import LogStep
from domain.steps.scrape import ScrapeStep


def test_json_loader_parses_steps(tmp_path: Path) -> None:
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(
        """
{
  "meta": {
    "id": 1,
    "name": "sample",
    "version": 2
  },
  "defaults": {
    "http": {
      "base_url": "https://example.com"
    }
  },
  "steps": [
    {
      "id": "request",
      "type": "http",
      "request": {
        "method": "POST",
        "url": "/submit",
        "form_list": [["foo", "bar"]]
      }
    },
    {
      "id": "done",
      "type": "result",
      "fields": {
        "status": "ok"
      }
    },
    {
      "id": "scrape_step",
      "type": "scrape",
      "command": "css",
      "selector": ".value",
      "save_as": "result",
      "save_to": "state",
      "source": "last.text"
    },
    {
      "id": "log_step",
      "type": "log",
      "message": "log ${vars.foo}"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    loader = JsonScenarioLoader()

    scenario = loader.load_from_file(str(scenario_path))

    assert scenario.meta.name == "sample"
    assert scenario.meta.version == 2
    assert scenario.defaults.http is not None
    assert scenario.defaults.http.base_url == "https://example.com"
    assert len(scenario.steps) == 4
    assert isinstance(scenario.steps[0], HttpStep)
    assert scenario.steps[0].request.form_list == [("foo", "bar")]
    assert isinstance(scenario.steps[1], ResultStep)
    assert isinstance(scenario.steps[2], ScrapeStep)
    assert scenario.steps[2].save_to == "state"
    assert scenario.steps[2].source == "last.text"
    assert isinstance(scenario.steps[3], LogStep)
