from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from websocket_handler import handle_connection
from room_manager import room_manager
import asyncio
from starlette.websockets import WebSocketState

app = FastAPI()
matchmaking_queue = asyncio.Queue()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def init_rooms():
    for i in range(1, 6):
        room_id = f"ROOM{i}"
        room_manager.create_room(room_id)

@app.websocket("/ws/match")
async def match_players(websocket: WebSocket):
    await websocket.accept()
    await matchmaking_queue.put(websocket)
    print("Player added to matchmaking queue")

    try:
        if matchmaking_queue.qsize() >= 2:
            player1_ws = await matchmaking_queue.get()
            player2_ws = await matchmaking_queue.get()
            if player1_ws == player2_ws:
                print("Duplicate player detected, aborting match")
                await matchmaking_queue.put(player1)  # Cho lại vào queue
                return
            # await player1_ws.accept()
            # await player2_ws.accept()

            room_id = f"MATCH_{id(player1_ws)}"
            room = room_manager.create_room(room_id)

            from models import Player  # Import ở đây để tránh circular import
            player1 = Player(player1_ws)
            player2 = Player(player2_ws)

            room.player1 = player1
            room.player2 = player2
            room.locked = True

            print(f"Match found! Room ID: {room_id}")

            # Gửi matched info
            try:
                if player1_ws.client_state == WebSocketState.CONNECTED:
                    print(player1_ws.client_state)
                    await player1_ws.send_text(f"matched:{room_id}:X")
                    
                if player2_ws.client_state == WebSocketState.CONNECTED:
                    await player2_ws.send_text(f"matched:{room_id}:O")
            except Exception as e:
                print(f"Error sending matched message: {e}")

            # Bắt đầu nhận dữ liệu song song
            await asyncio.gather(
                handle_connection(player1, room_id, "X"),
                handle_connection(player2, room_id, "O")
            )

    except WebSocketDisconnect:
        print("Player disconnected during matchmaking")
        try:
            matchmaking_queue._queue.remove(websocket)
        except ValueError:
            pass

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # await websocket.accept()
    from models import Player
    player = Player(websocket)
    await handle_connection(player, room_id)
