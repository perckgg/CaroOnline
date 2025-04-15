from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from websocket_handler import handle_connection
from room_manager import room_manager
import asyncio

app = FastAPI()
# Queue for matchmaking
matchmaking_queue = asyncio.Queue()
# Allow CORS for frontend dev
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
            player1 = await matchmaking_queue.get()
            player2 = await matchmaking_queue.get()
            
            room_id = f"MATCH_{id(player1)}"
            room = room_manager.create_room(room_id)
            room.player1 = player1
            room.player2 = player2
            room.locked = True
            print(f"Match found! Room ID: {room_id}")

            # Notify both players
            await player1.send_text(f"matched:{room_id}:X")
            await player2.send_text(f"matched:{room_id}:O")

            # Start the game
            await asyncio.gather(
                handle_connection(player1, room_id, "X"),
                handle_connection(player2, room_id, "O")
            )

    except WebSocketDisconnect:
        print("Player disconnected during matchmaking")
        # Remove from queue if still present
        try:
            matchmaking_queue._queue.remove(websocket)
        except ValueError:
            pass
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await handle_connection(websocket, room_id)

