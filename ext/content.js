// Content script to copy tab information with HTML
let tabInfoOverlay = null;

// Listen for messages from background script
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "copyTabInfoWithHTML") {
    copyTabInfoWithHTMLToClipboard(message.currentTab);
  } else if (message.action === "copyTabInfo") {
    copyTabInfoToClipboard(message.currentTab, message.allTabs);
  }
});

function copyTabInfoWithHTMLToClipboard(currentTab) {
  // Extract meaningful content from the page efficiently
  const content = extractPageContent();
  
  const tabData = {
    tab_number: currentTab.id,
    title: currentTab.title,
    url: currentTab.url,
    content: content
  };
  
  const jsonString = JSON.stringify(tabData, null, 2);
  const successMessage = "✅ Tab content copied!";
  
  navigator.clipboard.writeText(jsonString).then(() => {
    showCopyNotification(successMessage);
  }).catch((err) => {
    console.error('Failed to copy tab content to clipboard:', err);
    fallbackCopyToClipboard(jsonString, successMessage);
  });
}

function extractPageContent() {
  // Remove scripts, styles, and other non-content elements
  const elementsToRemove = ['script', 'style', 'noscript', 'iframe', 'object', 'embed', 'nav', 'aside', 'footer', 'header'];
  const clone = document.cloneNode(true);
  
  // Remove unwanted elements from the clone
  elementsToRemove.forEach(tag => {
    const elements = clone.querySelectorAll(tag);
    elements.forEach(el => el.remove());
  });
  
  // Remove elements with common noise classes/ids
  const noiseSelectors = [
    '[class*="ad"]', '[id*="ad"]', '[class*="advertisement"]',
    '[class*="sidebar"]', '[class*="cookie"]', '[class*="popup"]',
    '[class*="modal"]', '[class*="overlay"]', '[class*="banner"]',
    '[class*="newsletter"]', '[class*="subscribe"]', '[class*="social"]',
    '[class*="share"]', '[class*="comment"]', '[class*="related"]',
    '[class*="recommended"]', '[class*="promo"]', '[class*="widget"]'
  ];
  
  noiseSelectors.forEach(selector => {
    try {
      const elements = clone.querySelectorAll(selector);
      elements.forEach(el => el.remove());
    } catch(e) {
      // Ignore selector errors
    }
  });
  
  // Try to find main content area first
  let mainContent = null;
  const mainSelectors = [
    'main', 'article', '[role="main"]', '.main-content', 
    '#main-content', '.content', '#content', '.post-content',
    '.article-content', '.entry-content', '.page-content'
  ];
  
  for (const selector of mainSelectors) {
    const element = clone.querySelector(selector);
    if (element) {
      mainContent = element;
      break;
    }
  }
  
  // If no main content found, use body but filter more aggressively
  if (!mainContent) {
    mainContent = clone.querySelector('body') || clone;
  }
  
  // Extract text content and clean it up
  let textContent = mainContent.textContent || mainContent.innerText || '';
  
  // Clean up the text
  textContent = textContent
    // Replace multiple whitespaces with single space
    .replace(/\s+/g, ' ')
    // Remove excessive line breaks
    .replace(/\n\s*\n\s*\n/g, '\n\n')
    // Trim whitespace from start and end
    .trim();
  
  // If content is too short, try to get more content from the page
  if (textContent.length < 100) {
    // Fall back to getting text from the entire body, but still cleaned
    const bodyText = (document.body?.textContent || '').replace(/\s+/g, ' ').trim();
    if (bodyText.length > textContent.length) {
      textContent = bodyText;
    }
  }
  
  // Limit content length to prevent extremely large payloads (optional)
  const maxLength = 50000; // Adjust as needed
  if (textContent.length > maxLength) {
    textContent = textContent.substring(0, maxLength) + '\n\n[Content truncated due to length...]';
  }
  
  return textContent;
}

function copyTabInfoToClipboard(currentTabDetails, allTabsInWindow) {
  // The 'id' field in currentTabDetails and elements of allTabsInWindow is already the tab number
  const jsonData = {
    current_tab: {
      id: currentTabDetails.id, // This is the tab number
      title: currentTabDetails.title,
      url: currentTabDetails.url
    },
    other_tabs: allTabsInWindow
      .filter(tab => !tab.active) // Filter out the current tab using the 'active' flag
      .map(tab => ({
        id: tab.id, // This is the tab number
        title: tab.title,
        url: tab.url
      }))
  };
  
  const jsonStringToCopy = JSON.stringify(jsonData, null, 2);
  const successMessage = "✅ JSON tab info (with tab numbers) copied!";
  
  navigator.clipboard.writeText(jsonStringToCopy).then(() => {
    showCopyNotification(successMessage);
  }).catch((err) => {
    console.error('Failed to copy JSON to clipboard:', err);
    fallbackCopyToClipboard(jsonStringToCopy, successMessage);
  });
}

function fallbackCopyToClipboard(text, notificationMessage) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    document.execCommand('copy');
    showCopyNotification(notificationMessage);
  } catch (err) {
    console.error('Fallback copy failed:', err);
    showCopyNotification("❌ Failed to copy to clipboard.");
  }
  
  document.body.removeChild(textArea);
}

function showCopyNotification(message = "✅ Info copied to clipboard!") {
  const existing = document.getElementById('copy-notification');
  if (existing) existing.remove();
  
  const notification = document.createElement('div');
  notification.id = 'copy-notification';
  notification.innerHTML = message;
  notification.style.cssText = `
    position: fixed; top: 20px; right: 20px; background: rgba(31, 31, 31, 0.95);
    color: #ffffff; padding: 12px 20px; border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    z-index: 1000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px; opacity: 0; transform: translateY(-10px); transition: all 0.3s ease;
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.opacity = '1';
    notification.style.transform = 'translateY(0)';
  }, 10);
  
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(-10px)';
    setTimeout(() => { if (notification.parentNode) notification.remove(); }, 300);
  }, 3000);
}