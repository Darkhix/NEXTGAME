# ui.py
import pygame
import config

def draw_panel(surface, rect): #
    panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA) #
    pygame.draw.rect(panel_surface, (*config.BLACK, 170), panel_surface.get_rect(), border_radius=15) #
    surface.blit(panel_surface, rect.topleft) #

def draw_text(surface, text, font, color, x, y): #
    img = font.render(text, True, color) #
    surface.blit(img, (x, y)) #

def draw_bg(surface, bg_image): #
    scaled_bg = pygame.transform.scale(bg_image, surface.get_size()) #
    surface.blit(scaled_bg, (0, 0)) #

def draw_health_bar(surface, health, x, y): #
    ratio = health / 100 #
    pygame.draw.rect(surface, config.WHITE, (x - 2, y - 2, 404, 34)) #
    pygame.draw.rect(surface, config.RED, (x, y, 400, 30)) #
    pygame.draw.rect(surface, config.YELLOW, (x, y, 400 * ratio, 30)) #

def draw_menu(surface, font, items, selected_idx): #
    surface.fill(config.BLACK) #
    title = font.render('DARKHI GAME', True, config.WHITE)
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 100)) #
    for i, item in enumerate(items): #
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY #
        txt = font.render(item, True, color) #
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, 220 + i * 80)) #

def draw_options(surface, font, items, selected_idx, values): #
    surface.fill(config.BLACK) #
    title = font.render('Configuración', True, config.WHITE) #
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 100)) #
    for i, item in enumerate(items): #
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY #
        value = values.get(item, '') #
        text_to_render = f"{item}: {value}" if value else item #
        txt = font.render(text_to_render, True, color) #
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, 200 + i * 80)) #

def draw_character_select(surface, bg_image, font, title_font, character_names, selected_char_name, preview_fighter): #
    draw_bg(surface, bg_image) #
    panel_rect = pygame.Rect(surface.get_width() // 2 - 300, 50, 600, surface.get_height() - 100) #
    draw_panel(surface, panel_rect) #
    title_text = title_font.render("Seleccionar Personaje", True, config.WHITE) #
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 70)) #
    if character_names: #
        selected_idx = character_names.index(selected_char_name) #
        for i, name in enumerate(character_names): #
            color = config.HIGHLIGHT if i == selected_idx else config.GRAY #
            txt = font.render(name, True, color) #
            surface.blit(txt, (panel_rect.left + 30, 150 + i * 50)) #
        if preview_fighter: #
            preview_fighter.draw(surface) #
            draw_text(surface, f"Salud: {preview_fighter.base_health}", font, config.WHITE, panel_rect.left + 30, surface.get_height() - 150) #
            draw_text(surface, f"Daño: {preview_fighter.stats['damage']}", font, config.WHITE, panel_rect.left + 30, surface.get_height() - 120) #
            draw_text(surface, f"Velocidad: {preview_fighter.speed}", font, config.WHITE, panel_rect.left + 30, surface.get_height() - 90) #
    else: #
        no_chars_text = font.render("No hay personajes disponibles.", True, config.GRAY) #
        surface.blit(no_chars_text, (surface.get_width() // 2 - no_chars_text.get_width() // 2, 250)) #

def draw_admin_characters(surface, font, title_font, character_names, selected_char_idx, crud_options, selected_opt_idx): #
    surface.fill(config.BLACK) #
    panel_rect = pygame.Rect(surface.get_width() // 2 - 400, 50, 800, surface.get_height() - 100) #
    draw_panel(surface, panel_rect) #
    title_text = title_font.render("Administrar Personajes", True, config.WHITE) #
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 70)) #
    
    # Dibujar la lista de personajes
    if character_names: #
        for i, name in enumerate(character_names): #
            color = config.HIGHLIGHT if i == selected_char_idx else config.GRAY #
            txt = font.render(name, True, color) #
            surface.blit(txt, (panel_rect.left + 30, 150 + i * 50)) #
    else: #
        no_chars_text = font.render("No hay personajes para administrar.", True, config.GRAY) #
        surface.blit(no_chars_text, (panel_rect.left + 30, 150)) #

    # Dibujar las opciones CRUD
    crud_panel_rect = pygame.Rect(surface.get_width() // 2 - 150, surface.get_height() - 150, 300, 80) #
    draw_panel(surface, crud_panel_rect) #
    for i, option in enumerate(crud_options): #
        color = config.HIGHLIGHT if i == selected_opt_idx else config.GRAY #
        txt = font.render(option, True, color) #
        surface.blit(txt, (crud_panel_rect.left + 10 + i * 70, crud_panel_rect.top + 25)) #
    
def draw_battle_history(surface, font, title_font, history, selected_idx): #
    surface.fill(config.BLACK) #
    panel_rect = pygame.Rect(surface.get_width() // 2 - 450, 50, 900, surface.get_height() - 80) #
    draw_panel(surface, panel_rect) #
    title_text = title_font.render("Historial de Batallas", True, config.WHITE) #
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 70)) #
    if not history: #
        no_history_text = font.render("No hay batallas guardadas.", True, config.GRAY) #
        surface.blit(no_history_text, (surface.get_width() // 2 - no_history_text.get_width() // 2, 250)) #
    else:
        for i, battle in enumerate(history): #
            y_pos = 150 + i * 50 #
            if y_pos > panel_rect.bottom - 80: #
                break #
            color = config.HIGHLIGHT if i == selected_idx else config.GRAY #
            winner = battle['winner'] #
            p1 = battle['p1_char'] #
            p2 = battle['p2_char'] #
            timestamp = battle['timestamp'] #
            battle_text_str = f"{timestamp} - {p1} vs {p2} - Ganador: {winner}" #
            battle_text = font.render(battle_text_str, True, color) #
            surface.blit(battle_text, (panel_rect.left + 30, y_pos)) #

    controls_font = pygame.font.SysFont(None, 24)
    controls_text = controls_font.render("SHIFT + A: Añadir | SHIFT + E: Editar | DEL: Eliminar | SHIFT + D: Eliminar Todo", True, config.GRAY)
    surface.blit(controls_text, (panel_rect.left + 30, surface.get_height() - 50))