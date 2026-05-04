"""D-Bus service for gnome-activities daemon."""
import json
import logging
import sys

logger = logging.getLogger(__name__)

DBUS_BUS_NAME = "org.gnome.Activities"
DBUS_OBJECT_PATH = "/org/gnome/Activities"
DBUS_INTERFACE = "org.gnome.Activities"


def run_service():
    """Start the D-Bus service. Requires dbus-python."""
    try:
        import dbus
        import dbus.service
        import dbus.mainloop.glib
        from gi.repository import GLib
    except ImportError as e:
        logger.error(f"dbus-python or gi not available: {e}")
        sys.exit(1)

    from .activity_manager import ActivityManager

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus_name = dbus.service.BusName(DBUS_BUS_NAME, bus)

    class ActivitiesService(dbus.service.Object):
        def __init__(self):
            super().__init__(bus_name, DBUS_OBJECT_PATH)
            self.manager = ActivityManager()

        @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
        def ListActivities(self):
            acts = self.manager.list_activities()
            return json.dumps([a.to_dict() for a in acts])

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def AddActivity(self, name):
            activity = self.manager.add_activity(str(name))
            return json.dumps(activity.to_dict())

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="")
        def RemoveActivity(self, name):
            self.manager.remove_activity(str(name))

        @dbus.service.method(DBUS_INTERFACE, in_signature="ss", out_signature="s")
        def RenameActivity(self, old_name, new_name):
            activity = self.manager.rename_activity(str(old_name), str(new_name))
            if activity.is_active:
                self.ActivityChanged(activity.name)
            return json.dumps(activity.to_dict())

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="s")
        def ActivateActivity(self, name):
            activity = self.manager.activate_activity(str(name))
            self.ActivityChanged(activity.name)
            return json.dumps(activity.to_dict())

        @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
        def GetActiveActivity(self):
            active = self.manager.get_active_activity()
            if active:
                return json.dumps(active.to_dict())
            return "null"

        @dbus.service.method(DBUS_INTERFACE, in_signature="sssasb", out_signature="s")
        def AddAppToActivity(self, activity_name, app_id, exec_cmd, files, is_global):
            app = self.manager.add_app_to_activity(
                str(activity_name), str(app_id), str(exec_cmd),
                [str(f) for f in files], bool(is_global)
            )
            return json.dumps(app.to_dict())

        @dbus.service.method(DBUS_INTERFACE, in_signature="ss", out_signature="")
        def RemoveAppFromActivity(self, activity_name, app_id):
            self.manager.remove_app_from_activity(str(activity_name), str(app_id))

        @dbus.service.method(DBUS_INTERFACE, in_signature="ssb", out_signature="s")
        def SetAppGlobal(self, activity_name, app_id, is_global):
            app = self.manager.set_app_global(str(activity_name), str(app_id), bool(is_global))
            return json.dumps(app.to_dict())

        @dbus.service.method(DBUS_INTERFACE, in_signature="ssas", out_signature="")
        def TrackAppOpened(self, app_id, exec_cmd, files):
            self.manager.track_app_opened(str(app_id), str(exec_cmd), [str(f) for f in files])

        @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="")
        def TrackAppClosed(self, app_id):
            self.manager.track_app_closed(str(app_id))

        @dbus.service.signal(DBUS_INTERFACE, signature="s")
        def ActivityChanged(self, activity_name):
            pass

    ActivitiesService()
    logger.info(f"D-Bus service started at {DBUS_BUS_NAME}")
    loop = GLib.MainLoop()
    loop.run()
