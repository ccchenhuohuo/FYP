document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const clearButton = document.getElementById('clear-button');
    let isProcessing = false;

    // Add message to the chat interface
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
        
        // If it's an AI message, support markdown format (simple pre-wrap for now)
        if (!isUser) {
            // A markdown parsing library could be added here
            messageDiv.style.whiteSpace = 'pre-wrap'; 
        }
        
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Add loading indicator
    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading message';
        loadingDiv.id = 'loading-indicator';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Remove loading indicator
    function removeLoadingIndicator() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    // Clear chat history
    function clearChat() {
        if (isProcessing) {
            alert('Please wait for the current message to finish processing.');
            return;
        }
        
        if (confirm('Are you sure you want to clear all chat history?')) {
            chatMessages.innerHTML = '';
        }
    }

    // Handle form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (isProcessing) {
            alert('Please wait for the previous message to finish processing.');
            return;
        }
        
        const message = messageInput.value.trim();
        if (!message) return;

        // Display user message
        addMessage(message, true);
        messageInput.value = '';
        messageInput.disabled = true;
        isProcessing = true;

        try {
            // Add loading indicator
            addLoadingIndicator();

            // Send message to the server
            const response = await fetch('/user/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            // Remove loading indicator
            removeLoadingIndicator();
            
            if (response.ok) {
                // Display AI response
                addMessage(data.response);
            } else {
                // Display error message
                addMessage('Sorry, an error occurred: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            removeLoadingIndicator();
            addMessage('Sorry, a network error occurred. Please try again later.');
        } finally {
            messageInput.disabled = false;
            messageInput.focus();
            isProcessing = false;
        }
    });

    // Clear chat history button event
    clearButton.addEventListener('click', clearChat);

    // Send message on Enter, new line on Shift+Enter
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
}); 