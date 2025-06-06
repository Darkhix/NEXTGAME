# game.py
import pygame
import sys
import os
import json
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import config
import ui
import auth
from fighter import Fighter
from pygame import mixer

# ==============================================================================
# INICIO DEL CÓDIGO DE GESTIÓN
# ==============================================================================

def load_characters():
    try:
        with open(config.CHARACTERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_characters(characters):
    with open(config.CHARACTERS_FILE, 'w') as f:
        json.dump(characters, f, indent=2)

def _create_spritesheet_from_files(base_path, scale, offset):
    if not os.path.isdir(base_path):
        messagebox.showerror("Error", f"La carpeta base no existe:\n{base_path}")
        return None
    all_animations, max_frame_w, max_frame_h, max_frames_per_row, animation_steps = [], 0, 0, 0, []
    animation_folder_names = ['Idle', 'Run', 'Jump', 'Fall', 'Attack', 'Take Hit', 'Death', 'Block', 'Hold Shield']
    for anim_name in animation_folder_names:
        anim_path = os.path.join(base_path, anim_name)
        current_anim_frames = []
        if os.path.isdir(anim_path):
            filenames = sorted(os.listdir(anim_path))
            for filename in filenames:
                if filename.lower().endswith('.png'):
                    try:
                        img = Image.open(os.path.join(anim_path, filename))
                        current_anim_frames.append(img); max_frame_w = max(max_frame_w, img.width); max_frame_h = max(max_frame_h, img.height)
                    except Exception as e: print(f"Advertencia: No se pudo cargar {filename}: {e}")
        all_animations.append(current_anim_frames)
        num_frames = len(current_anim_frames)
        animation_steps.append(num_frames); max_frames_per_row = max(max_frames_per_row, num_frames)
    if max_frame_w == 0:
        messagebox.showerror("Error", "No se encontraron imágenes válidas en las carpetas."); return None
    sheet_width = max_frame_w * max_frames_per_row; sheet_height = max_frame_h * len(animation_folder_names)
    final_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    for y, anim_frames in enumerate(all_animations):
        for x, frame_image in enumerate(anim_frames):
            final_sheet.paste(frame_image, (x * max_frame_w, y * max_frame_h), frame_image)
    output_filename = f"{os.path.basename(base_path).replace(' ', '_').lower()}_spritesheet.png"
    output_path = os.path.join(base_path, output_filename)
    final_sheet.save(output_path)
    return {"sprite_sheet_path": output_path.replace("\\", "/"), "data": [max_frame_w, max_frame_h, scale, offset], "animation_steps": animation_steps}

class CharacterForm(ctk.CTkToplevel):
    def __init__(self, master, callback, character_data=None, character_name=None, read_only=False):
        super().__init__(master)
        self.root, self.callback, self.character_data, self.character_name = master, callback, character_data, character_name
        self.title("Añadir Personaje" if not character_name else f"Datos de {character_name}")
        self.geometry("550x650"); self.grid_columnconfigure(1, weight=1); self.fields = {}; self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()
        if self.character_data: self.fill_form()
        if read_only:
            for widget in self.fields.values():
                if isinstance(widget, (ctk.CTkEntry, ctk.CTkOptionMenu)): widget.configure(state="disabled")
            self.save_button.configure(state="disabled", text="Cerrar", command=self.on_closing)
        if self.character_name: self.fields["asset_type"].configure(state="disabled")
        self.grab_set()

    def on_closing(self): self.root.destroy()

    def create_widgets(self):
        self.fields = {}; row_counter = 0
        
        # --- ESTA ES LA FUNCIÓN INTERNA QUE FALTABA ---
        def create_row(key, text):
            nonlocal row_counter
            label = ctk.CTkLabel(self, text=text); label.grid(row=row_counter, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self); entry.grid(row=row_counter, column=1, padx=10, pady=5, sticky="ew")
            self.fields[key] = entry; row_counter += 1
            return label, entry

        create_row("nombre", "Nombre")
        label_asset = ctk.CTkLabel(self, text="Tipo de Asset"); label_asset.grid(row=row_counter, column=0, padx=10, pady=5, sticky="w")
        self.asset_type_var = ctk.StringVar(value="Spritesheet")
        asset_menu = ctk.CTkOptionMenu(self, values=["Spritesheet", "Archivos Individuales"], variable=self.asset_type_var, command=self.update_form_fields)
        asset_menu.grid(row=row_counter, column=1, padx=10, pady=5, sticky="ew"); self.fields['asset_type'] = asset_menu; row_counter += 1
        
        self.label_ss, self.entry_ss = create_row("sprite_sheet_path", "Ruta Spritesheet")
        self.label_as, self.entry_as = create_row("animation_steps", "Pasos Animación")
        self.label_bp, self.entry_bp = create_row("base_path", "Ruta Carpeta Base")
        self.label_w, self.entry_w = create_row("frame_w", "Ancho Frame")
        self.label_h, self.entry_h = create_row("frame_h", "Alto Frame")
        create_row("sound_path", "Ruta Sonido")
        create_row("escala", "Escala Imagen")
        create_row("offsetx", "Offset X")
        create_row("offsety", "Offset Y")
        self.save_button = ctk.CTkButton(self, text="Guardar", command=self.save); self.save_button.grid(row=row_counter, columnspan=2, pady=20)
        self.update_form_fields()

    def update_form_fields(self, selected_type=None):
        if selected_type is None: selected_type = self.asset_type_var.get()
        is_spritesheet = selected_type == "Spritesheet"
        def set_visibility(label, entry, is_visible):
            if is_visible: label.grid(); entry.grid()
            else: label.grid_remove(); entry.grid_remove()
        set_visibility(self.label_ss, self.entry_ss, is_spritesheet)
        set_visibility(self.label_as, self.entry_as, is_spritesheet)
        set_visibility(self.label_w, self.entry_w, is_spritesheet)
        set_visibility(self.label_h, self.entry_h, is_spritesheet)
        set_visibility(self.label_bp, self.entry_bp, not is_spritesheet)

    def fill_form(self):
        self.fields["nombre"].insert(0, self.character_name)
        if "sprite_sheet_path" in self.character_data:
            self.asset_type_var.set("Spritesheet")
            self.fields["sprite_sheet_path"].insert(0, self.character_data["sprite_sheet_path"])
            self.fields["animation_steps"].insert(0, ", ".join(map(str, self.character_data.get("animation_steps", []))))
        elif "base_path" in self.character_data:
            self.asset_type_var.set("Archivos Individuales")
            self.fields["base_path"].insert(0, self.character_data["base_path"])
        self.update_form_fields()
        self.fields["sound_path"].insert(0, self.character_data.get("sound_path", ""))
        data = self.character_data.get("data", [0, 0, 0, [0, 0]])
        self.fields["frame_w"].insert(0, str(data[0])); self.fields["frame_h"].insert(0, str(data[1]))
        self.fields["escala"].insert(0, str(data[2]))
        self.fields["offsetx"].insert(0, str(data[3][0])); self.fields["offsety"].insert(0, str(data[3][1]))

    def save(self):
        try:
            name = self.fields["nombre"].get()
            if not name: messagebox.showerror("Error", "El nombre no puede estar vacío."); return
            characters = load_characters()
            if not self.character_name and name in characters: messagebox.showerror("Error", "Ya existe un personaje con este nombre."); return
            new_data = {"sound_path": self.fields["sound_path"].get(), "stats": {"health": 100, "speed": 10}, "special_moves": {}}
            asset_type = self.asset_type_var.get()
            if asset_type == "Spritesheet":
                path = self.fields["sprite_sheet_path"].get()
                new_data["sprite_sheet_path"] = path
                new_data["animation_steps"] = [int(step.strip()) for step in self.fields["animation_steps"].get().split(',')]
                new_data["data"] = [int(self.fields["frame_w"].get()), int(self.fields["frame_h"].get()), int(self.fields["escala"].get()), [int(self.fields["offsetx"].get()), int(self.fields["offsety"].get())]]
                try: pygame.image.load(path)
                except pygame.error as e: messagebox.showerror("Error de Archivo", f"No se pudo cargar Spritesheet: {e}"); return
            elif asset_type == "Archivos Individuales":
                base_path = self.fields["base_path"].get()
                scale = int(self.fields["escala"].get()); offset = [int(self.fields["offsetx"].get()), int(self.fields["offsety"].get())]
                conversion_result = _create_spritesheet_from_files(base_path, scale, offset)
                if conversion_result is None: return
                new_data.update(conversion_result)
            characters[name] = new_data
            save_characters(characters); messagebox.showinfo("Éxito", f"Personaje '{name}' procesado y guardado."); self.callback(); self.root.destroy()
        except ValueError: messagebox.showerror("Error de Valor", "Introduce números válidos.")
        except Exception as e: messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")

class StatEditForm(ctk.CTkToplevel):
    def __init__(self, master, callback, character_name):
        super().__init__(master)
        self.root, self.callback, self.character_name = master, callback, character_name
        self.title(f"Editar Stats de {character_name}"); self.geometry("400x300")
        self.grid_columnconfigure(1, weight=1); self.fields = {}; self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets(); self.fill_form(); self.grab_set()
    def on_closing(self): self.root.destroy()
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
        self.fields["health"].insert(0, str(stats.get("health", 100))); self.fields["damage"].insert(0, str(stats.get("damage", 10))); self.fields["speed"].insert(0, str(stats.get("speed", 10)))
    def save(self):
        try:
            characters = load_characters()
            if "stats" not in characters[self.character_name]: characters[self.character_name]["stats"] = {}
            stats = {"health": int(self.fields["health"].get()), "damage": int(self.fields["damage"].get()), "speed": int(self.fields["speed"].get())}
            characters[self.character_name]["stats"] = stats
            save_characters(characters); messagebox.showinfo("Éxito", f"Stats de '{self.character_name}' guardadas."); self.callback(); self.root.destroy()
        except ValueError: messagebox.showerror("Error de Valor", "Introduce números válidos.")
        except Exception as e: messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")

class Game:
    def __init__(self, username, user_data):
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
    
    def update_volumes(self):
        mixer.music.set_volume(self.music_volume / 100)
        for assets in self.loaded_character_assets.values(): assets["sound"].set_volume(self.fx_volume / 100)
    
    def play_music(self, path):
        mixer.music.stop(); mixer.music.load(path)
        mixer.music.set_volume(self.music_volume / 100)
        mixer.music.play(-1, 0.0, 5000)

    def get_character_assets(self, char_name):
        if char_name in self.loaded_character_assets: return self.loaded_character_assets[char_name]
        try:
            char_data = self.all_characters_data[char_name]
            sound = mixer.Sound(char_data["sound_path"]); sound.set_volume(self.fx_volume / 100)
            animation_list = []
            if "sprite_sheet_path" in char_data:
                sprite_sheet = pygame.image.load(char_data["sprite_sheet_path"]).convert_alpha()
                animation_list = self._load_from_spritesheet(char_data, sprite_sheet)
            elif "base_path" in char_data:
                messagebox.showerror("Error de Carga", f"El personaje '{char_name}' está en formato obsoleto. Por favor, vuelve a añadirlo usando el formulario para convertirlo a spritesheet."); pygame.quit(); sys.exit()
            else: raise KeyError(f"'{char_name}' no tiene 'sprite_sheet_path' ni 'base_path'.")
            self.loaded_character_assets[char_name] = {"sound": sound, "animation_list": animation_list}
            return self.loaded_character_assets[char_name]
        except Exception as e: messagebox.showerror("Error de Carga", f"No se pudo cargar assets para '{char_name}'.\nError: {e}"); pygame.quit(); sys.exit()

    def _load_from_spritesheet(self, char_data, sprite_sheet):
        animation_list = []; frame_w, frame_h, image_scale = char_data["data"][0], char_data["data"][1], char_data["data"][2]
        sheet_width, sheet_height = sprite_sheet.get_width(), sprite_sheet.get_height()
        for y, frames in enumerate(char_data.get("animation_steps", [])):
            temp_img_list = []
            for x in range(frames):
                frame_x, frame_y = x * frame_w, y * frame_h
                if frame_x + frame_w <= sheet_width and frame_y + frame_h <= sheet_height:
                    img = sprite_sheet.subsurface(pygame.Rect(frame_x, frame_y, frame_w, frame_h)); img = pygame.transform.scale(img, (int(frame_w * image_scale), int(frame_h * image_scale))); temp_img_list.append(img)
            animation_list.append(temp_img_list)
        return animation_list

    def create_fighters(self):
        player_char_name = self.character_class
        player_char_data = self.all_characters_data[player_char_name]
        player_assets = self.get_character_assets(player_char_name)
        stats = player_char_data.get("stats", {"health": 100, "speed": 10})
        moves = player_char_data.get("special_moves", {})
        self.fighter_1 = Fighter(1, 200, 310, False, player_char_data["data"], player_assets["animation_list"], player_assets["sound"], stats, moves, username=self.username)
        ai_options = [name for name in self.all_characters_data if name != player_char_name]
        ai_char_name = ai_options[0] if ai_options else player_char_name
        ai_char_data = self.all_characters_data[ai_char_name]
        ai_assets = self.get_character_assets(ai_char_name)
        ai_stats = ai_char_data.get("stats", {"health": 100, "speed": 10})
        ai_moves = ai_char_data.get("special_moves", {})
        self.fighter_2 = Fighter(2, 700, 310, True, ai_char_data["data"], ai_assets["animation_list"], ai_assets["sound"], ai_stats, ai_moves, ai=True)
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
        if new_key_code in config.FORBIDDEN_KEYS: messagebox.showwarning("No permitido", "No puedes usar W, A, S o D."); self.is_listening_for_key = False; return
        new_key_str = next((k for k, v in pygame.__dict__.items() if k.startswith('K_') and v == new_key_code), None)
        if not new_key_str: messagebox.showwarning("No válido", "Esa tecla no es compatible."); self.is_listening_for_key = False; return
        characters = load_characters(); char_moves = characters[self.char_for_remap]["special_moves"]
        if new_key_str in char_moves: messagebox.showwarning("En uso", "La tecla ya está asignada."); self.is_listening_for_key = False; return
        move_data = char_moves.pop(self.move_to_remap)
        char_moves[new_key_str] = move_data
        save_characters(characters); self.refresh_character_data()
        messagebox.showinfo("Éxito", f"Movimiento reasignado a {new_key_str.split('_')[-1].upper()}.")
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
            if not selected_char_name and selected_option not in ['Añadir Personaje', 'Volver']: messagebox.showwarning("Atención", "No hay personajes para seleccionar."); return
            if selected_option == 'Añadir Personaje': root = ctk.CTk(); root.withdraw(); CharacterForm(root, self.refresh_character_data); root.mainloop()
            elif selected_option == 'Ver Datos': char_data = self.all_characters_data.get(selected_char_name); root = ctk.CTk(); root.withdraw(); CharacterForm(root, self.refresh_character_data, char_data, selected_char_name, read_only=True); root.mainloop()
            elif selected_option == 'Editar Estadísticas': root = ctk.CTk(); root.withdraw(); StatEditForm(root, self.refresh_character_data, selected_char_name); root.mainloop()
            elif selected_option == 'Gestionar Movimientos': self.game_state = 'move_crud'; self.crud_selected_char = selected_char_name; self.move_crud_move_idx = 0
            elif selected_option == 'Eliminar Personaje':
                if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar a {selected_char_name}?"): del self.all_characters_data[selected_char_name]; save_characters(self.all_characters_data); self.refresh_character_data()
            elif selected_option == 'Volver': self.game_state = 'menu'

    def handle_move_crud_keys(self, key):
        if key == pygame.K_ESCAPE: self.game_state = 'character_crud'; return
        char_moves = self.all_characters_data.get(self.crud_selected_char, {}).get("special_moves", {})
        move_keys = list(char_moves.keys())
        if key == pygame.K_UP: self.move_crud_move_idx = (self.move_crud_move_idx - 1) % len(move_keys) if move_keys else 0
        elif key == pygame.K_DOWN: self.move_crud_move_idx = (self.move_crud_move_idx + 1) % len(move_keys) if move_keys else 0
        elif key == pygame.K_RETURN:
            if not move_keys: messagebox.showinfo("Info", "Este personaje no tiene movimientos para editar."); return
            self.is_listening_for_key = True; self.move_to_remap = move_keys[self.move_crud_move_idx]; self.char_for_remap = self.crud_selected_char

    def handle_character_select_keys(self, key):
        char_names = list(self.all_characters_data.keys());
        if not char_names: return
        if key == pygame.K_UP: self.char_select_idx = (self.char_select_idx - 1) % len(char_names)
        elif key == pygame.K_DOWN: self.char_select_idx = (self.char_select_idx + 1) % len(char_names)
        elif key == pygame.K_RETURN: self.character_class = char_names[self.char_select_idx]; users = auth.load_users(); users[self.username]['character_class'] = self.character_class; auth.save_users(users); self.game_state = 'menu'

    def handle_options_keys(self, key):
        opt = config.OPTIONS_ITEMS[self.options_idx]
        if key == pygame.K_UP: self.options_idx = (self.options_idx - 1) % len(config.OPTIONS_ITEMS)
        elif key == pygame.K_DOWN: self.options_idx = (self.options_idx + 1) % len(config.OPTIONS_ITEMS)
        elif key == pygame.K_LEFT:
            if opt == 'Resolución': self.res_index = (self.res_index - 1) % len(config.RESOLUTIONS); self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = max(0, self.music_volume - 10); self.update_volumes()
            elif opt == 'Volumen FX': self.fx_volume = max(0, self.fx_volume - 10); self.update_volumes()
        elif key == pygame.K_RIGHT:
            if opt == 'Resolución': self.res_index = (self.res_index + 1) % len(config.RESOLUTIONS); self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = min(100, self.music_volume + 10); self.update_volumes()
            elif opt == 'Volumen FX': self.fx_volume = min(100, self.fx_volume + 10); self.update_volumes()
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