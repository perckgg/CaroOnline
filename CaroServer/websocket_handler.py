import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from models import Player
from room_manager import room_manager

PING_INTERVAL = 5
PING_TIMEOUT = 10

async def handle_connection(websocket: WebSocket, room_id: str):
    await websocket.accept()
    player = Player(websocket)
    room = room_manager.get_room(room_id) or room_manager.create_room(room_id)

    if not room.add_player(player):
        data = {"error":"Room full"}
        await websocket.send_json(data, mode = 'text')
        await websocket.close()
        return

    try:
        await websocket.send_json({"message": "Joined room: " + room_id})

        # Start ping/pong and game communication
        ping_task = asyncio.create_task(ping_loop(player))
        recv_task = asyncio.create_task(message_loop(player, room))
        timeout_task = asyncio.create_task(timeout_checker(room_id))

        await asyncio.wait(
            [ping_task, recv_task, timeout_task],
            return_when=asyncio.FIRST_COMPLETED
        )
    except WebSocketDisconnect:
        pass
    finally:
        room.remove_player(player)
        opponent = room.get_opponent(player)
        if opponent:
            await opponent.websocket.send_json({"message": "Opponent disconnected. You win!"})
        if room.is_empty():
            room_manager.remove_room(room_id)

async def message_loop(player: Player, room):
    while True:
        data = await player.websocket.receive_text()
        opponent = room.get_opponent(player)
        if opponent:
            await opponent.websocket.send_text(data)

async def ping_loop(player: Player):
    while True:
        await asyncio.sleep(PING_INTERVAL)
        try:
            await player.websocket.send_json({"type": "ping"})
        except:
            break

async def timeout_checker(room_id: str):
    await asyncio.sleep(30)
    room = room_manager.get_room(room_id)
    if room and room.is_waiting():
        try:
            await room.player1.websocket.send_json({"message": "No opponent joined. Closing room."})
            await room.player1.websocket.close()
        except:
            pass
        room_manager.remove_room(room_id)
