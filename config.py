"""Configuration for Teams mention monitor."""

# Polling interval in seconds
POLLING_INTERVAL_SEC: float = 5.0

# Substrings to match against NotificationHandler.PrimaryId (case-insensitive)
# to identify Teams handlers in the Windows notification database.
TEAMS_HANDLER_PATTERNS: list[str] = [
    "MSTeams",
    "Teams",
]

# Output datetime format
DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
