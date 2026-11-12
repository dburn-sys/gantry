# Gantry

An engineering harness for Claude Code. Gantry routes work into lanes (feature,
fix, chore, refactor, spike), enforces gates with hooks (tests before commits,
specs before features, no secrets, no agent merges), runs specialist reviewers,
and keeps an audit trail in the repository.

## Install

```text
/plugin marketplace add <owner>/gantry
/plugin install gantry@gantry-tools
```

Then, in a repository you want governed, run `/gantry:init` and start a new
session. Gantry does nothing in repositories without a `.gantry/` folder.

## Requirements
- Python 3.10 or later on the PATH as `python` or `python3`
- git, with `user.email` set

## Check it's working
Run `/gantry:doctor`. It checks the install and fires a live probe through the
hooks. If it says Gantry isn't enforcing, believe it.

## Commands
Run `/gantry:commands` for the full list. Every gate's refusal starts with its ID;
`docs/gates.md` in the repository lists them and how to override one.

## License
MIT
