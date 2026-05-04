/**
 * Background service worker for GNOME Activities Firefox extension.
 * Bridges browser tab events to the native GNOME Activities daemon.
 */

const NATIVE_HOST = "org.gnome.activities";
let nativePort = null;

function connectNativeHost() {
  try {
    nativePort = chrome.runtime.connectNative(NATIVE_HOST);

    nativePort.onMessage.addListener((message) => {
      if (message.activity) {
        chrome.storage.local.set({ currentActivity: message.activity });
      }
    });

    nativePort.onDisconnect.addListener(() => {
      console.warn("GNOME Activities: native host disconnected", chrome.runtime.lastError?.message);
      nativePort = null;
      // Retry connection after 5 seconds
      setTimeout(connectNativeHost, 5000);
    });

    // Send current tabs on connect
    sendCurrentTabs();
  } catch (e) {
    console.error("GNOME Activities: failed to connect to native host", e);
  }
}

function sendMessage(msg) {
  if (!nativePort) {
    connectNativeHost();
    return;
  }
  try {
    nativePort.postMessage(msg);
  } catch (e) {
    console.error("GNOME Activities: failed to send message", e);
    nativePort = null;
  }
}

async function sendCurrentTabs() {
  try {
    const tabs = await chrome.tabs.query({});
    for (const tab of tabs) {
      sendMessage({
        type: "tab_opened",
        url: tab.url || "",
        title: tab.title || "",
        tabId: tab.id,
      });
    }
  } catch (e) {
    console.error("GNOME Activities: error sending current tabs", e);
  }
}

// Listen for tab events
chrome.tabs.onCreated.addListener((tab) => {
  sendMessage({
    type: "tab_opened",
    url: tab.url || "",
    title: tab.title || "",
    tabId: tab.id,
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    sendMessage({
      type: "tab_updated",
      url: tab.url || "",
      title: tab.title || "",
      tabId: tabId,
    });
  }
});

chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
  sendMessage({
    type: "tab_closed",
    tabId: tabId,
    url: "",
    title: "",
  });
});

// Connect on startup
connectNativeHost();
