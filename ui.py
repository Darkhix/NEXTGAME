# ui.py
import pygame
import config

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
    title = font.render('Joseadores el juego', True, config.WHITE)
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

def draw_character_select(surface, font, items, selected_idx):
    surface.fill(config.BLACK)
    title = font.render('Selecciona tu personaje', True, config.WHITE)
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 100))
    for i, char_name in enumerate(items):
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY
        txt = font.render(char_name, True, color)
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, 220 + i * 80))

def draw_round_over_menu(surface, font, items, selected_idx, victory_img):
    surface.blit(victory_img, (surface.get_width() / 2 - victory_img.get_width() // 2, 150))
    base_y = 150 + victory_img.get_height() + 40
    for i, item in enumerate(items):
        color = config.HIGHLIGHT if i == selected_idx else config.GRAY
        txt = font.render(item, True, color)
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, base_y + i * 60))


# --- ESTA ES LA FUNCIÓN QUE FALTABA ---
def draw_character_crud(surface, bg_image, font, title_font, characters, options, char_idx, opt_idx):
    """Dibuja la pantalla de administración de personajes dentro de Pygame."""
    draw_bg(surface, bg_image)
    
    # Título
    title_text = title_font.render("Administrar Personajes", True, config.WHITE)
    surface.blit(title_text, (surface.get_width() // 2 - title_text.get_width() // 2, 50))

    # Columnas
    char_col_x = 150
    opt_col_x = surface.get_width() - 350
    
    # Lista de Personajes
    list_title = font.render("Personajes", True, config.WHITE)
    surface.blit(list_title, (char_col_x, 120))

    for i, name in enumerate(characters):
        color = config.HIGHLIGHT if i == char_idx else config.GRAY
        char_text = font.render(name, True, color)
        surface.blit(char_text, (char_col_x, 180 + i * 60))

    # Opciones
    options_title = font.render("Opciones", True, config.WHITE)
    surface.blit(options_title, (opt_col_x, 120))
    
    for i, option in enumerate(options):
        color = config.HIGHLIGHT if i == opt_idx else config.GRAY
        opt_text = font.render(option, True, color)
        surface.blit(opt_text, (opt_col_x, 180 + i * 60))

    # Indicador de selección de personaje
    if characters:
        marker_y = (180 + char_idx * 60) + (font.get_height() // 2)
        pygame.draw.polygon(surface, config.HIGHLIGHT, [
            (char_col_x - 30, marker_y - 10), 
            (char_col_x - 30, marker_y + 10), 
            (char_col_x - 15, marker_y)
        ])