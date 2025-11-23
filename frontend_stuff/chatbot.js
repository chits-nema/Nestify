// chatbot.js - AI Home Buying Advisor Integration

const CHATBOT_API = 'http://127.0.0.1:8000/chatbot';

// State
let conversationHistory = [];
let chatbotOpen = false;
let isProcessing = false;

// Quick reply suggestions
const quickReplies = [
  "What can I afford?",
  "Best neighborhoods?",
  "Analyze my preferences",
  "Check property value"
];

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initializeChatbot();
});

function initializeChatbot() {
  // Create chatbot UI elements
  createChatbotUI();
  
  // Attach event listeners
  document.getElementById('chatbotToggle').addEventListener('click', toggleChatbot);
  document.getElementById('chatbotClose').addEventListener('click', toggleChatbot);
  document.getElementById('chatbotClear').addEventListener('click', confirmClearChat);
  document.getElementById('chatbotSend').addEventListener('click', sendMessage);
  document.getElementById('chatbotInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Auto-resize textarea
  document.getElementById('chatbotInput').addEventListener('input', autoResizeTextarea);
  
  // Load conversation history from session storage
  loadConversationHistory();
  
  // Add welcome message if no history
  if (conversationHistory.length === 0) {
    addBotMessage("Hi! I'm your personal home buying advisor. I can help you understand your budget, analyze properties you like, and guide you through the home buying process. What would you like to know?");
    showQuickReplies();
  }
}

function createChatbotUI() {
  const chatbotHTML = `
    <!-- Chatbot Toggle Button -->
    <button id="chatbotToggle" class="chatbot-toggle" title="Chat with AI Advisor">
      💬
    </button>
    
    <!-- Chatbot Window -->
    <div id="chatbotWindow" class="chatbot-window">
      <div class="chatbot-header">
        <div>
          <h3>🏡 Home Advisor</h3>
          <p>AI-powered guidance</p>
        </div>
        <div class="chatbot-header-actions">
          <button id="chatbotClear" class="chatbot-icon-btn" title="Clear conversation">🗑️</button>
          <button id="chatbotClose" class="chatbot-close">✕</button>
        </div>
      </div>
      
      <div id="chatbotMessages" class="chatbot-messages">
        <!-- Messages will be added here -->
      </div>
      
      <div id="quickRepliesContainer" class="quick-replies-container">
        <!-- Quick reply buttons will be added here -->
      </div>
      
      <div class="chatbot-input-area">
        <textarea 
          id="chatbotInput" 
          placeholder="Ask me anything about home buying..."
          rows="2"
        ></textarea>
        <button id="chatbotSend" class="chatbot-send-btn">
          Send
        </button>
      </div>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', chatbotHTML);
}

function toggleChatbot() {
  chatbotOpen = !chatbotOpen;
  const window = document.getElementById('chatbotWindow');
  const toggle = document.getElementById('chatbotToggle');
  
  if (chatbotOpen) {
    window.classList.add('open');
    toggle.classList.add('hidden');
    // Focus input
    setTimeout(() => {
      document.getElementById('chatbotInput').focus();
    }, 300);
  } else {
    window.classList.remove('open');
    toggle.classList.remove('hidden');
  }
}

function addMessage(content, isUser = false) {
  const messagesContainer = document.getElementById('chatbotMessages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `chatbot-message ${isUser ? 'user' : 'bot'}`;
  
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  
  // Format message with basic markdown support
  bubble.innerHTML = formatMessage(content);
  
  messageDiv.appendChild(bubble);
  
  // Add timestamp
  const timestamp = document.createElement('div');
  timestamp.className = 'message-timestamp';
  timestamp.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  messageDiv.appendChild(timestamp);
  
  messagesContainer.appendChild(messageDiv);
  
  // Smooth scroll to bottom
  smoothScrollToBottom(messagesContainer);
  
  return messageDiv;
}

function addBotMessage(content) {
  const msg = addMessage(content, false);
  // Optional: Play subtle notification sound (can be enabled by user)
  // playNotificationSound();
  return msg;
}

function addUserMessage(content) {
  return addMessage(content, true);
}

function addTypingIndicator() {
  const messagesContainer = document.getElementById('chatbotMessages');
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chatbot-message bot typing-indicator';
  typingDiv.id = 'typingIndicator';
  
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = '<span></span><span></span><span></span>';
  
  typingDiv.appendChild(bubble);
  messagesContainer.appendChild(typingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  return typingDiv;
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typingIndicator');
  if (indicator) {
    indicator.remove();
  }
}

async function sendMessage(predefinedMessage = null) {
  if (isProcessing) return;
  
  const input = document.getElementById('chatbotInput');
  const message = predefinedMessage || input.value.trim();
  
  if (!message) return;
  
  isProcessing = true;
  const sendBtn = document.getElementById('chatbotSend');
  sendBtn.disabled = true;
  sendBtn.textContent = '...';
  
  // Hide quick replies
  hideQuickReplies();
  
  // Add user message to UI
  addUserMessage(message);
  
  // Clear input
  input.value = '';
  input.style.height = 'auto';
  
  // Add to conversation history
  conversationHistory.push({
    role: 'user',
    content: message
  });
  
  // Show typing indicator
  addTypingIndicator();
  
  try {
    // Gather context from the app
    const context = gatherUserContext();
    
    // Send to backend
    const response = await fetch(`${CHATBOT_API}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        user_budget: context.budget,
        liked_properties: context.likedProperties,
        conversation_history: conversationHistory
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to get response from advisor');
    }
    
    const data = await response.json();
    
    // Remove typing indicator
    removeTypingIndicator();
    
    // Add bot response
    addBotMessage(data.response);
    
    // Add to conversation history
    conversationHistory.push({
      role: 'assistant',
      content: data.response
    });
    
    // Save conversation to session storage
    saveConversationHistory();
    
    // Show quick replies if appropriate
    if (conversationHistory.length <= 4) {
      showQuickReplies();
    }
    
  } catch (error) {
    console.error('Chatbot error:', error);
    removeTypingIndicator();
    addErrorMessage("I'm having trouble connecting right now.", message);
  } finally {
    isProcessing = false;
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
  }
}

function gatherUserContext() {
  // Gather budget information if available
  let budget = 0;
  if (typeof buyingPower !== 'undefined' && buyingPower > 0) {
    budget = buyingPower;
  }
  
  // Gather liked properties if available (from swipe mode)
  let likedProperties = [];
  if (typeof likedHomes !== 'undefined' && likedHomes.length > 0) {
    likedProperties = likedHomes;
  }
  
  return {
    budget: budget,
    likedProperties: likedProperties
  };
}

// Helper function to check property affordability
async function checkAffordability(propertyPrice, userBudget) {
  try {
    const response = await fetch(`${CHATBOT_API}/affordability`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        property_price: propertyPrice,
        user_budget: userBudget
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to check affordability');
    }
    
    const data = await response.json();
    return data.analysis;
    
  } catch (error) {
    console.error('Affordability check error:', error);
    return null;
  }
}

// Utility Functions

function formatMessage(text) {
  // Basic markdown support
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/€([0-9,]+)/g, '<span class="price">€$1</span>')
    .replace(/\n/g, '<br>');
}

function smoothScrollToBottom(container) {
  container.scrollTo({
    top: container.scrollHeight,
    behavior: 'smooth'
  });
}

function autoResizeTextarea() {
  const textarea = document.getElementById('chatbotInput');
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function showQuickReplies() {
  const container = document.getElementById('quickRepliesContainer');
  container.innerHTML = '';
  
  quickReplies.forEach(reply => {
    const btn = document.createElement('button');
    btn.className = 'quick-reply-btn';
    btn.textContent = reply;
    btn.onclick = () => sendMessage(reply);
    container.appendChild(btn);
  });
  
  container.style.display = 'flex';
}

function hideQuickReplies() {
  const container = document.getElementById('quickRepliesContainer');
  container.style.display = 'none';
}

function addErrorMessage(errorText, originalMessage) {
  const messagesContainer = document.getElementById('chatbotMessages');
  const errorDiv = document.createElement('div');
  errorDiv.className = 'chatbot-message bot error-message';
  
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = `
    <p>${errorText}</p>
    <button class="retry-btn" onclick="retryMessage('${originalMessage.replace(/'/g, "\\'")}')">🔄 Retry</button>
  `;
  
  errorDiv.appendChild(bubble);
  messagesContainer.appendChild(errorDiv);
  smoothScrollToBottom(messagesContainer);
}

function retryMessage(message) {
  // Remove last error message
  const lastError = document.querySelector('.error-message');
  if (lastError) lastError.remove();
  
  // Retry sending
  sendMessage(message);
}

function saveConversationHistory() {
  try {
    sessionStorage.setItem('nestify_chat_history', JSON.stringify(conversationHistory));
  } catch (e) {
    console.warn('Failed to save conversation history:', e);
  }
}

function loadConversationHistory() {
  try {
    const saved = sessionStorage.getItem('nestify_chat_history');
    if (saved) {
      conversationHistory = JSON.parse(saved);
      // Restore messages in UI
      conversationHistory.forEach(msg => {
        if (msg.role === 'user') {
          addUserMessage(msg.content);
        } else if (msg.role === 'assistant') {
          addBotMessage(msg.content);
        }
      });
    }
  } catch (e) {
    console.warn('Failed to load conversation history:', e);
  }
}

function clearConversationHistory() {
  conversationHistory = [];
  sessionStorage.removeItem('nestify_chat_history');
  document.getElementById('chatbotMessages').innerHTML = '';
  addBotMessage("Hi! I'm your personal home buying advisor. How can I help you today?");
  showQuickReplies();
}

function confirmClearChat() {
  if (confirm('Clear conversation history? This cannot be undone.')) {
    clearConversationHistory();
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { checkAffordability, gatherUserContext, clearConversationHistory };
}
