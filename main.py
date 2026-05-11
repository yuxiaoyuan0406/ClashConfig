import argparse
import sys

import yaml

import util


def main():
    parser = argparse.ArgumentParser(description="Download and edit Clash/Mihomo config.")
    parser.add_argument("--url", required=True, help="Subscription URL.")
    parser.add_argument("--output", help="Output YAML file.", default="output.yaml")
    parser.add_argument(
        "--user-agent",
        default=None,
        help=(
            "User-Agent used when pulling subscription. "
            "Default is a conservative ClashforWindows UA; override it if your provider requires another client UA."
        ),
    )
    args = parser.parse_args()

    try:
        data = util.download_config(args.url, user_agent=args.user_agent)
        util.edit_config(data)
    except Exception as exc:
        print(f"Failed to generate config: {exc}", file=sys.stderr)
        return 1

    with open(args.output, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
