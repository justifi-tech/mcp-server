#!/usr/bin/env python3
"""
JustiFi Web Chat Example - v1.0.23 Standardized Response Format

This example demonstrates a web chat interface that properly handles
standardized responses from justifi-mcp-server v1.0.23. Shows how web
applications should consume and display JustiFi data consistently.

Key Features:
- Web-based chat interface using Starlette/FastAPI
- Consistent handling of standardized agent responses
- Real-time data formatting and display
- Error handling for failed requests
- Support for all JustiFi data types

Requirements:
    uv pip install starlette uvicorn langchain langchain-openai jinja2 python-multipart

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID  
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key

Usage:
    python examples/web_chat.py
    Open http://localhost:8000 in your browser
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

# Import our JustiFi MCP agent
from justifi_mcp import JustiFiMCPAgent


class WebChatService:
    """
    Web chat service that handles standardized JustiFi MCP responses.
    
    This service demonstrates how web applications should consume the
    v1.0.23 standardized response format consistently.
    """

    def __init__(self):
        """Initialize the web chat service."""
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the JustiFi MCP agent."""
        try:
            self.agent = JustiFiMCPAgent()
            print("✅ JustiFi MCP Agent initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize JustiFi MCP Agent: {e}")
            self.agent = None

    async def process_chat_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Process a chat message and return structured response.
        
        This method demonstrates proper handling of agent responses
        and consistent formatting for web display.
        """
        if not self.agent:
            return {
                "success": False,
                "message": "⚠️ JustiFi agent not available. Please check your configuration.",
                "error": "Agent initialization failed",
                "timestamp": datetime.now().isoformat()
            }

        try:
            # Process the message using our standardized agent
            response = await self.agent.process_request(message)
            
            # Parse and structure the response for web display
            return self._format_web_response(response, message)
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Error processing your request: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _format_web_response(self, agent_response: str, original_message: str) -> Dict[str, Any]:
        """
        Format agent response for web display.
        
        This demonstrates how web applications should handle the
        consistently formatted responses from the v1.0.23 agent.
        """
        # Determine response type based on original message
        response_type = self._detect_response_type(original_message)
        
        # Structure the response for web display
        return {
            "success": True,
            "message": agent_response,
            "type": response_type,
            "formatted": self._apply_web_formatting(agent_response, response_type),
            "timestamp": datetime.now().isoformat(),
            "original_message": original_message
        }

    def _detect_response_type(self, message: str) -> str:
        """Detect the type of response based on the user message."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["payout", "payouts"]):
            return "payouts"
        elif any(word in message_lower for word in ["payment", "payments"]):
            return "payments"
        elif any(word in message_lower for word in ["transaction", "transactions", "balance"]):
            return "transactions"
        elif any(word in message_lower for word in ["dispute", "disputes"]):
            return "disputes"
        elif any(word in message_lower for word in ["refund", "refunds"]):
            return "refunds"
        elif any(word in message_lower for word in ["checkout", "checkouts"]):
            return "checkouts"
        else:
            return "general"

    def _apply_web_formatting(self, response: str, response_type: str) -> Dict[str, Any]:
        """
        Apply web-specific formatting to the response.
        
        This shows how to convert the standardized agent response
        into structured data for web display components.
        """
        # Extract key information for web display
        lines = response.split('\n')
        
        formatted_response = {
            "type": response_type,
            "summary": {},
            "details": [],
            "raw_text": response
        }

        # Parse summary information (works with v1.0.23 standardized format)
        for line in lines:
            if "Total" in line and ":" in line:
                key, value = line.split(":", 1)
                formatted_response["summary"][key.strip("- *")] = value.strip()
            elif "Combined Amount" in line and ":" in line:
                key, value = line.split(":", 1)
                formatted_response["summary"][key.strip("- *")] = value.strip()
            elif "Status Breakdown" in line and ":" in line:
                key, value = line.split(":", 1)
                formatted_response["summary"][key.strip("- *")] = value.strip()

        # Extract detail items
        in_details = False
        for line in lines:
            if line.startswith("**Recent"):
                in_details = True
                continue
            elif in_details and line.startswith("•"):
                formatted_response["details"].append(line.strip("• "))

        return formatted_response


# Initialize the web chat service
web_chat_service = WebChatService()

# HTML template for the chat interface
CHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JustiFi Web Chat - v1.0.23 Demo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-header h1 {
            margin: 0;
            font-size: 24px;
        }
        .chat-header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }
        .chat-messages {
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 8px;
        }
        .user-message {
            background: #e3f2fd;
            margin-left: 50px;
            border-left: 4px solid #2196f3;
        }
        .bot-message {
            background: white;
            margin-right: 50px;
            border-left: 4px solid #4caf50;
        }
        .error-message {
            background: #ffebee;
            margin-right: 50px;
            border-left: 4px solid #f44336;
        }
        .message-header {
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 14px;
            color: #666;
        }
        .message-content {
            white-space: pre-wrap;
            line-height: 1.5;
        }
        .message-summary {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 14px;
        }
        .summary-item {
            margin: 5px 0;
        }
        .chat-input {
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            background: white;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        .message-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
        }
        .message-input:focus {
            border-color: #667eea;
        }
        .send-button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
        }
        .send-button:hover {
            opacity: 0.9;
        }
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .typing-indicator {
            padding: 10px 15px;
            background: white;
            margin-right: 50px;
            border-left: 4px solid #ffc107;
            border-radius: 8px;
            font-style: italic;
            color: #666;
        }
        .example-queries {
            padding: 15px 20px;
            background: #e8f5e8;
            border-top: 1px solid #c8e6c9;
        }
        .example-queries h3 {
            margin: 0 0 10px 0;
            color: #2e7d32;
            font-size: 16px;
        }
        .example-query {
            display: inline-block;
            background: #4caf50;
            color: white;
            padding: 8px 12px;
            margin: 4px 8px 4px 0;
            border-radius: 15px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        .example-query:hover {
            background: #388e3c;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🏦 JustiFi Web Chat</h1>
            <p>v1.0.23 Standardized Response Format Demo</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                <div class="message-header">🤖 JustiFi Assistant</div>
                <div class="message-content">Welcome! I'm your JustiFi assistant with v1.0.23 standardized response handling.

I can help you with:
• Payout information and analysis
• Payment details and status
• Transaction history and breakdowns
• Dispute and refund tracking
• Account and balance information

All responses use the new standardized format for consistent data display.</div>
            </div>
        </div>
        
        <div class="example-queries">
            <h3>💡 Try these examples:</h3>
            <span class="example-query" onclick="sendExampleQuery('Tell me about my last 5 payouts')">Last 5 payouts</span>
            <span class="example-query" onclick="sendExampleQuery('Show me recent payments and their status')">Recent payments</span>
            <span class="example-query" onclick="sendExampleQuery('Get my balance transactions')">Balance transactions</span>
            <span class="example-query" onclick="sendExampleQuery('Any disputes or refunds?')">Disputes & refunds</span>
        </div>
        
        <div class="chat-input">
            <div class="input-container">
                <input type="text" id="messageInput" class="message-input" 
                       placeholder="Ask about your payouts, payments, transactions..." 
                       onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" id="sendButton" class="send-button">Send</button>
            </div>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;

            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            const typingId = addTypingIndicator();
            
            // Disable input while processing
            setInputEnabled(false);

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                // Remove typing indicator
                removeTypingIndicator(typingId);
                
                // Add bot response
                if (data.success) {
                    addMessage(data.message, 'bot', data.formatted);
                } else {
                    addMessage(data.message || 'Sorry, something went wrong.', 'error');
                }
                
            } catch (error) {
                removeTypingIndicator(typingId);
                addMessage('Connection error. Please try again.', 'error');
            }
            
            // Re-enable input
            setInputEnabled(true);
        }

        function addMessage(content, type, formatted = null) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            
            let className = type === 'user' ? 'user-message' : 
                           type === 'error' ? 'error-message' : 'bot-message';
            
            let header = type === 'user' ? '👤 You' : 
                        type === 'error' ? '⚠️ Error' : '🤖 JustiFi Assistant';
            
            messageDiv.className = `message ${className}`;
            messageDiv.innerHTML = `
                <div class="message-header">${header}</div>
                <div class="message-content">${content}</div>
            `;
            
            // Add formatted summary if available (demonstrates v1.0.23 structured data)
            if (formatted && formatted.summary && Object.keys(formatted.summary).length > 0) {
                const summaryDiv = document.createElement('div');
                summaryDiv.className = 'message-summary';
                summaryDiv.innerHTML = '<strong>📊 Quick Summary:</strong><br>' + 
                    Object.entries(formatted.summary)
                        .map(([key, value]) => `<div class="summary-item"><strong>${key}:</strong> ${value}</div>`)
                        .join('');
                messageDiv.appendChild(summaryDiv);
            }
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addTypingIndicator() {
            const messagesContainer = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            const id = 'typing-' + Date.now();
            
            typingDiv.id = id;
            typingDiv.className = 'typing-indicator';
            typingDiv.innerHTML = '🤖 JustiFi Assistant is thinking...';
            
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            return id;
        }

        function removeTypingIndicator(id) {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
            }
        }

        function setInputEnabled(enabled) {
            document.getElementById('messageInput').disabled = !enabled;
            document.getElementById('sendButton').disabled = !enabled;
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function sendExampleQuery(query) {
            document.getElementById('messageInput').value = query;
            sendMessage();
        }

        // Focus input on page load
        document.getElementById('messageInput').focus();
    </script>
</body>
</html>
"""


async def chat_page(request):
    """Serve the chat interface."""
    return HTMLResponse(CHAT_HTML)


async def chat_api(request):
    """Handle chat API requests."""
    try:
        body = await request.json()
        message = body.get('message', '').strip()
        
        if not message:
            return JSONResponse({
                "success": False,
                "message": "Please provide a message.",
                "error": "Empty message"
            })

        # Process the message using our web chat service
        response = await web_chat_service.process_chat_message(message)
        return JSONResponse(response)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Server error: {str(e)}",
            "error": str(e)
        }, status_code=500)


async def health_check(request):
    """Health check endpoint."""
    agent_status = "ready" if web_chat_service.agent else "not initialized"
    
    return JSONResponse({
        "status": "ok",
        "version": "v1.0.23",
        "agent_status": agent_status,
        "standardized_responses": True,
        "timestamp": datetime.now().isoformat()
    })


# Define routes
routes = [
    Route('/', chat_page),
    Route('/chat', chat_api, methods=['POST']),
    Route('/health', health_check),
]

# Create Starlette application
app = Starlette(debug=True, routes=routes)


def main():
    """Main entry point for the web chat application."""
    print("🚀 Starting JustiFi Web Chat - v1.0.23 Demo")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["JUSTIFI_CLIENT_ID", "JUSTIFI_CLIENT_SECRET", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables and try again.")
        return
    
    print("✅ Environment variables configured")
    print("🌐 Starting web server...")
    print("📱 Open http://localhost:8000 in your browser")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()