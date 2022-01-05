from typing import List

from server import api
from server.classes import Dart
from server.game_loop import GameLoop

latest_darts: List[Dart] = []


def setup_game_loop():
    game_loop = GameLoop()
    game_loop.add_subscriber(lambda d: latest_darts.append(d))
    game_loop.start()


def setup_api_app():
    api.get_darts = lambda: [latest_darts.pop() for _ in range(len(latest_darts))]
    api.app.run(host='0.0.0.0', port=8000)


if __name__ == '__main__':
    setup_game_loop()
    setup_api_app()
