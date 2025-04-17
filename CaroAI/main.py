from turtle import Screen
import Buttons as button
import pygame
import sys
import caro
import os
from agent import Agent
import json
import threading
import websocket
import json
from queue import Queue
import time

API_BASE_URL = "http://10.229.134.211:8000"  # Đổi nếu server không chạy 10.229.134.221
WS_BASE_URL = "ws://10.229.134.211:8000/ws"  # WebSocket server
# Global WebSocket client
ws_client = None
ws_queue = Queue()
waiting_for_match = False
current_side = None
connected_room = None
# -------------------------Setup----------------------------
# Định nghĩa màu

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (77, 199, 61)
RED = (199, 36, 55)
BLUE = (68, 132, 222)
GRAY = (200,200,200)
LIGHT_BLUE = (135, 206, 250)
DARK_GRAY = (79, 79, 79)
DARK_BLUE = (0, 51, 102)  # hoặc dùng (0, 51, 102) nếu muốn dịu hơn
LIGHT_GRAY = (211, 211, 211)  # hoặc (224, 224, 224) nếu muốn sáng hơn

# Kí hiệu lúc ban đầu
XO = 'X'
FPS = 30
# Số hàng, cột
ROWNUM = 18
COLNUM = 20
# Số dòng thắng
winning_condition = 5

# developer_mode: ai vs ai
# Đặt is_developer_mode = True nếu muốn cho ai đấu với ai

is_developer_mode = False
# is_developer_mode = True

dev_mode_setup = {
    'ai_1': 'X',
    'ai_2': 'O',
    'ai_1_depth': 1,
    'ai_2_depth': 3,
    'start': False,
}



# Notification variables
not_found_message = ""
not_found_timer = 0
NOTIFY_DURATION = 2000  # milliseconds
def draw_notification():
    global not_found_message, not_found_timer
    if not_found_message:
        current_time = pygame.time.get_ticks()
        if current_time - not_found_timer < NOTIFY_DURATION:
            notify_font = pygame.font.SysFont("Arial", 36)
            text_surf = notify_font.render(not_found_message, True, RED)
            bg_rect = text_surf.get_rect(center=(Screen.get_width()//2, Screen.get_height() - 50))
            pygame.draw.rect(Screen, BLACK, bg_rect.inflate(20, 20))
            pygame.draw.rect(Screen, RED, bg_rect.inflate(20, 20), 2)
            Screen.blit(text_surf, bg_rect)
        else:
            not_found_message = ""
# init game and ai
my_game, agent, agent1, agent2 = None, None, None, None
def create_new_game():
    global my_game, agent, agent1, agent2, waiting_for_match, current_side, connected_room, ws_client
    my_game = caro.Caro(ROWNUM, COLNUM, winning_condition, XO)
    agent = Agent(max_depth=my_game.hard_ai,
                       XO=my_game.get_current_XO_for_AI())
    agent1 = Agent(max_depth=dev_mode_setup['ai_1_depth'],
                          XO=dev_mode_setup['ai_1'])
    agent2 = Agent(max_depth=dev_mode_setup['ai_2_depth'],
                          XO=dev_mode_setup['ai_2'])
    waiting_for_match = False
    current_side = None
    connected_room = None

create_new_game()



Window_size = [1280, 720]


my_len_min = min(900/COLNUM, (720) / ROWNUM)
# Độ dày đường kẻ
MARGIN = my_len_min/15
my_len_min = min((900 - MARGIN)/COLNUM, (720 - MARGIN) / ROWNUM)
my_len_min = my_len_min - MARGIN
# Chiều dài, rộng mỗi ô
WIDTH = my_len_min
HEIGHT = my_len_min

Screen = pygame.display.set_mode(Window_size)
# path = "Caro/asset"
path = os.getcwd()
path = os.path.join(path, './asset')

# ------------------------------Load asset----------------------------------------
x_img = pygame.transform.smoothscale(pygame.image.load(
    path + "/X_caro.png").convert_alpha(), (my_len_min, my_len_min))
o_img = pygame.transform.smoothscale(pygame.image.load(
    path + "/O_caro.png").convert_alpha(), (my_len_min, my_len_min))
# load button images
start_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/start_btn.png').convert_alpha(), (240, 105))
exit_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/exit_btn.png').convert_alpha(), (240, 105))
replay_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/replay_btn.png').convert_alpha(), (240, 105))
undo_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/undo_btn.png').convert_alpha(), (240, 105))
ai_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/ai_btn.png').convert_alpha(), (105, 105))
person_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/person_btn.png').convert_alpha(), (105, 105))
ai_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/ai_btn_gray.jpg').convert_alpha(), (105, 105))
person_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/person_btn_gray.jpg').convert_alpha(), (105, 105))
h_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/h_btn.png').convert_alpha(), (80, 80))
h_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/h_btn_gray.png').convert_alpha(), (80, 80))
m_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/m_btn.png').convert_alpha(), (80, 80))
m_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/m_btn_gray.png').convert_alpha(), (80, 80))
e_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/e_btn.png').convert_alpha(), (80, 80))
e_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/e_btn_gray.png').convert_alpha(), (80, 80))
pvp_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/player_vs_player.jpg').convert_alpha(), (105, 105))
pvp_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/player_vs_player_gray.jpg').convert_alpha(), (105, 105))
aivp_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/ai_vs_player.jpg').convert_alpha(), (105, 105))
aivp_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/ai_vs_player_gray.jpg').convert_alpha(), (105, 105))
ai_thinking_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/ai_thinking.png').convert_alpha(), (105, 105))
ai_thinking_img_gray = pygame.transform.smoothscale(pygame.image.load(
    path + '/ai_thinking_gray.png').convert_alpha(), (105, 105))
icon_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/old/icon.jpg').convert_alpha(), (20, 20))
logo_img = pygame.transform.smoothscale(pygame.image.load(
    path + '/logo.jpg').convert_alpha(), (240, 105))
# create button instances
start_button = button.Button(970, 200, start_img, start_img, 0.8)
replay_button = button.Button(970, 575, replay_img, replay_img, 0.8)
exit_button = button.Button(970, 485, exit_img, exit_img, 0.8)
undo_button = button.Button(970, 395, undo_img, undo_img, 0.8)
ai_btn = button.Button(970, 305, ai_img, ai_img_gray, 0.8)
person_btn = button.Button(1075, 305, person_img, person_img_gray, 0.8)
h_btn = button.Button(1100, 235, h_img, h_img_gray, 0.8)
m_btn = button.Button(1035, 235, m_img, m_img_gray, 0.8)
e_btn = button.Button(970, 235, e_img, e_img_gray, 0.8)
ai_thinking_btn = button.Button(
    1020, 30, ai_thinking_img, ai_thinking_img_gray, 0.8)
pvp_btn = button.Button(1075, 145, pvp_img, pvp_img_gray, 0.8)
aivp_btn = button.Button(970, 145, aivp_img, aivp_img_gray, 0.8)
logo_btn = button.Button(990, 660, logo_img, logo_img, 0.6)

person_btn.disable_button()
m_btn.disable_button()
pvp_btn.disable_button()
ai_thinking_btn.disable_button()
if (is_developer_mode == True):
    aivp_btn.disable_button()
    pvp_btn.disable_button()
    ai_btn.disable_button()
    person_btn.disable_button()
    h_btn.disable_button()
    m_btn.disable_button()
    e_btn.disable_button()
    ai_thinking_btn.disable_button()

pygame.display.set_caption('Caro game by nhóm 6')
pygame.display.set_icon(icon_img)
pygame.init()


# Loop until the user clicks the close button.
done = False
status = None
menu_active = True
font = pygame.font.SysFont("Arial", 50)
# Used to manage how fast the screen updates
clock = pygame.time.Clock()

# ----------------------- Function ------------------------------------


def logo():
    font = pygame.font.Font('freesansbold.ttf', 36)
    text = font.render('By AI - nhóm 6', True, WHITE, BLACK)
    textRect = text.get_rect()
    textRect.center = (1100, 700)
    Screen.blit(text, textRect)
    # logo_btn.draw(Screen)
    if is_developer_mode:
        font = pygame.font.Font('freesansbold.ttf', 36)
        text = font.render('Developer_Mode', True, WHITE, BLACK)
        textRect = text.get_rect()
        textRect.center = (1080, 160)
        Screen.blit(text, textRect)


def draw(this_game: caro.Caro, this_screen):
    logo()
    for row in range(ROWNUM):
        for column in range(COLNUM):
            color = WHITE
            if len(this_game.last_move) > 0:
                last_move_row, last_move_col = this_game.last_move[-1][0], this_game.last_move[-1][1]
                if row == last_move_row and column == last_move_col:
                    color = GREEN
            pygame.draw.rect(this_screen,
                             color,
                             [(MARGIN + WIDTH) * column + MARGIN,
                              (MARGIN + HEIGHT) * row + MARGIN,
                              WIDTH,
                              HEIGHT])
            if this_game.grid[row][column] == 'X':
                this_screen.blit(
                    x_img, ((WIDTH + MARGIN)*column + MARGIN, (HEIGHT + MARGIN)*row + MARGIN))
            if this_game.grid[row][column] == 'O':
                this_screen.blit(
                    o_img, ((WIDTH + MARGIN)*column + MARGIN, (HEIGHT + MARGIN)*row + MARGIN))


def re_draw():
    logo()
    Screen.fill(BLACK)
    for row in range(ROWNUM):
        for column in range(COLNUM):
            color = WHITE
            pygame.draw.rect(Screen,
                             color,
                             [(MARGIN + WIDTH) * column + MARGIN,
                              (MARGIN + HEIGHT) * row + MARGIN,
                              WIDTH,
                              HEIGHT])


def Undo(self: caro.Caro):
    re_draw()
    if self.is_use_ai:
        if len(self.last_move) > 2:
            last_move = self.last_move[-1]
            last_move_2 = self.last_move[-2]
            self.last_move.pop()
            self.last_move.pop()
            # print(self.last_move)
            # print(last_move, type(last_move), type(last_move[0]))
            row = int(last_move[0])
            col = int(last_move[1])
            row2 = int(last_move_2[0])
            col2 = int(last_move_2[1])
            self.grid[row][col] = '.'
            self.grid[row2][col2] = '.'
            draw(my_game, Screen)
    else:
        if len(self.last_move) > 0:
            last_move = self.last_move[-1]
            self.last_move.pop()
            # print(self.last_move)
            # print(last_move, type(last_move), type(last_move[0]))
            row = int(last_move[0])
            col = int(last_move[1])
            self.grid[row][col] = '.'
            if self.XO == 'X':
                self.XO = 'O'
            else:
                self.XO = 'X'
            if self.turn == 1:
                self.turn = 2
            else:
                self.turn = 1
            draw(my_game, Screen)
    pass


def checking_winning(status,mode="AI"):
    global menu_active, waiting_for_match, ws_client
    if status == 2:
        font = pygame.font.Font('freesansbold.ttf', 100)
        text = font.render('Draw', True, GREEN, BLUE)
        textRect = text.get_rect()
        textRect.center = (int(Window_size[0]/2), int(Window_size[1]/2))
        Screen.blit(text, textRect)
        # done = True
    if status == 0:
        font = pygame.font.Font('freesansbold.ttf', 100)
        text = font.render('X wins', True, RED, GREEN)
        textRect = text.get_rect()
        textRect.center = (int(Window_size[0]/2), int(Window_size[1]/2))
        Screen.blit(text, textRect)
        print("X wins")
        if mode == "online":
            create_new_game()
            menu_active = True
            ws_client.close()
        # done = True
    if status == 1:
        font = pygame.font.Font('freesansbold.ttf', 100)
        text = font.render('O wins', True, BLUE, GREEN)
        textRect = text.get_rect()
        textRect.center = (int(Window_size[0]/2), int(Window_size[1]/2))
        Screen.blit(text, textRect)
        if mode == "online":
            create_new_game()
            menu_active = True
            ws_client.close()
        # done = True


##Menu ITEM
menu_items = [
    ("1. Play with AI", 200),
    ("2. Play with Person", 300),
    ("3. Exit", 400)
]
def draw_main_menu():
    Screen.fill(BLACK)
    title_font = pygame.font.SysFont("Arial", 60, bold=True)
    title = title_font.render("CARO GAME", True, WHITE)
    Screen.blit(title, (Screen.get_width()//2 - title.get_width()//2, 50))

    mouse_x, mouse_y = pygame.mouse.get_pos()

    menu_items = [
        ("1. Play with AI", 200),
        ("2. Play with Person", 300),
        ("3. Exit", 400)
    ]

    for text, y in menu_items:
        text_surf = font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=(Screen.get_width()//2, y))
        if text_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(Screen, GRAY, text_rect.inflate(20, 10), 2)  # border effect
        Screen.blit(text_surf, text_rect)
def draw_opponent_left():
    font = pygame.font.Font('freesansbold.ttf', 100)
    text = font.render('Opponent left! You win!', True, GREEN, BLUE)
    textRect = text.get_rect()
    textRect.center = (int(Window_size[0]/2), int(Window_size[1]/2))
    count = 0
    while count < 2*FPS:
        count += 1
        Screen.blit(text, textRect)
        pygame.display.update()
        clock.tick(FPS)
def draw_waiting_screen():
    Screen.fill(BLACK)
    font = pygame.font.SysFont("Arial", 36)

    message = font.render("Waiting for Opponent...", True, WHITE)
    Screen.blit(message, (
        Screen.get_width() // 2 - message.get_width() // 2,
        Screen.get_height() // 2 - message.get_height() // 2
    ))

    # Nút quay lại menu
    button_font = pygame.font.SysFont("Arial", 24)
    back_text = button_font.render("← Menu", True, WHITE)
    back_rect = pygame.Rect(Screen.get_width() - 120, 10, 100, 40)
    pygame.draw.rect(Screen, (70, 70, 70), back_rect, border_radius=8)
    Screen.blit(back_text, (
        back_rect.x + (back_rect.width - back_text.get_width()) // 2,
        back_rect.y + (back_rect.height - back_text.get_height()) // 2
    ))

    return back_rect
          
playing_with_ai = False
playing_with_person = False

### Handle WebSocket connection
def connect_matchmaking():
    global ws_client, waiting_for_match

    def on_message(ws, message):
        data = json.loads(message)
        # current_side = data.get("side")
        # connected_room = data.get("room_id")
        ws_queue.put(data)

    def on_open(ws):
        print("WebSocket connection opened")

    def on_close(ws):
        print("WebSocket connection closed")

    def run():
        global ws_client, waiting_for_match
        waiting_for_match = True
        ws_client = websocket.WebSocketApp(
            f"{WS_BASE_URL}/match",
            on_message=on_message,
            on_open=on_open,
            on_close=on_close,
        )
        ws_client.run_forever()

    threading.Thread(target=run, daemon=True).start()
def handle_ws_messages():
    global waiting_for_match, menu_active, current_side, connected_room
    while not ws_queue.empty():
        msg = ws_queue.get()
        print("Received: ", msg)
        if msg.get("message") == "start":
            waiting_for_match = False
            # playing_with_ai = False
            # playing_with_person = True
        elif msg.get("message") == "waiting":
            current_side = msg.get("side")
            room_id = msg.get("room_id")
            print(f"Matched! Room: {room_id}, Side: {current_side}")

        elif msg.get("message") == "opponent left":
            not_found_message = "Opponent left the game. You win!"
            print(not_found_message)
            ws_client.close()
            draw_opponent_left()
            waiting_for_match = False
            menu_active = True
            create_new_game()

        elif msg.get("message") == "play":  # opponent move
            try:
                r, c = msg.get("row"), msg.get("col")
                my_game.make_move(r, c)
            except Exception as e:
                print("Invalid move received:", e)
        elif msg.get("message") == "end":
            waiting_for_match = False
            menu_active = True
            my_game.reset()

# --------- Main Program Loop -------------------------------------------
while not done:
    for event in pygame.event.get():  # User did something
        if event.type == pygame.QUIT:  # If user clicked close
                done = True  # Flag that we are done so we exit this loop
        if menu_active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                for idx, (text, y) in enumerate(menu_items):
                    text_rect = font.render(text, True, WHITE).get_rect(center=(Screen.get_width()//2, y))
                    if text_rect.collidepoint(mouse_x, mouse_y):
                        if idx == 0:
                            print("Play with AI")
                            my_game.use_ai(True)
                            playing_with_ai = True
                            menu_active = False
                        elif idx == 1:
                            print("Play with Person")
                            my_game.use_ai(False)
                            playing_with_person = True
                            menu_active = False
                            connect_matchmaking()
                            
                        elif idx == 2:
                            print("EXIT")
                            done = True
        
        if playing_with_person == True and not menu_active and playing_with_ai == False:
             if event.type == pygame.MOUSEBUTTONDOWN and my_game.get_winner() == -1:
                pos = pygame.mouse.get_pos()
                col = int(pos[0] // (WIDTH + MARGIN))
                row = int(pos[1] // (HEIGHT + MARGIN))
                if col < COLNUM and row < ROWNUM and my_game.XO == current_side:
                    if col < COLNUM and row < ROWNUM:
                        my_game.make_move(row, col)
                        move_msg = json.dumps({"type": "move", "row": row, "col": col})
                        if ws_client:
                            try:
                                ws_client.send(move_msg)
                            except Exception as e:
                                print("Send error:", e)
                    status = my_game.get_winner()
            
        if not menu_active and not playing_with_person:          
    # ---------------- Undo button ---------------------------------------------
            if undo_button.draw(Screen):  # Ấn nút Undo
                Undo(my_game)
                print("Undo")
                pass
    # --------------Exit button--------------------------------------------
            if exit_button.draw(Screen):  # Ấn nút Thoát
                print('EXIT')
                # quit game
                menu_active = True
                create_new_game()
    # --------------Replay button-------------------------------------------
            if replay_button.draw(Screen):  # Ấn nút Chơi lại
                print('Replay')
                my_game.reset()
                re_draw()
    # ---------Normal mode---------------------------------------------------
            if not is_developer_mode:
        # ------------- Setup button---------------------------------------------
                if len(my_game.last_move) > 0:
                    pass
                if not my_game.is_use_ai:
                    pass
                else:
        # --------------------- AI turn-------------------------------------------
                    if my_game.turn == my_game.ai_turn:
                        if my_game.get_winner() == -1:
        # ---------------------AI MAKE MOVE---------------------------------------- ==================================
                            # my_game.random_ai()                                    #||  Here is where to change AI  ||
                            best_move = agent.get_move(my_game)                      #||                              ||
                            my_game.make_move(best_move[0], best_move[1])            #||                              ||
                            # pygame.time.delay(500)                                   #||          (❁´◡`❁)           ||
        # ------------------------------------------------------------------------- =================================
                            draw(my_game, Screen)
                        ai_thinking_btn.disable_button()
                        ai_thinking_btn.re_draw(Screen)
                        status = my_game.get_winner()
                        checking_winning(status)
                    else:
                        pass

        # --------------Draw ai thinking button ------------------------------------
                if ai_thinking_btn.draw(Screen):
                    pass
        # ----------hard button-----------------------------------------------------
                if h_btn.draw(Screen):
                    h_btn.disable_button()
                    m_btn.enable_button()
                    e_btn.enable_button()
                    my_game.change_hard_ai("hard")
                    
                    agent = Agent(max_depth=my_game.hard_ai,
                                        XO=my_game.get_current_XO_for_AI())
                    print("Hard")
                    pass
        # ----------medium button---------------------------------------------------
                if m_btn.draw(Screen):
                    h_btn.enable_button()
                    m_btn.disable_button()
                    e_btn.enable_button()
                    my_game.change_hard_ai("medium")
                    
                    agent = Agent(max_depth=my_game.hard_ai,
                                        XO=my_game.get_current_XO_for_AI())
                    print("Medium")
                    pass
        # -------------easy button--------------------------------------------------
                if e_btn.draw(Screen):
                    h_btn.enable_button()
                    m_btn.enable_button()
                    e_btn.disable_button()
                    my_game.change_hard_ai("easy")                    

                    agent = Agent(max_depth=my_game.hard_ai,
                                        XO=my_game.get_current_XO_for_AI())
                    print("Easy")
                    pass
        # -------Choose person play first button------------------------------------
                if person_btn.draw(Screen):  # Ấn nút Chọn người đi trước
                    person_btn.disable_button()
                    ai_btn.enable_button()
                    my_game.set_ai_turn(2)
                    

                    agent = Agent(max_depth=my_game.hard_ai,
                                            XO=my_game.get_current_XO_for_AI())
                    print("Human")
                    pass
        # -------Choose AI play first button------------------------------------
                if ai_btn.draw(Screen):  # Ấn nút Chọn AI đi trước
                    ai_btn.disable_button()
                    person_btn.enable_button()
                    my_game.set_ai_turn(1)
                    

                    agent = Agent(max_depth=my_game.hard_ai,
                                    XO=my_game.get_current_XO_for_AI())
                    print("AI")
                    pass

        # -----------------checking is exit game? ------------------------------
                if event.type == pygame.QUIT:  # If user clicked close
                    done = True  # Flag that we are done so we exit this loop
                    # Set the screen background
        # -------Find pos mouse clicked and make a move-------------------------
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    col = int(pos[0] // (WIDTH + MARGIN))
                    row = int(pos[1] // (HEIGHT + MARGIN))
                    # print(pos, col, row)
                    if col < COLNUM and row < ROWNUM:
                        my_game.make_move(row, col)
                    status = my_game.get_winner()
                    if my_game.is_use_ai and my_game.turn == my_game.ai_turn:
                        ai_thinking_btn.enable_button()
                        ai_thinking_btn.re_draw(Screen)
                        draw(my_game, Screen)

    handle_ws_messages()
# ------ Draw screen---------------------------------------------------
    if menu_active:
        draw_main_menu()
    elif waiting_for_match:
        draw_waiting_screen()
        back_button_rect = draw_waiting_screen()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if back_button_rect.collidepoint(event.pos):
                print("Back to menu from waiting screen")
                waiting_for_match = False
                menu_active = True
            # try:
            #     if ws_client:
            #         ws_client.close()
            #         ws_client = None
            # except Exception as e:
            #             print("Error closing websocket:", e)
                
    else:
        Screen.fill(BLACK)
        draw(my_game, Screen)
        exit_button.draw(Screen)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if exit_button.rect.collidepoint(event.pos):
                print("Back to menu from game screen")
                ws_client.close()
                menu_active = True
                create_new_game()
        if playing_with_ai == True:
            undo_button.draw(Screen)
            replay_button.draw(Screen)   
            ai_thinking_btn.draw(Screen)
            h_btn.draw(Screen)
            m_btn.draw(Screen)
            e_btn.draw(Screen)
            person_btn.draw(Screen)
            ai_btn.draw(Screen)
            draw_notification()
    
# -------- checking winner --------------------------------------------
    status = my_game.get_winner()
    mode = None
    if playing_with_ai: mode = "AI"
    else: mode = "online"

    if status == 0 or status == 1:
        count = 0
        while count < 2*FPS:
            count += 1
            checking_winning(status)
            pygame.display.update()
            clock.tick(FPS)
    checking_winning(status, mode)
# Limit to 999999999 frames per second
    clock.tick(FPS)

    # Go ahead and update the screen with what we've drawn.
    pygame.display.update()

pygame.time.delay(50)
quit()
pygame.quit()
sys.exit()
