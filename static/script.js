// Wait for the entire HTML document to be loaded before running the script
document.addEventListener('DOMContentLoaded', () => {

    // Get references to all the necessary HTML elements
    const modelSelector = document.getElementById('model-selector');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatBox = document.getElementById('chat-box');
    const errorMessage = document.getElementById('error-message');

    const SESSION_STORAGE_KEY = 'agent-model-preference';

    // --- Function to display a message in the chat box ---
    function addMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = text;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
    }

    // --- Function to show or hide the error message box ---
    function displayError(message) {
        if (message) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
        } else {
            errorMessage.style.display = 'none';
        }
    }

    // --- Function to send the user's message to the backend ---
    async function sendMessage() {
        const query = chatInput.value.trim();
        if (!query) return; // Don't send empty messages

        const selectedProvider = modelSelector.value;
        addMessage(query, 'user');
        chatInput.value = ''; // Clear the input field
        displayError(null); // Clear any previous errors

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    provider: selectedProvider
                }),
            });

            if (!response.ok) {
                // Handle HTTP errors like 500 Internal Server Error
                const errorData = await response.json();
                throw new Error(errorData.error || `Server responded with status ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                // Handle application-specific errors returned from the agent
                throw new Error(data.error);
            }
            
            addMessage(data.result, 'bot');

        } catch (error) {
            console.error("Error:", error);
            displayError(error.message);
            addMessage("Sorry, I encountered an error. Please check the error message above.", 'bot');
        }
    }

    // --- Event Listeners ---

    // 1. Send message when the "Send" button is clicked
    sendButton.addEventListener('click', sendMessage);

    // 2. Send message when the "Enter" key is pressed in the input field
    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // 3. Save the user's model preference to sessionStorage whenever it changes
    modelSelector.addEventListener('change', () => {
        sessionStorage.setItem(SESSION_STORAGE_KEY, modelSelector.value);
    });

    // 4. Load the user's preference from sessionStorage when the page loads
    const savedPreference = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (savedPreference) {
        modelSelector.value = savedPreference;
    }
});

