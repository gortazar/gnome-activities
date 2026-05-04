"""Command-line interface for GNOME Activities Manager."""
from __future__ import annotations
import sys

import click

from gnome_activities.core.manager import ActivityManager, ActivityError


def _get_manager() -> ActivityManager:
    return ActivityManager()


@click.group()
@click.version_option()
def cli():
    """GNOME Activities Manager - KDE-like activities for GNOME."""


@cli.command("list")
def list_activities():
    """List all activities."""
    manager = _get_manager()
    activities = manager.list_activities()
    if not activities:
        click.echo("No activities defined.")
        return
    for act in activities:
        marker = "* " if act.is_active else "  "
        desc = f" - {act.description}" if act.description else ""
        click.echo(f"{marker}{act.name}{desc}")


@cli.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Activity description")
def create_activity(name, description):
    """Create a new activity."""
    manager = _get_manager()
    try:
        act = manager.create(name, description)
        click.echo(f"Created activity '{act.name}'.")
    except (ActivityError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("delete")
@click.argument("name")
def delete_activity(name):
    """Delete an activity."""
    manager = _get_manager()
    try:
        manager.delete(name)
        click.echo(f"Deleted activity '{name}'.")
    except (ActivityError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("activate")
@click.argument("name")
def activate_activity(name):
    """Activate an activity (switch to it)."""
    manager = _get_manager()
    try:
        act = manager.activate(name)
        click.echo(f"Activated activity '{act.name}'.")
    except (ActivityError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("modify")
@click.argument("name")
@click.option("--description", "-d", required=True, help="New description")
def modify_activity(name, description):
    """Modify an activity."""
    manager = _get_manager()
    try:
        act = manager.modify(name, description=description)
        click.echo(f"Modified activity '{act.name}'.")
    except (ActivityError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("current")
def current_activity():
    """Show the currently active activity."""
    manager = _get_manager()
    act = manager.get_current()
    if act:
        click.echo(f"Current activity: {act.name}")
        if act.description:
            click.echo(f"  Description: {act.description}")
        click.echo(f"  Apps tracked: {len(act.apps)}")
    else:
        click.echo("No activity is currently active.")


@cli.command("status")
def status():
    """Show overall status."""
    manager = _get_manager()
    activities = manager.list_activities()
    current = manager.get_current()
    always = manager.get_always_available_apps()
    click.echo(f"Activities: {len(activities)}")
    click.echo(f"Active: {current.name if current else 'none'}")
    if always:
        click.echo(f"Always-available apps: {', '.join(always)}")


@cli.group("always")
def always_group():
    """Manage always-available apps."""


@always_group.command("add")
@click.argument("app_id")
def always_add(app_id):
    """Mark an app as always available across all activities."""
    manager = _get_manager()
    manager.add_always_available_app(app_id)
    click.echo(f"Added '{app_id}' to always-available apps.")


@always_group.command("remove")
@click.argument("app_id")
def always_remove(app_id):
    """Remove an app from always-available list."""
    manager = _get_manager()
    manager.remove_always_available_app(app_id)
    click.echo(f"Removed '{app_id}' from always-available apps.")


@always_group.command("list")
def always_list():
    """List always-available apps."""
    manager = _get_manager()
    apps = manager.get_always_available_apps()
    if apps:
        for app in apps:
            click.echo(f"  {app}")
    else:
        click.echo("No always-available apps configured.")


@cli.command("daemon")
@click.option("--start", "action", flag_value="start", default=True)
@click.option("--stop", "action", flag_value="stop")
@click.option("--status", "action", flag_value="status")
def daemon_cmd(action):
    """Manage the background daemon."""
    if action == "start":
        try:
            from gnome_activities.daemon.service import run_service
            click.echo("Starting GNOME Activities daemon...")
            run_service()
        except SystemExit:
            pass
        except Exception as e:
            click.echo(f"Error starting daemon: {e}", err=True)
            sys.exit(1)
    elif action == "stop":
        click.echo("Stop daemon: use systemctl --user stop gnome-activities.")
    elif action == "status":
        click.echo("Daemon status check not yet implemented.")


def main():
    cli()


if __name__ == "__main__":
    main()
