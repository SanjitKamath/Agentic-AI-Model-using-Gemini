document.addEventListener("DOMContentLoaded", () => {
    const chatbox = document.getElementById("chatbox");
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");

    const appendMessage = (sender, message) => {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${sender}-message`);
        
        const p = document.createElement("p");
        p.innerHTML = message; // Use innerHTML to render any potential HTML in the message
        messageDiv.appendChild(p);
        
        chatbox.appendChild(messageDiv);
        chatbox.scrollTop = chatbox.scrollHeight;
    };

    const sendMessage = async () => {
        const userMessage = userInput.value.trim();
        if (!userMessage) return;

        appendMessage("user", userMessage);
        userInput.value = "";

        // Add a "thinking..." indicator
        const thinkingIndicator = document.createElement("div");
        thinkingIndicator.classList.add("message", "bot-message");
        thinkingIndicator.innerHTML = `<p class="thinking">Thinking...</p>`;
        chatbox.appendChild(thinkingIndicator);
        chatbox.scrollTop = chatbox.scrollHeight;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: userMessage }),
            });

            const data = await response.json();
            const botReply = data.result || data.error || "An unexpected error occurred.";
            
            // Remove the thinking indicator and add the actual reply
            chatbox.removeChild(thinkingIndicator);
            appendMessage("bot", botReply);

        } catch (error) {
            console.error("Error:", error);
            chatbox.removeChild(thinkingIndicator);
            appendMessage("bot", "Sorry, I encountered an error. Please try again.");
        }
    };

    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keyup", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
});
