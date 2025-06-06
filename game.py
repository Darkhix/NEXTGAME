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
# INICIO DEL CÓDIGO QUE ANTES ESTABA EN CHARACTER_MANAGER.PY
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
    """Ventana de formulario para Crear o Editar un personaje."""
    def __init__(self, master, callback, character_data=None, character_name=None):
        super().__init__(master)
        self.callback = callback
        self.character_data = character_data
        self.character_name = character_name
        self.title("Editar Personaje" if character_name else "Añadir Personaje")
        self.geometry("500x600")
        self.grid_columnconfigure(1, weight=1)
        self.fields = {}
        self.create_widgets()
        if self.character_data:
            self.fill_form()
        self.grab_set()

    def create_widgets(self):
        labels = ["Nombre", "Ruta SpriteSheet", "Ruta Sonido", "Tamaño Sprite", "Escala Imagen", "Offset X", "Offset Y", "Pasos Animación (separados por coma)"]
        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.fields[label_text.split(" ")[0].lower()] = entry
        save_button = ctk.CTkButton(self, text="Guardar", command=self.save)
        save_button.grid(row=len(labels), columnspan=2, pady=20)

    def fill_form(self):
        self.fields["nombre"].insert(0, self.character_name)
        self.fields["nombre"].configure(state="disabled")
        self.fields["rutasprite"].insert(0, self.character_data["sprite_sheet_path"])
        self.fields["rutasonido"].insert(0, self.character_data["sound_path"])
        self.fields["tamaño"].insert(0, self.character_data["data"][0])
        self.fields["escala"].insert(0, self.character_data["data"][1])
        self.fields["offsetx"].insert(0, self.character_data["data"][2][0])
        self.fields["offsety"].insert(0, self.character_data["data"][2][1])
        self.fields["pasos"].insert(0, ", ".join(map(str, self.character_data["animation_steps"])))

    def save(self):
        try:
            name_entry = self.fields["nombre"]
            name = name_entry.get() if name_entry.cget("state") == "normal" else self.character_name
            
            if not name:
                messagebox.showerror("Error", "El nombre no puede estar vacío.")
                return

            new_data = {
                "sprite_sheet_path": self.fields["rutasprite"].get(),
                "sound_path": self.fields["rutasonido"].get(),
                "data": [int(self.fields["tamaño"].get()), int(self.fields["escala"].get()), [int(self.fields["offsetx"].get()), int(self.fields["offsety"].get())]],
                "animation_steps": [int(step.strip()) for step in self.fields["pasos"].get().split(',')]
            }
            characters = load_characters()
            characters[name] = new_data
            save_characters(characters)
            messagebox.showinfo("Éxito", f"Personaje '{name}' guardado correctamente.")
            self.callback()
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Por favor, introduce números válidos en los campos numéricos.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")

class CharacterCrudWindow(ctk.CTk):
    """Ventana principal para gestionar el CRUD de personajes."""
    def __init__(self):
        super().__init__()
        self.title("Administrar Personajes")
        self.geometry("600x400")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Personajes")
        self.scroll_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.selected_character_var = ctk.StringVar()
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        add_button = ctk.CTkButton(button_frame, text="Añadir Nuevo", command=self.add_character)
        add_button.pack(side="left", expand=True, padx=5)
        edit_button = ctk.CTkButton(button_frame, text="Editar Seleccionado", command=self.edit_character)
        edit_button.pack(side="left", expand=True, padx=5)
        delete_button = ctk.CTkButton(button_frame, text="Eliminar Seleccionado", command=self.delete_character, fg_color="red")
        delete_button.pack(side="left", expand=True, padx=5)
        self.populate_list()

    def populate_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        characters = load_characters()
        for name in characters:
            rb = ctk.CTkRadioButton(self.scroll_frame, text=name, variable=self.selected_character_var, value=name)
            rb.pack(anchor="w", padx=10)

    def add_character(self):
        CharacterForm(self, self.populate_list)

    def edit_character(self):
        char_name = self.selected_character_var.get()
        if not char_name:
            messagebox.showwarning("Atención", "Por favor, selecciona un personaje para editar.")
            return
        characters = load_characters()
        char_data = characters.get(char_name)
        CharacterForm(self, self.populate_list, char_data, char_name)

    def delete_character(self):
        char_name = self.selected_character_var.get()
        if not char_name:
            messagebox.showwarning("Atención", "Por favor, selecciona un personaje para eliminar.")
            return
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que quieres eliminar a {char_name}?"):
            characters = load_characters()
            if char_name in characters:
                del characters[char_name]
                save_characters(characters)
                self.populate_list()

# ==============================================================================
# FIN DEL CÓDIGO DE CHARACTER_MANAGER
# ==============================================================================


class Game:
    def __init__(self, username, user_data):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        mixer.init()

        self.username = username
        self.user_data = user_data
        
        self.all_characters_data = load_characters()
        
        if not self.all_characters_data:
            messagebox.showerror("Error Crítico", "No hay personajes definidos en characters.json.")
            sys.exit()
            
        self.character_class = user_data.get('character_class', list(self.all_characters_data.keys())[0])

        self.res_index = 0
        self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
        pygame.display.set_caption('Brawler')
        self.clock = pygame.time.Clock()

        self.load_general_assets()
        self.loaded_character_assets = {} 

        self.music_volume = 50
        self.fx_volume = 50
        self.update_volumes()

        self.game_state = 'menu'
        self.menu_idx, self.options_idx, self.char_select_idx, self.round_sel_idx = 0, 0, 0, 0
        self.fighter_1, self.fighter_2 = None, None
        self.score = [0, 0]
        self.round_over = False
        self.round_over_time = 0
        self.intro_count = 3
        self.last_count_update = 0

    def load_general_assets(self):
        self.count_font = pygame.font.Font(config.FONT_PATH, 80)
        self.score_font = pygame.font.Font(config.FONT_PATH, 30)
        self.menu_font = pygame.font.SysFont(None, 60)
        self.bg_image = pygame.image.load(config.BG_IMG_PATH).convert_alpha()
        self.victory_img = pygame.image.load(config.VICTORY_IMG_PATH).convert_alpha()
    
    def get_character_assets(self, char_name):
        if char_name not in self.loaded_character_assets:
            char_data = self.all_characters_data[char_name]
            sprite_sheet = pygame.image.load(char_data["sprite_sheet_path"]).convert_alpha()
            sound = mixer.Sound(char_data["sound_path"])
            self.loaded_character_assets[char_name] = {"sprite_sheet": sprite_sheet, "sound": sound}
        return self.loaded_character_assets[char_name]

    def update_volumes(self):
        mixer.music.set_volume(self.music_volume / 100)
        for assets in self.loaded_character_assets.values():
            assets["sound"].set_volume(self.fx_volume / 100)

    def play_music(self, path):
        mixer.music.stop()
        mixer.music.load(path)
        mixer.music.play(-1, 0.0, 5000)

    def create_fighters(self):
        player_char_name = self.character_class
        player_char_data = self.all_characters_data[player_char_name]
        player_assets = self.get_character_assets(player_char_name)
        self.fighter_1 = Fighter(1, 200, 310, False, player_char_data["data"], player_assets["sprite_sheet"], player_char_data["animation_steps"], player_assets["sound"], username=self.username)

        ai_options = [name for name in self.all_characters_data if name != player_char_name]
        ai_char_name = ai_options[0] if ai_options else player_char_name
        ai_char_data = self.all_characters_data[ai_char_name]
        ai_assets = self.get_character_assets(ai_char_name)
        self.fighter_2 = Fighter(2, 700, 310, True, ai_char_data["data"], ai_assets["sprite_sheet"], ai_char_data["animation_steps"], ai_assets["sound"], ai=True)
        
        self.update_volumes()

    def reset_round(self):
        self.create_fighters()
        self.intro_count, self.last_count_update, self.round_over = 3, pygame.time.get_ticks(), False

    def run(self):
        self.play_music(config.MUSIC_PATH)
        while True:
            self.clock.tick(config.FPS)
            self.handle_events()
            self.draw_scenes()
            pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(), sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.game_state == 'menu': self.handle_menu_keys(event.key)
                elif self.game_state == 'character_select': self.handle_character_select_keys(event.key)
                elif self.game_state == 'options': self.handle_options_keys(event.key)
                elif self.game_state == 'playing':
                    if not self.round_over: self.handle_playing_keys(event.key)
                    else: self.handle_round_over_keys(event.key)
    
    def handle_playing_keys(self, key):
        if key == pygame.K_w: self.fighter_1.jump()
        if key == pygame.K_r: self.fighter_1.attack(self.fighter_2, 1)
        if key == pygame.K_t: self.fighter_1.attack(self.fighter_2, 2)

    def handle_menu_keys(self, key):
        if key == pygame.K_UP: self.menu_idx = (self.menu_idx - 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_DOWN: self.menu_idx = (self.menu_idx + 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_RETURN:
            selected = config.MENU_ITEMS[self.menu_idx]
            if selected == 'Jugar':
                self.reset_round()
                self.score = [0, 0]
                self.game_state = 'playing'
            elif selected == 'Personaje':
                self.game_state = 'character_select'
                self.char_select_idx = list(self.all_characters_data.keys()).index(self.character_class)
            elif selected == 'Administrar Personajes':
                crud_window = CharacterCrudWindow()
                crud_window.mainloop()
                self.all_characters_data = load_characters()
            elif selected == 'Opciones': self.game_state = 'options'
            elif selected == 'Salir': pygame.quit(), sys.exit()

    def handle_character_select_keys(self, key):
        char_names = list(self.all_characters_data.keys())
        if not char_names: return
        if key == pygame.K_UP: self.char_select_idx = (self.char_select_idx - 1) % len(char_names)
        elif key == pygame.K_DOWN: self.char_select_idx = (self.char_select_idx + 1) % len(char_names)
        elif key == pygame.K_RETURN:
            self.character_class = char_names[self.char_select_idx]
            users = auth.load_users()
            users[self.username]['character_class'] = self.character_class
            auth.save_users(users)
            self.game_state = 'menu'

    def handle_options_keys(self, key):
        opt = config.OPTIONS_ITEMS[self.options_idx]
        if key == pygame.K_UP: self.options_idx = (self.options_idx - 1) % len(config.OPTIONS_ITEMS)
        elif key == pygame.K_DOWN: self.options_idx = (self.options_idx + 1) % len(config.OPTIONS_ITEMS)
        elif key == pygame.K_LEFT:
            if opt == 'Resolución':
                self.res_index = (self.res_index - 1) % len(config.RESOLUTIONS)
                self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = max(0, self.music_volume - 10)
            elif opt == 'Volumen FX': self.fx_volume = max(0, self.fx_volume - 10)
            self.update_volumes()
        elif key == pygame.K_RIGHT:
            if opt == 'Resolución':
                self.res_index = (self.res_index + 1) % len(config.RESOLUTIONS)
                self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = min(100, self.music_volume + 10)
            elif opt == 'Volumen FX': self.fx_volume = min(100, self.fx_volume + 10)
            self.update_volumes()
        elif key == pygame.K_RETURN:
            if opt == 'Eliminar Cuenta':
                if messagebox.askyesno('Eliminar Cuenta', '¿Seguro? Esta acción es irreversible.'):
                    auth.delete_user(self.username)
                    pygame.quit(), sys.exit()
            elif opt == 'Volver': self.game_state = 'menu'
            
    def handle_round_over_keys(self, key):
        if key == pygame.K_UP: self.round_sel_idx = (self.round_sel_idx - 1) % len(config.ROUND_OPTIONS)
        elif key == pygame.K_DOWN: self.round_sel_idx = (self.round_sel_idx + 1) % len(config.ROUND_OPTIONS)
        elif key == pygame.K_RETURN:
            if config.ROUND_OPTIONS[self.round_sel_idx] == 'Reintentar': self.reset_round()
            else: self.game_state = 'menu'

    def draw_scenes(self):
        if self.game_state == 'menu':
            ui.draw_menu(self.screen, self.menu_font, config.MENU_ITEMS, self.menu_idx)
        elif self.game_state == 'character_select':
            ui.draw_character_select(self.screen, self.menu_font, list(self.all_characters_data.keys()), self.char_select_idx)
        elif self.game_state == 'options':
            values = {'Resolución': f"{config.RESOLUTIONS[self.res_index][0]}x{config.RESOLUTIONS[self.res_index][1]}", 'Volumen Música': str(self.music_volume), 'Volumen FX': str(self.fx_volume)}
            ui.draw_options(self.screen, self.menu_font, config.OPTIONS_ITEMS, self.options_idx, values)
        elif self.game_state == 'playing':
            self.run_game_logic()

    def run_game_logic(self):
        ui.draw_bg(self.screen, self.bg_image)
        ui.draw_health_bar(self.screen, self.fighter_1.health, 20, 20)
        ui.draw_health_bar(self.screen, self.fighter_2.health, self.screen.get_width() - 420, 20)
        ui.draw_text(self.screen, f'P1: {self.score[0]}', self.score_font, config.RED, 20, 60)
        ui.draw_text(self.screen, f'P2: {self.score[1]}', self.score_font, config.RED, self.screen.get_width() - 120, 60)

        if self.intro_count <= 0:
            self.fighter_1.move(self.screen.get_width(), self.screen.get_height(), self.fighter_2, self.round_over)
            self.fighter_2.move(self.screen.get_width(), self.screen.get_height(), self.fighter_1, self.round_over)
        else:
            ui.draw_text(self.screen, str(self.intro_count), self.count_font, config.RED, self.screen.get_width() / 2 - 20, self.screen.get_height() / 3)
            if pygame.time.get_ticks() - self.last_count_update >= 1000:
                self.intro_count -= 1
                self.last_count_update = pygame.time.get_ticks()

        self.fighter_1.update()
        self.fighter_2.update()
        self.fighter_1.draw(self.screen)
        self.fighter_2.draw(self.screen)

        if not self.round_over:
            if not self.fighter_1.alive:
                self.score[1] += 1
                self.round_over, self.round_over_time = True, pygame.time.get_ticks()
            elif not self.fighter_2.alive:
                self.score[0] += 1
                self.round_over, self.round_over_time = True, pygame.time.get_ticks()
        else:
            if pygame.time.get_ticks() - self.round_over_time > config.ROUND_COOLDOWN:
                ui.draw_round_over_menu(self.screen, self.menu_font, config.ROUND_OPTIONS, self.round_sel_idx, self.victory_img)