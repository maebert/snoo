from .client import Client
import argparse
import arrow
import sys


def date(value):
    return arrow.get(value)


def run(argv=None):
    client = Client()
    parser = argparse.ArgumentParser(description="Snoo CLI")
    parser.add_argument(
        "command", default="status", choices=["status", "sessions", "days"]
    )
    parser.add_argument(
        "-s",
        "--start",
        default=arrow.now().floor("day").shift(days=-1),
        type=date,
        help="Start date for exports, eg. 2019-12-01",
    )
    parser.add_argument(
        "-e",
        "--end",
        default=arrow.now().floor("day"),
        type=date,
        help="End date for exports, eg. 2019-12-03",
    )
    args = parser.parse_args(argv or sys.argv[1:])

    if args.command == "status":
        print(client.status())
    elif args.command == "sessions":
        data = client.export_sessions(args.start, args.end)
        print(data)
    elif args.command == "days":
        data = client.export_stats(args.start, args.end)
        print(data)


if __name__ == "__main__":
    run()
