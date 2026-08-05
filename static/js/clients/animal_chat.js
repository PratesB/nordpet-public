document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return; // Exit if not on the chat page
    
    // Retrieve metadata passed from Django template
    const petId = chatContainer.getAttribute('data-pet-id');
    const doctorName = chatContainer.getAttribute('data-doctor-name');

    // UI Elements
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const submitBtn = document.getElementById('chat-submit');
    
    // Array to keep track of conversation context for the AI
    let chatHistory = [];

    // Enable or disable the submit button based on user input
    input.addEventListener('input', function() {
        submitBtn.disabled = this.value.trim() === '';
    });
    
    // Initially disable the submit button since the input is empty
    submitBtn.disabled = true;

    // Helper function to auto-scroll to the newest message
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Helper function to generate the current timestamp
    function getCurrentTime() {
        const now = new Date();
        const date = now.toLocaleDateString([], {day: '2-digit', month: '2-digit', year: 'numeric'});
        const time = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        return `${date} - ${time}`;
    }

    // Appends the user's message to the chat interface using a hidden HTML template
    function appendUserMessage(text) {
        const template = document.getElementById('user-message-template');
        const clone = template.content.cloneNode(true);
        
        clone.querySelector('.user-meta').innerHTML = `${getCurrentTime()} &nbsp; <strong class="text-on-surface">${doctorName}</strong>`;
        clone.querySelector('.user-text').textContent = text;
        
        messagesContainer.appendChild(clone);
        scrollToBottom();
    }

    // Appends the AI's response to the chat interface using a hidden HTML template
    function appendAIMessage(text) {
        const template = document.getElementById('ai-message-template');
        const clone = template.content.cloneNode(true);
        
        clone.querySelector('.ai-meta').innerHTML = `
            <span class="material-symbols-outlined text-[14px] text-primary">smart_toy</span>
            <strong class="text-on-surface">AI Assistant</strong> &nbsp; <span class="opacity-70">${getCurrentTime()}</span>
        `;
        
        // Basic markdown formatting (bolding text and rendering line breaks)
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        clone.querySelector('.ai-text').innerHTML = formattedText;
        
        messagesContainer.appendChild(clone);
        scrollToBottom();
    }
    
    // Displays the "Typing..." animation while waiting for the API response
    function appendTypingIndicator() {
        const template = document.getElementById('typing-indicator-template');
        const clone = template.content.cloneNode(true);
        messagesContainer.appendChild(clone);
        scrollToBottom();
    }
    
    // Removes the "Typing..." animation once the API responds
    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Handle form submission (when the user sends a message)
    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent full page reload
        
        const question = input.value.trim();
        if (!question) return;

        // Clear and disable input/button while processing
        input.value = '';
        input.disabled = true;
        submitBtn.disabled = true;
        
        // Immediately show user message and typing animation for good UX
        appendUserMessage(question);
        appendTypingIndicator();

        try {
            // Helper function to extract CSRF token from browser cookies for security
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            const csrftoken = getCookie('csrftoken');

            // Send asynchronous request to Django API
            const response = await fetch(`/clients/api/animal-chat/${petId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken // Inject CSRF token to pass Django's security checks
                },
                body: JSON.stringify({
                    question: question
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            // Remove the typing animation as we are about to start receiving text
            removeTypingIndicator();
            
            // Create the AI message skeleton in the DOM immediately
            const template = document.getElementById('ai-message-template');
            const clone = template.content.cloneNode(true);
            
            clone.querySelector('.ai-meta').innerHTML = `
                <span class="material-symbols-outlined text-[14px] text-primary">smart_toy</span>
                <strong class="text-on-surface">AI Assistant</strong> &nbsp; <span class="opacity-70">${getCurrentTime()}</span>
            `;
            
            const aiTextElement = clone.querySelector('.ai-text');
            aiTextElement.innerHTML = ""; // Empty initially
            
            messagesContainer.appendChild(clone);
            
            // Read stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let aiMessageText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                // Decode binary chunks into strings
                const chunkStr = decoder.decode(value, { stream: true });
                
                // Split by Server-Sent Event boundary
                const lines = chunkStr.split("\n\n");
                
                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const dataStr = line.substring(6);
                        
                        if (dataStr === "[DONE]") break; // End of stream
                        
                        try {
                            const data = JSON.parse(dataStr);
                            aiMessageText += data.chunk;
                            
                            // Basic markdown formatting in real-time
                            const formattedText = aiMessageText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
                            aiTextElement.innerHTML = formattedText;
                            
                            // Autoscroll as new text arrives
                            scrollToBottom();
                        } catch (e) {
                            console.error('Error parsing stream data:', e);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            appendAIMessage("An error occurred. Please try again.");
        } finally {
            // Re-enable input and button, and set focus back to the input field
            input.disabled = false;
            submitBtn.disabled = false;
            input.focus();
        }
    });
});
