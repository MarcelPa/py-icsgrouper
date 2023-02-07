import argparse
import csv
import datetime
from typing import Dict, Optional

import arrow
import ics
from ics.timeline import Timeline


def read_file(path: str) -> ics.Calendar:
    with open(path, "r") as f:
        return ics.Calendar(f.read())


def group_events_between(
    calendar: ics.Calendar, start: str, end: Optional[str]
) -> Dict[str, datetime.timedelta]:
    if end is None:
        end = arrow.now().format("YYYY-MM-DD")
    start = arrow.get(start)
    end = arrow.get(end)

    groups: Dict[str, datetime.timedelta] = {}
    timeline = Timeline(calendar).included(start, end)
    for event in timeline:
        if event.name not in groups:
            groups[event.name] = datetime.timedelta()
        groups[event.name] += event.duration

    return groups


def main():
    parser = argparse.ArgumentParser(
        description="Group events in an ICS file by event name, aggregating on the duration of each event."
    )
    parser.add_argument("path", help="Path to the ics file", type=str)
    parser.add_argument("start", help="Start date in iso format", type=str)
    parser.add_argument("end", help="End date in iso format", type=str, nargs="?")
    parser.add_argument(
        "--output", "-o", help="Output file, will be written in CSV format", type=str
    )

    args = parser.parse_args()
    c = read_file(args.path)
    groups = group_events_between(c, args.start, args.end)

    if args.output is None:
        for group, duration in groups.items():
            print(f"{group}\t{duration.total_seconds() / 3600:.2f}")
    else:
        with open(args.output, "w+") as f:
            writer = csv.writer(f)
            writer.writerow(["group", "duration"])
            for group, duration in groups.items():
                writer.writerow([group, duration.total_seconds() / 3600])


if __name__ == "__main__":
    main()
