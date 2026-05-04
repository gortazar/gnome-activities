"""CLI for gnome-activities."""
import logging
import sys

import click

from .activity_manager import ActivityManager
from .storage import Storage

logging.basicConfig(level=logging.WARNING)


def _get_manager(ctx) -> ActivityManager:
    storage_path = ctx.obj.get("storage_path") if ctx.obj else None
    return ActivityManager(Storage(storage_path) if storage_path else Storage())


@click.group()
@click.pass_context
def cli(ctx):
    """GNOME Activities - KDE-like activities manager for GNOME."""
    ctx.ensure_object(dict)


@cli.command("list")
@click.pass_context
def list_activities(ctx):
    """List all activities."""
    manager = _get_manager(ctx)
    activities = manager.list_activities()
    if not activities:
        click.echo("No activities found.")
        return
    for a in activities:
        active_marker = " [ACTIVE]" if a.is_active else ""
        click.echo(f"  {a.name}{active_marker}")


@cli.command("add")
@click.argument("name")
@click.pass_context
def add_activity(ctx, name):
    """Add a new activity."""
    manager = _get_manager(ctx)
    try:
        activity = manager.add_activity(name)
        click.echo(f"Created activity '{activity.name}'.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("remove")
@click.argument("name")
@click.pass_context
def remove_activity(ctx, name):
    """Remove an activity."""
    manager = _get_manager(ctx)
    try:
        manager.remove_activity(name)
        click.echo(f"Removed activity '{name}'.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("rename")
@click.argument("old_name")
@click.argument("new_name")
@click.pass_context
def rename_activity(ctx, old_name, new_name):
    """Rename an activity."""
    manager = _get_manager(ctx)
    try:
        activity = manager.rename_activity(old_name, new_name)
        click.echo(f"Renamed activity '{old_name}' to '{activity.name}'.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("activate")
@click.argument("name")
@click.pass_context
def activate_activity(ctx, name):
    """Activate an activity (switches to it)."""
    manager = _get_manager(ctx)
    try:
        activity = manager.activate_activity(name)
        click.echo(f"Activated activity '{activity.name}'.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("status")
@click.pass_context
def status(ctx):
    """Show the currently active activity."""
    manager = _get_manager(ctx)
    active = manager.get_active_activity()
    if active:
        click.echo(f"Active activity: {active.name}")
        if active.apps:
            click.echo("  Apps:")
            for app in active.apps:
                global_tag = " [global]" if app.is_global else ""
                click.echo(f"    {app.app_id}{global_tag}: {app.exec_cmd}")
    else:
        click.echo("No active activity.")


@cli.group("app")
def app_group():
    """Manage apps within activities."""
    pass


@app_group.command("add")
@click.argument("activity")
@click.argument("app_id")
@click.argument("exec_cmd")
@click.option("--file", "files", multiple=True, help="Files to open with the app.")
@click.option("--global", "is_global", is_flag=True, default=False,
              help="Mark app as global (not closed when switching activities).")
@click.pass_context
def app_add(ctx, activity, app_id, exec_cmd, files, is_global):
    """Add an app to an activity."""
    manager = _get_manager(ctx)
    try:
        app = manager.add_app_to_activity(activity, app_id, exec_cmd, list(files), is_global)
        click.echo(f"Added app '{app.app_id}' to activity '{activity}'.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app_group.command("remove")
@click.argument("activity")
@click.argument("app_id")
@click.pass_context
def app_remove(ctx, activity, app_id):
    """Remove an app from an activity."""
    manager = _get_manager(ctx)
    try:
        manager.remove_app_from_activity(activity, app_id)
        click.echo(f"Removed app '{app_id}' from activity '{activity}'.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app_group.command("list")
@click.argument("activity")
@click.pass_context
def app_list(ctx, activity):
    """List apps in an activity."""
    manager = _get_manager(ctx)
    activities = manager.list_activities()
    target = next((a for a in activities if a.name == activity), None)
    if target is None:
        click.echo(f"Error: Activity '{activity}' not found.", err=True)
        sys.exit(1)
    if not target.apps:
        click.echo(f"No apps in activity '{activity}'.")
        return
    click.echo(f"Apps in '{activity}':")
    for app in target.apps:
        global_tag = " [global]" if app.is_global else ""
        files_tag = f" files={app.files}" if app.files else ""
        click.echo(f"  {app.app_id}{global_tag}: {app.exec_cmd}{files_tag}")


@cli.command("daemon")
def daemon():
    """Start the D-Bus daemon."""
    from .dbus_service import run_service
    run_service()


if __name__ == "__main__":
    cli()
