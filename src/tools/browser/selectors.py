"""
core_framework/browser/selectors.py

Stable CSS selectors for each benchmark frontend.
We own all target apps, so hardcoded selectors are safe and reliable.

All vulnerable apps share the same React component structure:
  .chat-input        — text input field
  .send-button       — submit button  (chatbot_vuln)
  .send-btn          — submit button  (rag_vuln, tool_agent_vuln, hardened)
  .message.bot       — assistant message bubbles (chatbot_vuln)
  .bubble.assistant  — assistant message bubbles (hardened variants)
  .message-wrapper   — message container rows

The hardened variants frontend uses tabs; the selector set includes a
tab switcher for selecting bot / rag / tool mode.
"""

from typing import TypedDict

__all__ = ["SELECTORS", "TargetSelectors"]


class TargetSelectors(TypedDict):
    chat_input: str             # CSS selector for the text input
    send_button: str            # CSS selector for the submit button
    bot_message: str            # CSS selector to grab the last assistant reply
    typing_indicator: str       # CSS selector for the loading spinner
    # Optional — only used by hardened_variants tab switching
    tab_button_template: str    # format string, fill with tab id: bot / rag / tool


# Shared base for the three simple single-page apps
_SIMPLE_APP: TargetSelectors = {
    "chat_input":         ".chat-input",
    "send_button":        ".send-button",
    "bot_message":        ".message.bot, .system-error",
    "typing_indicator":   ".typing-indicator",
    "tab_button_template": "",
}

# rag_vuln and tool_agent_vuln use .send-btn (not .send-button)
_SIMPLE_APP_ALT_BTN: TargetSelectors = {
    **_SIMPLE_APP,
    "send_button": ".send-btn",
}

SELECTORS: dict[str, TargetSelectors] = {
    "chatbot_vuln": _SIMPLE_APP,
    "rag_vuln": _SIMPLE_APP,
    # tool_agent uses Tailwind-only classes — no .message.bot or .chat-input exist.
    # Bot messages are divs with text-indigo-400; input is a bare <input>; submit is an icon-only <button type="submit">.
    "tool_agent_vuln": {
        "chat_input":         "input[placeholder*='command' i], input[placeholder*='operation' i], input[placeholder*='message' i]",
        "send_button":        "button[type='submit']",
        "bot_message":        "div.text-indigo-400 > div.flex-1, div.flex.gap-3.text-indigo-400 > div.flex-1",
        "typing_indicator":   "div.text-indigo-400 .animate-spin",
        "tab_button_template": "",
    },
    "hardened_variants": {
        # The hardened frontend renders all 3 ChatWindows simultaneously.
        # React sets display:flex on the active wrapper, display:none on inactive ones.
        # Scoping through div[style*='display: flex'] isolates the active tab's elements.
        # bot_message also includes .bubble.error so errors don't cause a timeout.
        "chat_input":         "div[style*='display: flex'] .chat-input",
        "send_button":        "div[style*='display: flex'] .send-btn",
        "bot_message":        "div[style*='display: flex'] .bubble.assistant, div[style*='display: flex'] .bubble.error",
        "typing_indicator":   "div[style*='display: flex'] .bubble.assistant.typing",
        "tab_button_template": ".tab-btn:has-text('{tab_label}')",
    },
    "generic": {
        "chat_input":         "textarea[placeholder*='message' i], input[placeholder*='message' i], textarea[placeholder*='question' i], textarea[placeholder*='ask' i], input[placeholder*='query' i], input[placeholder*='command' i], textarea[placeholder*='command' i], textarea[placeholder*='type' i], p[contenteditable='true'], div[contenteditable='true'], rich-textarea, .chat-input, #chat-input, #prompt-textarea, [data-testid*='input'], [aria-label*='message' i], [aria-label*='prompt' i], [aria-label*='chat' i], [aria-label*='ask' i], [placeholder*='Gemini' i]",
        "send_button":        "button[type='submit'], button.bg-zinc-100, button:has(svg[class*='arrow']), button:has(svg[class*='send']), button:has(svg[class*='plane']), button:has(svg[data-lucide]), button:has-text('Send'), .send-button, #send-button, .send-btn",
        "bot_message":        "p.text-zinc-500, div.text-zinc-500, div.text-zinc-300, .message.bot, .assistant-message, [class*='assistant'], [class*='bot-message'], div.justify-start > div.shadow-md, div.justify-start > div > p",
        "typing_indicator":   "div:has-text('THINKING'), .typing, .loading, .spinner, [class*='typing'], .animate-spin",
        "tab_button_template": ""
    }
}
