from typing import Dict, List
from models import Room
import asyncio
from datetime import datetime, timedelta

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
    def get_waiting_rooms(self) -> List[str]:
        return list(self.rooms.keys())
    def get_waiting_rooms(self) -> Dict[str, List[str]]:
        return {"rooms": [room_id for room_id, room in self.rooms.items()]} 

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
