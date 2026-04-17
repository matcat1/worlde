import pygame
import sys
import random
from words import WORDS
from words import WORDY

pygame.init()

info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Latviesu Wordle")
clock = pygame.time.Clock()

# krasas
MELNS = (20, 20, 20)
PELEKS = (58, 58, 60)
GAISS_PELEKS = (90, 90, 90)
ZALS = (80, 140, 80)
DZELTENS = (181, 159, 59)
BALTS = (255, 255, 255)
TUMSI_PELEKS = (130, 130, 130)
SARKANS = (220, 80, 80)
ZELTA = (200, 160, 50)

font_big = pygame.font.SysFont("DejaVu Sans", 36, bold=True)
font_small = pygame.font.SysFont("DejaVu Sans", 14, bold=True)
font_msg = pygame.font.SysFont("DejaVu Sans", 20, bold=True)
font_title = pygame.font.SysFont("Georgia", 26, bold=True)

# ja nospied ' un tad burtu, dabuu mikstinaajumu
# piem ' + a = ā
MIKSTINAJUMI = {
    "a": "ā", "e": "ē", "i": "ī", "u": "ū",
    "c": "č", "s": "š", "z": "ž",
    "g": "ģ", "k": "ķ", "l": "ļ", "n": "ņ",
}

# qwerty izkartojums
keyboard_rindas = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["Z", "X", "C", "V", "B", "N", "M", "'", "DEL"],
    ["ENTER"],
]

# speles stāvoklis
target_word = random.choice(WORDY)
visi_vardi = set(WORDS)

written_words = []        # visi jau nosūtītie vārdi
written_colours = []  # to krasas
current_word = ""       # ko šobrīd raksta
mikstinajuma_mode = False
game_over = False
uzvareja = False

# katras pogas krāsa uz klaviatūras
pogu_krasas = {}

msg = ""
msg_timer = 0  # ticks lidz kuram radīt msg


def reset():
    global target_word, written_words, written_colours, current_word
    global mikstinajuma_mode, game_over, uzvareja, pogu_krasas, msg, msg_timer

    target_word = random.choice(WORDY)
    written_words = []
    written_colours = []
    current_word = ""
    mikstinajuma_mode = False
    game_over = False
    uzvareja = False
    pogu_krasas = {}
    msg = ""
    msg_timer = 0


def rakstit(letter):
    global current_word, mikstinajuma_mode
    if game_over:
        return
    if mikstinajuma_mode:
        letter = MIKSTINAJUMI.get(letter, letter) #burts bus mikstinats, vai ja nevar paliks parasts
        mikstinajuma_mode = False
    if len(current_word) < 5:
        current_word += letter


def dzest():
    global current_word, mikstinajuma_mode
    if game_over:
        return
    mikstinajuma_mode = False
    current_word = current_word[:-1] #nodzes pedejo burtu


def set_msg(teksts, timer=2000):
    global msg, msg_timer
    msg = teksts
    msg_timer = pygame.time.get_ticks() + timer


def submit():
    global current_word, written_words, written_colours
    global pogu_krasas, game_over, uzvareja, mikstinajuma_mode

    # parbaudam vai spele ir beigusies
    if game_over == True:
        return
    
    mikstinajuma_mode = False

    # vajag 5 burtus!!!
    if len(current_word) < 5:
        set_msg("Vajag 5 burtus!")
        return
    # parbaudam vai vards eksiste vispaar
    if current_word not in visi_vardi:
        set_msg("Šāda vārda nav!")
        return

    # sakuma viss ir peleks (defaultais)
    krasas = [PELEKS, PELEKS, PELEKS, PELEKS, PELEKS]
    burti = list(target_word)  # sadala pa burtiem
    
    print("current word:", current_word)  # debugosanai
    print("target:", target_word)

    # ZALIE burti (pareiza vieta)
    for i in range(5):
        if current_word[i] == target_word[i]:
            krasas[i] = ZALS
            burti[i] = None  # lai neskaita divreiz

    # DZELENIE burti (nepareiza vieta bet eksiste)
    for i in range(5):
            if krasas[i] == ZALS:
                continue  # izlaiz ja jau zals
            if current_word[i] in burti:
                krasas[i] = DZELTENS
                burti[burti.index(current_word[i])] = None

    # updotojam klaviaturas krasas
    # lielaks skaitlis = labaka krasa (peleks=1, dzeltens=2, zals=3)
    krasu_limens = {None: 0, PELEKS: 1, DZELTENS: 2, ZALS: 3}
    
    for i in range(5):
        burts = current_word[i]
        new_colour = krasas[i]
        old_colour = pogu_krasas.get(burts)
        
        # updotojam tikai ja jaunaa krasa ir labaaka par veco
        if krasu_limens[new_colour] > krasu_limens.get(old_colour, 0):
          pogu_krasas[burts] = new_colour
        
        # TODO: varbuut sho var uzrakstit skaistaaak kadreiz
        # arii updotojam pamatburtu ja bija ar mikstinajumu
        for burt, mikst in MIKSTINAJUMI.items():
            if mikst == burts:
                    old2_colour = pogu_krasas.get(burt)
                    if krasu_limens[new_colour] > krasu_limens.get(old2_colour, 0):
                        pogu_krasas[burt] = new_colour

    written_words.append(current_word)
    written_colours.append(krasas)
    current_word = ""  # notira paasreizejo vardu


    # parbaudam vai uzvareeja
    zalo_skaits = 0
    for burtu_krasa in krasas:
        if burtu_krasa == ZALS:
            zalo_skaits += 1
    
    if zalo_skaits == 5:  # visi 5 ir zali = uzvara!!!
        uzvareja = True
        game_over = True
        set_msg("Malacits", timer=99999)
    elif len(written_words) >= 6:
        # speletajs zaudeja :(
        game_over = True
        set_msg("Atbilde: " + target_word.upper(), timer=99999)


# --------------------------------- ZIIMESANAS STUFF

TILE = 72
GAP = 6
BOARD_X = (WIDTH - (TILE * 5 + GAP * 4)) // 2  # centreet tafeliiti
BOARD_Y = 75
KB_Y = BOARD_Y + 6 * (TILE + GAP) + 14  # klaviatura saaksa sheit


def draw_tile(letter, bg, border, x, y):
	# uzzimee vienu kvadratiinu uz tafelites
	pygame.draw.rect(screen, bg, (x, y, TILE, TILE), border_radius=8)
	pygame.draw.rect(screen, border, (x, y, TILE, TILE), 2, border_radius=8)
	if letter != "":  # ziimee burtu tikai ja ir
		t = font_big.render(letter.upper(), True, BALTS)
		screen.blit(t, t.get_rect(center=(x + TILE//2, y + TILE//2)))


def draw_board():
    for rinda in range(6):        # 6 rindas
        for kolonna in range(5):  # 5 kolonnas
            x = BOARD_X + kolonna * (TILE + GAP)
            y = BOARD_Y + rinda * (TILE + GAP)

            if rinda < len(written_words):
                # jau uzmineeta rinda - raada krasas
                k = written_colours[rinda][kolonna]
                draw_tile(written_words[rinda][kolonna], k, k, x, y)
            
            elif rinda == len(written_words):
                    # paasreizeejaa rinda kur raksta
                    if kolonna < len(current_word):
                        b = current_word[kolonna]
                    else:
                            b = ""
                    draw_tile(b, MELNS, GAISS_PELEKS if b != "" else PELEKS, x, y)
            
            else:
                # tuksas naakamas rindas
                draw_tile("", MELNS, PELEKS, x, y)


def pogas_rect(ri, ci, label):
	# atgriez taisnstauri klaviaturas pogai
	KH = 43   # pogas augstums
	KW = 52   # pogas platums
	KG = 6    # atstarpe starp pogaam
	y = KB_Y + ri * (KH + KG)

	if ri == 0 or ri == 1:
		# parastaa rinda (Q W E R T utt)
		n = len(keyboard_rindas[ri])
		sx = (WIDTH - (n * KW + (n-1) * KG)) // 2
		return pygame.Rect(sx + ci * (KW + KG), y, KW, KH)

	elif ri == 2:
            # apaksejaa burti rinda: Z X C V B N M ' DEL
            sx = (WIDTH - (7 * KW + 7 * KG + (KW-10) + KG + (KW+16))) // 2
            if ci < 7:
                return pygame.Rect(sx + ci * (KW + KG), y, KW, KH)
            elif ci == 7:  # miikstinajuma poga
                return pygame.Rect(sx + 7 * (KW + KG), y, KW - 10, KH)
            else:  # DEL poga (lielaka)
                return pygame.Rect(sx + 7 * (KW + KG) + (KW-10) + KG, y, KW + 16, KH)

	else:
		# ENTER poga (ļoti plata)
		w = KW * 3 + KG * 2
		return pygame.Rect((WIDTH - w) // 2, y, w, KH)


def draw_keyboard():
    for ri, rinda in enumerate(keyboard_rindas):
        for ci, label in enumerate(rinda):
            r = pogas_rect(ri, ci, label)

            # nosakaam kadu krasu pogai
            if label == "ENTER":
                krasa = ZALS  # vienmer zala
            elif label == "DEL":
                krasa = (90, 90, 100)  # peelciga krasa
            elif label == "'":
                    # zelta ja miikstinajuma rezims ieslgts
                    if mikstinajuma_mode == True:
                        krasa = ZELTA
                    else:
                        krasa = TUMSI_PELEKS
            else:
                # parasts burts - izmanto uzmineeto krasu vai default
                krasa = pogu_krasas.get(label.lower(), TUMSI_PELEKS)

            pygame.draw.rect(screen, krasa, r, border_radius=6)
            
            # uzzimee burtu uz pogas
            t = font_small.render(label, True, BALTS)
            screen.blit(t, t.get_rect(center=r.center))


def handle_click(pos):
    global mikstinajuma_mode

    # paarbaudam katru pogu vai klikis bija uz taas
    for ri, rinda in enumerate(keyboard_rindas):
            for ci, label in enumerate(rinda):
                r = pogas_rect(ri, ci, label)
                if r.collidepoint(pos):
                    # atraam pogu uz kuras noklikskinja!!!
                    if label == "DEL":
                            dzest()
                    elif label == "ENTER":
                        submit()
                    elif label == "'":
                        if game_over == False:
                            mikstinajuma_mode = not mikstinajuma_mode
                    else:
                        rakstit(label.lower())
                    return  # paartrauc meklesanu pec atrasanas


def draw_all():
    screen.fill(MELNS)  # melns fons

    # virsrakts augsa
    t = font_title.render("LATVIESU WORDLE", True, BALTS)
    screen.blit(t, t.get_rect(center=(WIDTH/2, 35)))


    # raada zinojumu vai miikstinajuma padominju
    if mikstinajuma_mode == True:
        t = font_msg.render("' raksti burtinu ar garumzimi", True, ZELTA)
        screen.blit(t, t.get_rect(center=(WIDTH/2, 57)))
    elif msg and pygame.time.get_ticks() < msg_timer:
        # sarkans kludam, zals labajiem zinojumiem
        if "nav" in msg or "Vajag" in msg:
            krasa = SARKANS
        else:
            krasa = ZALS
        t = font_msg.render(msg, True, krasa)
        screen.blit(t, t.get_rect(center=(WIDTH/2, 57)))

    draw_board()      # uzzimee 6x5 rezgi
    draw_keyboard()   # uzzimee klaviatauru apaksa

    if game_over == True:
        # raada ka restarteet
        t = font_small.render("Nospied R lai speleetu velreiz", True, (100, 100, 100))
        screen.blit(t, t.get_rect(center=(320, 768)))


####-------- GALVENAIS SPELES CIKLS (neaizskari) --------####

while True:
    draw_all()
    pygame.display.flip()
    clock.tick(60)  # 60 kadri sekundee

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over == True:
                reset()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                submit()
            elif event.key == pygame.K_BACKSPACE:
                dzest()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_QUOTE or event.key == pygame.K_BACKQUOTE:
                if game_over == False:
                    mikstinajuma_mode = not mikstinajuma_mode
            else:
                # mapo klaviaturas taustiņus uz burtiem
                fiziskais = {
                    pygame.K_a: "a", pygame.K_b: "b", pygame.K_c: "c", pygame.K_d: "d",
                    pygame.K_e: "e", pygame.K_f: "f", pygame.K_g: "g", pygame.K_h: "h",
                    pygame.K_i: "i", pygame.K_j: "j", pygame.K_k: "k", pygame.K_l: "l",
                    pygame.K_m: "m", pygame.K_n: "n", pygame.K_o: "o", pygame.K_p: "p",
                    pygame.K_q: "q", pygame.K_r: "r", pygame.K_s: "s", pygame.K_t: "t",
                    pygame.K_u: "u", pygame.K_v: "v", pygame.K_w: "w", pygame.K_x: "x",
                    pygame.K_y: "y", pygame.K_z: "z",
                }
                ch = fiziskais.get(event.key)
                if ch != None:  # raksta tikai ja derigs burts
                    rakstit(ch)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_click(event.pos)