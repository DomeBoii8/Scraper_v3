document.addEventListener("DOMContentLoaded", () => {
  const sendBtn = document.getElementById("sendBtn");
  const queryInput = document.getElementById("query");
  const chatArea = document.getElementById("chatArea");

  const sendQuery = () => {
    const query = queryInput.value.trim();
    if (!query) return;

    console.log("🔗 URL:", window.location.href);
    console.log("📝 QUERY:", query);

    // Show user message
    const userMsg = document.createElement("div");
    userMsg.className = "message user";
    userMsg.textContent = query;
    chatArea.appendChild(userMsg);

    // Show loading message
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "message ai";
    loadingMsg.textContent = "🔄 Scraping... This may take 20-60 seconds...";
    chatArea.appendChild(loadingMsg);

    queryInput.value = "";
    chatArea.scrollTop = chatArea.scrollHeight;

    chrome.runtime.sendMessage(
      {
        type: "USER_SCRAPE_REQUEST",
        payload: {
          URL: window.location.href,
          UserPrompt: query
        }
      },
      (response) => {
        // Remove loading message
        chatArea.removeChild(loadingMsg);

        const aiMsg = document.createElement("div");
        aiMsg.className = "message ai";

        if (response?.success) {
          const data = response.data.data || response.data;

          // Format the response nicely
          let formatted = "✅ Scraping complete!\n\n";

          if (data.product) {
            formatted += `📦 Product: ${data.product}\n`;
          }

          if (data.columns && data.columns.length > 0) {
            formatted += `📋 Columns: ${data.columns.join(", ")}\n`;
          }

          if (data.records && data.records.length > 0) {
            formatted += `📊 Records found: ${data.records.length}\n\n`;
            formatted += `Sample data:\n`;

            // Show first 3 records
            data.records.slice(0, 3).forEach((record, i) => {
              formatted += `\n${i + 1}. ${record.join(" | ")}`;
            });

            if (data.records.length > 3) {
              formatted += `\n\n... and ${data.records.length - 3} more records`;
            }

            formatted += `\n\n💾 File saved to exports/${data.product}.${data.outputFormat}`;
          } else {
            formatted += "\n⚠️ No records extracted. Try a different prompt or page.";
          }

          aiMsg.textContent = formatted;
        } else {
          aiMsg.textContent = `❌ Error: ${response?.error || "Unknown error"}`;
        }

        chatArea.appendChild(aiMsg);
        chatArea.scrollTop = chatArea.scrollHeight;
      }
    );
  };

  sendBtn.addEventListener("click", sendQuery);

  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendQuery();
    }
  });
});