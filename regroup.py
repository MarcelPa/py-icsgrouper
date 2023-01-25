import argparse
import csv
from typing import Dict, List, Iterable
import sys


def read_file(path: str) -> List[Dict[str, float]]:
    with open(path, "r") as f:
        return csv.DictReader(f)


def read_stdin(stdin) -> List[Dict[str, float]]:
    return csv.DictReader(
        stdin.splitlines(), delimiter="\t", fieldnames=["group", "duration"]
    )


def main():
    parser = argparse.ArgumentParser(
        description="Group events in an ICS file by event name, aggregating on the duration of each event."
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Input file, will be read in CSV format. Has to contain the headers 'group' and 'duration'.",
        type=str,
    )
    args = parser.parse_args()

    if args.input is None:
        input_data = read_stdin(sys.stdin.read())
    else:
        input_data = read_file(args.input)

    new_groups = {}
    for element in input_data:
        print(element["group"])
        print("Assign to: ", end="")
        new_group = input()
        if new_group not in new_groups:
            new_groups[new_group] = 0.0
        new_groups[new_group] += float(element["duration"])

    print(new_groups)


if __name__ == "__main__":
    main()
