# Manual hook checks (Chapter 9)

Run from a repo that has a `.gantry/` folder, on `main`. Each should print a deny.

    echo '{"tool_name":"Bash","cwd":".","tool_input":{"command":"git push origin +main"}}' | python hooks/pre_bash.py
    echo '{"tool_name":"Bash","cwd":".","tool_input":{"command":"git -c push.default=current push --force"}}' | python hooks/pre_bash.py
    echo '{"tool_name":"Bash","cwd":".","tool_input":{"command":"npm test && git push --force-with-lease"}}' | python hooks/pre_bash.py
    echo '{"tool_name":"Bash","cwd":".","tool_input":{"command":"git push origin HEAD"}}' | python hooks/pre_bash.py

Fail-open check (prints a systemMessage warning, exits 0):

    echo 'this is not json' | python hooks/pre_bash.py
