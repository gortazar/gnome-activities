"""D-Bus service for GNOME Activities daemon."""

from __future__ import annotations

import json
import logging
import sys

try:
    import dbus
    import dbus.service
    import dbus.mainloop.glib
    from gi.repository import GLib

    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False

from gnome_activities.core.manager import ActivityManager, ActivityError

logger = logging.getLogger(__name__)

DBUS_BUS_NAME = "org.gnome.Activities"
DBUS_OBJECT_PATH = "/org/gnome/Activities"
DBUS_INTERFACE = "org.gnome.Activities"


if DBUS_AVAILABLE:

    class ActivitiesService(dbus.service.Object):
        """D-Bus service exposing activities management.

        Method names are kept consistent with the GNOME Shell extension so the
        extension can talk to this daemon without any adaptation layer.
        """

        def __init__(self, bus, manager: ActivityManager):
            super().__init__(bus, DBUS_OBJECT_PATH)
            self._manager = manager

        # ── Activity CRUD ─────────────────────────────────────────────────────

        @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
        def ListActivities(self):
            acts = self._manager.list_activities()
            return json.dumps([a.to_dict() for a in acts])

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def AddActivity(self, name: str):
            try:
                act = self._manager.create(str(name))
                return json.dumps({"status": "ok", "activity": act.to_dict()})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="ss", out_signature="s")
        def RenameActivity(self, old_name: str, new_name: str):
            try:
                act = self._manager.rename(str(old_name), str(new_name))
                if act.is_active:
                    self.ActivityChanged(act.name)
                return json.dumps({"status": "ok", "activity": act.to_dict()})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def ActivateActivity(self, name: str):
            try:
                act = self._manager.activate(str(name))
                self.ActivityChanged(act.name)
                return json.dumps({"status": "ok", "activity": act.to_dict()})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
        def GetActiveActivity(self):
            act = self._manager.get_current()
            if act:
                return json.dumps(act.to_dict())
            return json.dumps(None)

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def RemoveActivity(self, name: str):
            try:
                self._manager.delete(str(name))
                return json.dumps({"status": "ok"})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        # ── App tracking (called by the GNOME Shell extension) ─────────────────

        @dbus.service.method(DBUS_INTERFACE, in_signature="ssas", out_signature="")
        def TrackAppOpened(self, app_id: str, exec_cmd: str, files):
            """Record that an app was opened in the current activity."""
            current = self._manager.get_current()
            if not current:
                return
            from gnome_activities.core.activity import AppState

            apps = list(current.apps)
            for app in apps:
                if app.app_id == str(app_id):
                    app.command = str(exec_cmd)
                    app.files = [str(f) for f in files]
                    break
            else:
                apps.append(
                    AppState(
                        app_id=str(app_id),
                        command=str(exec_cmd),
                        files=[str(f) for f in files],
                    )
                )
            self._manager.update_app_state(current.name, apps)

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="")
        def TrackAppClosed(self, app_id: str):
            """Record that an app was closed; remove it from the current activity."""
            current = self._manager.get_current()
            if not current:
                return
            apps = [a for a in current.apps if a.app_id != str(app_id)]
            self._manager.update_app_state(current.name, apps)

        # ── Signal ─────────────────────────────────────────────────────────────

        @dbus.service.signal(DBUS_INTERFACE, signature="s")
        def ActivityChanged(self, new_name: str):
            pass

else:

    class ActivitiesService:  # type: ignore[no-redef]
        """Stub when D-Bus is unavailable."""

        def __init__(self, bus, manager: ActivityManager):
            self._manager = manager


def run_service():
    """Start the D-Bus service."""
    if not DBUS_AVAILABLE:
        logger.error("D-Bus not available. Install python3-dbus and python3-gi.")
        sys.exit(1)
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    bus_name = dbus.service.BusName(DBUS_BUS_NAME, bus=session_bus)  # noqa: F841
    manager = ActivityManager()
    service = ActivitiesService(session_bus, manager)  # noqa: F841

    # Start the window monitor so the active activity's app list stays current.
    from gnome_activities.daemon.monitor import WindowMonitor

    monitor = WindowMonitor(manager)
    monitor.start()

    loop = GLib.MainLoop()
    logger.info("GNOME Activities daemon started.")
    try:
        loop.run()
    finally:
        monitor.stop()
