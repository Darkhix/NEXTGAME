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