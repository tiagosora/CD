import argparse
from importlib.resources import path
import os
from src.daemon import Daemon   

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "n", help="node to create", type=dir_path
    )
    parser.add_argument(
        "p", help="daemon port to the network", type=int
    )
    args = parser.parse_args()
    d = Daemon(args.n, args.p)

    
    d.loop()
