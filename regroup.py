import argparse
import csv
import io
from typing import Dict, List
import sys


def read_file(content: io.TextIOWrapper) -> List[Dict[str, float]]:
    return csv.DictReader(content.readlines(), delimiter=",")


def read_stdin(stdin: str) -> List[Dict[str, float]]:
    return csv.DictReader(
        stdin.splitlines(), delimiter="\t", fieldnames=["group", "duration"]
    )


def main():
    parser = argparse.ArgumentParser(
        description="Interactively regroup a list of groups and durations, summing up the durations to new groups."
    )
    parser.add_argument(
        "input",
        help="Input to read. Can be either stdin or a path to a CSV with headers 'group' and 'duration'.",
        type=argparse.FileType("r"),
        default="-",
    )
    parser.add_argument(
        "--output", "-o", help="Ouptut file, will be written in CSV format", type=str
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
            new_groups[new_group] = []
        new_groups[new_group].append(element)

    for group, durations in new_groups.items():
        print(f"{group}: {sum([float(d['duration']) for d in durations])}")

    if args.output:
        with open(args.output, "w") as f:
            writer = csv.DictWriter(f, fieldnames=["group", "duration", "regroup"])
            writer.writeheader()
            for group, durations in new_groups.items():
                for duration in durations:
                    writer.writerow(
                        {
                            "group": duration["group"],
                            "regroup": group,
                            "duration": duration["duration"],
                        }
                    )


if __name__ == "__main__":
    main()
