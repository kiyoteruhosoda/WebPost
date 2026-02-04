# tests/domain/test_ids.py
import pytest
from domain.ids import ScenarioId, RunId, ScenarioVersion, IdempotencyKey
from domain.exceptions import ValidationError


class TestScenarioId:
    def test_create_scenario_id(self):
        scenario_id = ScenarioId(value=1)
        assert scenario_id.value == 1

    def test_scenario_id_frozen(self):
        scenario_id = ScenarioId(value=1)
        with pytest.raises(Exception):  # FrozenInstanceError
            scenario_id.value = 2

    def test_scenario_id_equality(self):
        scenario_id1 = ScenarioId(value=1)
        scenario_id2 = ScenarioId(value=1)
        scenario_id3 = ScenarioId(value=2)
        assert scenario_id1 == scenario_id2
        assert scenario_id1 != scenario_id3

    def test_scenario_id_hashable(self):
        scenario_id1 = ScenarioId(value=1)
        scenario_id2 = ScenarioId(value=1)
        id_set = {scenario_id1, scenario_id2}
        assert len(id_set) == 1


class TestRunId:
    def test_create_run_id(self):
        run_id = RunId(value="run-123")
        assert run_id.value == "run-123"

    def test_run_id_frozen(self):
        run_id = RunId(value="run-123")
        with pytest.raises(Exception):  # FrozenInstanceError
            run_id.value = "run-456"

    def test_run_id_equality(self):
        run_id1 = RunId(value="run-123")
        run_id2 = RunId(value="run-123")
        run_id3 = RunId(value="run-456")
        assert run_id1 == run_id2
        assert run_id1 != run_id3

    def test_run_id_hashable(self):
        run_id1 = RunId(value="run-123")
        run_id2 = RunId(value="run-123")
        id_set = {run_id1, run_id2}
        assert len(id_set) == 1


class TestScenarioVersion:
    def test_create_scenario_version(self):
        version = ScenarioVersion(value=1)
        assert version.value == 1

    def test_scenario_version_frozen(self):
        version = ScenarioVersion(value=1)
        with pytest.raises(Exception):  # FrozenInstanceError
            version.value = 2

    def test_scenario_version_equality(self):
        version1 = ScenarioVersion(value=1)
        version2 = ScenarioVersion(value=1)
        version3 = ScenarioVersion(value=2)
        assert version1 == version2
        assert version1 != version3

    def test_scenario_version_hashable(self):
        version1 = ScenarioVersion(value=1)
        version2 = ScenarioVersion(value=1)
        version_set = {version1, version2}
        assert len(version_set) == 1


class TestIdempotencyKey:
    def test_create_idempotency_key(self):
        key = IdempotencyKey(value="key-123")
        assert key.value == "key-123"

    def test_idempotency_key_empty_raises(self):
        with pytest.raises(ValidationError):
            IdempotencyKey(value=" ")
