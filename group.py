import argparse
import copy
import csv
import datetime
from typing import Dict, Iterator, Optional

import arrow
import ics
from ics.timeline import Timeline

# https://tools.ietf.org/html/rfc5545#section-3.3.10
rrule_mappings = {
    "FREQ": {
        "SECONDLY": "second",
        "MINUTELY": "minute",
        "HOURLY": "hour",
        "DAILY": "day",
        "WEEKLY": "week",
        "MONTHLY": "month",
        "YEARLY": "year",
    },
}
rfc5545_weekdays = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def read_file(path: str) -> ics.Calendar:
    with open(path, "r") as f:
        return ics.Calendar(f.read())

def frequency_iterator(event: ics.Event, end: arrow.Arrow) -> Iterator[ics.Event]:
    rrule = {"FREQ": "YEARLY", "COUNT": 1}
    exceptions = []
    for extra_content in event.extra:
        if extra_content.name == "RRULE":
            rrule = {rule_part.split("=")[0]: rule_part.split("=")[1] for rule_part in extra_content.value.split(";")}
        if extra_content.name == "EXDATE":
            if "TZID" in extra_content.params:
                exceptions.append(arrow.get(extra_content.value, tzinfo=extra_content.params["TZID"][0]))
            else:
                exceptions.append(arrow.get(extra_content.value))

    if "FREQ" not in rrule:
        raise ValueError("RRULE must contain FREQ as per RFC 5545")

    range_kwargs = {
        "frame": rrule_mappings["FREQ"][rrule["FREQ"]],
        "start": event.begin,
        "end": end,
    }
    if "COUNT" in rrule:
        if rrule["FREQ"] not in rrule_mappings["FREQ"].keys():
            raise NotImplementedError(f"Frequency {rrule['FREQ']} with COUNT is not implemented")
        range_kwargs["limit"] = int(rrule["COUNT"])

    if "UNTIL" in rrule:
        if "limit" in range_kwargs:
            raise ValueError("Cannot have both COUNT and UNTIL in RRULE as per RFC 5545")
        range_kwargs["end"] = min(arrow.get(rrule["UNTIL"]), end)

    days = []
    if "BYDAY" in rrule and rrule["BYDAY"].count(",") > 0:
        days = [rfc5545_weekdays.index(d) for d in rrule["BYDAY"].split(",")]

    for starts in arrow.Arrow.range(**range_kwargs):
        event.end = event.duration + starts
        event.begin = starts
        if days:
            for starts_byday in arrow.Arrow.range(frame="day", start=starts, end=range_kwargs["end"], limit=7):
                if starts_byday.weekday() in days:
                    event.end = event.duration + starts_byday
                    event.begin = starts_byday
                    if starts_byday not in exceptions:
                        yield event
        else:
            if starts not in exceptions:
                yield event


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
        for event_instance in frequency_iterator(event, end):
            groups[event.name] += event_instance.duration

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
