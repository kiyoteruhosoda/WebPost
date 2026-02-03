from __future__ import annotations

import json

from infrastructure.logging.console_logger import ConsoleLogger


def test_console_logger_emits_type_field(capsys) -> None:
    logger = ConsoleLogger()

    logger.info("step.start", step_id="s1")

    captured = capsys.readouterr()
    line = captured.out.strip()

    assert line.startswith("step.start ")
    payload = json.loads(line.replace("step.start ", "", 1))
    assert payload["type"] == "step.start"
    assert payload["step_id"] == "s1"
