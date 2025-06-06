# game.py
import pygame
import sys
import os
import json
import customtkinter as ctk
from tkinter import messagebox
import config
import ui
import auth
from fighter import Fighter
from pygame import mixer

# ==============================================================================
# INICIO DEL CÓDIGO DE GESTIÓN (FORMULARIOS EMERGENTES)
# ==============================================================================

def load_characters():
    """Carga los personajes desde el archivo JSON."""
    try:
        with open(config.CHARACTERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_characters(characters):
    """Guarda los personajes en el archivo JSON."""
    with open(config.CHARACTERS_FILE, 'w') as f:
        json.dump(characters, f, indent=2)

class CharacterForm(ctk.CTkToplevel):
    """Formulario para Añadir o Ver los datos de un Personaje."""
    def __init__(self, master, callback, character_data=None, character_name=None, read_only=False):
        super().__init__(master)
        self.root = master
        self.callback = callback
        self.character_data = character_data
        self.character_name = character_name
        
        form_title = "Añadir Personaje" if not read_only else f"Datos de {character_name}"
        self.title(form_title)
        self.geometry("500x600")
        # --- CORREGIDO: Se quita el guion bajo de la función ---
        self.grid_columnconfigure(1, weight=1)
        self.fields = {}
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()

        if self.character_data:
            self.fill_form()
        
        if read_only:
            for field in self.fields.values():
                field.configure(state="disabled")
            self.save_button.configure(state="disabled", text="Cerrar", command=self.on_closing)

        self.grab_set()

    def on_closing(self):
        self.root.destroy()

    def create_widgets(self):
        field_map = {"nombre": "Nombre", "rutasprite": "Ruta SpriteSheet", "rutasonido": "Ruta Sonido", "tamaño": "Tamaño Sprite", "escala": "Escala Imagen", "offsetx": "Offset X", "offsety": "Offset Y", "pasos": "Pasos Animación (separados por coma)"}
        for i, (key, label_text) in enumerate(field_map.items()):
            label = ctk.CTkLabel(self, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.fields[key] = entry
        self.save_button = ctk.CTkButton(self, text="Guardar", command=self.save)
        self.save_button.grid(row=len(field_map), columnspan=2, pady=20)

    def fill_form(self):
        self.fields["nombre"].insert(0, self.character_name)
        if self.character_data.get('sprite_sheet_path'): self.fields["rutasprite"].insert(0, self.character_data["sprite_sheet_path"])
        if self.character_data.get('sound_path'): self.fields["rutasonido"].insert(0, self.character_data["sound_path"])
        if self.character_data.get('data'):
            self.fields["tamaño"].insert(0, str(self.character_data["data"][0]))
            self.fields["escala"].insert(0, str(self.character_data["data"][1]))
            self.fields["offsetx"].insert(0, str(self.character_data["data"][2][0]))
            self.fields["offsety"].insert(0, str(self.character_data["data"][2][1]))
        if self.character_data.get('animation_steps'): self.fields["pasos"].insert(0, ", ".join(map(str, self.character_data["animation_steps"])))

    def save(self):
        try:
            name = self.fields["nombre"].get()
            if not name: messagebox.showerror("Error", "El nombre no puede estar vacío."); return
            characters = load_characters()
            if not self.character_name and name in characters:
                messagebox.showerror("Error", "Ya existe un personaje con este nombre."); return

            sprite_path, sound_path = self.fields["rutasprite"].get(), self.fields["rutasonido"].get()
            try: pygame.image.load(sprite_path); pygame.mixer.Sound(sound_path)
            except pygame.error as e: messagebox.showerror("Error de Archivo", f"No se pudo cargar un asset.\nError: {e}"); return

            new_data = {
                "sprite_sheet_path": sprite_path, "sound_path": sound_path,
                "data": [int(self.fields["tamaño"].get()), int(self.fields["escala"].get()), [int(self.fields["offsetx"].get()), int(self.fields["offsety"].get())]],
                "animation_steps": [int(step.strip()) for step in self.fields["pasos"].get().split(',')],
                "stats": {"health": 100, "damage": 10, "speed": 10},
                "special_moves": {}
            }
            characters[name] = new_data
            save_characters(characters)
            messagebox.showinfo("Éxito", f"Personaje '{name}' guardado."); self.callback(); self.root.destroy()
        except ValueError: messagebox.showerror("Error de Valor", "Introduce números válidos.")
        except Exception as e: messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")

class StatEditForm(ctk.CTkToplevel):
    """Formulario para editar las estadísticas de un personaje."""
    def __init__(self, master, callback, character_name):
        super().__init__(master)
        self.root, self.callback, self.character_name = master, callback, character_name
        self.title(f"Editar Stats de {character_name}"); self.geometry("400x300")
        # --- CORREGIDO: Se quita el guion bajo de la función ---
        self.grid_columnconfigure(1, weight=1)
        self.fields = {}
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets(); self.fill_form(); self.grab_set()

    def on_closing(self):
        self.root.destroy()
        
    def create_widgets(self):
        self.character_data = load_characters()[self.character_name]
        field_map = {"health": "Vida", "damage": "Daño", "speed": "Velocidad"}
        for i, (key, label_text) in enumerate(field_map.items()):
            label = ctk.CTkLabel(self, text=label_text); label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
            entry = ctk.CTkEntry(self); entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
            self.fields[key] = entry
        save_button = ctk.CTkButton(self, text="Guardar Stats", command=self.save); save_button.grid(row=len(field_map), columnspan=2, pady=20)

    def fill_form(self):
        stats = self.character_data.get("stats", {})
        self.fields["health"].insert(0, str(stats.get("health", 100)))
        self.fields["damage"].insert(0, str(stats.get("damage", 10)))
        self.fields["speed"].insert(0, str(stats.get("speed", 10)))

    def save(self):
        try:
            characters = load_characters()
            if "stats" not in characters[self.character_name]: characters[self.character_name]["stats"] = {}
            stats = {"health": int(self.fields["health"].get()), "damage": int(self.fields["damage"].get()), "speed": int(self.fields["speed"].get())}
            characters[self.character_name]["stats"] = stats
            save_characters(characters); messagebox.showinfo("Éxito", f"Stats de '{self.character_name}' guardadas."); self.callback(); self.root.destroy()
        except ValueError: messagebox.showerror("Error de Valor", "Introduce números válidos.")
        except Exception as e: messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")

# ==============================================================================
# La clase Game (sin cambios desde aquí)
# ==============================================================================
class Game:
    def __init__(self, username, user_data):
        # ... (El resto del archivo no necesita cambios)
        os.environ['SDL_VIDEO_CENTERED'] = '1'; pygame.init(); mixer.init()
        self.username, self.user_data = username, user_data
        self.all_characters_data = load_characters()
        if not self.all_characters_data: messagebox.showerror("Error", "No hay personajes."); sys.exit()
        self.character_class = user_data.get('character_class', list(self.all_characters_data.keys())[0])
        self.res_index = 0
        self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
        pygame.display.set_caption('Brawler'); self.clock = pygame.time.Clock()
        self.load_general_assets(); self.loaded_character_assets = {}
        self.music_volume, self.fx_volume = 50, 50; self.update_volumes()
        self.game_state = 'menu'
        self.menu_idx, self.options_idx, self.char_select_idx, self.round_sel_idx = 0,0,0,0
        self.crud_char_idx, self.crud_opt_idx = 0,0
        self.move_crud_move_idx = 0
        self.is_listening_for_key, self.move_to_remap, self.char_for_remap = False, None, None
        self.fighter_1, self.fighter_2 = None, None
        self.score, self.round_over, self.round_over_time = [0,0], False, 0
        self.intro_count, self.last_count_update = 3, 0

    def refresh_character_data(self):
        self.all_characters_data = load_characters()
        char_count = len(self.all_characters_data)
        self.crud_char_idx = min(self.crud_char_idx, char_count - 1) if char_count > 0 else 0

    def load_general_assets(self):
        self.count_font = pygame.font.Font(config.FONT_PATH, 80); self.score_font = pygame.font.Font(config.FONT_PATH, 30)
        self.menu_font = pygame.font.SysFont(None, 60); self.title_font = pygame.font.SysFont(None, 80)
        self.bg_image = pygame.image.load(config.BG_IMG_PATH).convert_alpha(); self.victory_img = pygame.image.load(config.VICTORY_IMG_PATH).convert_alpha()
    
    def get_character_assets(self, char_name):
        if char_name not in self.loaded_character_assets:
            try:
                char_data = self.all_characters_data[char_name]
                sprite_sheet = pygame.image.load(char_data["sprite_sheet_path"]).convert_alpha()
                sound = mixer.Sound(char_data["sound_path"])
                self.loaded_character_assets[char_name] = {"sprite_sheet": sprite_sheet, "sound": sound}
            except pygame.error as e: messagebox.showerror("Error", f"No se pudo cargar assets para '{char_name}'.\nError: {e}"); pygame.quit(); sys.exit()
        return self.loaded_character_assets[char_name]

    def update_volumes(self):
        mixer.music.set_volume(self.music_volume / 100)
        for assets in self.loaded_character_assets.values(): assets["sound"].set_volume(self.fx_volume / 100)

    def play_music(self, path):
        mixer.music.stop(); mixer.music.load(path); mixer.music.play(-1, 0.0, 5000)

    def create_fighters(self):
        player_char_name = self.character_class
        player_char_data = self.all_characters_data[player_char_name]
        player_assets = self.get_character_assets(player_char_name)
        stats = player_char_data.get("stats", {"health": 100, "damage": 10, "speed": 10})
        moves = player_char_data.get("special_moves", {})
        self.fighter_1 = Fighter(1, 200, 310, False, player_char_data["data"], player_assets["sprite_sheet"], player_char_data["animation_steps"], player_assets["sound"], stats, moves, username=self.username)
        ai_options = [name for name in self.all_characters_data if name != player_char_name]
        ai_char_name = ai_options[0] if ai_options else player_char_name
        ai_char_data = self.all_characters_data[ai_char_name]
        ai_assets = self.get_character_assets(ai_char_name)
        ai_stats = ai_char_data.get("stats", {"health": 100, "damage": 10, "speed": 10})
        ai_moves = ai_char_data.get("special_moves", {})
        self.fighter_2 = Fighter(2, 700, 310, True, ai_char_data["data"], ai_assets["sprite_sheet"], ai_char_data["animation_steps"], ai_assets["sound"], ai_stats, ai_moves, ai=True)
        self.update_volumes()

    def reset_round(self):
        self.create_fighters(); self.intro_count, self.last_count_update, self.round_over = 3, pygame.time.get_ticks(), False

    def run(self):
        self.play_music(config.MUSIC_PATH)
        while True: self.clock.tick(config.FPS); self.handle_events(); self.draw_scenes(); pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(), sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.is_listening_for_key: self.remap_move_key(event.key); continue
                if self.game_state == 'menu': self.handle_menu_keys(event.key)
                elif self.game_state == 'character_crud': self.handle_crud_keys(event.key)
                elif self.game_state == 'move_crud': self.handle_move_crud_keys(event.key)
                elif self.game_state == 'character_select': self.handle_character_select_keys(event.key)
                elif self.game_state == 'options': self.handle_options_keys(event.key)
                elif self.game_state == 'playing':
                    if not self.round_over: self.handle_playing_keys(event.key)
                    else: self.handle_round_over_keys(event.key)
    
    def remap_move_key(self, new_key_code):
        if new_key_code in config.FORBIDDEN_KEYS: messagebox.showwarning("Tecla no permitida", "No puedes usar W, A, S o D."); self.is_listening_for_key = False; return
        new_key_str = next((k for k, v in pygame.__dict__.items() if k.startswith('K_') and v == new_key_code), None)
        if not new_key_str: messagebox.showwarning("Tecla no válida", "Esa tecla no es compatible."); self.is_listening_for_key = False; return
        characters = load_characters()
        char_moves = characters[self.char_for_remap]["special_moves"]
        if new_key_str in char_moves: messagebox.showwarning("Tecla en uso", f"La tecla ya está asignada."); self.is_listening_for_key = False; return
        move_data = char_moves.pop(self.move_to_remap)
        char_moves[new_key_str] = move_data
        save_characters(characters); self.refresh_character_data()
        messagebox.showinfo("Éxito", f"Movimiento reasignado a la tecla {new_key_str.split('_')[-1].upper()}.")
        self.is_listening_for_key = False; self.move_to_remap = None; self.char_for_remap = None
    
    def handle_playing_keys(self, key):
        if key == pygame.K_w: self.fighter_1.jump()
        for move_key_str in self.fighter_1.special_moves:
            if hasattr(pygame, move_key_str) and key == getattr(pygame, move_key_str): self.fighter_1.attack(self.fighter_2, move_key_str); break

    def handle_menu_keys(self, key):
        if key == pygame.K_UP: self.menu_idx = (self.menu_idx - 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_DOWN: self.menu_idx = (self.menu_idx + 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_RETURN:
            selected = config.MENU_ITEMS[self.menu_idx]
            if selected == 'Jugar': self.reset_round(); self.game_state = 'playing'
            elif selected == 'Personaje': self.game_state = 'character_select'; self.char_select_idx = list(self.all_characters_data.keys()).index(self.character_class)
            elif selected == 'Administrar Personajes': self.game_state = 'character_crud'; self.crud_char_idx, self.crud_opt_idx = 0, 0
            elif selected == 'Opciones': self.game_state = 'options'
            elif selected == 'Salir': pygame.quit(), sys.exit()

    def handle_crud_keys(self, key):
        char_names = list(self.all_characters_data.keys())
        if key == pygame.K_UP: self.crud_char_idx = (self.crud_char_idx - 1) % len(char_names) if char_names else 0
        elif key == pygame.K_DOWN: self.crud_char_idx = (self.crud_char_idx + 1) % len(char_names) if char_names else 0
        elif key == pygame.K_RIGHT: self.crud_opt_idx = (self.crud_opt_idx + 1) % len(config.CRUD_MENU_ITEMS)
        elif key == pygame.K_LEFT: self.crud_opt_idx = (self.crud_opt_idx - 1) % len(config.CRUD_MENU_ITEMS)
        elif key == pygame.K_RETURN:
            selected_option = config.CRUD_MENU_ITEMS[self.crud_opt_idx]
            selected_char_name = char_names[self.crud_char_idx] if char_names else None
            if not selected_char_name and selected_option not in ['Añadir Personaje', 'Volver']:
                 messagebox.showwarning("Atención", "No hay personajes para seleccionar."); return

            if selected_option == 'Añadir Personaje':
                root = ctk.CTk(); root.withdraw()
                CharacterForm(root, self.refresh_character_data, read_only=False)
                root.mainloop()
            elif selected_option == 'Ver Datos':
                char_data = self.all_characters_data.get(selected_char_name)
                root = ctk.CTk(); root.withdraw()
                CharacterForm(root, self.refresh_character_data, char_data, selected_char_name, read_only=True)
                root.mainloop()
            elif selected_option == 'Editar Estadísticas':
                root = ctk.CTk(); root.withdraw()
                StatEditForm(root, self.refresh_character_data, selected_char_name)
                root.mainloop()
            elif selected_option == 'Gestionar Movimientos': 
                self.game_state = 'move_crud'
                self.crud_selected_char = selected_char_name
                self.move_crud_move_idx, self.move_crud_opt_idx = 0, 0
            elif selected_option == 'Eliminar Personaje':
                if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar a {selected_char_name}?"):
                    del self.all_characters_data[selected_char_name]
                    save_characters(self.all_characters_data)
                    self.refresh_character_data()
            elif selected_option == 'Volver':
                self.game_state = 'menu'

    def handle_move_crud_keys(self, key):
        if key == pygame.K_ESCAPE: self.game_state = 'character_crud'; return
        char_moves = self.all_characters_data.get(self.crud_selected_char, {}).get("special_moves", {})
        move_keys = list(char_moves.keys())
        if key == pygame.K_UP: self.move_crud_move_idx = (self.move_crud_move_idx - 1) % len(move_keys) if move_keys else 0
        elif key == pygame.K_DOWN: self.move_crud_move_idx = (self.move_crud_move_idx + 1) % len(move_keys) if move_keys else 0
        elif key == pygame.K_RETURN:
            if not move_keys: messagebox.showinfo("Info", "Este personaje no tiene movimientos para editar."); return
            self.is_listening_for_key = True
            self.move_to_remap = move_keys[self.move_crud_move_idx]
            self.char_for_remap = self.crud_selected_char

    def handle_character_select_keys(self, key):
        char_names = list(self.all_characters_data.keys())
        if not char_names: return
        if key == pygame.K_UP: self.char_select_idx = (self.char_select_idx - 1) % len(char_names)
        elif key == pygame.K_DOWN: self.char_select_idx = (self.char_select_idx + 1) % len(char_names)
        elif key == pygame.K_RETURN:
            self.character_class = char_names[self.char_select_idx]
            users = auth.load_users(); users[self.username]['character_class'] = self.character_class; auth.save_users(users)
            self.game_state = 'menu'

    def handle_options_keys(self, key):
        opt = config.OPTIONS_ITEMS[self.options_idx]
        if key == pygame.K_UP: self.options_idx = (self.options_idx - 1) % len(config.OPTIONS_ITEMS)
        elif key == pygame.K_DOWN: self.options_idx = (self.options_idx + 1) % len(config.OPTIONS_ITEMS)
        elif key == pygame.K_LEFT:
            if opt == 'Resolución': self.res_index = (self.res_index - 1) % len(config.RESOLUTIONS); self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = max(0, self.music_volume - 10)
            elif opt == 'Volumen FX': self.fx_volume = max(0, self.fx_volume - 10)
            self.update_volumes()
        elif key == pygame.K_RIGHT:
            if opt == 'Resolución': self.res_index = (self.res_index + 1) % len(config.RESOLUTIONS); self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = min(100, self.music_volume + 10)
            elif opt == 'Volumen FX': self.fx_volume = min(100, self.fx_volume + 10)
            self.update_volumes()
        elif key == pygame.K_RETURN:
            if opt == 'Eliminar Cuenta':
                if messagebox.askyesno('Confirmar', '¿Seguro?'): auth.delete_user(self.username); pygame.quit(), sys.exit()
            elif opt == 'Volver': self.game_state = 'menu'
            
    def handle_round_over_keys(self, key):
        if key == pygame.K_UP: self.round_sel_idx = (self.round_sel_idx - 1) % len(config.ROUND_OPTIONS)
        elif key == pygame.K_DOWN: self.round_sel_idx = (self.round_sel_idx + 1) % len(config.ROUND_OPTIONS)
        elif key == pygame.K_RETURN:
            if config.ROUND_OPTIONS[self.round_sel_idx] == 'Reintentar': self.reset_round()
            else: self.game_state = 'menu'

    def draw_scenes(self):
        if self.game_state == 'menu': ui.draw_menu(self.screen, self.menu_font, config.MENU_ITEMS, self.menu_idx)
        elif self.game_state == 'character_crud': ui.draw_character_crud(self.screen, self.bg_image, self.menu_font, self.title_font, list(self.all_characters_data.keys()), config.CRUD_MENU_ITEMS, self.crud_char_idx, self.crud_opt_idx)
        elif self.game_state == 'move_crud':
            char_moves = self.all_characters_data.get(self.crud_selected_char, {}).get("special_moves", {})
            ui.draw_move_crud(self.screen, self.bg_image, self.menu_font, self.title_font, self.crud_selected_char, char_moves, self.move_crud_move_idx, self.is_listening_for_key)
        elif self.game_state == 'character_select': ui.draw_character_select(self.screen, self.menu_font, list(self.all_characters_data.keys()), self.char_select_idx)
        elif self.game_state == 'options':
            values = {'Resolución': f"{config.RESOLUTIONS[self.res_index][0]}x{config.RESOLUTIONS[self.res_index][1]}", 'Volumen Música': str(self.music_volume), 'Volumen FX': str(self.fx_volume)}
            ui.draw_options(self.screen, self.menu_font, config.OPTIONS_ITEMS, self.options_idx, values)
        elif self.game_state == 'playing': self.run_game_logic()

    def run_game_logic(self):
        ui.draw_bg(self.screen, self.bg_image); ui.draw_health_bar(self.screen, self.fighter_1.health, 20, 20)
        ui.draw_health_bar(self.screen, self.fighter_2.health, self.screen.get_width() - 420, 20)
        ui.draw_text(self.screen, f'P1: {self.score[0]}', self.score_font, config.RED, 20, 60)
        ui.draw_text(self.screen, f'P2: {self.score[1]}', self.score_font, config.RED, self.screen.get_width() - 120, 60)
        if self.intro_count <= 0:
            self.fighter_1.move(self.screen.get_width(), self.screen.get_height(), self.fighter_2, self.round_over)
            self.fighter_2.move(self.screen.get_width(), self.screen.get_height(), self.fighter_1, self.round_over)
        else:
            ui.draw_text(self.screen, str(self.intro_count), self.count_font, config.RED, self.screen.get_width() / 2 - 20, self.screen.get_height() / 3)
            if pygame.time.get_ticks() - self.last_count_update >= 1000: self.intro_count -= 1; self.last_count_update = pygame.time.get_ticks()
        self.fighter_1.update(); self.fighter_2.update()
        self.fighter_1.draw(self.screen); self.fighter_2.draw(self.screen)
        if not self.round_over:
            if not self.fighter_1.alive: self.score[1] += 1; self.round_over, self.round_over_time = True, pygame.time.get_ticks()
            elif not self.fighter_2.alive: self.score[0] += 1; self.round_over, self.round_over_time = True, pygame.time.get_ticks()
        else:
            if pygame.time.get_ticks() - self.round_over_time > config.ROUND_COOLDOWN:
                ui.draw_round_over_menu(self.screen, self.menu_font, config.ROUND_OPTIONS, self.round_sel_idx, self.victory_img)