import pygame
import time
from settings import *
from logic import check_guess
from structures import Stack
from file_system import save_session, save_time_score, get_random_mix

def draw_text(screen, text, size, color, center_pos, bold=False):
    # handle text rendering
    font = pygame.font.SysFont(FONT_NAME, size, bold=bold)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=center_pos))

def draw_keyboard(screen, guesses, target_word):
    # draws togglable keyboard to keep track of letter statuses
    key_status = {}

    # determine status of each letter based on guesses
    for word in guesses:
        res = check_guess(word, target_word)
        for i, char in enumerate(word):
            status = res[i]
            if char not in key_status: 
                key_status[char] = status
            else: 
                key_status[char] = max(key_status[char], status)

    rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"] #qwerty keyboard
    key_w, key_h = 35, 45
    gap = 5
    total_h = (len(rows) * key_h) + ((len(rows)-1) * gap)
    start_y = HEIGHT - total_h - 20 

    # draw keyboard
    for r, row_keys in enumerate(rows):
        row_width = len(row_keys) * (key_w + gap) - gap
        start_x = (WIDTH - row_width) // 2
        for c, char in enumerate(row_keys):
            x = start_x + c * (key_w + gap)
            y = start_y + r * (key_h + gap)
            rect = pygame.Rect(x, y, key_w, key_h)
            status = key_status.get(char, -1)
            
            if status == 2: bg = GREEN
            elif status == 1: bg = YELLOW
            elif status == 0: bg = GRAY
            else: bg = ACCENT_COLOR
            
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            text_col = WHITE if status != -1 else TEXT_COLOR
            draw_text(screen, char, 20, text_col, rect.center, True)

def play_game(screen, category, target_word, max_guesses, user_name, initial_guesses=[], overwrite_func=None):

    # initialize game state
    clock = pygame.time.Clock()
    undo_stack = Stack()
    redo_stack = Stack()
    
    guesses = initial_guesses[:]
    current_guess = ""
    start_time = time.time()
    game_over = False
    result_data = None 
    message = "Undo: '[' | Redo: ']'"
    
    show_keyboard = True 

    # UI consts
    BOX_SIZE, GAP = 48, 5 
    
    running = True
    while running:
        screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        
        # header
        title_text = "WORDLE" if category == "WORDLE" else category
        draw_text(screen, title_text, 28, TEXT_COLOR, (WIDTH//2, 40), True)
        
        # keyboard toggle button
        toggle_btn_rect = pygame.Rect(WIDTH - 100, 15, 90, 28)
        btn_color = BUTTON_HOVER if toggle_btn_rect.collidepoint(mouse_pos) else ACCENT_COLOR
        pygame.draw.rect(screen, btn_color, toggle_btn_rect, border_radius=5)
        btn_text = "HIDE KEY" if show_keyboard else "SHOW KEY"
        draw_text(screen, btn_text, 14, WHITE, toggle_btn_rect.center, True)
        
        # win/lose message
        msg_color = GRAY
        if game_over:
            msg_color = GREEN if result_data['res'] == "WIN" else RED
        draw_text(screen, message, 16, msg_color, (WIDTH//2, 65))

        # guess grid
        grid_h = (BOX_SIZE * max_guesses) + (GAP * (max_guesses-1))
        start_y = 90
        
        for row in range(max_guesses):
            for col in range(5):
                total_grid_w = (BOX_SIZE * 5) + (GAP * 4)
                start_x = (WIDTH - total_grid_w) // 2
                
                x = start_x + col * (BOX_SIZE + GAP)
                y = start_y + row * (BOX_SIZE + GAP)
                rect = pygame.Rect(x, y, BOX_SIZE, BOX_SIZE)
                
                color, text_col, style, letter = ACCENT_COLOR, TEXT_COLOR, "border", ""

                # fill in past guesses
                if row < len(guesses):
                    past = guesses[row]
                    letter = past[col]
                    res = check_guess(past, target_word)
                    if res[col] == 2: color = GREEN
                    elif res[col] == 1: color = YELLOW
                    else: color = GRAY
                    style, text_col = "fill", WHITE
                
                # current guess
                elif row == len(guesses) and not game_over:
                    if col < len(current_guess):
                        letter, color = current_guess[col], (100, 100, 100)
                    if col == len(current_guess): color = BLACK 
                
                if style == "fill": 
                    pygame.draw.rect(screen, color, rect, border_radius=BORDER_RADIUS)
                else: 
                    pygame.draw.rect(screen, color, rect, width=2, border_radius=BORDER_RADIUS)
                
                if letter: 
                    draw_text(screen, letter, 26, text_col, rect.center, True)

        # keyboard
        if show_keyboard:
            draw_keyboard(screen, guesses, target_word)

        # guide the player to continue after game over
        if game_over:
            draw_text(screen, "Press ENTER to Continue", 16, TEXT_COLOR, (WIDTH//2, 418), True)
        pygame.display.flip()

        # event handling
        for event in pygame.event.get():

            # quit event
            if event.type == pygame.QUIT:

                # save session in "resume" if game not over
                if not game_over:
                    state = {"guesses":guesses, "target":target_word, "category":category}
                    success = save_session(user_name, state)
                    if not success and overwrite_func:
                        victim = overwrite_func()
                        if victim: 
                            save_session(user_name, state, overwrite_target=victim)

                return "QUIT"
            
            # toggle button event
            if event.type == pygame.MOUSEBUTTONDOWN:
                if toggle_btn_rect.collidepoint(event.pos):
                    show_keyboard = not show_keyboard
            
            # keypress events
            if event.type == pygame.KEYDOWN:

                # handle game over state
                if game_over:
                    if event.key in [pygame.K_RETURN, pygame.K_ESCAPE]: 
                        return result_data
                    
                # handle regular gameplay
                else:
                    if event.key == pygame.K_ESCAPE:
                        state = {"guesses":guesses, "target":target_word, "category":category}
                        success = save_session(user_name, state)

                        # overwrite account in "resume" if needed
                        if not success and overwrite_func:
                            victim = overwrite_func()
                            if victim: save_session(user_name, state, overwrite_target=victim)
                        return "MENU"
                    
                    # undo guesses
                    if event.key == pygame.K_LEFTBRACKET:
                        if not undo_stack.is_empty():
                            # save current state to Redo before undoing
                            redo_stack.push(guesses[:])
                            guesses = undo_stack.pop()
                            current_guess = ""
                            message = "Undone!"

                    # redo guesses
                    elif event.key == pygame.K_RIGHTBRACKET:
                        if not redo_stack.is_empty():
                            # save current state back to Undo before redoing
                            undo_stack.push(guesses[:])
                            guesses = redo_stack.pop()
                            current_guess = ""
                            message = "Redone!"

                    # backspace to delete last letter
                    elif event.key == pygame.K_BACKSPACE: 
                        current_guess = current_guess[:-1]

                    # enter key to submit guess
                    elif event.key == pygame.K_RETURN:
                        if len(current_guess) == 5:
                            undo_stack.push(guesses[:])
                            guesses.append(current_guess)
                            current_guess = ""
                            if guesses[-1] == target_word:
                                message = "VICTORY!"; game_over = True
                                # save 'target' and 'guesses' in result_data for leaderboard history view
                                result_data = {
                                    "res": "WIN", 
                                    "time": time.time()-start_time,
                                    "target": target_word,
                                    "guesses": guesses[:]
                                }
                            elif len(guesses) >= max_guesses:
                                message = f"GAME OVER! Word: {target_word}"; game_over = True
                                # save 'target' and 'guesses' in result_data for leaderboard history view
                                result_data = {
                                    "res": "LOSE", 
                                    "time": time.time()-start_time,
                                    "target": target_word,
                                    "guesses": guesses[:]
                                }
                        else: message = "Not enough letters"
                    elif len(current_guess) < 5 and event.unicode.isalpha():
                        current_guess += event.unicode.upper()

        clock.tick(FPS)

# time attack gamemode
def play_time_attack(screen, duration, user_name):

    # initialize game state
    clock = pygame.time.Clock()
    start_time = time.time()
    score = 0
    time_up = False
    
    animating = False
    anim_start_time = 0
    anim_duration = 0.5
    last_snapshot = None
    announcement = ""

    show_keyboard = True 

    # UI consts
    BOX_SIZE, GAP = 48, 5 

    # configure new round
    def new_round():
        c, w, d = get_random_mix()
        return c, w, d, [], ""

    # draw guess grid
    def draw_grid_at_y(surf, start_y, g_list, curr, target, max_g, cat_hint):
        draw_text(surf, f"Category: {cat_hint}", 14, GRAY, (WIDTH//2, start_y - 40))
        
        for row in range(max_g):
            for col in range(5):
                total_grid_w = (BOX_SIZE * 5) + (GAP * 4)
                start_x = (WIDTH - total_grid_w) // 2
                
                x = start_x + col * (BOX_SIZE + GAP)
                y = start_y + row * (BOX_SIZE + GAP) - 20
                rect = pygame.Rect(x, y, BOX_SIZE, BOX_SIZE)
                color, text_col, style, letter = ACCENT_COLOR, TEXT_COLOR, "border", ""

                # fill in past guesses
                if row < len(g_list): 
                    past = g_list[row]; letter = past[col]; res = check_guess(past, target)
                    if res[col] == 2: color = GREEN
                    elif res[col] == 1: color = YELLOW
                    else: color = GRAY
                    style, text_col = "fill", WHITE

                # current guess
                elif row == len(g_list): 
                    if col < len(curr): letter, color = curr[col], (100,100,100)
                    if col == len(curr): color = BLACK 
                
                if style == "fill": 
                    pygame.draw.rect(surf, color, rect, border_radius=BORDER_RADIUS)
                else: 
                    pygame.draw.rect(surf, color, rect, width=2, border_radius=BORDER_RADIUS)

                if letter: 
                    draw_text(surf, letter, 26, text_col, rect.center, True)

    category, target_word, max_guesses, guesses, current_guess = new_round()
    
    # main loop
    running = True
    while running:
        screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        # calculate remaining time
        current_time = time.time()
        elapsed = current_time - start_time
        remaining = max(0, duration - elapsed)
        
        if remaining == 0 and not time_up:
            time_up = True
            save_time_score(duration, score, user_name)

        # header (includes timer and score)
        pygame.draw.line(screen, ACCENT_COLOR, (0, 60), (WIDTH, 60), 2)
        timer_col = RED if remaining < 10 else GREEN
        draw_text(screen, f"{int(remaining)}s", 40, timer_col, (WIDTH - 60, 30), True)
        draw_text(screen, f"SCORE: {score}", 30, TEXT_COLOR, (100, 30), True)

        # keyboard toggle button
        toggle_btn_rect = pygame.Rect(WIDTH - 100, 70, 90, 28)
        btn_color = BUTTON_HOVER if toggle_btn_rect.collidepoint(mouse_pos) else ACCENT_COLOR
        if not time_up:
            pygame.draw.rect(screen, btn_color, toggle_btn_rect, border_radius=5)
            btn_text = "HIDE KEY" if show_keyboard else "SHOW KEY"
            draw_text(screen, btn_text, 12, WHITE, toggle_btn_rect.center, True)

        if not time_up:
            base_y = 125 

            if not animating:
                draw_grid_at_y(screen, base_y, guesses, current_guess, target_word, max_guesses, category)
                # only draw keyboard if toggled on
                if show_keyboard:
                    draw_keyboard(screen, guesses, target_word) 
            else:
                # animation logic
                progress = (current_time - anim_start_time) / anim_duration
                if progress >= 1: 
                    animating = False; announcement = ""
                else:
                    smooth = 1 - pow(1 - progress, 3)
                    offset = HEIGHT * smooth
                    o_gs, o_tar, o_cat, o_max = last_snapshot
                    draw_grid_at_y(screen, base_y - offset, o_gs, "", o_tar, o_max, o_cat)
                    draw_grid_at_y(screen, base_y + HEIGHT - offset, guesses, current_guess, target_word, max_guesses, category)

                    if announcement:
                        s = pygame.Surface((WIDTH, 80)); s.set_alpha(200); s.fill((0,0,0))
                        screen.blit(s, (0, HEIGHT//2 - 40))
                        draw_text(screen, announcement, 20, GREEN, (WIDTH//2, HEIGHT//2), True)
        else:
            draw_text(screen, "TIME'S UP!", 50, RED, (WIDTH//2, HEIGHT//2 - 50), True)
            draw_text(screen, f"Final Score: {score}", 30, TEXT_COLOR, (WIDTH//2, HEIGHT//2 + 10))
            draw_text(screen, "Press ESC to return", 20, GRAY, (WIDTH//2, HEIGHT - 100))

        pygame.display.flip()

        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                return "QUIT"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if toggle_btn_rect.collidepoint(event.pos) and not time_up:
                    show_keyboard = not show_keyboard

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    return
                
                if not time_up and not animating:
                    if event.key == pygame.K_BACKSPACE: 
                        current_guess = current_guess[:-1]

                    elif event.key == pygame.K_RETURN:
                        if len(current_guess) == 5:
                            guesses.append(current_guess)
                            if current_guess == target_word:
                                score += 1
                                last_snapshot = (guesses, target_word, category, max_guesses)
                                category, target_word, max_guesses, guesses, current_guess = new_round()
                                animating = True; anim_start_time = time.time(); announcement = f"CORRECT! Next: {category}"
                            elif len(guesses) >= max_guesses:
                                last_snapshot = (guesses, target_word, category, max_guesses)
                                category, target_word, max_guesses, guesses, current_guess = new_round()
                                animating = True; anim_start_time = time.time(); announcement = f"MISSED! Next: {category}"
                            current_guess = ""

                    elif len(current_guess) < 5 and event.unicode.isalpha(): current_guess += event.unicode.upper()
        
        clock.tick(FPS)