"""End-to-end tests for CLI commands."""
import pytest
from click.testing import CliRunner
import gnome_activities.core.storage as storage
from gnome_activities.cli.main import cli


@pytest.fixture
def runner(tmp_path, monkeypatch):
    """CLI runner with isolated config dir."""
    monkeypatch.setattr(storage, "CONFIG_DIR", tmp_path / "gnome-activities")
    monkeypatch.setattr(storage, "ACTIVITIES_FILE", storage.CONFIG_DIR / "activities.json")
    monkeypatch.setattr(storage, "CONFIG_FILE", storage.CONFIG_DIR / "config.json")
    return CliRunner()


def test_list_empty(runner):
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No activities" in result.output


def test_create_activity(runner):
    result = runner.invoke(cli, ["create", "work", "--description", "Work tasks"])
    assert result.exit_code == 0
    assert "Created activity 'work'" in result.output


def test_create_and_list(runner):
    runner.invoke(cli, ["create", "work"])
    runner.invoke(cli, ["create", "play"])
    result = runner.invoke(cli, ["list"])
    assert "work" in result.output
    assert "play" in result.output


def test_activate_activity(runner):
    runner.invoke(cli, ["create", "work"])
    result = runner.invoke(cli, ["activate", "work"])
    assert result.exit_code == 0
    assert "Activated" in result.output


def test_current_after_activate(runner):
    runner.invoke(cli, ["create", "work"])
    runner.invoke(cli, ["activate", "work"])
    result = runner.invoke(cli, ["current"])
    assert "work" in result.output


def test_delete_activity(runner):
    runner.invoke(cli, ["create", "work"])
    result = runner.invoke(cli, ["delete", "work"])
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_create_invalid_name(runner):
    result = runner.invoke(cli, ["create", "../hack"])
    assert result.exit_code != 0


def test_delete_nonexistent(runner):
    result = runner.invoke(cli, ["delete", "nonexistent"])
    assert result.exit_code != 0


def test_status_command(runner):
    runner.invoke(cli, ["create", "work"])
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Activities" in result.output


def test_always_add_remove(runner):
    result = runner.invoke(cli, ["always", "add", "thunderbird"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["always", "list"])
    assert "thunderbird" in result.output
    runner.invoke(cli, ["always", "remove", "thunderbird"])
    result = runner.invoke(cli, ["always", "list"])
    assert "No always-available" in result.output


def test_modify_activity(runner):
    runner.invoke(cli, ["create", "work", "--description", "Old desc"])
    result = runner.invoke(cli, ["modify", "work", "--description", "New desc"])
    assert result.exit_code == 0
