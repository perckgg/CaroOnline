import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from models import Player
from room_manager import room_manager
import json


async def handle_connection(websocket: WebSocket, room_id: str, side: str = None):
    room = room_manager.get_room(room_id)
    player_symbol = side

    # Register player
    if not player_symbol:
        if room.player1 is None:
            room.player1 = websocket
            player_symbol = "X"
        elif room.player2 is None:
            room.player2 = websocket
            player_symbol = "O"
        else:
            await websocket.send_text("Room full")
            # await websocket.close()
            return

    await websocket.send_text(f"joined:{room_id}:{player_symbol}")

    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                if data.get("type") == "move":
                    target_ws = room.player2 if player_symbol == "X" else room.player1
                    if target_ws:
                        await target_ws.send_text(json.dumps({
                            "type": "move",
                            "row": data["row"],
                            "col": data["col"]
                        }))
            except Exception as e:
                print("Invalid message:", e)

    except WebSocketDisconnect:
        print(f"{player_symbol} disconnected from room {room_id}")
        if player_symbol == "X":
            room.player1 = None
            if room.player2:
                await room.player2.send_text("opponent_left")
        else:
            room.player2 = None
            if room.player1:
                await room.player1.send_text("opponent_left")

        # Auto-cleanup
        if room.player1 is None and room.player2 is None:
            room_manager.remove_room(room_id)
