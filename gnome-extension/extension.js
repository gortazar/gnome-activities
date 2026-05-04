/**
 * GNOME Shell Extension: GNOME Activities
 * Adds a panel indicator showing the current activity and allows switching.
 *
 * Compatible with GNOME Shell 45+ (ESM imports).
 */

import St from 'gi://St';
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import GObject from 'gi://GObject';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

const DBUS_BUS_NAME = 'org.gnome.Activities';
const DBUS_OBJECT_PATH = '/org/gnome/Activities';
const DBUS_INTERFACE = 'org.gnome.Activities';

const ActivitiesIndicator = GObject.registerClass(
    class ActivitiesIndicator extends PanelMenu.Button {
        _init(extension) {
            super._init(0.0, 'GNOME Activities');
            this._extension = extension;
            this._proxy = null;
            this._signalId = null;

            this._label = new St.Label({
                text: 'Activities',
                y_align: 2, // Clutter.ActorAlign.CENTER
                style_class: 'gnome-activities-indicator',
            });
            this.add_child(this._label);

            this._connectDBus();
        }

        _connectDBus() {
            try {
                const iface = `
                <node>
                  <interface name="${DBUS_INTERFACE}">
                    <method name="ListActivities">
                      <arg type="s" direction="out"/>
                    </method>
                    <method name="ActivateActivity">
                      <arg type="s" direction="in"/>
                      <arg type="s" direction="out"/>
                    </method>
                    <method name="GetActiveActivity">
                      <arg type="s" direction="out"/>
                    </method>
                    <signal name="ActivityChanged">
                      <arg type="s"/>
                    </signal>
                  </interface>
                </node>`;

                this._proxy = new Gio.DBusProxy.makeProxyWrapper(iface)(
                    Gio.DBus.session,
                    DBUS_BUS_NAME,
                    DBUS_OBJECT_PATH,
                    (proxy, error) => {
                        if (error) {
                            logError(error, 'GNOME Activities: D-Bus connection failed');
                            this._label.set_text('No Activity');
                            return;
                        }
                        this._onProxyReady();
                    }
                );
            } catch (e) {
                logError(e, 'GNOME Activities: failed to create D-Bus proxy');
                this._label.set_text('No Activity');
            }
        }

        _onProxyReady() {
            // Connect to ActivityChanged signal
            this._signalId = this._proxy.connectSignal('ActivityChanged', (proxy, sender, [name]) => {
                this._label.set_text(name || 'No Activity');
                this._refreshMenu();
            });

            this._updateActiveLabel();
            this.menu.connect('open-state-changed', (menu, open) => {
                if (open) this._refreshMenu();
            });
        }

        _updateActiveLabel() {
            if (!this._proxy) return;
            try {
                this._proxy.GetActiveActivityRemote((result, error) => {
                    if (error) {
                        this._label.set_text('No Activity');
                        return;
                    }
                    const data = JSON.parse(result[0]);
                    this._label.set_text(data ? data.name : 'No Activity');
                });
            } catch (e) {
                this._label.set_text('No Activity');
            }
        }

        _refreshMenu() {
            this.menu.removeAll();
            if (!this._proxy) return;

            try {
                this._proxy.ListActivitiesRemote((result, error) => {
                    if (error) return;
                    let activities;
                    try {
                        activities = JSON.parse(result[0]);
                    } catch (e) {
                        return;
                    }

                    for (const activity of activities) {
                        const item = new PopupMenu.PopupMenuItem(activity.name, {
                            style_class: 'gnome-activities-menu-item',
                        });
                        if (activity.is_active) {
                            item.label.style_class = 'gnome-activities-active';
                        }
                        item.connect('activate', () => {
                            this._activateActivity(activity.name);
                        });
                        this.menu.addMenuItem(item);
                    }

                    if (activities.length === 0) {
                        const empty = new PopupMenu.PopupMenuItem('No activities', { reactive: false });
                        this.menu.addMenuItem(empty);
                    }
                });
            } catch (e) {
                logError(e, 'GNOME Activities: error refreshing menu');
            }
        }

        _activateActivity(name) {
            if (!this._proxy) return;
            try {
                this._proxy.ActivateActivityRemote(name, (result, error) => {
                    if (error) {
                        logError(error, `GNOME Activities: failed to activate '${name}'`);
                    } else {
                        this._label.set_text(name);
                    }
                });
            } catch (e) {
                logError(e, 'GNOME Activities: error activating activity');
            }
        }

        destroy() {
            if (this._proxy && this._signalId) {
                this._proxy.disconnectSignal(this._signalId);
                this._signalId = null;
            }
            super.destroy();
        }
    }
);

export default class GnomeActivitiesExtension extends Extension {
    enable() {
        this._indicator = new ActivitiesIndicator(this);
        Main.panel.addToStatusArea('gnome-activities', this._indicator, 1, 'right');
    }

    disable() {
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
