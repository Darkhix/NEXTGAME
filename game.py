# game.py
import pygame
import sys
import os
import json
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from datetime import datetime
import config
import ui
import auth
from auth import load_users, save_users, delete_user
from fighter import Fighter
from pygame import mixer

# ==============================================================================
# INICIO DEL CÓDIGO DE GESTIÓN
# ==============================================================================

def load_json_data(file_path, default_data):
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return default_data

def save_json_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)

def load_characters(): return load_json_data(config.CHARACTERS_FILE, {})
def save_characters(characters): save_json_data(config.CHARACTERS_FILE, characters)

def _create_spritesheet_from_files(base_path, scale, offset):
    if not os.path.isdir(base_path):
        messagebox.showerror("Error", f"La carpeta base no existe:\n{base_path}"); return None
    all_animations, max_frame_w, max_frame_h, max_frames_per_row, animation_steps = [], 0, 0, 0, []
    animation_folder_names = ['Idle', 'Run', 'Jump', 'Attack1', 'Attack2', 'Hit', 'Death']
    for folder_name in animation_folder_names:
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path): continue
        images = sorted([img for img in os.listdir(folder_path) if img.endswith('.png')])
        animation = []
        for img_name in images:
            img_path = os.path.join(folder_path, img_name)
            img = pygame.image.load(img_path).convert_alpha()
            animation.append(img)
            max_frame_w = max(max_frame_w, img.get_width())
            max_frame_h = max(max_frame_h, img.get_height())
        all_animations.append(animation)
        animation_steps.append(len(images))
        max_frames_per_row = max(max_frames_per_row, len(images))
    if not all_animations: return None
    sprite_sheet_width = max_frames_per_row * max_frame_w
    sprite_sheet_height = len(animation_folder_names) * max_frame_h
    sprite_sheet = pygame.Surface((sprite_sheet_width, sprite_sheet_height), pygame.SRCALPHA)
    for row_idx, animation in enumerate(all_animations):
        for col_idx, frame in enumerate(animation):
            sprite_sheet.blit(frame, (col_idx * max_frame_w, row_idx * max_frame_h))
    return sprite_sheet, [max_frame_w, max_frame_h, scale, offset], animation_steps

# ==============================================================================
# FIN DEL CÓDIGO DE GESTIÓN
# ==============================================================================

class Game:
    def __init__(self, username, user_data):
        pygame.init()
        mixer.init()
        self.username = username
        self.user_data = user_data
        self.screen_width, self.screen_height = config.RESOLUTIONS[0]
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("DARKHI GAME")
        self.clock = pygame.time.Clock()
        self.bg_image = pygame.image.load(config.BG_IMG_PATH).convert_alpha()
        self.victory_image = pygame.image.load(config.VICTORY_IMG_PATH).convert_alpha()
        
        # Fuentes
        self.font = pygame.font.Font(config.FONT_PATH, 40)
        self.score_font = pygame.font.Font(config.FONT_PATH, 30)
        self.count_font = pygame.font.Font(config.FONT_PATH, 80)
        self.small_font = pygame.font.Font(config.FONT_PATH, 25)
        self.char_info_font = pygame.font.Font(config.FONT_PATH, 20)

        # Música y sonido
        mixer.music.load(config.MUSIC_PATH)
        mixer.music.set_volume(0.5)
        mixer.music.play(-1)
        self.sword_fx = pygame.mixer.Sound("assets/audio/sword.wav")
        self.sword_fx.set_volume(0.5)

        # Variables del juego
        self.intro_count = 3
        self.last_count_update = pygame.time.get_ticks()
        self.round_over = False
        self.round_over_cooldown = config.ROUND_COOLDOWN
        self.score = [0, 0]
        self.total_rounds = 3
        self.current_round = 0
        self.round_winner = None
        self.game_running = True

        # Inicialización de estados y índices
        self.game_state = 'menu' # Estados: 'menu', 'playing', 'character_select', 'battle_history', 'crud_menu', 'options', 'move_crud'
        self.menu_selected_idx = 0
        self.options_selected_idx = 0
        self.crud_selected_idx = 0
        self.move_crud_selected_idx = 0
        self.history_selected_idx = 0
        self.char_select_idx = 0
        self.crud_char_idx = 0 # Índice del personaje seleccionado en CRUD
        self.is_listening_for_key = False
        self.key_to_configure = None
        self.move_crud_char_name = None
        self.move_crud_idx = 0
        self.input_box_active = False
        self.current_input_text = ""
        self.input_field_type = None # 'character_name', 'move_name', 'damage', 'cooldown', 'health', 'speed'
        self.input_field_key = None # Usado para saber qué clave del diccionario actualizar
        self.current_selected_char_name = None
        self.preview_fighter = None
        self.p2_char_name = None # Inicialización del nombre del personaje del jugador 2
        self.round_options_idx = 0 # Índice para las opciones de reintentar/volver al menú

        self.characters = load_characters()
        self.characters_names = list(self.characters.keys())
        
        # Carga del historial de batallas
        self.battle_history = load_json_data('battle_history.json', [])
        
        # Volúmenes
        self.music_volume = mixer.music.get_volume() * 100
        self.fx_volume = self.sword_fx.get_volume() * 100
        
        # Inicialización de fighters
        self.fighter_1 = None
        self.fighter_2 = None

    def update_volumes(self):
        mixer.music.set_volume(self.music_volume / 100)
        self.sword_fx.set_volume(self.fx_volume / 100)

    def save_battle_history(self):
        save_json_data('battle_history.json', self.battle_history)

    def create_fighters(self):
        if self.current_selected_char_name not in self.characters or self.p2_char_name not in self.characters:
            print("Error: Personaje no encontrado para uno de los jugadores.")
            self.game_state = 'menu'
            return

        p1_char_data = self.characters[self.current_selected_char_name]
        p2_char_data = self.characters[self.p2_char_name]

        fighter_1_animation_list = self.load_animations(p1_char_data['sprite_sheet_path'], p1_char_data['animation_steps'])
        fighter_2_animation_list = self.load_animations(p2_char_data['sprite_sheet_path'], p2_char_data['animation_steps'])

        self.fighter_1 = Fighter(
            1, 200, 310, False, p1_char_data['data'], fighter_1_animation_list,
            pygame.mixer.Sound(p1_char_data['sound_path']), p1_char_data['stats'],
            p1_char_data['special_moves'], username=self.username
        )
        self.fighter_2 = Fighter(
            2, 700, 310, True, p2_char_data['data'], fighter_2_animation_list,
            pygame.mixer.Sound(p2_char_data['sound_path']), p2_char_data['stats'],
            p2_char_data['special_moves'], ai=True, username=self.p2_char_name
        )
        self.intro_count = 3
        self.last_count_update = pygame.time.get_ticks()
        self.round_over = False
        self.round_over_cooldown = config.ROUND_COOLDOWN
        self.game_state = 'playing'
        self.current_round = 0
        self.score = [0, 0]

    def load_animations(self, sprite_sheet_path, animation_steps):
        sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        animation_list = []
        for y, num_frames in enumerate(animation_steps):
            temp_list = []
            for x in range(num_frames):
                temp_list.append(sprite_sheet.subsurface(x * self.characters[self.current_selected_char_name]['data'][0], y * self.characters[self.current_selected_char_name]['data'][1], self.characters[self.current_selected_char_name]['data'][0], self.characters[self.current_selected_char_name]['data'][1]))
            animation_list.append(temp_list)
        return animation_list

    def handle_menu_keys(self, key):
        if key == pygame.K_UP: self.menu_selected_idx = (self.menu_selected_idx - 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_DOWN: self.menu_selected_idx = (self.menu_selected_idx + 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_RETURN:
            if self.menu_selected_idx == 0: self.game_state = 'character_select'
            elif self.menu_selected_idx == 1: # Personaje
                self.current_selected_char_name = self.user_data.get('character_class')
                if self.current_selected_char_name:
                    self.game_state = 'preview_character'
                else:
                    messagebox.showerror("Error", "No tienes un personaje asignado. Por favor, selecciona uno primero.", parent=self.screen)
            elif self.menu_selected_idx == 2: self.game_state = 'battle_history'
            elif self.menu_selected_idx == 3: self.game_state = 'crud_menu'; self.crud_selected_idx = 0
            elif self.menu_selected_idx == 4: self.game_state = 'options'; self.options_selected_idx = 0
            elif self.menu_selected_idx == 5: self.game_running = False

    def handle_character_select_keys(self, key):
        if key == pygame.K_LEFT: self.char_select_idx = (self.char_select_idx - 1) % len(self.characters_names)
        elif key == pygame.K_RIGHT: self.char_select_idx = (self.char_select_idx + 1) % len(self.characters_names)
        elif key == pygame.K_RETURN:
            selected_char = self.characters_names[self.char_select_idx]
            if not self.current_selected_char_name:
                self.current_selected_char_name = selected_char
                self.user_data['character_class'] = selected_char
                auth.save_users(auth.load_users().update({self.username: self.user_data}) or auth.load_users())
                messagebox.showinfo("Personaje Seleccionado", f"Has seleccionado a {selected_char} como tu personaje.", parent=self.screen)
            else:
                self.p2_char_name = selected_char
                self.create_fighters()
        elif key == pygame.K_ESCAPE: self.game_state = 'menu'

    def handle_game_keys(self, key):
        if self.round_over:
            if key == pygame.K_UP: self.round_options_idx = (self.round_options_idx - 1) % len(config.ROUND_OPTIONS)
            elif key == pygame.K_DOWN: self.round_options_idx = (self.round_options_idx + 1) % len(config.ROUND_OPTIONS)
            elif key == pygame.K_RETURN:
                if self.round_options_idx == 0: # Reintentar
                    self.create_fighters()
                elif self.round_options_idx == 1: # Volver al menú
                    self.game_state = 'menu'
                    self.round_over = False
                    self.score = [0, 0]
                    self.current_round = 0

    def handle_options_keys(self, key):
        if self.input_box_active:
            if key == pygame.K_RETURN:
                if self.input_field_type == 'delete_account':
                    if self.current_input_text == self.username:
                        if auth.delete_user(self.username):
                            messagebox.showinfo("Cuenta Eliminada", "Tu cuenta ha sido eliminada.", parent=self.screen)
                            self.game_running = False
                        else:
                            messagebox.showerror("Error", "No se pudo eliminar la cuenta.", parent=self.screen)
                    else:
                        messagebox.showerror("Error", "El nombre de usuario no coincide.", parent=self.screen)
                self.input_box_active = False
                self.current_input_text = ""
                self.input_field_type = None
            elif key == pygame.K_BACKSPACE: self.current_input_text = self.current_input_text[:-1]
            else: self.current_input_text += key.unicode if key.unicode else ''
        else:
            if key == pygame.K_UP: self.options_selected_idx = (self.options_selected_idx - 1) % len(config.OPTIONS_ITEMS)
            elif key == pygame.K_DOWN: self.options_selected_idx = (self.options_selected_idx + 1) % len(config.OPTIONS_ITEMS)
            elif key == pygame.K_LEFT and self.options_selected_idx in [1, 2]: # Volumen Música/FX
                if self.options_selected_idx == 1: self.music_volume = max(0, self.music_volume - 5)
                elif self.options_selected_idx == 2: self.fx_volume = max(0, self.fx_volume - 5)
                self.update_volumes()
            elif key == pygame.K_RIGHT and self.options_selected_idx in [1, 2]: # Volumen Música/FX
                if self.options_selected_idx == 1: self.music_volume = min(100, self.music_volume + 5)
                elif self.options_selected_idx == 2: self.fx_volume = min(100, self.fx_volume + 5)
                self.update_volumes()
            elif key == pygame.K_RETURN:
                if self.options_selected_idx == 0: # Resolución
                    current_res_idx = config.RESOLUTIONS.index((self.screen_width, self.screen_height))
                    new_res_idx = (current_res_idx + 1) % len(config.RESOLUTIONS)
                    self.screen_width, self.screen_height = config.RESOLUTIONS[new_res_idx]
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                    self.bg_image = pygame.transform.scale(self.bg_image, (self.screen_width, self.screen_height))
                elif self.options_selected_idx == 3: # Eliminar Cuenta
                    self.input_box_active = True
                    self.input_field_type = 'delete_account'
                elif self.options_selected_idx == 4: self.game_state = 'menu'
            elif key == pygame.K_ESCAPE: self.game_state = 'menu'
            
    def handle_crud_keys(self, key):
        if self.input_box_active:
            if key == pygame.K_RETURN:
                if self.input_field_type == 'character_name':
                    if self.current_input_text and self.current_input_text not in self.characters:
                        self.characters[self.current_input_text] = {
                            "sprite_sheet_path": "", "sound_path": "", "data": [0,0,0,[0,0]],
                            "animation_steps": [0]*7, "stats": {"health": 100, "damage": 10, "speed": 10},
                            "special_moves": {}
                        }
                        self.characters_names = list(self.characters.keys())
                        save_characters(self.characters)
                        messagebox.showinfo("Éxito", f"Personaje '{self.current_input_text}' añadido. Ahora configura sus datos.", parent=self.screen)
                        self.move_crud_char_name = self.current_input_text
                        self.game_state = 'move_crud' # Ir a configurar movimientos
                        self.input_box_active = False
                    else: messagebox.showerror("Error", "Nombre de personaje inválido o ya existe.", parent=self.screen)
                elif self.input_field_type in ['health', 'damage', 'speed']:
                    try:
                        value = int(self.current_input_text)
                        if self.move_crud_char_name and self.move_crud_char_name in self.characters:
                            self.characters[self.move_crud_char_name]['stats'][self.input_field_type] = value
                            save_characters(self.characters)
                            messagebox.showinfo("Éxito", f"Estadística '{self.input_field_type}' actualizada.", parent=self.screen)
                        else: messagebox.showerror("Error", "No se ha seleccionado un personaje.", parent=self.screen)
                    except ValueError: messagebox.showerror("Error", "Entrada inválida. Debe ser un número.", parent=self.screen)
                self.input_box_active = False
                self.current_input_text = ""
                self.input_field_type = None
                self.input_field_key = None

            elif key == pygame.K_BACKSPACE: self.current_input_text = self.current_input_text[:-1]
            else: self.current_input_text += key.unicode if key.unicode else ''
        else:
            if key == pygame.K_UP: self.crud_selected_idx = (self.crud_selected_idx - 1) % len(config.CRUD_MENU_ITEMS)
            elif key == pygame.K_DOWN: self.crud_selected_idx = (self.crud_selected_idx + 1) % len(config.CRUD_MENU_ITEMS)
            elif key == pygame.K_RETURN:
                if self.crud_selected_idx == 0: # Añadir Personaje
                    self.input_box_active = True
                    self.input_field_type = 'character_name'
                elif self.crud_selected_idx == 1: # Ver Datos
                    if self.characters_names:
                        self.move_crud_char_name = self.characters_names[self.crud_char_idx]
                        self.game_state = 'view_character_data'
                    else: messagebox.showerror("Error", "No hay personajes para ver.", parent=self.screen)
                elif self.crud_selected_idx == 2: # Editar Estadísticas
                    if self.characters_names:
                        self.move_crud_char_name = self.characters_names[self.crud_char_idx]
                        self.game_state = 'edit_stats'
                    else: messagebox.showerror("Error", "No hay personajes para editar.", parent=self.screen)
                elif self.crud_selected_idx == 3: # Gestionar Movimientos
                    if self.characters_names:
                        self.move_crud_char_name = self.characters_names[self.crud_char_idx]
                        self.game_state = 'move_crud'
                        self.move_crud_selected_idx = 0
                    else: messagebox.showerror("Error", "No hay personajes para gestionar movimientos.", parent=self.screen)
                elif self.crud_selected_idx == 4: # Eliminar Personaje
                    if self.characters_names:
                        char_to_delete = self.characters_names[self.crud_char_idx]
                        if messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar a '{char_to_delete}'?", parent=self.screen):
                            del self.characters[char_to_delete]
                            self.characters_names = list(self.characters.keys())
                            save_characters(self.characters)
                            messagebox.showinfo("Éxito", f"Personaje '{char_to_delete}' eliminado.", parent=self.screen)
                            if self.crud_char_idx >= len(self.characters_names) and self.crud_char_idx > 0: self.crud_char_idx -= 1
                    else: messagebox.showerror("Error", "No hay personajes para eliminar.", parent=self.screen)
                elif self.crud_selected_idx == 5: self.game_state = 'menu'
            elif key == pygame.K_LEFT and self.crud_selected_idx in [1,2,3,4]:
                if self.characters_names: self.crud_char_idx = (self.crud_char_idx - 1) % len(self.characters_names)
            elif key == pygame.K_RIGHT and self.crud_selected_idx in [1,2,3,4]:
                if self.characters_names: self.crud_char_idx = (self.crud_char_idx + 1) % len(self.characters_names)
            elif key == pygame.K_ESCAPE: self.game_state = 'menu'

    def handle_move_crud_keys(self, key):
        if self.input_box_active:
            if key == pygame.K_RETURN:
                current_char = self.characters[self.move_crud_char_name]
                if self.input_field_type == 'new_move_name':
                    if self.current_input_text and self.current_input_text not in current_char['special_moves']:
                        current_char['special_moves'][self.current_input_text] = {"name": self.current_input_text, "animation_row": 0, "damage": 0, "cooldown": 0}
                        save_characters(self.characters)
                        messagebox.showinfo("Éxito", f"Movimiento '{self.current_input_text}' añadido.", parent=self.screen)
                    else: messagebox.showerror("Error", "Nombre de movimiento inválido o ya existe.", parent=self.screen)
                elif self.input_field_type == 'edit_key':
                    if self.key_to_configure and self.current_input_text and self.current_input_text not in config.FORBIDDEN_KEYS:
                        old_move_key = list(current_char['special_moves'].keys())[self.move_crud_idx]
                        move_data = current_char['special_moves'].pop(old_move_key)
                        current_char['special_moves'][self.current_input_text] = move_data
                        save_characters(self.characters)
                        messagebox.showinfo("Éxito", f"Tecla de movimiento actualizada a '{self.current_input_text}'.", parent=self.screen)
                    else: messagebox.showerror("Error", "Tecla inválida o ya en uso.", parent=self.screen)
                elif self.input_field_type in ['animation_row', 'damage', 'cooldown']:
                    try:
                        value = int(self.current_input_text)
                        move_key = list(current_char['special_moves'].keys())[self.move_crud_idx]
                        current_char['special_moves'][move_key][self.input_field_type] = value
                        save_characters(self.characters)
                        messagebox.showinfo("Éxito", f"Campo '{self.input_field_type}' actualizado.", parent=self.screen)
                    except ValueError: messagebox.showerror("Error", "Entrada inválida. Debe ser un número.", parent=self.screen)
                
                self.input_box_active = False
                self.current_input_text = ""
                self.input_field_type = None
                self.key_to_configure = None
            elif key == pygame.K_BACKSPACE: self.current_input_text = self.current_input_text[:-1]
            else: self.current_input_text += key.unicode if key.unicode else ''

        else:
            if key == pygame.K_UP: self.move_crud_selected_idx = (self.move_crud_selected_idx - 1) % len(config.MOVE_CRUD_OPTIONS)
            elif key == pygame.K_DOWN: self.move_crud_selected_idx = (self.move_crud_selected_idx + 1) % len(config.MOVE_CRUD_OPTIONS)
            elif key == pygame.K_LEFT and self.move_crud_selected_idx in [1, 2]: # Navegar movimientos existentes
                if self.characters[self.move_crud_char_name]['special_moves']:
                    self.move_crud_idx = (self.move_crud_idx - 1) % len(self.characters[self.move_crud_char_name]['special_moves'])
            elif key == pygame.K_RIGHT and self.move_crud_selected_idx in [1, 2]: # Navegar movimientos existentes
                if self.characters[self.move_crud_char_name]['special_moves']:
                    self.move_crud_idx = (self.move_crud_idx + 1) % len(self.characters[self.move_crud_char_name]['special_moves'])
            elif key == pygame.K_RETURN:
                if self.move_crud_selected_idx == 0: # Añadir Movimiento
                    self.input_box_active = True
                    self.input_field_type = 'new_move_name'
                elif self.move_crud_selected_idx == 1: # Editar Tecla / Atributos
                    if self.characters[self.move_crud_char_name]['special_moves']:
                        move_keys = list(self.characters[self.move_crud_char_name]['special_moves'].keys())
                        if move_keys:
                            self.key_to_configure = move_keys[self.move_crud_idx]
                            self.input_box_active = True
                            self.input_field_type = 'edit_key' # O 'animation_row', 'damage', 'cooldown'
                    else: messagebox.showerror("Error", "No hay movimientos para editar.", parent=self.screen)
                elif self.move_crud_selected_idx == 2: # Eliminar Movimiento
                    if self.characters[self.move_crud_char_name]['special_moves']:
                        move_to_delete_key = list(self.characters[self.move_crud_char_name]['special_moves'].keys())[self.move_crud_idx]
                        if messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar el movimiento '{move_to_delete_key}'?", parent=self.screen):
                            del self.characters[self.move_crud_char_name]['special_moves'][move_to_delete_key]
                            save_characters(self.characters)
                            messagebox.showinfo("Éxito", "Movimiento eliminado.", parent=self.screen)
                            if self.move_crud_idx >= len(self.characters[self.move_crud_char_name]['special_moves']) and self.move_crud_idx > 0: self.move_crud_idx -= 1
                    else: messagebox.showerror("Error", "No hay movimientos para eliminar.", parent=self.screen)
                elif self.move_crud_selected_idx == 3: self.game_state = 'crud_menu'
            elif key == pygame.K_ESCAPE: self.game_state = 'crud_menu'

    def handle_battle_history_keys(self, key):
        mods = pygame.key.get_mods() # Obtener el estado de los modificadores
        if key == pygame.K_UP: self.history_selected_idx = (self.history_selected_idx - 1) % len(self.battle_history)
        elif key == pygame.K_DOWN: self.history_selected_idx = (self.history_selected_idx + 1) % len(self.battle_history)
        elif key == pygame.K_BACKSPACE and (mods & pygame.KMOD_CTRL): # Eliminar con Ctrl + Backspace
            if self.battle_history and messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar el historial de batallas?", parent=self.screen):
                self.battle_history = []
                self.save_battle_history()
                messagebox.showinfo("Éxito", "Historial de batallas eliminado.", parent=self.screen)
                self.history_selected_idx = 0
        elif key == pygame.K_ESCAPE: self.game_state = 'menu'
        

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_state == 'menu': self.handle_menu_keys(event.key)
                elif self.game_state == 'character_select': self.handle_character_select_keys(event.key)
                elif self.game_state == 'playing': self.handle_game_keys(event.key)
                elif self.game_state == 'options': self.handle_options_keys(event.key)
                elif self.game_state == 'crud_menu' or self.game_state == 'edit_stats' or self.game_state == 'view_character_data': self.handle_crud_keys(event.key)
                elif self.game_state == 'move_crud': self.handle_move_crud_keys(event.key)
                elif self.game_state == 'battle_history': self.handle_battle_history_keys(event.key)
                elif self.game_state == 'preview_character':
                    if event.key == pygame.K_ESCAPE: self.game_state = 'menu'

    def draw_scenes(self):
        ui.draw_bg(self.screen, self.bg_image)
        if self.game_state == 'menu':
            ui.draw_menu(self.screen, self.font, config.MENU_ITEMS, self.menu_selected_idx)
        elif self.game_state == 'character_select':
            ui.draw_character_select(self.screen, self.font, self.characters_names, self.char_select_idx)
        elif self.game_state == 'playing':
            ui.draw_health_bar(self.screen, self.fighter_1.health, 20, 20)
            ui.draw_health_bar(self.screen, self.fighter_2.health, self.screen_width - 420, 20)
            ui.draw_text(self.screen, f'P1: {self.username}', self.score_font, config.WHITE, 20, 60)
            ui.draw_text(self.screen, f'P2: {self.p2_char_name}', self.score_font, config.WHITE, self.screen_width - 420, 60)
            ui.draw_text(self.screen, f'Ronda {self.current_round + 1}/{self.total_rounds}', self.score_font, config.WHITE, self.screen_width // 2 - 100, 20)
            ui.draw_text(self.screen, f'Score: {self.score[0]} - {self.score[1]}', self.score_font, config.RED, self.screen.get_width() / 2 - 100, 60)

            if self.intro_count <= 0:
                self.fighter_1.move(self.screen_width, self.screen_height, self.fighter_2, self.round_over)
                self.fighter_2.move(self.screen_width, self.screen_height, self.fighter_1, self.round_over)
            else:
                ui.draw_text(self.screen, str(self.intro_count), self.count_font, config.RED, self.screen.get_width() / 2 - 20, self.screen.get_height() / 3)
                if pygame.time.get_ticks() - self.last_count_update >= 1000: self.intro_count -= 1; self.last_count_update = pygame.time.get_ticks()
            
            self.fighter_1.update(); self.fighter_2.update()
            self.fighter_1.draw(self.screen); self.fighter_2.draw(self.screen)
            
            if not self.round_over:
                winner_name = None
                if not self.fighter_1.alive: winner_name = self.p2_char_name; self.score[1] += 1
                elif not self.fighter_2.alive: winner_name = self.username; self.score[0] += 1

                if winner_name:
                    self.round_winner = winner_name
                    self.round_over = True
                    self.round_over_time = pygame.time.get_ticks()
                    self.current_round += 1
                    self.battle_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "p1_char": self.username,
                        "p2_char": self.p2_char_name,
                        "winner": winner_name
                    })
                    self.save_battle_history()

            if self.round_over:
                if self.current_round >= self.total_rounds: # Final del juego
                    if self.score[0] > self.score[1]: final_winner = self.username
                    elif self.score[1] > self.score[0]: final_winner = self.p2_char_name
                    else: final_winner = "Empate"
                    
                    ui.draw_text(self.screen, "FIN DEL JUEGO!", self.font, config.WHITE, self.screen_width // 2 - 200, self.screen_height // 2 - 100)
                    ui.draw_text(self.screen, f"GANADOR: {final_winner}", self.font, config.YELLOW, self.screen_width // 2 - 150, self.screen_height // 2)
                else:
                    ui.draw_text(self.screen, "FIN DE LA RONDA!", self.font, config.WHITE, self.screen_width // 2 - 200, self.screen_height // 2 - 100)
                    ui.draw_text(self.screen, f"Ganador: {self.round_winner}", self.font, config.YELLOW, self.screen_width // 2 - 100, self.screen_height // 2)

                ui.draw_round_options(self.screen, self.small_font, config.ROUND_OPTIONS, self.round_options_idx, self.screen_width // 2 - 100, self.screen_height // 2 + 80)


        elif self.game_state == 'battle_history':
            ui.draw_battle_history(self.screen, self.font, self.small_font, self.battle_history, self.history_selected_idx)
        elif self.game_state == 'crud_menu':
            current_char_name = self.characters_names[self.crud_char_idx] if self.characters_names else "N/A"
            ui.draw_crud_menu(self.screen, self.font, config.CRUD_MENU_ITEMS, self.crud_selected_idx, current_char_name, self.char_info_font)
            if self.input_box_active: ui.draw_input_box(self.screen, self.small_font, self.current_input_text, f"Ingrese {self.input_field_type}:")
        elif self.game_state == 'view_character_data':
            if self.move_crud_char_name and self.move_crud_char_name in self.characters:
                ui.draw_character_data(self.screen, self.font, self.small_font, self.char_info_font, self.move_crud_char_name, self.characters[self.move_crud_char_name])
            else: self.game_state = 'crud_menu'
        elif self.game_state == 'edit_stats':
            if self.move_crud_char_name and self.move_crud_char_name in self.characters:
                ui.draw_edit_stats_menu(self.screen, self.font, self.small_font, self.char_info_font, self.move_crud_char_name, self.characters[self.move_crud_char_name]['stats'], self.input_box_active, self.current_input_text, self.input_field_type, self)
            else: self.game_state = 'crud_menu'
            if self.input_box_active: ui.draw_input_box(self.screen, self.small_font, self.current_input_text, f"Ingrese nuevo valor para {self.input_field_type}:")
        elif self.game_state == 'move_crud':
            if self.move_crud_char_name and self.move_crud_char_name in self.characters:
                current_moves = list(self.characters[self.move_crud_char_name]['special_moves'].keys())
                current_move_name = current_moves[self.move_crud_idx] if current_moves else "N/A"
                current_move_data = self.characters[self.move_crud_char_name]['special_moves'].get(current_move_name, {})
                ui.draw_move_crud_menu(self.screen, self.font, self.small_font, config.MOVE_CRUD_OPTIONS, self.move_crud_selected_idx, self.move_crud_char_name, current_move_name, current_move_data, self.char_info_font)
            else: self.game_state = 'crud_menu'
            if self.input_box_active: ui.draw_input_box(self.screen, self.small_font, self.current_input_text, f"Ingrese {self.input_field_type}:")

        elif self.game_state == 'options':
            ui.draw_options_menu(self.screen, self.font, config.OPTIONS_ITEMS, self.options_selected_idx, self.screen_width, self.screen_height, self.music_volume, self.fx_volume)
            if self.input_box_active: ui.draw_input_box(self.screen, self.small_font, self.current_input_text, "Ingrese su nombre de usuario para confirmar:")
        
        elif self.game_state == 'preview_character':
            if self.current_selected_char_name and self.current_selected_char_name in self.characters:
                char_data = self.characters[self.current_selected_char_name]
                if not self.preview_fighter:
                    animation_list = self.load_animations(char_data['sprite_sheet_path'], char_data['animation_steps'])
                    self.preview_fighter = Fighter(
                        1, self.screen_width // 2 - 100, 310, False, char_data['data'], animation_list,
                        pygame.mixer.Sound(char_data['sound_path']), char_data['stats'],
                        char_data['special_moves'], username=self.username
                    )
                self.preview_fighter.update()
                self.preview_fighter.draw(self.screen)
                ui.draw_text(self.screen, f"Personaje: {self.current_selected_char_name}", self.font, config.WHITE, 50, 50)
                ui.draw_text(self.screen, f"Salud: {char_data['stats']['health']}", self.small_font, config.WHITE, 50, 100)
                ui.draw_text(self.screen, f"Velocidad: {char_data['stats']['speed']}", self.small_font, config.WHITE, 50, 130)
                ui.draw_text(self.screen, f"Daño Base: {char_data['stats']['damage']}", self.small_font, config.WHITE, 50, 160)
                ui.draw_text(self.screen, "Movimientos Especiales:", self.small_font, config.WHITE, 50, 200)
                y_offset = 230
                for key, move in char_data['special_moves'].items():
                    ui.draw_text(self.screen, f"  {move['name']} (Tecla: {key.upper()}): Daño {move['damage']}, Cooldown {move['cooldown']}", self.char_info_font, config.WHITE, 70, y_offset)
                    y_offset += 25
                ui.draw_text(self.screen, "Presiona ESC para volver al menú", self.small_font, config.GRAY, self.screen_width // 2 - 150, self.screen_height - 50)
            else:
                self.game_state = 'menu'
                self.preview_fighter = None

        pygame.display.update()

    def run(self):
        while self.game_running:
            self.handle_events()
            self.draw_scenes()
            self.clock.tick(config.FPS)
        pygame.quit()
        sys.exit()