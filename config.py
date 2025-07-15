# config.py
import pygame

# --- CONSTANTES PARA RANKEDS ---
LP_WIN = 15
LP_LOSS = 10

RANKS = [
    {"name": "Bronce", "lp_required": 0, "color": (139, 69, 19)},
    {"name": "Plata", "lp_required": 100, "color": (192, 192, 192)},
    {"name": "Oro", "lp_required": 200, "color": (255, 215, 0)},
    {"name": "Platino", "lp_required": 300, "color": (229, 228, 226)},
    {"name": "Maestro", "lp_required": 500, "color": (186, 85, 211)}
]

# --- RUTAS DE ARCHIVOS ---
USERS_FILE = 'users.json'
CHARACTERS_FILE = 'characters.json'
MISSIONS_FILE = 'missions.json'
VALID_DOMAINS = ['@gmail.com', '@yahoo.cl', '@hotmail.com']
FONT_PATH = 'assets/fonts/turok.ttf'
MUSIC_PATH = 'assets/audio/music.mp3'
BG_IMG_PATH = 'assets/images/background/background.jpg'
VICTORY_IMG_PATH = 'assets/images/icons/victory.png'
DEFEAT_IMG_PATH = 'assets/images/icons/defeat.png'

# --- MAPAS (ACTUALIZADO) ---
MAPS = {
    'Night': {
        'background': 'assets/images/background/map2.png',
        'thumbnail': 'assets/images/background/map_thumbnails/map2.png'
    },
    'Desert': {
        'background': 'assets/images/background/background.jpg',
        'thumbnail': 'assets/images/background/map_thumbnails/background.jpg'
    },
    'Tomato Temple': {
        'background': 'assets/images/background/map4.gif',
        'thumbnail': 'assets/images/background/map_thumbnails/map4.gif'
    },
    'Greece': {
        'background': 'assets/images/background/map5.gif',
        'thumbnail': 'assets/images/background/map_thumbnails/map5.gif'
    },
    'Shelter': {
        'background': 'assets/images/background/map6.gif',
        'thumbnail': 'assets/images/background/map_thumbnails/map6.gif'
    },
    'Apocalypsis': {
        'background': 'assets/images/background/map3.gif',
        'thumbnail': 'assets/images/background/map_thumbnails/map3.gif'
    },
    'Train': {
        'background': 'assets/images/background/map7.gif',
        'thumbnail': 'assets/images/background/map_thumbnails/map7.gif'
    }
}

# --- CONSTANTES DEL JUEGO ---
FPS = 60
RESOLUTIONS = [(800, 600), (1024, 768), (1280, 720), (1920, 1080)]
ROUND_COOLDOWN = 2000
DAILY_MISSIONS_COUNT = 3

# --- COLORES ---
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
HIGHLIGHT = (50, 150, 255)

# --- TEXTOS DE MENÚS ---
MENU_ITEMS = ['Jugar', 'Clasificatoria', 'Misiones Diarias', 'Clasificación', 'Personaje', 'Administrar Personajes', 'Gestionar Usuarios', 'Gestionar Misiones', 'Ajustes', 'Salir']
AJUSTES_ITEMS = ['Ver Perfil', 'Resolución', 'Volumen Música', 'Volumen FX', 'Eliminar Cuenta', 'Volver']
ROUND_OPTIONS = ['Reintentar', 'Volver al menú']
CRUD_MENU_ITEMS = ['Añadir Personaje', 'Ver Datos', 'Editar Estadísticas', 'Gestionar Movimientos', 'Eliminar Personaje', 'Volver']
USER_CRUD_ITEMS = ['Editar Perfil', 'Resetear Perfil', 'Editar Ranked', 'Resetear Ranked', 'Volver']
MISSION_CRUD_ITEMS = ['Añadir Misión', 'Editar Misión', 'Eliminar Misión', 'Volver']
MOVE_CRUD_OPTIONS = ['Añadir', 'Editar Tecla', 'Eliminar', 'Volver']
FORBIDDEN_KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]