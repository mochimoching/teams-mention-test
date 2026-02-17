"""Teams mention monitor – entry point.

Polls the Windows notification database for Teams @mentions
and prints them to stdout.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

from src.config import POLLING_INTERVAL_SEC, DATETIME_FORMAT
from src.notification_listener import NotificationMonitor, NotificationRecord
from src.teams_parser import (
    MentionNotification,
    parse_teams_notification,
    is_mention_notification,
)


def format_output(
    notification: MentionNotification,
    timestamp: str | None = None,
) -> str:
    """Format a parsed mention notification as a single log line.

    Format:
        [timestamp] channel | sender: message   (with channel)
        [timestamp] sender: message              (without channel)
        [timestamp] message                      (no sender/channel)

    Args:
        notification: Parsed notification.
        timestamp: Optional pre-formatted timestamp string.
                   If None, the current time is used.

    Returns:
        Formatted log line.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime(DATETIME_FORMAT)

    parts: list[str] = [f"[{timestamp}]"]

    if notification.channel and notification.sender:
        parts.append(
            f"{notification.channel} | {notification.sender}: {notification.message}"
        )
    elif notification.sender:
        parts.append(f"{notification.sender}: {notification.message}")
    else:
        parts.append(notification.message)

    return " ".join(parts)


def process_notifications(
    records: list[NotificationRecord],
    target_name: str | None,
) -> int:
    """Process a batch of notification records: parse, filter, print.

    Args:
        records: NotificationRecord objects from the monitor.
        target_name: Display name to match @mentions against. None = all.

    Returns:
        Number of mentions printed.
    """
    count = 0
    for rec in records:
        parsed = parse_teams_notification(rec.text_elements)
        if parsed is None:
            continue

        if not is_mention_notification(parsed, target_name):
            continue

        line = format_output(parsed)
        print(line, flush=True)
        count += 1

    return count


def run_monitor(
    target_name: str | None = None,
    polling_interval: float = POLLING_INTERVAL_SEC,
    monitor: NotificationMonitor | None = None,
) -> None:
    """Main loop: poll the notification DB forever.

    Args:
        target_name: Display name to watch for @mentions.
        polling_interval: Seconds between each poll cycle.
        monitor: Optional pre-configured monitor (for testing).
    """
    if monitor is None:
        monitor = NotificationMonitor()

    print(
        f"Teams mention monitor started. "
        f"Watching for mentions of: {target_name or '(all notifications)'}",
        file=sys.stderr,
    )
    print(
        f"Polling every {polling_interval}s. Press Ctrl+C to stop.",
        file=sys.stderr,
    )

    # Initial poll to seed seen-IDs (don't print existing notifications)
    try:
        initial = monitor.poll()
        print(
            f"Skipped {len(initial)} existing notification(s).",
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"WARNING: Initial poll failed: {exc}", file=sys.stderr)

    # Main polling loop
    try:
        while True:
            time.sleep(polling_interval)
            try:
                new_records = monitor.poll()
                if new_records:
                    process_notifications(new_records, target_name)
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                print(f"WARNING: Poll error: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nMonitor stopped.", file=sys.stderr)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Teams @mention notifications and log to stdout."
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help=(
            "Your Teams display name to filter @mentions. "
            "If omitted, all Teams notifications are logged."
        ),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=POLLING_INTERVAL_SEC,
        help=f"Polling interval in seconds (default: {POLLING_INTERVAL_SEC}).",
    )
    args = parser.parse_args()

    run_monitor(target_name=args.name, polling_interval=args.interval)


if __name__ == "__main__":
    main()
