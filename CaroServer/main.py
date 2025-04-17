from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from websocket_handler import handle_connection
from room_manager import room_manager
import asyncio
from starlette.websockets import WebSocketState
from models import Player
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_rooms():
    for i in range(1, 6):
        room_id = f"ROOM{i}"
        room_manager.create_room(room_id)
        print(f"Room {room_id} created")
init_rooms()

@app.websocket("/ws/match")
async def match_players(websocket: WebSocket):
    await websocket.accept()
    print("Player added to matchmaking queue")
    player = Player(websocket)
    try:
        room, empty_status = room_manager.assign_player_to_waiting_room(player)

        keep_connection = True
        side = None
        if room is None: 
            keep_connection = False

        if empty_status: 
            await websocket.send_json({"room_id": room.room_id, "side": "X", "message": "waiting"})
            side = 'X'
        else:
            await websocket.send_json({"room_id": room.room_id, "side": "O", "message": "waiting"})
            side = 'O'
        
        while not room.is_full():
            await asyncio.sleep(1)
            
        await websocket.send_json({"message": "start"})

        while keep_connection:
            message = await websocket.receive_json()
            message["message"] = "play"
            print("Room ID: ", room.room_id, "- side: ", side, "- message: ", message)
            if side == 'X':
                oponent_socket = room.player2.websocket
            else:
                oponent_socket = room.player1.websocket
        room.reset()

    except WebSocketDisconnect:
        print("Player disconnected during matchmaking")
        player.socket = None
        if side == 'X':
            oponent_socket = room.player2.websocket
        else:
            oponent_socket = room.player1.websocket
        oponent_socket.send_json({"message": "opponent left"})
        room.reset()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)