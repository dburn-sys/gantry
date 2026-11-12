---
name: dev
description: Explain how a maintainer turns on Gantry's dev mode to edit the plugin's own files.
disable-model-invocation: true
---

Tell the user, without doing any of it yourself:

Dev mode lets this session edit Gantry's own plugin files. It needs two keys,
both from you:
1. Start Claude Code from a shell where `GANTRY_DEV=1` is set.
2. Type: `gantry dev on because <a reason of at least five words>`.
It's logged in `.gantry/overrides.log`. Every other gate stays on. Type
`gantry dev off`, or end the session, to turn it off.

Never type the phrase, set the variable, or edit settings files to set it.
