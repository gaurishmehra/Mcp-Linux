// Background script to handle keyboard shortcuts
browser.commands.onCommand.addListener((command) => {
  if (command === "copy-tab-info-html") {
    // Get the active tab's internal browser ID first to identify it later
    browser.tabs.query({active: true, currentWindow: true}).then((activeTabs) => {
      const activeBrowserTab = activeTabs[0]; // This is the browser's internal Tab object for the active tab
      if (!activeBrowserTab) {
        console.warn("No active tab found.");
        return;
      }
      
      // Get all tabs in the current window to determine tab number
      browser.tabs.query({currentWindow: true}).then((allTabsInWindow) => {
        const activeIndex = allTabsInWindow.findIndex(tab => tab.id === activeBrowserTab.id);
        const tabNumber = activeIndex !== -1 ? activeIndex + 1 : 'unknown';
        
        const currentTabInfo = {
          id: tabNumber, // Use tabNumber as the ID for the payload
          title: activeBrowserTab.title,
          url: activeBrowserTab.url
        };
        
        // Send message to the content script of the actual active tab using its browser ID
        browser.tabs.sendMessage(activeBrowserTab.id, {
          action: "copyTabInfoWithHTML",
          currentTab: currentTabInfo
        }).catch(error => {
          console.error(`Error sending message to tab ${activeBrowserTab.id}:`, error);
          // You might want to inform the user if the content script isn't available
          // (e.g., on special browser pages like about:addons or new tab page)
        });
      }).catch(error => console.error("Error querying all tabs:", error));
    }).catch(error => console.error("Error querying active tab:", error));
  } else if (command === "copy-tab-info") {
    // Keep existing functionality for Ctrl+E
    // Get the active tab's internal browser ID first to identify it later
    browser.tabs.query({active: true, currentWindow: true}).then((activeTabs) => {
      const activeBrowserTab = activeTabs[0]; // This is the browser's internal Tab object for the active tab
      if (!activeBrowserTab) {
        console.warn("No active tab found.");
        return;
      }
      
      // Get all tabs in the current window, they are generally ordered by their position
      browser.tabs.query({currentWindow: true}).then((allTabsInWindow) => {
        let currentTabInfoForPayload = null;
        const allTabsPayload = allTabsInWindow.map((tab, index) => {
          const tabNumber = index + 1; // 1-based index is our "tab number"
          const isCurrent = tab.id === activeBrowserTab.id; // Compare internal browser IDs
          if (isCurrent) {
            currentTabInfoForPayload = {
              id: tabNumber, // Use tabNumber as the ID for the payload
              title: tab.title,
              url: tab.url
              // 'active' status is implicitly true for currentTab in its own object
            };
          }
          return {
            id: tabNumber, // Use tabNumber as the ID for the payload
            title: tab.title,
            url: tab.url,
            active: isCurrent // Retain 'active' status for filtering in content.js
          };
        });
        
        // Fallback if currentTabInfoForPayload wasn't set during the map
        if (!currentTabInfoForPayload && activeBrowserTab) {
          console.warn("Current tab info not set during map, attempting fallback.");
          const activeIndex = allTabsInWindow.findIndex(t => t.id === activeBrowserTab.id);
          if (activeIndex !== -1) {
            currentTabInfoForPayload = {
              id: activeIndex + 1,
              title: activeBrowserTab.title,
              url: activeBrowserTab.url
            };
          } else {
            // As a last resort, if active tab somehow not in the list (very unlikely)
            currentTabInfoForPayload = {
              id: 'unknown', // Or handle as an error
              title: activeBrowserTab.title,
              url: activeBrowserTab.url
            };
            console.error("Active tab not found in allTabsInWindow list.");
          }
        }
        
        // Ensure currentTabInfoForPayload is not null
        if (!currentTabInfoForPayload) {
          console.error("Could not determine current tab information for payload.");
          // Potentially provide a default or skip sending if this is critical
          currentTabInfoForPayload = { id: 'error', title: 'Error', url: 'Error' };
        }
        
        const tabData = {
          currentTab: currentTabInfoForPayload,
          allTabs: allTabsPayload // This array contains all tabs with 'id' as their 1-based tab number
        };
        
        // Send message to the content script of the actual active tab using its browser ID
        browser.tabs.sendMessage(activeBrowserTab.id, {
          action: "copyTabInfo",
          ...tabData
        }).catch(error => {
          console.error(`Error sending message to tab ${activeBrowserTab.id}:`, error);
          // You might want to inform the user if the content script isn't available
          // (e.g., on special browser pages like about:addons or new tab page)
        });
      }).catch(error => console.error("Error querying all tabs:", error));
    }).catch(error => console.error("Error querying active tab:", error));
  }
});