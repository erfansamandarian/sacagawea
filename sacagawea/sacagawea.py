import argparse
from sacagawea.core.config import Config
from sacagawea.core.runner import Runner


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="base language")
    parser.add_argument("path", help="path to audio file")
    parser.add_argument("from_code", help="language to translate from")
    parser.add_argument("to_code", help="language to translate to")
    args = parser.parse_args()
    return Config(args)


def main():
    config = arguments()
    Runner(config).run()


if __name__ == "__main__":
    main()
