import os
import sys
import yaml
import httpx
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Include parent directory to locate local dependencies
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark_apps.factory_defenses import InputFilter, OutputFilter, DLPMonitor, SemanticFilter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("factory_server")

# Load environment configs
load_dotenv()

app = FastAPI(title="Aegis-Red Benchmark Target Factory")

# Enable CORS for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active Target configurations
target_config = {}
input_filter: Optional[InputFilter] = None
output_filter: Optional[OutputFilter] = None
dlp_monitor: Optional[DLPMonitor] = None
semantic_filter: Optional[SemanticFilter] = None

class Message(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    messages: List[Message]

@app.get("/health")
def health():
    return {"status": "healthy", "target": target_config.get("id", "none")}

HTML_CHAT_UI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Aegis-Red Target Chatbot UI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #0a0b0d;
            color: #c5c6c7;
        }
    </style>
</head>
<body class="flex flex-col h-screen">
    <header class="bg-gray-950 border-b border-gray-800 p-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-teal-400 font-mono" id="target-title">CHATBOT TARGET</h1>
        <span class="px-3 py-1 bg-gray-900 text-xs text-gray-400 font-mono rounded" id="target-type-badge">TYPE: unknown</span>
    </header>
    
    <main class="flex-1 overflow-y-auto p-4 space-y-4" id="chat-messages">
        <div class="assistant-message bg-gray-900 p-3 rounded-lg max-w-xl text-zinc-300">
            Hello, how can I assist you today?
        </div>
    </main>

    <div id="typing-indicator" class="hidden px-4 py-2 text-sm text-gray-500 font-mono animate-pulse">
        Bot is thinking...
    </div>

    <footer class="p-4 bg-gray-950 border-t border-gray-800">
        <form id="chat-form" class="flex gap-2">
            <textarea id="chat-input" class="chat-input flex-1 bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none focus:border-teal-500" placeholder="Type a message..." rows="1"></textarea>
            <button type="submit" id="send-button" class="send-button px-6 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded font-bold font-mono transition-colors">Send</button>
        </form>
    </footer>

    <script>
        const chatForm = document.getElementById('chat-form');
        const chatInput = document.getElementById('chat-input');
        const chatMessages = document.getElementById('chat-messages');
        const typingIndicator = document.getElementById('typing-indicator');
        const targetTitle = document.getElementById('target-title');
        const targetTypeBadge = document.getElementById('target-type-badge');

        let messages = [];

        fetch('/health')
            .then(res => res.json())
            .then(data => {
                if (data.target && data.target !== 'none') {
                    targetTitle.textContent = data.target.toUpperCase();
                    targetTypeBadge.textContent = 'TYPE: ' + data.target;
                }
            });

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (!text) return;

            chatInput.value = '';

            const userDiv = document.createElement('div');
            userDiv.className = 'user-message bg-gray-800 p-3 rounded-lg max-w-xl ml-auto text-white';
            userDiv.textContent = text;
            chatMessages.appendChild(userDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            messages.push({ role: 'user', content: text });

            typingIndicator.classList.remove('hidden');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: messages })
                });
                
                const data = await response.json();
                
                typingIndicator.classList.add('hidden');

                const botDiv = document.createElement('div');
                botDiv.className = 'assistant-message bg-gray-900 p-3 rounded-lg max-w-xl text-zinc-300';
                botDiv.textContent = data.content;
                chatMessages.appendChild(botDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;

                messages.push({ role: 'assistant', content: data.content });
            } catch (err) {
                typingIndicator.classList.add('hidden');
                const errDiv = document.createElement('div');
                errDiv.className = 'assistant-message bg-red-950 border border-red-800 p-3 rounded-lg max-w-xl text-red-200';
                errDiv.textContent = '[AEGIS_ERROR: Failed to connect to server backend]';
                chatMessages.appendChild(errDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        });

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    </script>
</body>
</html>"""

@app.get("/chat", response_class=HTMLResponse)
def get_chat_page():
    return HTML_CHAT_UI

@app.post("/configure")
def configure(config: dict):
    """
    Dynamically re-configure the server behavior from YAML target blueprint mappings.
    """
    global target_config, input_filter, output_filter, dlp_monitor, semantic_filter
    target_config = config
    
    # Initialize defense wrappers
    defenses = config.get("defenses", {})
    input_filter = InputFilter(defenses.get("input_filter", {}))
    output_filter = OutputFilter(defenses.get("output_filter", {}))
    dlp_monitor = DLPMonitor(defenses.get("dlp", {}))
    semantic_filter = SemanticFilter(defenses.get("semantic_filter", {}))
    
    # Supply secondary key if enabled
    secondary_key = os.getenv("SECONDARY_GROQ_API_KEY")
    if not secondary_key:
        secondary_key = os.getenv("GROQ_API_KEY") # Fallback to primary key if secondary is absent
    semantic_filter.set_api_key(secondary_key)

    logger.info(f"Target Factory configured as: {config.get('name')} (Tier {config.get('tier')})")
    return {"status": "configured", "name": config.get("name")}

def query_model(messages: List[dict], system_prompt: str) -> str:
    """
    Direct model execution layer using primary configuration key.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("Missing GROQ_API_KEY inside environment configuration.")
        return "[AEGIS_ERROR: Server missing API key configuration]"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepend target system prompt
    formatted_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        formatted_messages.append({"role": msg["role"], "content": msg["content"]})
        
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": formatted_messages,
        "temperature": 0.2
    }
    
    try:
        with httpx.Client() as client:
            r = client.post(url, json=payload, headers=headers, timeout=30.0)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"Groq API Error: {r.status_code} - {r.text}")
                return f"[AEGIS_ERROR: API returned code {r.status_code}]"
    except Exception as e:
        logger.error(f"Failed model invocation: {e}")
        return "[AEGIS_ERROR: Connection failed]"

@app.post("/chat")
def chat(payload: ChatPayload):
    global target_config, input_filter, output_filter, dlp_monitor, semantic_filter
    
    if not target_config:
        raise HTTPException(status_code=400, detail="Target not configured. Call /configure first.")

    messages = [msg.dict() for msg in payload.messages]
    last_user_message = messages[-1]["content"] if messages else ""

    # 1. Input Defenses
    if input_filter:
        passed, error_msg = input_filter.check(last_user_message)
        if not passed:
            return {"role": "assistant", "content": error_msg}

    # 2. Semantic Defenses (if enabled)
    if semantic_filter:
        passed, error_msg = semantic_filter.check_injection(last_user_message)
        if not passed:
            return {"role": "assistant", "content": error_msg}

    # 3. Retrieve context for RAG targets
    system_prompt = target_config.get("system_prompt", "")
    target_type = target_config.get("type", "chatbot")
    
    if target_type == "rag" and "documents" in target_config:
        # Simple TF-IDF/Keyword scoring for dynamic context assembly
        docs = target_config.get("documents", [])
        matched_docs = []
        user_words = set(last_user_message.lower().split())
        
        for doc in docs:
            # Check RBAC settings first
            is_confidential = doc.get("classification") == "confidential"
            rbac_enabled = target_config.get("defenses", {}).get("rbac", {}).get("enabled", False)
            confidential_keyword = target_config.get("defenses", {}).get("rbac", {}).get("confidential_keyword", "confidential")
            
            if rbac_enabled and is_confidential:
                # Basic context sanitization: reject if context query has direct matches or lacks permissions
                if confidential_keyword.lower() in last_user_message.lower():
                    logger.warning(f"RBAC dropped document retrieval: {doc.get('title')}")
                    continue

            # Core keyword match overlap ranking
            doc_words = set(doc.get("content", "").lower().split())
            score = len(user_words.intersection(doc_words))
            if score > 0:
                matched_docs.append((score, doc))
                
        # Sort and take top matches
        matched_docs.sort(key=lambda x: x[0], reverse=True)
        retrieved_content = []
        for _, doc in matched_docs[:2]:
            retrieved_content.append(f"Document: {doc['title']}\nContent: {doc['content']}")
            
        if retrieved_content:
            context_block = "\n\nContext Documents:\n" + "\n---\n".join(retrieved_content)
            system_prompt += context_block

    # 4. Handle Tool Agent behaviors
    if target_type == "tool_agent":
        # Check if the user attempts to invoke a configured tool
        tools = target_config.get("tools", [])
        for tool in tools:
            tool_name = tool.get("name")
            if tool_name in last_user_message.lower():
                # Check for Server-Side RBAC enforcement
                if tool.get("requires_admin") and tool.get("server_side_check"):
                    # Check for direct auth token inside mock request headers
                    if "fortress-admin" not in last_user_message.lower() and "super-secret" not in last_user_message.lower():
                        logger.warning(f"Server-Side Tool verification failed for: {tool_name}")
                        return {"role": "assistant", "content": f"Server Error: Unauthorized access. Incident logged for execution: {tool_name}."}
                
                # Dynamic logging output stub for executable triggers
                logger.info(f"Tool executed: {tool_name}")

    # 5. Execute LLM generation
    # Apply Meta-Prompt wrapping if enabled
    if target_config.get("meta_prompt_wrapping"):
        messages[-1]["content"] = f"User Input:\n===\n{last_user_message}\n==="
        
    raw_response = query_model(messages, system_prompt)

    # 6. Output defenses & DLP monitors
    if dlp_monitor:
        passed, error_msg = dlp_monitor.check(raw_response)
        if not passed:
            return {"role": "assistant", "content": error_msg}

    if output_filter:
        raw_response = output_filter.clean(raw_response)

    # Apply length limits if configured
    length_limit = target_config.get("defenses", {}).get("response_length_limit", {})
    if length_limit.get("enabled"):
        max_chars = length_limit.get("max_chars", 500)
        if len(raw_response) > max_chars:
            raw_response = raw_response[:max_chars] + "\n[Truncated due to output safety constraints]"

    return {"role": "assistant", "content": raw_response}

if __name__ == "__main__":
    import uvicorn
    # Accept configuration filepath as argument
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to initial configuration YAML file")
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_known_args()[0]
    
    if args.config:
        with open(args.config, "r") as f:
            yaml_config = yaml.safe_load(f)
            configure(yaml_config)
            
    uvicorn.run(app, host="127.0.0.1", port=args.port)
