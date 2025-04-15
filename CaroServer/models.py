from typing import Optional
from fastapi import WebSocket
from datetime import datetime

class Player:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.last_ping = datetime.now()
        self.user_id = 'X'
class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.player1: Optional[Player] = None
        self.player2: Optional[Player] = None
        self.created_at = datetime.now()
        self.locked = False  # Lock when full

    def is_full(self):
        return self.player1 and self.player2

    def is_empty(self):
        return not self.player1 and not self.player2

    def is_waiting(self):
        return self.player1 is not None and self.player2 is None

    def get_opponent(self, player: Player):
        return self.player2 if self.player1 == player else self.player1

    def add_player(self, player: Player) -> bool:
        if self.locked or self.is_full():
            return False
        if not self.player1:
            self.player1 = player
        elif not self.player2:
            self.player2 = player
            self.locked = True
        return True

    def remove_player(self, player: Player):
        if self.player1 == player:
            self.player1 = None
        elif self.player2 == player:
            self.player2 = None
        self.locked = False
