"""
Example 3 — Log classifier
===========================

Classify structured log lines: match a date-prefix (``YYYY MM DD``), then
a severity level, then an arbitrary message.

* Only ``ERROR`` and ``CRITICAL`` are flagged.
* ``INFO``, ``WARN``, ``DEBUG`` are silently ignored.

Run:  python examples/log_classifier.py
"""

from latychain import Chain, Patom

# ── Pattern ─────────────────────────────────────────────────
#   rex(r'\d{4}')  → year
#   rex(r'\d{2}')  → month
#   rex(r'\d{2}')  → day
#   enum(ERROR, CRITICAL)  → only these two
#   any(0)                 → rest of the message
# ────────────────────────────────────────────────────────────

error_rule = (
    Chain
    / Patom.rex(r"\d{4}")      # YYYY
    / Patom.rex(r"\d{2}")      # MM
    / Patom.rex(r"\d{2}")      # DD
    / Patom.enum(
        Chain(["ERROR"]),
        Chain(["CRITICAL"]),
    )
    / Patom.any(0)             # message
)

# ── Test log lines (tokenised) ──────────────────────────────

logs = [
    (["2024", "01", "15", "ERROR", "timeout"],      True,  "error log"),
    (["2024", "03", "22", "CRITICAL", "oom"],       True,  "critical log"),
    (["2024", "01", "15", "INFO", "request"],       False, "info ignored"),
    (["2024", "07", "09", "WARN", "slow query"],    False, "warn ignored"),
    (["2024", "12", "01", "DEBUG", "trace"],        False, "debug ignored"),
    (["2024", "13", "01", "ERROR", "bad month"],    True,  "13 matched by \\d{2} (2 digits)"),
    (["ERROR", "timeout"],                          False, "missing date"),
    (["24", "1", "15", "ERROR", "x"],               False, "malformed date"),
]

print("=" * 55)
print("Log classifier  (ERROR / CRITICAL only)")
print("=" * 55)

for tokens, expected, label in logs:
    data = Chain(tokens)
    result = data.match(error_rule, partial=True)
    flagged = "🚨 FLAGGED" if result else "ignored"
    status = "✓" if result == expected else "✗ FAIL"
    raw = ".".join(tokens)
    print(f"  {status}  {label:25s}  {flagged:12s}  │ {raw}")
