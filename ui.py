# ui.py
import pygame
import config

def draw_text(surface, text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    surface.blit(img, (x, y))

def draw_bg(surface, bg_image):
    scaled_bg = pygame.transform.scale(bg_image, (surface.get_width(), surface.get_height()))
    surface.blit(scaled_bg, (0, 0))

def draw_health_bar(surface, health, x, y):
    ratio = health / 100
    pygame.draw.rect(surface, config.WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(surface, config.RED, (x, y, 400, 30))
    pygame.draw.rect(surface, config.YELLOW, (x, y, 400 * ratio, 30))

def draw_menu(surface, font, menu_items, selected_idx):
    surface.fill((30, 30, 30))
    draw_text(surface, "DARKHI GAME", font, config.WHITE, surface.get_width() / 2 - 150, 100)
    for i, item in enumerate(menu_items):
        color = config.HIGHLIGHT if i == selected_idx else config.WHITE
        draw_text(surface, item, font, color, surface.get_width() / 2 - 100, 200 + i * 50)

def draw_ajustes(surface, font, option_items, selected_idx, values):
    surface.fill((30, 30, 30))
    draw_text(surface, "Ajustes", font, config.WHITE, 100, 40)
    for i, item in enumerate(option_items):
        color = config.HIGHLIGHT if i == selected_idx else config.WHITE
        text = f"{item}: {values.get(item, '')}" if item in values else item
        draw_text(surface, text, font, color, 100, 100 + i * 60)

def draw_profile_screen(surface, title_font, menu_font, username, stats, play_time_str, char_image):
    draw_text(surface, f"Perfil de {username}", title_font, config.WHITE, 50, 40)
    if char_image:
        char_image_scaled = pygame.transform.scale(char_image, (char_image.get_width() * 1.5, char_image.get_height() * 1.5))
        char_rect = char_image_scaled.get_rect(center=(surface.get_width() * 0.75, surface.get_height() / 2))
        surface.blit(char_image_scaled, char_rect)
        pygame.draw.rect(surface, config.HIGHLIGHT, char_rect.inflate(10, 10), 3)

    y_pos = 150
    stats_to_draw = {
        "Horas Jugadas": play_time_str,
        "Partidas Totales": stats.get('matches_played', 0),
        "Victorias": stats.get('matches_won', 0),
        "Derrotas": stats.get('matches_lost', 0)
    }
    for label, value in stats_to_draw.items():
        draw_text(surface, f"{label}:", menu_font, config.WHITE, 60, y_pos)
        draw_text(surface, str(value), menu_font, config.YELLOW, 350, y_pos)
        y_pos += 60
    draw_text(surface, "Presiona ESC o ENTER para volver", pygame.font.SysFont(None, 36), config.GRAY, 50, surface.get_height() - 80)

def draw_daily_missions(surface, bg_image, font, title_font, missions_with_details, selected_idx, user_currency):
    draw_bg(surface, bg_image)
    draw_text(surface, "Misiones Diarias", title_font, config.WHITE, 50, 20)
    currency_text = f"Moneda: {user_currency}"
    draw_text(surface, currency_text, font, config.YELLOW, surface.get_width() - 300, 30)
    y_pos = 120
    for i, data in enumerate(missions_with_details):
        mission_info = data['info']; mission_progress = data['progress']
        base_color = config.GRAY if mission_progress['claimed'] else config.YELLOW if mission_progress['completed'] else config.WHITE
        if i == selected_idx:
            pygame.draw.rect(surface, config.HIGHLIGHT, (40, y_pos - 10, surface.get_width() - 80, 80), 3, border_radius=5)
        description = f"{i+1}. {mission_info['description']}"; reward_text = f"Recompensa: {mission_info['reward']}"
        draw_text(surface, description, font, base_color, 60, y_pos)
        draw_text(surface, reward_text, font, config.YELLOW, surface.get_width() - 400, y_pos)
        progress_text = f"{mission_progress['progress']} / {mission_info['target']}"
        draw_text(surface, progress_text, font, base_color, 60, y_pos + 35)
        status_text, status_color = ("", config.WHITE)
        if mission_progress['claimed']: status_text, status_color = "RECLAMADO", config.GRAY
        elif mission_progress['completed']: status_text, status_color = "¡COMPLETADO! (Presiona ENTER)", (0, 255, 0)
        draw_text(surface, status_text, font, status_color, 300, y_pos + 35)
        y_pos += 100

def draw_round_over_menu(surface, font, round_options, selected_idx, image_to_show, lp_change=0):
    scaled_image = pygame.transform.scale(image_to_show, (300, 150))
    surface.blit(scaled_image, (surface.get_width() / 2 - 150, 100))
    if lp_change != 0:
        sign = "+" if lp_change > 0 else ""; color = (0, 255, 0) if lp_change > 0 else config.RED
        lp_text = f"{sign}{lp_change} LP"
        draw_text(surface, lp_text, font, color, surface.get_width() / 2 - 50, 260)
    for i, item in enumerate(round_options):
        color = config.HIGHLIGHT if i == selected_idx else config.WHITE
        draw_text(surface, item, font, color, surface.get_width() / 2 - 100, 320 + i * 60)

def draw_leaderboard(surface, title_font, menu_font, players):
    surface.fill((20, 20, 40))
    draw_text(surface, "Tabla de Clasificación", title_font, config.WHITE, 50, 40)
    header_font = pygame.font.SysFont(None, 42, bold=True)
    draw_text(surface, "Rango", header_font, config.YELLOW, 50, 120)
    draw_text(surface, "Jugador", header_font, config.YELLOW, 250, 120)
    draw_text(surface, "Puntos (LP)", header_font, config.YELLOW, 550, 120)
    y_pos = 170
    for i, player in enumerate(players[:10]):
        rank_color = next((r['color'] for r in config.RANKS if r['name'] == player['rank']), config.WHITE)
        draw_text(surface, player['rank'], menu_font, rank_color, 50, y_pos)
        draw_text(surface, player['name'], menu_font, config.WHITE, 250, y_pos)
        draw_text(surface, str(player['lp']), menu_font, config.WHITE, 550, y_pos)
        y_pos += 50
    draw_text(surface, "Presiona ESC o ENTER para volver", pygame.font.SysFont(None, 36), config.GRAY, 50, surface.get_height() - 80)

def draw_map_select(surface, title_font, menu_font, maps, thumbnails, selected_idx):
    draw_bg(surface, thumbnails[list(maps.keys())[selected_idx]])
    title_surf = title_font.render("Selecciona un Mapa", True, config.WHITE)
    pygame.draw.rect(surface, config.BLACK, (0, 40, surface.get_width(), 100), 0)
    surface.blit(title_surf, (surface.get_width()/2 - title_surf.get_width()/2, 60))
    map_keys = list(maps.keys())
    for i, map_name in enumerate(map_keys):
        color = config.HIGHLIGHT if i == selected_idx else config.WHITE
        x_pos = (surface.get_width() // (len(map_keys) + 1)) * (i + 1)
        y_pos = surface.get_height() - 100
        thumbnail_img = pygame.transform.scale(thumbnails[map_name], (220, 165))
        rect = thumbnail_img.get_rect(center=(x_pos, y_pos - 120))
        surface.blit(thumbnail_img, rect.topleft)
        if i == selected_idx:
            pygame.draw.rect(surface, config.HIGHLIGHT, rect.inflate(10, 10), 5)
        text_surf = menu_font.render(map_name, True, color)
        surface.blit(text_surf, (x_pos - text_surf.get_width() // 2, y_pos))

def draw_character_crud(surface, bg_image, menu_font, title_font, char_names, crud_items, char_idx, opt_idx):
    draw_bg(surface, bg_image)
    draw_text(surface, "Administrar Personajes", title_font, config.WHITE, 50, 50)
    for i, name in enumerate(char_names):
        color = config.HIGHLIGHT if i == char_idx else config.WHITE
        draw_text(surface, name, menu_font, color, 100, 150 + i * 50)
    for i, opt in enumerate(crud_items):
        color = config.HIGHLIGHT if i == opt_idx else config.WHITE
        draw_text(surface, opt, menu_font, color, 450 + (i % 2) * 300, 150 + (i // 2) * 80)

def draw_move_crud(surface, bg_image, menu_font, title_font, char_name, moves, selected_idx, is_listening):
    draw_bg(surface, bg_image)
    draw_text(surface, f"Movimientos de {char_name}", title_font, config.WHITE, 50, 50)
    if is_listening:
        draw_text(surface, "Presiona una nueva tecla...", menu_font, config.YELLOW, 100, 150)
    else:
        for i, (key, move_data) in enumerate(moves.items()):
            color = config.HIGHLIGHT if i == selected_idx else config.WHITE
            text = f"{key.split('_')[-1]} - {move_data['name']}"
            draw_text(surface, text, menu_font, color, 100, 150 + i * 50)

def draw_character_select(surface, bg_image, menu_font, title_font, char_names, selected_idx, preview_fighter):
    draw_bg(surface, bg_image)
    draw_text(surface, "Elige tu Personaje", title_font, config.WHITE, 50, 50)
    for i, name in enumerate(char_names):
        color = config.HIGHLIGHT if i == selected_idx else config.WHITE
        draw_text(surface, name, menu_font, color, 100, 150 + i * 70)
    if preview_fighter:
        preview_fighter.draw(surface)

def draw_battle_history(surface, bg_image, font, title_font, history, selected_idx):
    draw_bg(surface, bg_image)
    draw_text(surface, "Historial de Batallas", title_font, config.WHITE, 50, 20)
    instructions = "A: Añadir | E: Editar | SUPR: Borrar | SHIFT+D: Borrar todo"
    draw_text(surface, instructions, font, config.YELLOW, 50, 80)
    for i, record in enumerate(history):
        if i > 15: break 
        color = config.HIGHLIGHT if i == selected_idx else config.WHITE
        text = f"{record['timestamp']} - {record['p1_char']} vs {record['p2_char']} - Ganador: {record['winner']}"
        draw_text(surface, text, font, color, 50, 140 + i * 35)

def draw_user_crud_screen(surface, bg_image, menu_font, title_font, user_names, user_idx, opt_idx):
    draw_bg(surface, bg_image)
    draw_text(surface, "Gestionar Usuarios", title_font, config.WHITE, 50, 50)
    draw_text(surface, "Usuarios:", menu_font, config.YELLOW, 100, 120)
    for i, name in enumerate(user_names):
        color = config.HIGHLIGHT if i == user_idx else config.WHITE
        draw_text(surface, name, menu_font, color, 100, 180 + i * 50)
    draw_text(surface, "Acciones:", menu_font, config.YELLOW, 550, 120)
    for i, opt in enumerate(config.USER_CRUD_ITEMS):
        color = config.HIGHLIGHT if i == opt_idx else config.WHITE
        draw_text(surface, opt, menu_font, color, 550, 180 + i * 60)

def draw_mission_crud_screen(surface, bg_image, menu_font, title_font, missions, mission_idx, opt_idx):
    draw_bg(surface, bg_image)
    draw_text(surface, "Gestionar Misiones", title_font, config.WHITE, 50, 50)
    draw_text(surface, "Misiones:", menu_font, config.YELLOW, 100, 120)
    y_pos = 180
    mission_items = list(missions.items())
    for i, (m_id, m_data) in enumerate(mission_items):
        color = config.HIGHLIGHT if i == mission_idx else config.WHITE
        text = f"{m_id}: {m_data['description'][:40]}"
        if len(m_data['description']) > 40: text += "..."
        draw_text(surface, text, pygame.font.SysFont(None, 36), color, 100, y_pos)
        y_pos += 40
    draw_text(surface, "Acciones:", menu_font, config.YELLOW, 600, 120)
    for i, opt in enumerate(config.MISSION_CRUD_ITEMS):
        color = config.HIGHLIGHT if i == opt_idx else config.WHITE
        draw_text(surface, opt, menu_font, color, 600, 180 + i * 60)