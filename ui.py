# ui.py
import pygame
import config

def draw_panel(surface, rect):
    panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (*config.BLACK, 170), panel_surface.get_rect(), border_radius=15)
    surface.blit(panel_surface, rect.topleft)

def draw_text(surface, text, font, color, x, y):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def draw_bg(surface, bg_image):
    scaled_bg = pygame.transform.scale(bg_image, surface.get_size())
    surface.blit(scaled_bg, (0, 0))

def draw_health_bar(surface, health, x, y):
    ratio = health / 100
    pygame.draw.rect(surface, config.WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(surface, config.RED, (x, y, 400, 30))
    pygame.draw.rect(surface, config.YELLOW, (x, y, 400 * ratio, 30))

def draw_menu(surface, font, items, selected_idx):
    surface.fill(config.BLACK)
    title = font.render('DARKHI GAME', True, config.WHITE)
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 100))
    for i, item in enumerate(items):
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY
        txt = font.render(item, True, color)
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, 220 + i * 80))

def draw_options(surface, font, items, selected_idx, values):
    surface.fill(config.BLACK)
    title = font.render('Configuración', True, config.WHITE)
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 100))
    for i, item in enumerate(items):
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY
        value = values.get(item, '')
        text_to_render = f"{item}: {value}" if value else item
        txt = font.render(text_to_render, True, color)
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, 200 + i * 80))

def draw_character_select(surface, bg_image, font, title_font, items, selected_idx, preview_fighter):
    draw_bg(surface, bg_image)
    panel_rect = pygame.Rect(50, 40, surface.get_width() - 100, surface.get_height() - 80)
    draw_panel(surface, panel_rect)

    title_text = title_font.render('Selecciona tu Personaje', True, config.WHITE)
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 70))

    list_x = panel_rect.left + 50
    for i, char_name in enumerate(items):
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY
        txt = font.render(char_name, True, color)
        surface.blit(txt, (list_x, 180 + i * 70))

    if preview_fighter:
        preview_fighter.draw(surface)

def draw_round_over_menu(surface, font, items, selected_idx, victory_img):
    surface.blit(victory_img, (surface.get_width() / 2 - victory_img.get_width() // 2, 150))
    base_y = 150 + victory_img.get_height() + 40
    for i, item in enumerate(items):
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY
        txt = font.render(item, True, color)
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, base_y + i * 60))

def draw_character_crud(surface, bg_image, font, title_font, characters, options, char_idx, opt_idx):
    draw_bg(surface, bg_image)
    panel_rect = pygame.Rect(50, 40, surface.get_width() - 100, surface.get_height() - 80)
    draw_panel(surface, panel_rect)
    
    title_text = title_font.render("Administrar Personajes", True, config.WHITE)
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 70))
    col_1_x = panel_rect.left + 50
    col_2_x = panel_rect.centerx + 50
    draw_text(surface, "Personajes", font, config.WHITE, col_1_x, 150)
    for i, name in enumerate(characters):
        color = config.HIGHLIGHT if i == char_idx else config.GRAY
        draw_text(surface, name, font, color, col_1_x, 210 + i * 60)
    draw_text(surface, "Opciones", font, config.WHITE, col_2_x, 150)
    for i, option in enumerate(options):
        color = config.HIGHLIGHT if i == opt_idx else config.GRAY
        draw_text(surface, option, font, color, col_2_x, 210 + i * 60)

def draw_move_crud(surface, bg_image, font, title_font, char_name, moves, move_idx, is_listening):
    draw_bg(surface, bg_image)
    panel_rect = pygame.Rect(50, 40, surface.get_width() - 100, surface.get_height() - 80)
    draw_panel(surface, panel_rect)
    title_text = title_font.render(f"Movimientos de {char_name}", True, config.WHITE)
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 70))
    col_x = panel_rect.centerx - 200
    draw_text(surface, "Selecciona un movimiento para cambiar su tecla:", font, config.WHITE, col_x, 150)
    for i, (key, move_data) in enumerate(moves.items()):
        color = config.HIGHLIGHT if i == move_idx else config.GRAY
        display_key = key.split('_')[1].upper() if '_' in key else key.upper()
        move_text_str = f"Tecla [{display_key}] - {move_data['name']}"
        draw_text(surface, move_text_str, font, color, col_x, 210 + i * 60)
    if is_listening:
        prompt_text = title_font.render("Presiona una nueva tecla...", True, config.YELLOW)
        prompt_x = surface.get_width() // 2 - prompt_text.get_width() // 2
        prompt_y = panel_rect.bottom - prompt_text.get_height() - 20
        surface.blit(prompt_text, (prompt_x, prompt_y))
    back_text = font.render("Presiona ESC para Volver", True, config.GRAY)
    surface.blit(back_text, (panel_rect.left + 20, panel_rect.bottom - back_text.get_height() - 20))

def draw_battle_history(surface, bg_image, font, title_font, history, selected_idx):
    """Dibuja la pantalla del historial de batallas."""
    draw_bg(surface, bg_image)
    panel_rect = pygame.Rect(50, 40, surface.get_width() - 100, surface.get_height() - 80)
    draw_panel(surface, panel_rect)
    
    title_text = title_font.render("Historial de Batallas", True, config.WHITE)
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 70))

    if not history:
        no_history_text = font.render("No hay batallas guardadas.", True, config.GRAY)
        surface.blit(no_history_text, (surface.get_width() // 2 - no_history_text.get_width() // 2, 250))
        return

    for i, battle in enumerate(history):
        y_pos = 150 + i * 50
        if y_pos > panel_rect.bottom - 50:
            break

        color = config.HIGHLIGHT if i == selected_idx else config.GRAY
        
        winner = battle['winner']
        p1 = battle['p1_char']
        p2 = battle['p2_char']
        timestamp = battle['timestamp']

        battle_text_str = f"{timestamp} - {p1} vs {p2} - Ganador: {winner}"
        
        battle_text = font.render(battle_text_str, True, color)
        surface.blit(battle_text, (panel_rect.left + 30, y_pos))