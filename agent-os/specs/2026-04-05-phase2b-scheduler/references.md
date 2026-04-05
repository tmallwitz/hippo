# References for Phase 2b

## Phase 1+2 Store Patterns

- **Location:** hippo/memory/semantic.py, hippo/memory/episodic.py
- **Key patterns:** asyncio.to_thread, asyncio.Lock, python-frontmatter,
  module-level stores with getter functions in server.py

## Telegram Proactive Messaging

- **API:** `bot.send_message(chat_id=user_id, text=...)` for unprompted messages
- **Formatting:** reuse convert_to_telegram() from telegram_bridge.py
