# Inbox

Drop zone. Put anything here the agent should learn from: emails, notes, exports,
transcripts, screenshots, a pasted message. Then tell the agent "remember the inbox".

The agent files each item, verbatim, into `memory/raw/` (`python3 tools/memory.py file`)
and compiles what matters into `memory/wiki/`. This folder empties as it goes.
