/**
 * GNOME Shell Extension: GNOME Activities
 * Adds a panel indicator showing the current activity and allows switching,
 * creating, and renaming activities directly from the panel.
 *
 * Apps are automatically tracked: when the user opens an app while an activity
 * is active, it is added to that activity; when closed, it is removed.
 *
 * Compatible with GNOME Shell 45+ (ESM imports).
 */

import St from 'gi://St';
import Clutter from 'gi://Clutter';
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import GObject from 'gi://GObject';
import Shell from 'gi://Shell';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

const DBUS_BUS_NAME = 'org.gnome.Activities';
const DBUS_OBJECT_PATH = '/org/gnome/Activities';
const DBUS_INTERFACE = 'org.gnome.Activities';

// Full D-Bus interface XML including all methods the extension uses.
const DBUS_IFACE_XML = `
<node>
  <interface name="${DBUS_INTERFACE}">
    <method name="List">
      <arg type="s" direction="out"/>
    </method>
    <method name="Create">
      <arg type="s" direction="in"/>
      <arg type="s" direction="in"/>
      <arg type="s" direction="out"/>
    </method>
    <method name="Rename">
      <arg type="s" direction="in"/>
      <arg type="s" direction="in"/>
      <arg type="s" direction="out"/>
    </method>
    <method name="Activate">
      <arg type="s" direction="in"/>
      <arg type="s" direction="out"/>
    </method>
    <method name="Current">
      <arg type="s" direction="out"/>
    </method>
    <method name="TrackAppOpened">
      <arg type="s" direction="in"/>
      <arg type="s" direction="in"/>
      <arg type="as" direction="in"/>
    </method>
    <method name="TrackAppClosed">
      <arg type="s" direction="in"/>
    </method>
    <signal name="ActivityChanged">
      <arg type="s"/>
      <arg type="s"/>
    </signal>
  </interface>
</node>`;

const ActivitiesIndicator = GObject.registerClass(
    class ActivitiesIndicator extends PanelMenu.Button {
        _init(extension) {
            super._init(0.0, 'GNOME Activities');
            this._extension = extension;
            this._proxy = null;
            this._activityChangedId = null;
            this._appStateChangedId = null;
            this._renameTarget = null;

            this._label = new St.Label({
                text: 'Activities',
                y_align: Clutter.ActorAlign.CENTER,
                style_class: 'gnome-activities-indicator',
            });
            this.add_child(this._label);

            this._connectDBus();
        }

        // ── D-Bus connection ──────────────────────────────────────────────────

        _connectDBus() {
            try {
                this._proxy = new Gio.DBusProxy.makeProxyWrapper(DBUS_IFACE_XML)(
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
            // Reflect activity switches in the label.
            this._activityChangedId = this._proxy.connectSignal(
                'ActivityChanged',
                (_proxy, _sender, [_oldName, newName]) => {
                    this._label.set_text(newName || 'No Activity');
                    if (this.menu.isOpen)
                        this._refreshMenu();
                }
            );

            this._updateActiveLabel();

            this.menu.connect('open-state-changed', (_menu, open) => {
                if (open)
                    this._refreshMenu();
            });

            // ── Automatic app tracking ────────────────────────────────────────
            // Whenever the user opens or closes an app, notify the daemon so
            // it can add/remove the app from the currently active activity.
            const appSystem = Shell.AppSystem.get_default();
            this._appStateChangedId = appSystem.connect(
                'app-state-changed',
                (_appSys, app) => this._onAppStateChanged(app)
            );
        }

        // ── Automatic app tracking ────────────────────────────────────────────

        _onAppStateChanged(app) {
            if (!this._proxy) return;

            const state = app.get_state();
            const appId = app.get_id() || app.get_name();

            if (state === Shell.AppState.RUNNING) {
                // App just started — add it to the active activity.
                const appInfo = app.get_app_info();
                // get_commandline() may include desktop entry field codes; strip them all.
                let execCmd = appInfo ? appInfo.get_commandline() : null;
                if (execCmd)
                    execCmd = execCmd.replace(/%[a-zA-Z]/g, '').trim();
                execCmd = execCmd || appId;

                this._proxy.TrackAppOpenedRemote(appId, execCmd, [], (_r, err) => {
                    if (err)
                        logError(err, `GNOME Activities: TrackAppOpened failed for '${appId}'`);
                });
            } else if (state === Shell.AppState.STOPPED) {
                // App closed — remove it from the active activity.
                this._proxy.TrackAppClosedRemote(appId, (_r, err) => {
                    if (err)
                        logError(err, `GNOME Activities: TrackAppClosed failed for '${appId}'`);
                });
            }
        }

        // ── Label update ──────────────────────────────────────────────────────

        _updateActiveLabel() {
            if (!this._proxy) return;
            this._proxy.CurrentRemote((result, error) => {
                if (error) {
                    this._label.set_text('No Activity');
                    return;
                }
                try {
                    const data = JSON.parse(result[0]);
                    this._label.set_text(data ? data.name : 'No Activity');
                } catch (_e) {
                    this._label.set_text('No Activity');
                }
            });
        }

        // ── Menu building ─────────────────────────────────────────────────────

        /**
         * Rebuild the popup menu with the current list of activities plus
         * a "New Activity" entry at the bottom.
         */
        _refreshMenu() {
            this.menu.removeAll();
            if (!this._proxy) return;

            this._proxy.ListRemote((result, error) => {
                if (error) {
                    logError(error, 'GNOME Activities: List failed');
                    return;
                }

                let activities;
                try {
                    activities = JSON.parse(result[0]);
                } catch (_e) {
                    return;
                }

                if (activities.length === 0) {
                    const empty = new PopupMenu.PopupMenuItem('No activities', {
                        reactive: false,
                    });
                    this.menu.addMenuItem(empty);
                } else {
                    for (const activity of activities)
                        this.menu.addMenuItem(this._buildActivityRow(activity));
                }

                this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
                this.menu.addMenuItem(this._buildNewActivityItem());
            });
        }

        /**
         * Build one row for an activity: clicking it switches to that activity;
         * a pencil button on the right opens an inline rename entry.
         */
        _buildActivityRow(activity) {
            const item = new PopupMenu.PopupBaseMenuItem();

            // Activity name label (fills remaining space).
            // The 'gnome-activities-active' CSS class provides the visual active indicator.
            const label = new St.Label({
                text: activity.name,
                x_expand: true,
                style_class: activity.is_active
                    ? 'gnome-activities-active'
                    : 'gnome-activities-menu-item',
            });
            item.add_child(label);

            // Rename button (pencil).
            const renameBtn = new St.Button({
                label: '✏',
                style_class: 'gnome-activities-rename-btn',
                reactive: true,
                can_focus: true,
                track_hover: true,
            });
            item.add_child(renameBtn);

            // Clicking the row body activates the activity.
            item.connect('activate', (_item, _event) => {
                if (_event && _event.get_source() === renameBtn)
                    return; // handled by the button
                this._activateActivity(activity.name);
            });

            // Clicking the pencil shows the inline rename entry.
            renameBtn.connect('clicked', () => {
                this._showRenameEntry(activity.name);
            });

            return item;
        }

        /**
         * Build the "＋ New Activity" footer item which, when activated,
         * replaces the menu content with an inline text-entry widget.
         */
        _buildNewActivityItem() {
            const item = new PopupMenu.PopupMenuItem('+ New Activity', {
                style_class: 'gnome-activities-new-item',
            });
            item.connect('activate', () => {
                this._showCreateEntry();
            });
            return item;
        }

        // ── Inline text entry helpers ─────────────────────────────────────────

        /**
         * Replace the menu with a single text-entry row for creating a new
         * activity.  Press Enter to confirm, Escape to cancel.
         */
        _showCreateEntry() {
            this.menu.removeAll();
            this.menu.addMenuItem(
                this._buildEntryItem('New activity name…', '', (name) => {
                    this._createActivity(name);
                })
            );
        }

        /**
         * Replace the menu with a text-entry row pre-filled with the current
         * activity name so the user can rename it.
         */
        _showRenameEntry(oldName) {
            this.menu.removeAll();
            this.menu.addMenuItem(
                this._buildEntryItem('Rename activity…', oldName, (newName) => {
                    this._renameActivity(oldName, newName);
                })
            );
        }

        /**
         * Build a PopupBaseMenuItem that contains an St.Entry plus Cancel/OK
         * buttons.  Calls `onConfirm(text)` when the user confirms.
         */
        _buildEntryItem(hintText, initialText, onConfirm) {
            const item = new PopupMenu.PopupBaseMenuItem({ reactive: false });
            const box = new St.BoxLayout({
                vertical: false,
                x_expand: true,
                style_class: 'gnome-activities-entry-box',
            });

            const entry = new St.Entry({
                hint_text: hintText,
                text: initialText,
                x_expand: true,
                can_focus: true,
                style_class: 'gnome-activities-entry',
            });

            const okBtn = new St.Button({
                label: '✔',
                style_class: 'gnome-activities-ok-btn',
                reactive: true,
                can_focus: true,
            });
            const cancelBtn = new St.Button({
                label: '✖',
                style_class: 'gnome-activities-cancel-btn',
                reactive: true,
                can_focus: true,
            });

            box.add_child(entry);
            box.add_child(okBtn);
            box.add_child(cancelBtn);
            item.add_child(box);

            const confirm = () => {
                const text = entry.get_text().trim();
                if (text) {
                    onConfirm(text);
                } else {
                    // Empty name — just redraw the normal menu.
                    this._refreshMenu();
                }
                this.menu.close();
            };

            const cancel = () => {
                this._refreshMenu();
            };

            entry.clutter_text.connect('key-press-event', (_actor, event) => {
                const sym = event.get_key_symbol();
                if (sym === Clutter.KEY_Return || sym === Clutter.KEY_KP_Enter) {
                    confirm();
                    return Clutter.EVENT_STOP;
                }
                if (sym === Clutter.KEY_Escape) {
                    cancel();
                    return Clutter.EVENT_STOP;
                }
                return Clutter.EVENT_PROPAGATE;
            });

            okBtn.connect('clicked', confirm);
            cancelBtn.connect('clicked', cancel);

            // Auto-focus the entry once the item is shown.
            GLib.idle_add(GLib.PRIORITY_DEFAULT, () => {
                entry.grab_key_focus();
                return GLib.SOURCE_REMOVE;
            });

            return item;
        }

        // ── D-Bus action helpers ──────────────────────────────────────────────

        _activateActivity(name) {
            if (!this._proxy) return;
            this._proxy.ActivateRemote(name, (_result, error) => {
                if (error)
                    logError(error, `GNOME Activities: failed to activate '${name}'`);
                else
                    this._label.set_text(name);
            });
        }

        _createActivity(name) {
            if (!this._proxy) return;
            this._proxy.CreateRemote(name, '', (_result, error) => {
                if (error)
                    logError(error, `GNOME Activities: failed to create '${name}'`);
                else
                    this._refreshMenu();
            });
        }

        _renameActivity(oldName, newName) {
            // Activity names are case-sensitive; 'Work' and 'work' are different activities.
            if (!this._proxy || oldName === newName) return;
            this._proxy.RenameRemote(oldName, newName, (_result, error) => {
                if (error)
                    logError(error, `GNOME Activities: failed to rename '${oldName}'`);
                else
                    this._updateActiveLabel();
            });
        }

        // ── Cleanup ───────────────────────────────────────────────────────────

        destroy() {
            if (this._appStateChangedId) {
                Shell.AppSystem.get_default().disconnect(this._appStateChangedId);
                this._appStateChangedId = null;
            }
            if (this._proxy && this._activityChangedId) {
                this._proxy.disconnectSignal(this._activityChangedId);
                this._activityChangedId = null;
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
