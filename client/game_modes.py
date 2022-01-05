from abc import abstractmethod
from typing import List

from server.classes import Player


class GameMode:

    @abstractmethod
    def get_start_score(self) -> int:
        pass

    @abstractmethod
    def is_game_finished(self, players: List[Player]) -> bool:
        pass

    @abstractmethod
    def is_capture_finished(self, player: Player) -> bool:
        pass

    @abstractmethod
    def is_capture_valid(self, player: Player) -> bool:
        pass

    @abstractmethod
    def update_player_score(self, player: Player) -> None:
        pass


class XX1(GameMode):

    def __init__(self, xx1, double_in=False, double_out=False):
        self.xx1 = xx1
        self.double_in = double_in
        self.double_out = double_out

    def get_start_score(self) -> int:
        return self.xx1

    def is_game_finished(self, players: List[Player]) -> bool:
        for player in players:
            if player.score == 0 and self.is_capture_valid(player):
                return True
        return False

    def is_capture_finished(self, current_player: Player) -> bool:
        current_capture = current_player.captures[-1]
        score_sum = sum([dart.base * dart.multiplier for dart in current_capture.darts])
        new_score = current_player.score - score_sum
        return len(current_capture.darts) == 3 or new_score < (2 if self.double_out else 1)

    def is_capture_valid(self, current_player: Player) -> bool:
        current_capture = current_player.captures[-1]
        try:
            latest_dart = current_capture.darts[-1]
        except IndexError:
            return True
        score_sum = sum([dart.base * dart.multiplier for dart in current_capture.darts])
        new_score = current_player.score - score_sum
        if self.double_out:
            return new_score > 1 or new_score == 0 and latest_dart.multiplier == 2
        else:
            return new_score >= 0

    def update_player_score(self, current_player: Player) -> None:
        current_capture = current_player.captures[-1]
        if self.double_in and not current_player.is_in:
            score_sum = 0
            for dart in current_capture.darts:
                if not current_player.is_in:
                    if dart.multiplier == 2:
                        current_player.is_in = True
                    else:
                        continue
                score_sum += dart.base * dart.multiplier
        else:
            score_sum = sum([dart.base * dart.multiplier for dart in current_capture.darts])
        current_player.score -= score_sum


class FromZero(GameMode):

    def __init__(self, to: int):
        self.target_score = to

    def get_start_score(self) -> int:
        return self.target_score

    def is_game_finished(self, players: List[Player]) -> bool:
        for player in players:
            if player.score >= self.target_score:
                return True
        return False

    def is_capture_finished(self, current_player: Player) -> bool:
        current_capture = current_player.captures[-1]
        score_sum = sum([dart.base * dart.multiplier for dart in current_capture.darts])
        new_score = current_player.score - score_sum
        return new_score >= self.target_score

    def is_capture_valid(self, _: Player) -> bool:
        return True

    def update_player_score(self, current_player: Player) -> None:
        current_capture = current_player.captures[-1]
        score_sum = sum([dart.base * dart.multiplier for dart in current_capture.darts])
        current_player.score += score_sum
