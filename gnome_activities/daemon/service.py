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

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def Activate(self, name: str):
            try:
                act = self._manager.activate(str(name))
                self.ActivityChanged("", str(name))
                return json.dumps({"status": "ok", "activity": act.to_dict()})
            except ActivityError as e:
                return json.dumps({"status": "error", "message": str(e)})

        @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
        def Current(self):
            act = self._manager.get_current()
            if act:
                return json.dumps(act.to_dict())
            return json.dumps(None)

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
    bus_name = dbus.service.BusName(DBUS_BUS_NAME, bus=session_bus)
    manager = ActivityManager()
    service = ActivitiesService(session_bus, manager)
    loop = GLib.MainLoop()
    logger.info("GNOME Activities daemon started.")
    loop.run()
