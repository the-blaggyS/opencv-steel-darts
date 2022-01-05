from typing import List
from uuid import uuid4

from client.game_modes import GameMode
from server.classes import Player


class Game:
    id: uuid4
    game_mode: GameMode
    players: List[Player]
    current_player: int
    is_running: bool

    def __init__(self, game_mode: GameMode, players: List[Player]):
        self.id = uuid4()
        self.game_mode = game_mode
        self.players = players
        self.current_player = 0
        self.is_running = True

        for player in self.players:
            player.score = self.game_mode.get_start_score()

    def next_player(self) -> None:
        self.current_player += 1
        self.current_player %= len(self.players)

    def get_current_player(self) -> Player:
        return self.players[self.current_player]

    def is_game_finished(self) -> bool:
        return self.game_mode.is_game_finished(self.players)

    def is_capture_finished(self) -> bool:
        return self.game_mode.is_capture_finished(self.get_current_player())

    def is_capture_valid(self) -> bool:
        return self.game_mode.is_capture_valid(self.get_current_player())
