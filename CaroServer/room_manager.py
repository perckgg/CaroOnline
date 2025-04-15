from typing import Dict, List
from models import Room
import asyncio
from datetime import datetime, timedelta
from typing import Optional

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def create_room(self, room_id: str) -> Room:
        room = Room(room_id)
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Room:
        return self.rooms.get(room_id)

    # def get_waiting_rooms(self) -> List[str]:
    #     # return [rid for rid, room in self.rooms.items() if room.is_waiting()]
    #     return [rid for rid in self.rooms.items()]
    # def get_waiting_rooms(self) -> List[str]:
    #     return list(self.rooms.keys())
    def assign_player_to_waiting_room(self, player):
        '''
            Return room + status empty or waiting ( 1: waiting, 0: empty)
            Assigns a player to a waiting room. If no waiting room is available, it creates a new one.

        '''
        waiting_rooms = self._get_waiting_rooms()
        status = 0
        if len(waiting_rooms) == 0:
            print("No waiting rooms available")
            return None, None
        for room in waiting_rooms:
            if not room.is_full() and not room.is_empty():
                room.add_player(player)
                print("Player added to waiting room with ID: ", waiting_rooms[0].room_id, " and status: 1(room has 2 player)")
                return room, 0
        waiting_rooms[0].add_player(player)
        print("Player added to waiting room with ID: ", waiting_rooms[0].room_id, " and status: 0(room has 1 player)")
        return waiting_rooms[0], 1
        
    def _get_waiting_rooms(self) -> Dict[str, List[str]]:
        waiting_rooms = []
        for room_id, room in self.rooms.items():
            if room.is_empty() or room.is_waiting():
                waiting_rooms.append(room)
        return waiting_rooms

    def remove_room(self, room_id: str):
        if room_id in self.rooms:
            del self.rooms[room_id]
 

    async def cleanup_rooms(self):
        now = datetime.now()
        for room_id in list(self.rooms.keys()):
            room = self.rooms[room_id]
            if room.is_waiting() and now - room.created_at > timedelta(minutes=5):
                self.remove_room(room_id)
            elif room.is_empty():
                self.remove_room(room_id)

room_manager = RoomManager()
