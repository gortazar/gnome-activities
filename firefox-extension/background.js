/**
 * GNOME Activities - Firefox Background Script
 * Connects to the native messaging host and syncs tab state.
 */

const NATIVE_APP = "gnome.activities";
const RECONNECT_DELAY_MS = 5000;

let port = null;
let reconnectTimer = null;

function connect() {
  try {
    port = browser.runtime.connectNative(NATIVE_APP);

    port.onMessage.addListener((message) => {
      handleNativeMessage(message);
    });

    port.onDisconnect.addListener((p) => {
      console.warn("GNOME Activities: native host disconnected", p.error);
      port = null;
      scheduleReconnect();
    });

    console.log("GNOME Activities: connected to native host");
    sendCurrentTabs();
  } catch (err) {
    console.error("GNOME Activities: failed to connect", err);
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, RECONNECT_DELAY_MS);
}

function sendMessage(msg) {
  if (port) {
    try {
      port.postMessage(msg);
    } catch (err) {
      console.error("GNOME Activities: send error", err);
      port = null;
      scheduleReconnect();
    }
  }
}

async function sendCurrentTabs() {
  const tabs = await browser.tabs.query({});
  const tabList = tabs.map((t) => ({ id: t.id, url: t.url, title: t.title }));
  sendMessage({ type: "tabs_snapshot", tabs: tabList });
}

async function handleNativeMessage(message) {
  if (!message || !message.type) return;

  if (message.type === "activity_changed") {
    const { old_activity, new_activity, urls_to_open, close_tabs } = message;
    console.log(`GNOME Activities: switching from '${old_activity}' to '${new_activity}'`);

    if (close_tabs && Array.isArray(close_tabs) && close_tabs.length > 0) {
      const allTabs = await browser.tabs.query({});
      const tabsToClose = allTabs
        .filter((t) => close_tabs.includes(t.url))
        .map((t) => t.id);
      if (tabsToClose.length > 0) {
        await browser.tabs.remove(tabsToClose);
      }
    }

    if (urls_to_open && Array.isArray(urls_to_open)) {
      for (const url of urls_to_open) {
        await browser.tabs.create({ url });
      }
    }
  }
}

// Tab event listeners
browser.tabs.onCreated.addListener(async (tab) => {
  sendMessage({ type: "tab_opened", tab: { id: tab.id, url: tab.url, title: tab.title } });
});

browser.tabs.onRemoved.addListener((tabId, removeInfo) => {
  sendMessage({ type: "tab_closed", tabId });
});

browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url || changeInfo.title) {
    sendMessage({
      type: "tab_updated",
      tab: { id: tabId, url: tab.url, title: tab.title },
    });
  }
});

// Initial connection
connect();
