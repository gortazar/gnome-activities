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
        """D-Bus service exposing activities management."""

        def __init__(self, bus, manager: ActivityManager):
            super().__init__(bus, DBUS_OBJECT_PATH)
            self._manager = manager

        @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
        def List(self):
            acts = self._manager.list_activities()
            return json.dumps([a.to_dict() for a in acts])

        @dbus.service.method(DBUS_INTERFACE, in_signature="ss", out_signature="s")
        def Create(self, name: str, description: str):
            try:
                act = self._manager.create(str(name), str(description))
                return json.dumps({"status": "ok", "activity": act.to_dict()})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def Delete(self, name: str):
            try:
                self._manager.delete(str(name))
                return json.dumps({"status": "ok"})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="ss", out_signature="s")
        def Rename(self, old_name: str, new_name: str):
            try:
                act = self._manager.rename(str(old_name), str(new_name))
                self.ActivityChanged(str(old_name), str(new_name))
                return json.dumps({"status": "ok", "activity": act.to_dict()})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def Activate(self, name: str):
            try:
                current = self._manager.get_current()
                old_name = current.name if current else ""
                act = self._manager.activate(str(name))
                self.ActivityChanged(old_name, str(name))
                return json.dumps({"status": "ok", "activity": act.to_dict()})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
        def Current(self):
            act = self._manager.get_current()
            if act:
                return json.dumps(act.to_dict())
            return json.dumps(None)

        @dbus.service.method(DBUS_INTERFACE, in_signature="ssas", out_signature="s")
        def TrackAppOpened(self, app_id: str, exec_cmd: str, files):
            try:
                current = self._manager.get_current()
                if current:
                    from gnome_activities.core.activity import AppState
                    existing = {a.app_id: a for a in current.apps}
                    if str(app_id) not in existing:
                        app_state = AppState(
                            app_id=str(app_id),
                            command=str(exec_cmd),
                            files=list(files),
                        )
                        current.apps.append(app_state)
                        self._manager.update_app_state(current.name, current.apps)
                return json.dumps({"status": "ok"})
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def TrackAppClosed(self, app_id: str):
            try:
                current = self._manager.get_current()
                if current:
                    current.apps = [a for a in current.apps if a.app_id != str(app_id)]
                    self._manager.update_app_state(current.name, current.apps)
                return json.dumps({"status": "ok"})
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="ss", out_signature="s")
        def SetActivityTabs(self, activity_name: str, urls_json: str):
            try:
                tabs = json.loads(urls_json)
                self._manager.update_activity_tabs(str(activity_name), tabs)
                return json.dumps({"status": "ok"})
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def GetActivityTabs(self, activity_name: str):
            try:
                act = self._manager.get(str(activity_name))
                return json.dumps(act.tabs)
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.signal(DBUS_INTERFACE, signature="ss")
        def ActivityChanged(self, old_name: str, new_name: str):
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

    from gnome_activities.daemon.monitor import WindowMonitor
    monitor = WindowMonitor(manager)
    monitor.start()

    loop = GLib.MainLoop()
    logger.info("GNOME Activities daemon started.")
    try:
        loop.run()
    finally:
        monitor.stop()
