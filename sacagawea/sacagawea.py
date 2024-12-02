import argparse
from sacagawea.core.config import Config
from sacagawea.core.runner import Runner


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="base language")
    parser.add_argument("path", help="path to audio file")
    args = parser.parse_args()
    return Config(args)


def main():
    config = arguments()
    Runner(config).run()


if __name__ == "__main__":
    main()
