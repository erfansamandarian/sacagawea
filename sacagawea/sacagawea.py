import argparse
from sacagawea.core.config import Config
from sacagawea.core.runner import Runner
from sacagawea.interface.gui import main as gui_main
from io import StringIO


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="start in GUI mode")
    parser.add_argument("--model", help="base language")
    parser.add_argument("--path", help="path to audio file")
    parser.add_argument("--from-code", help="language to translate from")
    parser.add_argument("--to-code", help="language to translate to")
    args = parser.parse_args()
    return args


def main():
    args = arguments()

    if args.gui:
        gui_main()
    else:
        if not all([args.model, args.path, args.from_code, args.to_code]):
            print("error: all arguments are required")
            return
        config = Config(args)
        Runner(config).run()


if __name__ == "__main__":
    main()
