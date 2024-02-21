#!/usr/bin/python

import os
import argparse


def get_makefiles() -> list[str]:
    paths: list[str] = []
    for root, _, files in os.walk("./"):
        for file in files:
            if file == "Makefile":
                paths.append(root)
    return paths


def make(paths: list[str]):
    for path in paths:
        os.system("make -C {}".format(path))


def clean(paths: list[str]):
    for path in paths:
        os.system("make -C {} clean".format(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Execute make for all subdir.")
    parser.add_argument('--clean',
                        help='execute make clean',
                        action="store_true")
    args = parser.parse_args()

    paths: list[str] = get_makefiles()
    if args.clean:
        clean(paths)
    else:
        make(paths)
