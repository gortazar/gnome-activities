/**
 * Popup script for GNOME Activities extension.
 * Reads current activity from chrome.storage.local and renders it.
 */

async function render() {
  const currentNameEl = document.getElementById("current-name");
  const listEl = document.getElementById("activities-list");
  const noActivitiesEl = document.getElementById("no-activities");

  // Get stored data
  const data = await chrome.storage.local.get(["currentActivity", "activities"]);
  const currentActivity = data.currentActivity || null;
  const activities = data.activities || [];

  // Render current activity
  currentNameEl.textContent = currentActivity ? currentActivity : "None";

  // Render list
  listEl.innerHTML = "";
  if (activities.length === 0) {
    noActivitiesEl.style.display = "block";
  } else {
    noActivitiesEl.style.display = "none";
    for (const activity of activities) {
      const li = document.createElement("li");
      li.textContent = activity.name || activity;
      const isActive =
        (currentActivity && (activity.name === currentActivity || activity === currentActivity));
      if (isActive) {
        li.classList.add("active");
      }
      listEl.appendChild(li);
    }
  }
}

document.addEventListener("DOMContentLoaded", render);
