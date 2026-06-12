"""
Example 5 — Mini command DSL
=============================

Build a tiny command dispatcher using pattern matching.  Demonstrates:

* ``enum`` — pick one command alternative
* ``rex`` — match numeric arguments
* ``ext`` — optional flags
* ``apply`` — custom validation on the command

Commands supported:

    move <x> <y> [--fast]
    say <message...>
    quit

Run:  python examples/mini_commands.py
"""

from latychain import Chain, Patom

# ── Patterns ────────────────────────────────────────────────

move_rule = (
    Chain
    / "move"
    / Patom.rex(r"\d+")                         # x
    / Patom.rex(r"\d+")                         # y
    / Patom.ext(Chain(["--fast"]))              # optional flag
)

say_rule = (
    Chain
    / "say"
    / Patom.any(1)                              # at least 1 word
)

quit_rule = Chain(["quit"])

# Master dispatcher — try each command
master_rule = Chain / Patom.enum(move_rule, say_rule, quit_rule)

# ── Execute ─────────────────────────────────────────────────

def dispatch(tokens: list[str]) -> str:
    data = Chain(tokens)
    if not data.match(master_rule):
        return "❌ Unknown command"

    if data.match(move_rule):
        fast = "fast " if "--fast" in data else ""
        return f"🏃 Moving {fast}to ({data[1]}, {data[2]})"

    if data.match(say_rule):
        words = " ".join(data.to_list()[1:])
        return f"💬 {words}"

    if data.match(quit_rule):
        return "👋 Goodbye!"

    return "❌ Unknown command"

# ── Tests ───────────────────────────────────────────────────

print("=" * 55)
print("Mini command DSL")
print("=" * 55)

commands = [
    ["move", "10", "20"],
    ["move", "5", "99", "--fast"],
    ["say", "hello", "world"],
    ["say", "one"],
    ["quit"],
    ["jump"],                    # unknown
    ["move", "abc", "10"],       # x not a number
    ["say"],                     # no message
]

for cmd in commands:
    result = dispatch(cmd)
    raw = " ".join(cmd)
    print(f"  {raw:30s}  → {result}")
