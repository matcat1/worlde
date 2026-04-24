
import pygame
import sys
import threading
import time
import requests

# interneta setup
if len(sys.argv) > 1:
    server_ip = sys.argv[1]
else:
    server_ip = input("Ievadi servera IP (vai enter priekš localhost): ").strip() or "localhost"

server_url = f"http://{server_ip}:5000"
player_id  = 0

print(f"Pievienojas {server_url} ...")
try:
    r = requests.post(f"{server_url}/join", timeout=5)
    if not r.ok:
        print("Kļūda:", r.json().get("error", "Neizdevās savienoties"))
        sys.exit(1)
    player_id = r.json()["player_id"]
    print(f"Tu esi Spēlētājs {player_id}. Gaidi otru spēlētāju. ok?")
except Exception as e:
    print(f"Nevarēja pievienoties serverim: {e}")
    sys.exit(1)

# pygame

pygame.init()
info   = pygame.display.Info()
WIDTH  = info.current_w
HEIGHT = info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Wordle, tu esi spēlētājs: {player_id}")
clock  = pygame.time.Clock()

# Krāsas
MELNS       = (20,  20,  20)
PELEKS      = (58,  58,  60)
GAISS_PELEKS= (90,  90,  90)
ZALS        = (80,  140, 80)
DZELTENS    = (181, 159, 59)
BALTS       = (255, 255, 255)
TUMSI_PELEKS= (130, 130, 130)
SARKANS     = (220, 80,  80)
ZELTA       = (200, 160, 50)
GAIŠI_ZILS  = (80,  160, 200)

COLOR_MAP = {"grey": PELEKS, "green": ZALS, "yellow": DZELTENS}

font_big   = pygame.font.SysFont("Georgia", 36, bold=True)
font_small = pygame.font.SysFont("Georgia", 14, bold=True)
font_msg   = pygame.font.SysFont("Georgia", 20, bold=True)
font_title = pygame.font.SysFont("Georgia",      26, bold=True)
font_score = pygame.font.SysFont("Georgia", 20, bold=True)

MIKSTINAJUMI = {
    "a":"ā","e":"ē","i":"ī","u":"ū",
    "c":"č","s":"š","z":"ž",
    "g":"ģ","k":"ķ","l":"ļ","n":"ņ",
}

keyboard_rindas = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M","'","DEL"],
    ["ENTER"],
]

# servera states 

server_state = {}
state_lock   = threading.Lock() # paralēla darbība, lai programma darbotos bez raustijumiem


def poll_state():
    global server_state  
    while True: 
        try:
           
            r = requests.get(f"{server_url}/state", timeout=2)
            if r.ok: 
                with state_lock:  # "aizslēdz" piekļuvi
                    server_state = r.json()  # saglabā jauno state
        except Exception:
            pass 
        time.sleep(0.4)


poller = threading.Thread(target=poll_state, daemon=True)

poller.start()


def get_state():
    with state_lock:  
        return dict(server_state) 

# localie veriables

current_word      = ""
mikstinajuma_mode = False
local_msg         = ""
local_msg_timer   = 0

def set_local_msg(teksts, ms=2000):
    global local_msg, local_msg_timer
    local_msg       = teksts
    local_msg_timer = pygame.time.get_ticks() + ms

#klavieraturas krasosana

def compute_pogu_krasas(written_words, written_colours):
    
    rank = {None:0, "grey":1, "yellow":2, "green":3}
    #vārdnīca burts-krāsa
    pk = {}
    
    
    for word, colours in zip(written_words, written_colours):
        
        for i, burts in enumerate(word): #visi burti
            c = colours[i]
            if rank[c] > rank.get(pk.get(burts), 0):
                pk[burts] = c #updato krasu ja kas mainas
            
            #to pašu ari burtam bez mikstinajuma piem š, s ari iekrasojas
            for base, mikst in MIKSTINAJUMI.items():
                if mikst == burts and rank[c] > rank.get(pk.get(base), 0):
                    pk[base] = c

    return pk

# darbibas

def rakstit(letter):
    global current_word, mikstinajuma_mode
    s = get_state()
    if s.get("round_over") or s.get("current_turn") != player_id:
        return
    if mikstinajuma_mode:
        letter = MIKSTINAJUMI.get(letter, letter)
        mikstinajuma_mode = False
    if len(current_word) < 5:
        current_word += letter

def dzest():
    global current_word, mikstinajuma_mode
    s = get_state()
    if s.get("round_over") or s.get("current_turn") != player_id:
        return
    mikstinajuma_mode = False
    current_word = current_word[:-1]

def submit():
    global current_word, mikstinajuma_mode
    s = get_state()
    if s.get("round_over"):
        return
    if s.get("current_turn") != player_id:
        set_local_msg("Gaidi savu kārtu!")
        return
    mikstinajuma_mode = False
    if len(current_word) < 5:
        set_local_msg("Vajag 5 burtus!")
        return
    try:
        r = requests.post(f"{server_url}/guess",
                          json={"player_id": player_id, "word": current_word},
                          timeout=3)
        if r.ok:
            current_word = ""
        else:
            set_local_msg(r.json().get("error", "Kautkas nav kā vajag"))
    except Exception:
        set_local_msg("Mmmm, kautkas ar savienojumu ne tā")

def do_next_round():
    global current_word, mikstinajuma_mode
    current_word      = ""
    mikstinajuma_mode = False
    try:
        requests.post(f"{server_url}/next_round", timeout=3)
    except Exception:
        pass

# layout

TILE    = 72
GAP     = 8
BOARD_X = (WIDTH - (TILE * 5 + GAP * 4)) // 2
BOARD_Y = 100
KB_Y    = BOARD_Y + 6 * (TILE + GAP) + 14

def draw_tile(letter, bg, border, x, y):
    pygame.draw.rect(screen, bg,     (x, y, TILE, TILE), border_radius=8)
    pygame.draw.rect(screen, border, (x, y, TILE, TILE), 2, border_radius=8)
    if letter:
        t = font_big.render(letter.upper(), True, BALTS)
        screen.blit(t, t.get_rect(center=(x + TILE//2, y + TILE//2)))

def draw_board(s):
    ww = s.get("written_words",   [])
    wc = s.get("written_colours", [])
    round_over = s.get("round_over", False)

    for rinda in range(6):
        for kolonna in range(5):
            x = BOARD_X + kolonna * (TILE + GAP)
            y = BOARD_Y + rinda   * (TILE + GAP)

            if rinda < len(ww):
                k = COLOR_MAP[wc[rinda][kolonna]]
                draw_tile(ww[rinda][kolonna], k, k, x, y)
            elif rinda == len(ww) and not round_over:
                b = current_word[kolonna] if kolonna < len(current_word) else ""
                draw_tile(b, MELNS, GAISS_PELEKS if b else PELEKS, x, y)
            else:
                draw_tile("", MELNS, PELEKS, x, y)

def pogas_rect(ri, ci, label):
    KH, KW, KG = 43, 52, 6
    y = KB_Y + ri * (KH + KG)
    if ri in (0, 1):
        n  = len(keyboard_rindas[ri])
        sx = (WIDTH - (n * KW + (n-1) * KG)) // 2
        return pygame.Rect(sx + ci * (KW + KG), y, KW, KH)
    elif ri == 2:
        sx = (WIDTH - (7 * KW + 7 * KG + (KW-10) + KG + (KW+16))) // 2
        if ci < 7:
            return pygame.Rect(sx + ci * (KW + KG), y, KW, KH)
        elif ci == 7:
            return pygame.Rect(sx + 7*(KW+KG), y, KW-10, KH)
        else:
            return pygame.Rect(sx + 7*(KW+KG) + (KW-10) + KG, y, KW+16, KH)
    else:
        w = KW*3 + KG*2
        return pygame.Rect((WIDTH - w)//2, y, w, KH)

def draw_keyboard(s):
    ww  = s.get("written_words",   [])
    wc  = s.get("written_colours", [])
    pk  = compute_pogu_krasas(ww, wc)
    my_turn = s.get("current_turn") == player_id and not s.get("round_over")

    for ri, rinda in enumerate(keyboard_rindas):
        for ci, label in enumerate(rinda):
            r = pogas_rect(ri, ci, label)
            if label == "ENTER":
                krasa = ZALS if my_turn else GAISS_PELEKS
            elif label == "DEL":
                krasa = (90, 90, 100)
            elif label == "'":
                krasa = ZELTA if mikstinajuma_mode else TUMSI_PELEKS
            else:
                c_name = pk.get(label.lower())
                krasa  = COLOR_MAP[c_name] if c_name else TUMSI_PELEKS

            # padara tavu klaviaturu tumsaku kad nav tavs gajiens
            if not my_turn and label not in ("DEL", "'", "ENTER"):
                krasa = tuple(max(0, c - 40) for c in krasa)

            pygame.draw.rect(screen, krasa, r, border_radius=6)
            t = font_small.render(label, True, BALTS)
            screen.blit(t, t.get_rect(center=r.center))

def handle_click(pos, s):
    global mikstinajuma_mode
    for ri, rinda in enumerate(keyboard_rindas):
        for ci, label in enumerate(rinda):
            if pogas_rect(ri, ci, label).collidepoint(pos):
                if label == "DEL":
                    dzest()
                elif label == "ENTER":
                    submit()
                elif label == "'":
                    if s.get("current_turn") == player_id and not s.get("round_over"):
                        mikstinajuma_mode = not mikstinajuma_mode
                else:
                    rakstit(label.lower())
                return

# Draw

def draw_all(s):
    screen.fill(MELNS)

    # nosaukums
    t = font_title.render("LATVIESU WORDLE", True, BALTS)
    screen.blit(t, t.get_rect(center=(WIDTH/2, 22)))

    # liderbords
    scores  = s.get("scores", {"1":0,"2":0})
    s1, s2  = scores.get("1",0), scores.get("2",0)

    def star_row(n, total=3):
        return "+"*n + "-"*(total-n)

    p1_col = GAIŠI_ZILS if player_id == 1 else TUMSI_PELEKS
    p2_col = GAIŠI_ZILS if player_id == 2 else TUMSI_PELEKS
    you     = " (tu)" if player_id == 1 else ""
    opp     = " (tu)" if player_id == 2 else ""

    t1 = font_score.render(f"Spēlētājs 1{you}: {star_row(s1)}", True, p1_col)
    t2 = font_score.render(f"Spēlētājs 2{opp}: {star_row(s2)}", True, p2_col)
    sep= font_score.render("  |  ", True, TUMSI_PELEKS)

    total_w = t1.get_width() + sep.get_width() + t2.get_width()
    cx = (WIDTH - total_w) // 2
    cy = 48
    screen.blit(t1,  (cx, cy))
    screen.blit(sep, (cx + t1.get_width(), cy))
    screen.blit(t2,  (cx + t1.get_width() + sep.get_width(), cy))

    # messagi
    round_over   = s.get("round_over",   False)
    match_over   = s.get("match_over",   False)
    current_turn = s.get("current_turn", 1)
    round_winner = s.get("round_winner")
    target       = s.get("target_word",  "")

    if match_over:
        mw = s.get("match_winner")
        if mw == player_id:
            status, col = "Good boy, uzvarēji!", ZALS
        else:
            status, col = f"Spēlētājs {mw} uzvarēja, tu zaudēji.", SARKANS
    elif round_over:
        if round_winner is None:
            status, col = f"Neizšķirts  Atbilde: {target.upper()}", DZELTENS
        elif round_winner == player_id:
            status, col = f"Malacis, tu uzminēji! +1  (atbilde: {target.upper()})", ZALS
        else:
            status, col = f"Tavs opponents uzminēja, get better.  Atbilde: {target.upper()}", SARKANS
    elif mikstinajuma_mode:
        status, col = "' raksti burtinu ar garumzimi", ZELTA
    elif local_msg and pygame.time.get_ticks() < local_msg_timer:
        bad = any(w in local_msg for w in ("nav","Vajag","kārta","kaut"))
        status, col = local_msg, (SARKANS if bad else ZALS)
    elif current_turn == player_id:
        status, col = "Tavs gājiens", ZALS
    else:
        status, col = f"Gaidam otru spēlētāju…", TUMSI_PELEKS

    t = font_msg.render(status, True, col)
    screen.blit(t, t.get_rect(center=(WIDTH/2, 76)))

    draw_board(s)
    draw_keyboard(s)

    # 
    if round_over:
        hint = "R – nākamā kārta" if not match_over else "R – jauns mačs"
        t = font_small.render(hint, True, (100,100,100))
        screen.blit(t, t.get_rect(center=(WIDTH/2, KB_Y + 195)))

# gaidām ekrāns

def draw_waiting():
    screen.fill(MELNS)
    lines = [
        ("LATVIESU WORDLE", font_title, BALTS),
        ("", None, None),
        (f"Tu esi spēlētājs {player_id}", font_msg, GAIŠI_ZILS),
        ("Esi pacietīgs, gaidam tavu draugu...", font_msg, TUMSI_PELEKS),
        ("", None, None),
        (f"Aizsūti savu IP adresi savam draugam", font_small, TUMSI_PELEKS),
    ]
    y = HEIGHT//2 - 80
    for text, font, col in lines:
        if font:
            t = font.render(text, True, col)
            screen.blit(t, t.get_rect(center=(WIDTH//2, y)))
        y += 34

# gaidam abus playerus

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

    s = get_state()
    if s.get("players_joined", 0) >= 2:
        break

    draw_waiting()
    pygame.display.flip()
    clock.tick(30)

# main loop ===================================================================================

while True:
    s = get_state()
    draw_all(s)
    pygame.display.flip()
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:
            k = event.key

            if k == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            elif k == pygame.K_r and s.get("round_over"):
                do_next_round()

            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                submit()

            elif k == pygame.K_BACKSPACE:
                dzest()

            elif k in (pygame.K_QUOTE, pygame.K_BACKQUOTE):
                if s.get("current_turn") == player_id and not s.get("round_over"):
                    mikstinajuma_mode = not mikstinajuma_mode

            else:
                fiziskais = {
                    pygame.K_a:"a", pygame.K_b:"b", pygame.K_c:"c", pygame.K_d:"d",
                    pygame.K_e:"e", pygame.K_f:"f", pygame.K_g:"g", pygame.K_h:"h",
                    pygame.K_i:"i", pygame.K_j:"j", pygame.K_k:"k", pygame.K_l:"l",
                    pygame.K_m:"m", pygame.K_n:"n", pygame.K_o:"o", pygame.K_p:"p",
                    pygame.K_q:"q", pygame.K_r:"r", pygame.K_s:"s", pygame.K_t:"t",
                    pygame.K_u:"u", pygame.K_v:"v", pygame.K_w:"w", pygame.K_x:"x",
                    pygame.K_y:"y", pygame.K_z:"z",
                }
                ch = fiziskais.get(k)
                if ch:
                    rakstit(ch)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_click(event.pos, s)
