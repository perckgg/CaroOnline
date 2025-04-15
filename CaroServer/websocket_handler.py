import asyncio
from fastapi import WebSocketDisconnect
from room_manager import room_manager
from starlette.websockets import WebSocketState
import json

async def handle_connection(player, room_id: str, side: str = None):
    room = room_manager.get_room(room_id)
    player_symbol = side

    # Gán player vào room nếu cần
    if not player_symbol:
        if room.player1 is None:
            room.player1 = player
            player_symbol = "X"
        elif room.player2 is None:
            room.player2 = player
            player_symbol = "O"
        else:
            try:
                await player.websocket.send_text("Room full")
            except Exception as e:
                print("Could not notify: Room full:", e)
            # await player.websocket.close()
            return

    # Gửi thông báo đã vào phòng
    try:
        if player.websocket.client_state == WebSocketState.CONNECTED:
            await player.websocket.send_text(f"joined:{room_id}:{player_symbol}")
        else:
            print("out")
    except Exception as e:
        print("Send join message failed:", e)
        return

    # Nhận và chuyển tiếp các nước đi
    try:
        while True:
            msg = await player.websocket.receive_text()
            try:
                data = json.loads(msg)
                if data.get("type") == "move":
                    opponent = room.player2 if player_symbol == "X" else room.player1
                    if opponent and opponent.websocket.client_state == WebSocketState.CONNECTED:
                        await opponent.websocket.send_text(json.dumps({
                            "type": "move",
                            "row": data["row"],
                            "col": data["col"]
                        }))
            except Exception as e:
                print("Invalid message or forward error:", e)

    except WebSocketDisconnect:
        print(f"{player_symbol} disconnected from room {room_id}")

        opponent = room.player2 if player_symbol == "X" else room.player1

        if player_symbol == "X":
            room.player1 = None
        else:
            room.player2 = None

        if opponent:
            try:
                await opponent.websocket.send_text("opponent_left")
            except Exception as e:
                print("Could not notify opponent:", e)

        if room.player1 is None and room.player2 is None:
            room_manager.remove_room(room_id)
