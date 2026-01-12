const HOST_NAME = "com.weebcoders.ai_scraper";

/**
 * UI ↔ Background uses PORT
 * Background ↔ Native Host uses PORT
 * This keeps the service worker alive and avoids context invalidation
 */
chrome.runtime.onConnect.addListener((uiPort) => {
  if (uiPort.name !== "ai-scraper-ui") return;

  console.log("🔌 UI connected");

  uiPort.onMessage.addListener((msg) => {
    if (msg.type !== "USER_SCRAPE_REQUEST") return;

    console.log("📥 Scrape request from UI:", msg.payload);

    const nativePort = chrome.runtime.connectNative(HOST_NAME);
    let responded = false;

    nativePort.onMessage.addListener((response) => {
      if (responded) return;
      responded = true;

      console.log("✅ Response from native host:", response);

      uiPort.postMessage({
        success: response.status === "success",
        data: response.data,
        error: response.error
      });

      nativePort.disconnect();
    });

    nativePort.onDisconnect.addListener(() => {
      if (responded) return;
      responded = true;

      const error = chrome.runtime.lastError;

      console.error("❌ Native host disconnected:", error);

      uiPort.postMessage({
        success: false,
        error: error?.message || "Native host disconnected"
      });
    });

    nativePort.postMessage({
      url: msg.payload.URL,
      user_prompt: msg.payload.UserPrompt
    });
  });

  uiPort.onDisconnect.addListener(() => {
    console.log("🔌 UI disconnected");
  });
});

