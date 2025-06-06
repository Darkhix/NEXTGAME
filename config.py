# config.py
import pygame

# --- Rutas de Archivos y Configuración ---
USERS_FILE = 'users.json'
CHARACTERS_FILE = 'characters.json'
VALID_DOMAINS = ['@gmail.com', '@yahoo.cl', '@hotmail.com']
FONT_PATH = 'assets/fonts/turok.ttf'
MUSIC_PATH = 'assets/audio/music.mp3'
BG_IMG_PATH = 'assets/images/background/background.jpg'
VICTORY_IMG_PATH = 'assets/images/icons/victory.png'

# --- Constantes del Juego ---
FPS = 60
RESOLUTIONS = [(800, 600), (1024, 768), (1280, 720), (1920, 1080)]
ROUND_COOLDOWN = 2000

# --- Colores ---
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
HIGHLIGHT = (50, 150, 255)

# --- Opciones de Menú ---
MENU_ITEMS = ['Jugar', 'Personaje', 'Administrar Personajes', 'Opciones', 'Salir']
OPTIONS_ITEMS = ['Resolución', 'Volumen Música', 'Volumen FX', 'Eliminar Cuenta', 'Volver']
ROUND_OPTIONS = ['Reintentar', 'Volver al menú']
CRUD_MENU_ITEMS = ['Añadir', 'Editar', 'Eliminar', 'Volver'] # <-- ESTA ES LA LÍNEA QUE FALTABA