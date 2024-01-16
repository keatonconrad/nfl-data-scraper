import argparse
from game_getter import GameGetter

game_getter = GameGetter()

def main():
    parser = argparse.ArgumentParser(description="NFL Data Scraper CLI")
    parser.add_argument("--all", help="Get all games", action="store_true")
    parser.add_argument(
        "--recent", help="Get the most recent games", action="store_true"
    )

    args = parser.parse_args()

    if args.recent:
        game_getter.get_most_recent_games()
    else:
        game_getter.get_all_games()


if __name__ == "__main__":
    main()
