import argparse
from src.client import Client

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", help="number of folders to create", type=int
    )
    args = parser.parse_args()
    d = Client(args.p)

    d.loop()