import argparse
import csv
from typing import Dict, List
import sys


def read_file(content: str) -> List[Dict[str, float]]:
    return csv.DictReader(content.splitlines(), delimiter=",")


def read_stdin(stdin: str) -> List[Dict[str, float]]:
    return csv.DictReader(
        stdin.splitlines(), delimiter="\t", fieldnames=["group", "duration"]
    )


def main():
    parser = argparse.ArgumentParser(
        description="Group events in an ICS file by event name, aggregating on the duration of each event."
    )
    parser.add_argument(
        "input",
        help="Input to read. Can be either stdin or a path to a CSV with headers 'group' and 'duration'.",
        type=argparse.FileType("r"),
        default="-",
    )
    args = parser.parse_args()
    if args.input.name == "<stdin>":
        input_data = read_stdin(args.input.read())
    else:
        input_data = read_file(args.input)

    # reopen stdin
    # thanks to VPfB https://stackoverflow.com/a/66143581
    sys.stdin.close()
    sys.stdin = open("/dev/tty")

    new_groups = {}
    for element in input_data:
        new_group = input(f"{element['group']} ({element['duration']}h)\nAssign to: ")
        if new_group not in new_groups:
            new_groups[new_group] = 0.0
        new_groups[new_group] += float(element["duration"])

    for group, duration in new_groups.items():
        print(f"{group}:\t{duration}")


if __name__ == "__main__":
    main()
