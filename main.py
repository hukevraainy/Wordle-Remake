import pygame
import sys
from settings import *
from file_system import load_users, save_users, get_standard_word, get_random_word, load_session, save_session, get_session_users, load_words, load_time_stats, get_timed_word, get_random_mix
from game_loop import play_game, play_time_attack

# initialize pygame and global variables
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)

USERS_LIST = load_users()
CURRENT_USER = None

def draw_button(rect, text, hover=False, color=ACCENT_COLOR, disabled=False):
    # draws a button with hover and disabled states
    if disabled:
        draw_col = (180, 180, 170)  # gray = disabled
        text_col = (130, 130, 120)  # faded text
    else:
        draw_col = BUTTON_HOVER if hover else color
        text_col = TEXT_COLOR

    # button shadow
    pygame.draw.rect(SCREEN, BLACK, (rect.x, rect.y+4, rect.w, rect.h), border_radius=10)
    
    # main body
    pygame.draw.rect(SCREEN, draw_col, rect, border_radius=10)
    
    # text
    font = pygame.font.SysFont(FONT_NAME, 20, bold=True)
    surf = font.render(text, True, text_col)
    SCREEN.blit(surf, surf.get_rect(center=rect.center))

def update_stats(res):
    # updates leaderboard stats if user won
    if not isinstance(res, dict) or 'res' not in res: 
        return
    
    if res['res'] == "WIN":
        existing_data = USERS_LIST.find_user(CURRENT_USER)
        
        # get data returned from game_loop.py
        l_word = res.get('target', 'N/A')
        l_guesses = ",".join(res.get('guesses', []))
        
        # prepare new stats dictionary
        new_stats = {
            'name': CURRENT_USER,
            'last_word': l_word,
            'last_guesses': l_guesses
        }
        
        # update existing stats
        if existing_data:
            new_total = float(existing_data['total_time']) + float(res['time'])
            new_games = int(existing_data['games']) + 1
            new_stats.update({
                'avg_time': new_total / new_games,
                'games': new_games,
                'total_time': new_total
            })
            USERS_LIST.remove_user(CURRENT_USER)

        # new user entry
        else:
            new_stats.update({
                'avg_time': float(res['time']),
                'games': 1,
                'total_time': float(res['time'])
            })
            
        USERS_LIST.add_sorted(new_stats)
        save_users(USERS_LIST)


def show_match_history(user_data):
    # displays past game history for a user
    while True:
        SCREEN.fill(BG_COLOR)
        mse = pygame.mouse.get_pos()
        
        font_h = pygame.font.SysFont(FONT_NAME, 30, bold=True)
        font_r = pygame.font.SysFont(FONT_NAME, 22)
        
        title = font_h.render(f"HISTORY: {user_data['name']}", True, TEXT_COLOR)
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        word_txt = font_r.render(f"Target Word: {user_data.get('word', 'N/A')}", True, GREEN)
        SCREEN.blit(word_txt, (WIDTH//2 - word_txt.get_width()//2, 100))
        
        guesses = user_data.get('guesses', "").split(',')
        start_y = 150
        for i, g in enumerate(guesses):
            if g:
                txt = font_r.render(f"Guess {i+1}: {g}", True, BLACK)
                SCREEN.blit(txt, (WIDTH//2 - txt.get_width()//2, start_y))
                start_y += 30
        
        btn_rect = pygame.Rect(WIDTH//2 - 50, HEIGHT - 100, 100, 40)
        draw_button(btn_rect, "CLOSE", btn_rect.collidepoint(mse))
        
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and btn_rect.collidepoint(mse):
                return

def select_overwrite_slot():
    # prompts player to select which session to overwrite
    sessions = get_session_users()
    while True:
        SCREEN.fill(BG_COLOR)
        mse = pygame.mouse.get_pos()
        font = pygame.font.SysFont(FONT_NAME, 22, bold=True)
        SCREEN.blit(font.render("STORAGE FULL (5/5)", True, RED), (WIDTH//2-100, 50))
        for i, name in enumerate(sessions):
            r = pygame.Rect((WIDTH-260)//2, 130 + i*60, 260, 50)
            draw_button(r, f"Replace: {name}", r.collidepoint(mse), color=(200, 100, 100))
            if pygame.mouse.get_pressed()[0] and r.collidepoint(mse): return name
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()

def run_game_wrapper(cat, word, diff, guesses=[]):

    # runs the game and handles cleanup.
    # if finished, removes from resume tab and updates leaderboard
    from file_system import delete_session # import helper
    
    # 1. start game
    res = play_game(SCREEN, cat, word, diff, CURRENT_USER, guesses, overwrite_func=select_overwrite_slot)
    
    # 2. check if game is finished
    if isinstance(res, dict):
        # cleanup: remove this account from "resume"
        delete_session(CURRENT_USER)
        
        # leaderboard: update their leaderboard stats
        if res.get('res') == "WIN":
            update_stats(res)

def time_attack_select():
    # select time duration for time attack mode
    while True:
        SCREEN.fill(BG_COLOR)
        mse = pygame.mouse.get_pos()
        draw_button(pygame.Rect(10, 10, 80, 30), "BACK")
        font = pygame.font.SysFont(FONT_NAME, 30, bold=True)
        head = font.render("SELECT DURATION", True, TEXT_COLOR)
        SCREEN.blit(head, (WIDTH//2 - head.get_width()//2, 80))
        opts = [30, 60, 90]
        rects = []
        for i, dur in enumerate(opts):
            r = pygame.Rect((WIDTH-200)//2, 160 + i*70, 200, 50)
            rects.append(r)
            draw_button(r, f"{dur} SECONDS", r.collidepoint(mse))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(10,10,80,30).collidepoint(mse): return
                # PASS CURRENT_USER HERE
                if rects[0].collidepoint(mse): play_time_attack(SCREEN, 30, CURRENT_USER); return
                if rects[1].collidepoint(mse): play_time_attack(SCREEN, 60, CURRENT_USER); return
                if rects[2].collidepoint(mse): play_time_attack(SCREEN, 90, CURRENT_USER); return

# category selection
def cat_select():
    cats = list(load_words().keys())
    while True:
        SCREEN.fill(BG_COLOR)
        mse = pygame.mouse.get_pos()
        draw_button(pygame.Rect(10, 10, 80, 30), "BACK")
        for i, cat in enumerate(cats):
            r = pygame.Rect((WIDTH-200)//2, 100 + i*60, 200, 50)
            draw_button(r, cat, r.collidepoint(mse))
            if pygame.mouse.get_pressed()[0] and r.collidepoint(mse):
                word, diff = get_random_word(cat)
                run_game_wrapper(cat, word, diff)
                return
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and pygame.Rect(10,10,80,30).collidepoint(mse): return

def gamemode_select(username):
    # select gamemode after username entry
    global CURRENT_USER
    CURRENT_USER = username
    while True:
        SCREEN.fill(BG_COLOR)
        mse = pygame.mouse.get_pos()
        draw_button(pygame.Rect(10, 10, 80, 30), "BACK")
        
        head = pygame.font.SysFont(FONT_NAME, 30, bold=True).render(f"Welcome, {username}", True, TEXT_COLOR)
        SCREEN.blit(head, (WIDTH//2 - head.get_width()//2, 80))
        
        opts = ["TIMED WORDLE", "INFINITE WORDLE", "CATEGORY MODE", "TIME ATTACK"]
        rects = []
        for i, opt in enumerate(opts):
            r = pygame.Rect((WIDTH-220)//2, 160 + i*70, 220, 50)
            rects.append(r)
            draw_button(r, opt, r.collidepoint(mse))
            
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(10, 10, 80, 30).collidepoint(e.pos): return
                
                # 1. timed wordle (tradional daily wordle gamemode)
                if rects[0].collidepoint(e.pos):
                    w, d = get_timed_word()
                    run_game_wrapper("TIMED", w, d)
                    return
                
                # 2. infinite wordle (random words until quit)
                if rects[1].collidepoint(e.pos):
                    w, d = get_standard_word()
                    run_game_wrapper("INFINITE", w, d)
                    return
                    
                # 3. category mode (guess from categories)
                if rects[2].collidepoint(e.pos):
                    cat, word, diff = get_random_mix()
                    run_game_wrapper(cat, word, diff)
                    return
                    
                # 4. time attack (new gamemode expansion)
                if rects[3].collidepoint(e.pos):
                    time_attack_select()
                    return

def new_game_flow():

    # get username, checks uniqueness against leaderboard and resume tab, then goes to gamemode select.
    name = ""
    font = pygame.font.SysFont(FONT_NAME, 30)
    error_msg = ""
    
    while True:
        SCREEN.fill(BG_COLOR)
        
        # title
        head = font.render("NEW GAME REGISTRATION", True, TEXT_COLOR)
        SCREEN.blit(head, (WIDTH//2 - head.get_width()//2, 50))
        
        # label
        lbl = font.render("ENTER NEW USERNAME:", True, BLACK)
        SCREEN.blit(lbl, (WIDTH//2 - lbl.get_width()//2, HEIGHT//2 - 60))
        
        # input name box
        box = pygame.Rect(WIDTH//2 - 120, HEIGHT//2, 240, 50)
        pygame.draw.rect(SCREEN, WHITE, box, border_radius=5)
        pygame.draw.rect(SCREEN, ACCENT_COLOR, box, 2, border_radius=5)
        
        # render name
        txt = font.render(name, True, BLACK)
        SCREEN.blit(txt, (box.x + 10, box.y + 10))
        
        # error message display
        if error_msg:
            err = pygame.font.SysFont(FONT_NAME, 20).render(error_msg, True, RED)
            SCREEN.blit(err, (WIDTH//2 - err.get_width()//2, HEIGHT//2 + 70))
        
        # back button
        back_rect = pygame.Rect(10, 10, 80, 30)
        draw_button(back_rect, "BACK", back_rect.collidepoint(pygame.mouse.get_pos()))
        
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                 if back_rect.collidepoint(e.pos): 
                     return
            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and len(name) > 0:
                    # 1. fetch current active sessions in "resume" 
                    active_sessions = get_session_users()
                    
                    # 2. checks for uniqueness
                    if USERS_LIST.find_user(name):
                        # name exists in "leaderboard"
                        error_msg = "User already exists! Please choose another."
                    elif name in active_sessions:
                        # name exists in "resume"
                        error_msg = "Account is active in Resume! Use a different name."
                    else:
                        # successful entry, go to gamemode select
                        gamemode_select(name)
                        return
                    
                elif e.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                    error_msg = ""

                elif len(name) < 12 and e.unicode.isalnum():
                    name += e.unicode

def resume_menu():

    # allows user to select from active sessions to resume
    global CURRENT_USER
    
    pygame.event.clear(pygame.MOUSEBUTTONDOWN)
    
    while True:
        SCREEN.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        draw_button(pygame.Rect(10, 10, 80, 30), "BACK")
        
        head = pygame.font.SysFont(FONT_NAME, 30, bold=True).render("SELECT ACCOUNT", True, TEXT_COLOR)
        SCREEN.blit(head, (WIDTH//2 - head.get_width()//2, 60))
        
        sessions = get_session_users()
        if not sessions:
            return # safety check: if no sessions, return to main menu
        
        start_y = 130
        account_rects = []

        for i, name in enumerate(sessions):
            r = pygame.Rect((WIDTH-260)//2, start_y + i*60, 260, 50)
            account_rects.append((r, name))
            draw_button(r, name, r.collidepoint(mouse_pos))
            
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                # 1. check back button
                if pygame.Rect(10, 10, 80, 30).collidepoint(e.pos):
                    return
                
                # 2. check account list
                for rect, name in account_rects:
                    if rect.collidepoint(e.pos):
                        CURRENT_USER = name
                        data = load_session(name)
                        if data: 
                            diff = 6
                            if data['category'] != "WORDLE":
                                all_words = load_words()
                                if data['category'] in all_words: 
                                    diff = all_words[data['category']]['diff']
                            
                            run_game_wrapper(data['category'], data['target'], diff, data['guesses'])
                        return

def show_leaderboard():

    # displays the leaderboard with tabs for classic and time attack modes
    tab = "CLASSIC"
    scroll_y = 0  
    
    while True:
        SCREEN.fill(BG_COLOR)
        mse = pygame.mouse.get_pos()
        
        # 1. scrollable content area
        content_surface = pygame.Surface((WIDTH, 400)) 
        content_surface.fill(BG_COLOR)
        y_offset = 10 + scroll_y 
        
        # classic tab
        if tab == "CLASSIC":
            users = USERS_LIST.to_list()
            for u in users:
                if -30 < y_offset < 400:
                    row = f"{u['name']:<25} {u['avg_time']:.1f}s"
                    content_surface.blit(pygame.font.SysFont(FONT_NAME, 20).render(row, True, TEXT_COLOR), (50, y_offset))
                    
                    # history button
                    btn_rect = pygame.Rect(320, y_offset, 80, 25)
                    adj_mouse = (mse[0], mse[1] - 155)
                    btn_hover = btn_rect.collidepoint(adj_mouse)
                    
                    pygame.draw.rect(content_surface, BLACK, (btn_rect.x, btn_rect.y+2, btn_rect.w, btn_rect.h), border_radius=5)
                    pygame.draw.rect(content_surface, BUTTON_HOVER if btn_hover else ACCENT_COLOR, btn_rect, border_radius=5)
                    btn_txt = pygame.font.SysFont(FONT_NAME, 14, bold=True).render("VIEW", True, WHITE)
                    content_surface.blit(btn_txt, btn_txt.get_rect(center=btn_rect.center))
                    
                    if btn_hover and pygame.mouse.get_pressed()[0]:
                        history_data = {'name': u['name'], 'word': u.get('last_word', 'N/A'), 'guesses': u.get('last_guesses', '')}
                        show_match_history(history_data)
                y_offset += 35
            max_scroll = max(0, (len(users) * 35) - 350)

        # time attack tab (does not handle uniqueness checking here)
        else:
            from file_system import load_time_stats_list
            records = load_time_stats_list()
            for r in records:
                if -30 < y_offset < 400:
                    row = f"{r['name']:<25} {r['score']} Words          {r['dur']}s"
                    content_surface.blit(pygame.font.SysFont(FONT_NAME, 20).render(row, True, TEXT_COLOR), (50, y_offset))
                y_offset += 35
            max_scroll = max(0, (len(records) * 35) - 350)

        SCREEN.blit(content_surface, (0, 155))

        pygame.draw.rect(SCREEN, BG_COLOR, (0, 0, WIDTH, 155))
        pygame.draw.rect(SCREEN, BG_COLOR, (0, 550, WIDTH, 50))

        # draw title
        font_title = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        title_surf = font_title.render("LEADERBOARD", True, TEXT_COLOR)
        SCREEN.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 20))

        # draw back button
        draw_button(pygame.Rect(10, 10, 80, 30), "BACK")
        
        # draw tabs
        c_rect = pygame.Rect(WIDTH//2 - 110, 70, 100, 30)
        t_rect = pygame.Rect(WIDTH//2 + 10, 70, 100, 30)
        c_col = GREEN if tab == "CLASSIC" else ACCENT_COLOR
        t_col = YELLOW if tab == "TIME" else ACCENT_COLOR
        draw_button(c_rect, "CLASSIC", False, color=c_col)
        draw_button(t_rect, "TIME", False, color=t_col)
        
        # column headers
        font_bold = pygame.font.SysFont(FONT_NAME, 20, bold=True)
        if tab == "CLASSIC":
            SCREEN.blit(font_bold.render("NAME              AVG TIME", True, BLACK), (50, 120))
        else:
            SCREEN.blit(font_bold.render("PLAYER          SCORE          DUR", True, BLACK), (50, 120))
        pygame.draw.line(SCREEN, GRAY, (50, 150), (450, 150))

        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 4: scroll_y = min(0, scroll_y + 20)
                if e.button == 5: scroll_y = max(-max_scroll, scroll_y - 20)
                if pygame.Rect(10, 10, 80, 30).collidepoint(e.pos): return
                if c_rect.collidepoint(e.pos): tab, scroll_y = "CLASSIC", 0
                if t_rect.collidepoint(e.pos): tab, scroll_y = "TIME", 0

def main_menu():
    # main menu display and navigation
    global CURRENT_USER

    while True:
        SCREEN.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        
        # check active sessions
        active_sessions = get_session_users()
        sessions_available = len(active_sessions) > 0 
        
        font = pygame.font.SysFont(FONT_NAME, 40, bold=True)
        title = font.render("Khoa's Wordle", True, TEXT_COLOR)
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        options = ["NEW GAME", "RESUME", "LEADERBOARD", "EXIT"]
        rects = []
        for i, opt in enumerate(options):
            r = pygame.Rect((WIDTH-200)//2, 150 + i*70, 200, 50)
            rects.append(r)
            
            if opt == "RESUME":
                is_hover = r.collidepoint(mouse_pos) and sessions_available
                draw_button(r, opt, is_hover, disabled=not sessions_available)
            else:
                draw_button(r, opt, r.collidepoint(mouse_pos))
        
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if rects[0].collidepoint(e.pos):
                    new_game_flow()
                
                # only enter resume menu if sessions exist
                elif rects[1].collidepoint(e.pos) and sessions_available:
                    resume_menu()
                
                elif rects[2].collidepoint(e.pos):
                    show_leaderboard()
                
                elif rects[3].collidepoint(e.pos):
                    sys.exit()
if __name__ == "__main__":
    main_menu()