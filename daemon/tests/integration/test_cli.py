"""Integration tests for the CLI using Click's CliRunner."""
import json
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from gnome_activities.cli import cli
from gnome_activities.storage import Storage


def make_runner_and_invoke(tmp_path, args, catch_exceptions=False):
    """Helper to invoke CLI with a temp storage path."""
    runner = CliRunner()
    state_path = tmp_path / "state.json"
    env = {}
    result = runner.invoke(
        cli,
        args,
        obj={"storage_path": state_path},
        catch_exceptions=catch_exceptions,
    )
    return result


def test_list_shows_empty_initially(tmp_path):
    result = make_runner_and_invoke(tmp_path, ["list"])
    assert result.exit_code == 0
    assert "No activities" in result.output


def test_add_command_creates_activity(tmp_path):
    result = make_runner_and_invoke(tmp_path, ["add", "Work"])
    assert result.exit_code == 0
    assert "Work" in result.output

    result2 = make_runner_and_invoke(tmp_path, ["list"])
    assert "Work" in result2.output


def test_add_duplicate_shows_error(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    result = make_runner_and_invoke(tmp_path, ["add", "Work"])
    assert result.exit_code != 0
    assert "Error" in result.output or "already exists" in result.output


def test_remove_command_removes_activity(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    result = make_runner_and_invoke(tmp_path, ["remove", "Work"])
    assert result.exit_code == 0

    result2 = make_runner_and_invoke(tmp_path, ["list"])
    assert "Work" not in result2.output


def test_rename_command_renames(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    result = make_runner_and_invoke(tmp_path, ["rename", "Work", "NewWork"])
    assert result.exit_code == 0
    assert "NewWork" in result.output

    result2 = make_runner_and_invoke(tmp_path, ["list"])
    assert "NewWork" in result2.output
    assert "Work" not in result2.output or "NewWork" in result2.output


def test_status_shows_no_active_activity(tmp_path):
    result = make_runner_and_invoke(tmp_path, ["status"])
    assert result.exit_code == 0
    assert "No active activity" in result.output


def test_activate_activates_activity(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    with patch("gnome_activities.activity_manager.app_launcher") as mock_launcher:
        mock_launcher.launch_app.return_value = True
        mock_launcher.close_app.return_value = True
        result = make_runner_and_invoke(tmp_path, ["activate", "Work"])
    assert result.exit_code == 0
    assert "Work" in result.output

    result2 = make_runner_and_invoke(tmp_path, ["status"])
    assert "Work" in result2.output


def test_app_add_subcommand(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    result = make_runner_and_invoke(tmp_path, ["app", "add", "Work", "firefox", "firefox"])
    assert result.exit_code == 0
    assert "firefox" in result.output


def test_app_remove_subcommand(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    make_runner_and_invoke(tmp_path, ["app", "add", "Work", "firefox", "firefox"])
    result = make_runner_and_invoke(tmp_path, ["app", "remove", "Work", "firefox"])
    assert result.exit_code == 0


def test_app_list_subcommand(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    make_runner_and_invoke(tmp_path, ["app", "add", "Work", "firefox", "firefox"])
    result = make_runner_and_invoke(tmp_path, ["app", "list", "Work"])
    assert result.exit_code == 0
    assert "firefox" in result.output


def test_app_add_with_files_and_global_flag(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    result = make_runner_and_invoke(
        tmp_path,
        ["app", "add", "Work", "gedit", "gedit", "--file", "/home/user/doc.txt", "--global"]
    )
    assert result.exit_code == 0


def test_app_list_shows_no_apps_if_empty(tmp_path):
    make_runner_and_invoke(tmp_path, ["add", "Work"])
    result = make_runner_and_invoke(tmp_path, ["app", "list", "Work"])
    assert result.exit_code == 0
    assert "No apps" in result.output
