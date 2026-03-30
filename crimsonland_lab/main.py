from pathlib import Path

from src.app import App


def main() -> None:
    """Create the application and start the main loop.

    Returns:
        None. The function blocks until the pygame application exits.
    """
    base_dir = Path(__file__).resolve().parent
    app = App(base_dir)
    app.run()


if __name__ == "__main__":
    main()
