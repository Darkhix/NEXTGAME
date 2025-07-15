# game.py
import pygame
import sys
import os
import json
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from datetime import date, datetime
import random
import time
import config
import ui
import auth
from auth import load_users, save_users, delete_user
from fighter import Fighter
from pygame import mixer

# ==============================================================================
# CÓDIGO DE GESTIÓN DE DATOS JSON
# ==============================================================================
def load_json_data(file_path, default_data):
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return default_data

def save_json_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

def load_characters():
    return load_json_data(config.CHARACTERS_FILE, {})

def save_characters(characters):
    save_json_data(config.CHARACTERS_FILE, characters)

def record_battle_result(winner_user, p1_char, p2_char):
    history = load_json_data("battle_history.json", [])
    new_record = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "p1_char": p1_char, "p2_char": p2_char, "winner": winner_user}
    history.insert(0, new_record)
    if len(history) > 50: history = history[:50]
    save_json_data("battle_history.json", history)

def _create_spritesheet_from_files(base_path, scale, offset):
    if not os.path.isdir(base_path):
        messagebox.showerror("Error", f"La carpeta base no existe:\n{base_path}"); return None
    all_animations, max_frame_w, max_frame_h, max_frames_per_row, animation_steps = [], 0, 0, 0, []
    animation_folder_names = ['Idle', 'Run', 'Jump', 'Fall', 'Attack', 'Take Hit', 'Death', 'Block', 'Hold Shield']
    for anim_name in animation_folder_names:
        anim_path = os.path.join(base_path, anim_name)
        current_anim_frames = []
        if os.path.isdir(anim_path):
            filenames = sorted([f for f in os.listdir(anim_path) if f.lower().endswith('.png')])
            for filename in filenames:
                try:
                    img = Image.open(os.path.join(anim_path, filename)); current_anim_frames.append(img)
                    max_frame_w = max(max_frame_w, img.width); max_frame_h = max(max_frame_h, img.height)
                except Exception as e: print(f"Advertencia: No se pudo cargar {filename}: {e}")
        all_animations.append(current_anim_frames)
        num_frames = len(current_anim_frames)
        animation_steps.append(num_frames); max_frames_per_row = max(max_frames_per_row, num_frames)
    if max_frame_w == 0: messagebox.showerror("Error", "No se encontraron imágenes válidas."); return None
    sheet_width = max_frame_w * max_frames_per_row; sheet_height = max_frame_h * len(animation_folder_names)
    final_sheet = Image.new('RGBA', (sheet_width, sheet_height))
    for y, anim_frames in enumerate(all_animations):
        for x, frame_image in enumerate(anim_frames):
            final_sheet.paste(frame_image, (x * max_frame_w, y * max_frame_h), frame_image)
    output_filename = f"{os.path.basename(os.path.normpath(base_path)).replace(' ', '_').lower()}_spritesheet.png"
    output_path = os.path.join(base_path, output_filename)
    final_sheet.save(output_path)
    return {"sprite_sheet_path": output_path.replace("\\", "/"), "data": [max_frame_w, max_frame_h, scale, offset], "animation_steps": animation_steps}

# --- INICIO: FUNCIONES PARA GESTIÓN DE MISIONES Y PERFIL ---
def load_missions_master_list():
    return load_json_data(config.MISSIONS_FILE, {})

def update_user_match_stats(username, won_match):
    users = load_users()
    if username in users:
        if 'profile_stats' not in users[username]:
            users[username]['profile_stats'] = {'play_time_seconds': 0, 'matches_played': 0, 'matches_won': 0, 'matches_lost': 0}
        stats = users[username]['profile_stats']
        stats['matches_played'] = stats.get('matches_played', 0) + 1
        if won_match: stats['matches_won'] = stats.get('matches_won', 0) + 1
        else: stats['matches_lost'] = stats.get('matches_lost', 0) + 1
        save_users(users)

def update_rank(username, lp_change):
    users = load_users()
    if username in users:
        if 'ranked_stats' not in users[username]:
            users[username]['ranked_stats'] = {'league_points': 0, 'rank': 'Bronce'}
        ranked_stats = users[username]['ranked_stats']
        current_lp = ranked_stats.get('league_points', 0)
        new_lp = max(0, current_lp + lp_change)
        ranked_stats['league_points'] = new_lp
        new_rank_name = "Bronce"
        for rank in reversed(config.RANKS):
            if new_lp >= rank['lp_required']:
                new_rank_name = rank['name']; break
        ranked_stats['rank'] = new_rank_name
        save_users(users)
        return lp_change
    return 0

def get_or_generate_daily_missions(username):
    users = load_users()
    user_data = users[username]
    today_str = date.today().isoformat()
    if user_data.get('daily_missions', {}).get('last_updated') != today_str:
        master_list = load_missions_master_list()
        available_mission_ids = list(master_list.keys())
        num_to_select = min(config.DAILY_MISSIONS_COUNT, len(available_mission_ids))
        selected_ids = random.sample(available_mission_ids, num_to_select) if available_mission_ids else []
        new_missions = []
        for mid in selected_ids:
            new_missions.append({"id": mid, "progress": 0, "completed": False, "claimed": False})
        user_data['daily_missions'] = {'last_updated': today_str, 'missions': new_missions}
        save_users(users)
    return user_data['daily_missions']

def update_mission_progress(username, event_type, **kwargs):
    users = load_users()
    user_data = users[username]
    missions = user_data.get('daily_missions', {}).get('missions', [])
    master_list = load_missions_master_list()
    for mission in missions:
        if mission['completed']: continue
        mission_info = master_list.get(mission['id'])
        if not mission_info: continue
        updated = False
        if mission_info['type'] == event_type:
            if event_type in ['play_with_char', 'win_with_char'] and mission_info.get('character') == kwargs.get('character'): updated = True
            elif event_type == 'use_specials': updated = True
            elif event_type == 'win_perfect' and kwargs.get('is_perfect', False): updated = True
            elif event_type in ['win_games', 'play_games']: updated = True
        if updated:
            if event_type == 'use_specials': mission['progress'] += kwargs.get('count', 0)
            else: mission['progress'] += 1
            if mission['progress'] >= mission_info['target']:
                mission['progress'] = mission_info['target']; mission['completed'] = True
    save_users(users)

def claim_mission_reward(username, mission_index):
    users = load_users()
    user_data = users[username]
    missions = user_data.get('daily_missions', {}).get('missions', [])
    if 0 <= mission_index < len(missions):
        mission = missions[mission_index]
        if mission['completed'] and not mission['claimed']:
            master_list = load_missions_master_list()
            mission_info = master_list.get(mission['id'])
            reward = mission_info.get('reward', 0)
            user_data['currency'] = user_data.get('currency', 0) + reward
            mission['claimed'] = True
            save_users(users)
            messagebox.showinfo("¡Recompensa!", f"Has ganado {reward} de moneda.")
        elif mission['claimed']: messagebox.showinfo("Info", "Ya has reclamado esta recompensa.")
        else: messagebox.showwarning("Info", "Aún no has completado esta misión.")
# --- FIN: FUNCIONES ---

# --- INICIO: CLASES DE FORMULARIOS ---
class CharacterForm(ctk.CTkToplevel):
    def __init__(self, master, callback, character_data=None, character_name=None, read_only=False):
        super().__init__(master)
        self.callback = callback; self.character_data = character_data; self.character_name = character_name
        self.title("Añadir Personaje" if not character_name else f"Datos de {character_name}")
        self.geometry("550x700"); self.grid_columnconfigure(1, weight=1); self.fields = {};
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.create_widgets()
        if self.character_data: self.fill_form()
        if read_only:
            for widget in self.fields.values():
                if isinstance(widget, (ctk.CTkEntry, ctk.CTkOptionMenu)): widget.configure(state="disabled")
            self.save_button.configure(state="disabled", text="Cerrar", command=self.destroy)
        if self.character_name: self.fields["asset_type"].configure(state="disabled")
        self.grab_set()

    def create_widgets(self):
        self.fields = {}; row_counter = 0
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
        set_visibility(self.label_ss, self.entry_ss, is_spritesheet); set_visibility(self.label_as, self.entry_as, is_spritesheet)
        set_visibility(self.label_w, self.entry_w, is_spritesheet); set_visibility(self.label_h, self.entry_h, is_spritesheet)
        set_visibility(self.label_bp, self.entry_bp, not is_spritesheet)

    def fill_form(self):
        self.fields["nombre"].insert(0, self.character_name)
        if "sprite_sheet_path" in self.character_data:
            self.asset_type_var.set("Spritesheet")
            self.fields["sprite_sheet_path"].insert(0, self.character_data["sprite_sheet_path"])
            self.fields["animation_steps"].insert(0, ", ".join(map(str, self.character_data.get("animation_steps", []))))
            data = self.character_data.get("data", [0, 0, 4, [0, 0]])
            self.fields["frame_w"].insert(0, str(data[0])); self.fields["frame_h"].insert(0, str(data[1]))
        elif "base_path" in self.character_data:
            self.asset_type_var.set("Archivos Individuales"); self.fields["base_path"].insert(0, self.character_data["base_path"])
        self.update_form_fields()
        self.fields["sound_path"].insert(0, self.character_data.get("sound_path", ""))
        data = self.character_data.get("data", [0, 0, 4, [0, 0]])
        self.fields["escala"].insert(0, str(data[2])); self.fields["offsetx"].insert(0, str(data[3][0])); self.fields["offsety"].insert(0, str(data[3][1]))
    
    def save(self):
        try:
            name = self.fields["nombre"].get()
            if not name: messagebox.showerror("Error", "El nombre no puede estar vacío.", parent=self); return
            characters = load_characters()
            if not self.character_name and name in characters: messagebox.showerror("Error", "Ya existe un personaje con este nombre.", parent=self); return
            new_data = {"sound_path": self.fields["sound_path"].get(), "stats": {"health": 100, "speed": 10, "damage": 10}, "special_moves": {}}
            if self.asset_type_var.get() == "Spritesheet":
                new_data["sprite_sheet_path"] = self.fields["sprite_sheet_path"].get()
                new_data["animation_steps"] = [int(s.strip()) for s in self.fields["animation_steps"].get().split(',')]
                new_data["data"] = [int(self.fields["frame_w"].get()), int(self.fields["frame_h"].get()), int(self.fields["escala"].get()), [int(self.fields["offsetx"].get()), int(self.fields["offsety"].get())]]
            else:
                conversion_result = _create_spritesheet_from_files(self.fields["base_path"].get(), int(self.fields["escala"].get()), [int(self.fields["offsetx"].get()), int(self.fields["offsety"].get())])
                if conversion_result is None: return
                new_data.update(conversion_result)
            characters[name] = new_data
            save_characters(characters)
            messagebox.showinfo("Éxito", f"Personaje '{name}' procesado y guardado.", parent=self)
            self.callback(); self.destroy()
        except ValueError: messagebox.showerror("Error de Valor", "Introduce números válidos.", parent=self)
        except Exception as e: messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}", parent=self)

class StatEditForm(ctk.CTkToplevel):
    def __init__(self, master, callback, character_name):
        super().__init__(master)
        self.callback = callback; self.character_name = character_name
        self.title(f"Editar Stats de {character_name}"); self.geometry("400x300")
        self.grid_columnconfigure(1, weight=1); self.fields = {}; self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.create_widgets(); self.fill_form(); self.grab_set()
    def create_widgets(self):
        self.character_data = load_characters()[self.character_name]
        field_map = {"health": "Vida", "damage": "Daño", "speed": "Velocidad"}
        for i, (key, label_text) in enumerate(field_map.items()):
            label = ctk.CTkLabel(self, text=label_text); label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
            entry = ctk.CTkEntry(self); entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew"); self.fields[key] = entry
        save_button = ctk.CTkButton(self, text="Guardar Stats", command=self.save); save_button.grid(row=len(field_map), columnspan=2, pady=20)
    def fill_form(self):
        stats = self.character_data.get("stats", {})
        self.fields["health"].insert(0, str(stats.get("health", 100))); self.fields["damage"].insert(0, str(stats.get("damage", 10))); self.fields["speed"].insert(0, str(stats.get("speed", 10)))
    def save(self):
        try:
            characters = load_characters()
            characters[self.character_name]["stats"] = {"health": int(self.fields["health"].get()), "damage": int(self.fields["damage"].get()), "speed": int(self.fields["speed"].get())}
            save_characters(characters); messagebox.showinfo("Éxito", f"Stats de '{self.character_name}' guardadas.", parent=self)
            self.callback(); self.destroy()
        except ValueError: messagebox.showerror("Error de Valor", "Introduce números válidos.", parent=self)

class BattleHistoryForm(ctk.CTkToplevel):
    def __init__(self, master, callback, battle_data=None, record_index=None):
        super().__init__(master)
        self.callback = callback; self.battle_data = battle_data; self.record_index = record_index
        self.title("Editar Registro" if battle_data else "Añadir Registro")
        self.geometry("400x300"); self.grid_columnconfigure(1, weight=1); self.fields = {}
        self.protocol("WM_DELETE_WINDOW", self.destroy); self.create_widgets()
        if battle_data: self.fill_form()
        self.grab_set()
    def create_widgets(self):
        row_counter = 0; field_map = {"p1_char": "Jugador 1", "p2_char": "Jugador 2", "winner": "Ganador"}
        for key, text in field_map.items():
            label = ctk.CTkLabel(self, text=text); label.grid(row=row_counter, column=0, padx=10, pady=10, sticky="w")
            entry = ctk.CTkEntry(self); entry.grid(row=row_counter, column=1, padx=10, pady=10, sticky="ew"); self.fields[key] = entry; row_counter += 1
        self.save_button = ctk.CTkButton(self, text="Guardar", command=self.save); self.save_button.grid(row=row_counter, columnspan=2, pady=20)
    def fill_form(self):
        self.fields["p1_char"].insert(0, self.battle_data.get("p1_char", "")); self.fields["p2_char"].insert(0, self.battle_data.get("p2_char", "")); self.fields["winner"].insert(0, self.battle_data.get("winner", ""))
    def save(self):
        p1 = self.fields["p1_char"].get(); p2 = self.fields["p2_char"].get(); winner = self.fields["winner"].get()
        if not all([p1, p2, winner]): messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self); return
        history = load_json_data("battle_history.json", [])
        new_record = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "p1_char": p1, "p2_char": p2, "winner": winner}
        if self.record_index is not None: history[self.record_index] = new_record
        else: history.insert(0, new_record)
        save_json_data("battle_history.json", history)
        messagebox.showinfo("Éxito", "El historial ha sido actualizado.", parent=self); self.callback(); self.destroy()

class ProfileStatEditForm(ctk.CTkToplevel):
    def __init__(self, master, callback, username):
        super().__init__(master)
        self.callback = callback; self.username = username
        self.user_data = load_users().get(username, {})
        self.title(f"Editar Perfil de {username}")
        self.geometry("400x400"); self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.destroy); self.fields = {}
        self.create_widgets(); self.fill_form(); self.grab_set()

    def create_widgets(self):
        field_map = {"play_time_seconds": "Tiempo Jugado (s)", "matches_played": "Partidas Jugadas", "matches_won": "Victorias", "matches_lost": "Derrotas"}
        for i, (key, text) in enumerate(field_map.items()):
            label = ctk.CTkLabel(self, text=text); label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
            entry = ctk.CTkEntry(self); entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew"); self.fields[key] = entry
        save_button = ctk.CTkButton(self, text="Guardar Cambios", command=self.save); save_button.grid(row=len(field_map), columnspan=2, pady=20)

    def fill_form(self):
        stats = self.user_data.get("profile_stats", {})
        for key, widget in self.fields.items():
            widget.insert(0, str(stats.get(key, 0)))

    def save(self):
        try:
            users = load_users()
            if self.username in users:
                if 'profile_stats' not in users[self.username]: users[self.username]['profile_stats'] = {}
                for key, widget in self.fields.items():
                    users[self.username]['profile_stats'][key] = int(widget.get())
                save_users(users)
                messagebox.showinfo("Éxito", "Estadísticas de perfil actualizadas.", parent=self)
                self.callback(); self.destroy()
        except ValueError: messagebox.showerror("Error", "Todos los campos deben ser números enteros.", parent=self)

class RankedStatEditForm(ctk.CTkToplevel):
    def __init__(self, master, callback, username):
        super().__init__(master)
        self.callback = callback; self.username = username
        self.user_data = load_users().get(username, {})
        self.title(f"Editar Ranked de {username}"); self.geometry("400x250"); self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.destroy); self.fields = {}
        self.create_widgets(); self.fill_form(); self.grab_set()

    def create_widgets(self):
        lp_label = ctk.CTkLabel(self, text="Puntos de Liga (LP)"); lp_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.lp_entry = ctk.CTkEntry(self); self.lp_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        rank_label = ctk.CTkLabel(self, text="Rango"); rank_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        rank_names = [r['name'] for r in config.RANKS]
        self.rank_var = ctk.StringVar()
        self.rank_menu = ctk.CTkOptionMenu(self, variable=self.rank_var, values=rank_names)
        self.rank_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        save_button = ctk.CTkButton(self, text="Guardar Cambios", command=self.save); save_button.grid(row=2, columnspan=2, pady=20)

    def fill_form(self):
        stats = self.user_data.get("ranked_stats", {})
        self.lp_entry.insert(0, str(stats.get("league_points", 0)))
        self.rank_var.set(stats.get("rank", "Bronce"))

    def save(self):
        try:
            users = load_users()
            if self.username in users:
                if 'ranked_stats' not in users[self.username]: users[self.username]['ranked_stats'] = {}
                users[self.username]['ranked_stats']['league_points'] = int(self.lp_entry.get())
                users[self.username]['ranked_stats']['rank'] = self.rank_var.get()
                save_users(users)
                messagebox.showinfo("Éxito", "Estadísticas de ranked actualizadas.", parent=self)
                self.callback(); self.destroy()
        except ValueError: messagebox.showerror("Error", "Los LP deben ser un número entero.", parent=self)

class MissionEditForm(ctk.CTkToplevel):
    def __init__(self, master, callback, mission_data=None, mission_id=None):
        super().__init__(master)
        self.callback = callback; self.mission_data = mission_data if mission_data else {}; self.mission_id = mission_id
        is_editing = mission_id is not None
        self.title("Editar Misión" if is_editing else "Añadir Nueva Misión")
        self.geometry("500x400"); self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.destroy); self.fields = {}
        self.create_widgets(); self.fill_form(); self.grab_set()

    def create_widgets(self):
        row = 0; field_map = {"id": "ID de la Misión (ej: m8)", "description": "Descripción", "type": "Tipo de Misión", "target": "Objetivo (número)", "reward": "Recompensa (número)", "character": "Personaje (opcional)"}
        for key, text in field_map.items():
            label = ctk.CTkLabel(self, text=text); label.grid(row=row, column=0, padx=10, pady=10, sticky="w")
            entry = ctk.CTkEntry(self); entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew"); self.fields[key] = entry; row += 1
        if self.mission_id: self.fields['id'].configure(state='disabled')
        save_button = ctk.CTkButton(self, text="Guardar Misión", command=self.save); save_button.grid(row=row, columnspan=2, pady=20)

    def fill_form(self):
        if self.mission_id: self.fields['id'].insert(0, self.mission_id)
        for key, widget in self.fields.items():
            if key != 'id' and key in self.mission_data: widget.insert(0, str(self.mission_data[key]))

    def save(self):
        try:
            missions = load_missions_master_list()
            mission_id = self.fields['id'].get()
            if not mission_id: messagebox.showerror("Error", "El ID de la misión no puede estar vacío.", parent=self); return
            if not self.mission_id and mission_id in missions: messagebox.showerror("Error", "Ya existe una misión con ese ID.", parent=self); return
            new_data = {"description": self.fields['description'].get(), "type": self.fields['type'].get(), "target": int(self.fields['target'].get()), "reward": int(self.fields['reward'].get())}
            if self.fields['character'].get(): new_data['character'] = self.fields['character'].get()
            missions[mission_id] = new_data
            save_json_data(config.MISSIONS_FILE, missions)
            messagebox.showinfo("Éxito", "Misión guardada correctamente.", parent=self)
            self.callback(); self.destroy()
        except ValueError: messagebox.showerror("Error", "Objetivo y Recompensa deben ser números.", parent=self)
# --- FIN: CLASES DE FORMULARIOS ---


class Game:
    def __init__(self, username, user_data):
        os.environ['SDL_VIDEO_CENTERED'] = '1'; pygame.init(); mixer.init()
        self.username, self.user_data = username, user_data
        self.all_characters_data = load_characters()
        if not self.all_characters_data: messagebox.showerror("Error", "No hay personajes."); sys.exit()
        self.character_class = user_data.get('character_class', list(self.all_characters_data.keys())[0])
        self.res_index = 0
        self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
        pygame.display.set_caption('DARKHI GAME'); self.clock = pygame.time.Clock()
        self.loaded_character_assets = {}
        self.map_thumbnails = {}
        self.load_general_assets()
        self.map_select_idx = 0
        self.selected_map_key = None
        self.music_volume, self.fx_volume = 50, 50; self.update_volumes()
        self.game_state = 'menu'
        self.menu_idx, self.ajustes_idx, self.char_select_idx, self.round_sel_idx = 0,0,0,0
        self.crud_char_idx, self.crud_opt_idx = 0,0
        self.user_crud_user_idx, self.user_crud_opt_idx = 0,0
        self.mission_crud_idx, self.mission_crud_opt_idx = 0,0
        self.move_crud_move_idx = 0
        self.crud_selected_char = None
        self.is_listening_for_key, self.move_to_remap, self.char_for_remap = False, None, None
        self.preview_fighter = None
        self.history_selected_idx = 0
        self.battle_history = []
        self.p1_char_name, self.p2_char_name = "", ""
        self.fighter_1, self.fighter_2 = None, None
        self.score, self.round_over, self.round_over_time = [0,0], False, 0
        self.intro_count, self.last_count_update = 3, 0
        self.player1_won_round = False
        self.is_ranked_match = False
        self.last_lp_change = 0
        self.leaderboard_scroll_offset = 0
        self.time_accumulator = 0
        self.time_save_interval = 30000
        self.missions_master_list = load_missions_master_list()
        self.current_daily_missions = []
        self.missions_selected_idx = 0

    def save_user_playtime(self):
        users = load_users()
        if self.username in users:
            if 'profile_stats' not in users[self.username]:
                users[self.username]['profile_stats'] = {'play_time_seconds': 0, 'matches_played': 0, 'matches_won': 0, 'matches_lost': 0}
            stats = users[self.username]['profile_stats']
            stats['play_time_seconds'] = stats.get('play_time_seconds', 0) + int(self.time_accumulator / 1000)
            save_users(users)
            self.time_accumulator = 0

    def refresh_character_data(self):
        self.all_characters_data = load_characters()
        char_count = len(self.all_characters_data)
        self.crud_char_idx = min(self.crud_char_idx, char_count - 1) if char_count > 0 else 0

    def refresh_battle_history(self):
        self.battle_history = load_json_data("battle_history.json", [])
        self.history_selected_idx = min(len(self.battle_history) - 1, self.history_selected_idx) if self.battle_history else 0
    
    def load_general_assets(self):
        self.count_font = pygame.font.Font(config.FONT_PATH, 80); self.score_font = pygame.font.Font(config.FONT_PATH, 30)
        self.menu_font = pygame.font.SysFont(None, 48); self.title_font = pygame.font.SysFont(None, 72)
        self.bg_image = pygame.image.load(config.BG_IMG_PATH).convert_alpha()
        self.victory_img = pygame.image.load(config.VICTORY_IMG_PATH).convert_alpha()
        self.defeat_img = pygame.image.load(config.DEFEAT_IMG_PATH).convert_alpha()
        for key, data in config.MAPS.items():
            try:
                self.map_thumbnails[key] = pygame.image.load(data['thumbnail']).convert_alpha()
            except (FileNotFoundError, pygame.error) as e:
                print(f"ADVERTENCIA: No se pudo cargar la miniatura para '{key}'. Error: {e}")
                placeholder = pygame.Surface((220, 165)); placeholder.fill(config.GRAY)
                self.map_thumbnails[key] = placeholder
    
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
            sprite_sheet = pygame.image.load(char_data["sprite_sheet_path"]).convert_alpha()
            animation_list = self._load_from_spritesheet(char_data, sprite_sheet)
            self.loaded_character_assets[char_name] = {"sound": sound, "animation_list": animation_list}
            return self.loaded_character_assets[char_name]
        except Exception as e: messagebox.showerror("Error de Carga", f"No se pudo cargar assets para '{char_name}'.\nError: {e}"); pygame.quit(); sys.exit()

    def _load_from_spritesheet(self, char_data, sprite_sheet):
        animation_list = []; frame_w, frame_h, image_scale = char_data["data"][0], char_data["data"][1], char_data["data"][2]
        for y, frames in enumerate(char_data.get("animation_steps", [])):
            temp_img_list = []
            for x in range(frames):
                img = sprite_sheet.subsurface(pygame.Rect(x * frame_w, y * frame_h, frame_w, frame_h))
                img = pygame.transform.scale(img, (int(frame_w * image_scale), int(frame_h * image_scale)))
                temp_img_list.append(img)
            animation_list.append(temp_img_list)
        return animation_list

    def _update_preview_fighter(self):
        char_names = list(self.all_characters_data.keys())
        if not char_names or self.char_select_idx >= len(char_names): self.preview_fighter = None; return
        selected_char_name = char_names[self.char_select_idx]
        if self.preview_fighter and self.preview_fighter.username == selected_char_name: return
        char_data = self.all_characters_data[selected_char_name]
        assets = self.get_character_assets(selected_char_name)
        stats = char_data.get("stats", {}); moves = char_data.get("special_moves", {})
        preview_x = self.screen.get_width() * 0.7 - 40; preview_y = self.screen.get_height() * 0.6 - 90
        self.preview_fighter = Fighter(0, preview_x, preview_y, True, char_data["data"], assets["animation_list"], assets["sound"], stats, moves, username=selected_char_name)

    def create_fighters(self):
        self.p1_char_name = self.character_class
        player_char_data = self.all_characters_data[self.p1_char_name]
        player_assets = self.get_character_assets(self.p1_char_name)
        stats = player_char_data.get("stats", {}); moves = player_char_data.get("special_moves", {})
        self.fighter_1 = Fighter(1, 200, 310, False, player_char_data["data"], player_assets["animation_list"], player_assets["sound"], stats, moves, username=self.username)
        ai_options = [name for name in self.all_characters_data if name != self.p1_char_name]
        self.p2_char_name = random.choice(ai_options) if ai_options else self.p1_char_name
        ai_char_data = self.all_characters_data[self.p2_char_name]
        ai_assets = self.get_character_assets(self.p2_char_name)
        ai_stats = ai_char_data.get("stats", {}); ai_moves = ai_char_data.get("special_moves", {})
        self.fighter_2 = Fighter(2, 700, 310, True, ai_char_data["data"], ai_assets["animation_list"], ai_assets["sound"], ai_stats, ai_moves, ai=True, username=self.p2_char_name)
        self.update_volumes()

    def reset_round(self):
        self.create_fighters(); self.intro_count, self.last_count_update, self.round_over = 3, pygame.time.get_ticks(), False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_user_playtime(); pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.is_listening_for_key: self.remap_move_key(event.key); continue
                
                state_handlers = {
                    'menu': self.handle_menu_keys, 'map_select': self.handle_map_select_keys,
                    'character_crud': self.handle_crud_keys, 'move_crud': self.handle_move_crud_keys,
                    'character_select': self.handle_character_select_keys, 'ajustes': self.handle_ajustes_keys,
                    'profile': self.handle_profile_keys, 'daily_missions': self.handle_missions_keys,
                    'leaderboard': self.handle_leaderboard_keys, 'user_crud': self.handle_user_crud_keys,
                    'mission_crud': self.handle_mission_crud_keys,
                    'battle_history': lambda key: self.handle_battle_history_keys(event),
                    'playing': self.handle_playing_keys if not self.round_over else self.handle_round_over_keys
                }
                handler = state_handlers.get(self.game_state)
                if handler:
                    if self.game_state == 'battle_history': handler(event)
                    else: handler(event.key)

    def handle_menu_keys(self, key):
        if key == pygame.K_UP: self.menu_idx = (self.menu_idx - 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_DOWN: self.menu_idx = (self.menu_idx + 1) % len(config.MENU_ITEMS)
        elif key == pygame.K_RETURN:
            selected = config.MENU_ITEMS[self.menu_idx]
            if selected == 'Jugar': self.is_ranked_match = False; self.game_state = 'map_select'
            elif selected == 'Clasificatoria': self.is_ranked_match = True; self.game_state = 'map_select'
            elif selected == 'Misiones Diarias':
                self.current_daily_missions = get_or_generate_daily_missions(self.username)
                self.missions_selected_idx = 0; self.game_state = 'daily_missions'
            elif selected == 'Clasificación': self.game_state = 'leaderboard'
            elif selected == 'Personaje':
                self.game_state = 'character_select'
                char_names = list(self.all_characters_data.keys())
                self.char_select_idx = char_names.index(self.character_class) if self.character_class in char_names else 0
                self._update_preview_fighter()
            elif selected == 'Administrar Personajes': self.game_state = 'character_crud'; self.crud_char_idx = 0; self.crud_opt_idx = 0
            elif selected == 'Gestionar Usuarios': self.game_state = 'user_crud'; self.user_crud_user_idx = 0; self.user_crud_opt_idx = 0
            elif selected == 'Gestionar Misiones':
                self.game_state = 'mission_crud'
                self.missions_master_list = load_missions_master_list()
                self.mission_crud_idx = 0; self.mission_crud_opt_idx = 0
            elif selected == 'Historial de Batallas': self.game_state = 'battle_history'; self.refresh_battle_history()
            elif selected == 'Ajustes': self.game_state = 'ajustes'; self.ajustes_idx = 0
            elif selected == 'Salir': self.save_user_playtime(); pygame.quit(); sys.exit()

    def handle_map_select_keys(self, key):
        map_keys = list(config.MAPS.keys())
        if not map_keys: self.game_state = 'menu'; return
        num_maps = len(map_keys)
        if key == pygame.K_RIGHT: self.map_select_idx = (self.map_select_idx + 1) % num_maps
        elif key == pygame.K_LEFT: self.map_select_idx = (self.map_select_idx - 1) % num_maps
        elif key == pygame.K_ESCAPE: self.game_state = 'menu'
        elif key == pygame.K_RETURN:
            self.selected_map_key = map_keys[self.map_select_idx]
            map_path = config.MAPS[self.selected_map_key]['background']
            try:
                self.bg_image = pygame.image.load(map_path).convert_alpha()
            except (FileNotFoundError, pygame.error) as e:
                print(f"ADVERTENCIA: No se pudo cargar fondo: {e}")
                self.bg_image = pygame.image.load(config.BG_IMG_PATH).convert_alpha()
            self.reset_round()
            self.game_state = 'playing'

    def handle_crud_keys(self, key):
        char_names = list(self.all_characters_data.keys())
        selected_option = config.CRUD_MENU_ITEMS[self.crud_opt_idx]
        if not char_names and selected_option not in ['Añadir Personaje', 'Volver']:
            messagebox.showwarning("Atención", "No hay personajes para seleccionar.")
            return

        if key == pygame.K_UP: self.crud_char_idx = (self.crud_char_idx - 1) % len(char_names) if char_names else 0
        elif key == pygame.K_DOWN: self.crud_char_idx = (self.crud_char_idx + 1) % len(char_names) if char_names else 0
        elif key == pygame.K_RIGHT: self.crud_opt_idx = (self.crud_opt_idx + 1) % len(config.CRUD_MENU_ITEMS)
        elif key == pygame.K_LEFT: self.crud_opt_idx = (self.crud_opt_idx - 1) % len(config.CRUD_MENU_ITEMS)
        elif key == pygame.K_RETURN:
            selected_char_name = char_names[self.crud_char_idx] if char_names else None
            root = ctk.CTk(); root.withdraw()
            form_to_open = None
            if selected_option == 'Añadir Personaje': form_to_open = CharacterForm(root, self.refresh_character_data)
            elif selected_char_name:
                if selected_option == 'Ver Datos': form_to_open = CharacterForm(root, self.refresh_character_data, self.all_characters_data.get(selected_char_name), selected_char_name, read_only=True)
                elif selected_option == 'Editar Estadísticas': form_to_open = StatEditForm(root, self.refresh_character_data, selected_char_name)
            
            if form_to_open: root.wait_window(form_to_open)
            
            elif selected_option == 'Gestionar Movimientos' and selected_char_name:
                self.game_state = 'move_crud'; self.crud_selected_char = selected_char_name; self.move_crud_move_idx = 0
            elif selected_option == 'Eliminar Personaje' and selected_char_name:
                if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar a {selected_char_name}?"):
                    del self.all_characters_data[selected_char_name]
                    save_characters(self.all_characters_data); self.refresh_character_data()
            elif selected_option == 'Volver': self.game_state = 'menu'
            root.destroy()

    def handle_move_crud_keys(self, key):
        if key == pygame.K_ESCAPE: self.game_state = 'character_crud'; return
        char_moves = self.all_characters_data.get(self.crud_selected_char, {}).get("special_moves", {})
        move_keys = list(char_moves.keys())
        if key == pygame.K_UP: self.move_crud_move_idx = (self.move_crud_move_idx - 1) % len(move_keys) if move_keys else 0
        elif key == pygame.K_DOWN: self.move_crud_move_idx = (self.move_crud_move_idx + 1) % len(move_keys) if move_keys else 0
        elif key == pygame.K_RETURN:
            if not move_keys: messagebox.showinfo("Info", "Este personaje no tiene movimientos para editar."); return
            self.is_listening_for_key = True; self.move_to_remap = move_keys[self.move_crud_move_idx]; self.char_for_remap = self.crud_selected_char

    def handle_user_crud_keys(self, key):
        user_names = list(load_users().keys())
        if not user_names: self.game_state = 'menu'; return

        if key == pygame.K_UP: self.user_crud_user_idx = (self.user_crud_user_idx - 1) % len(user_names)
        elif key == pygame.K_DOWN: self.user_crud_user_idx = (self.user_crud_user_idx + 1) % len(user_names)
        elif key == pygame.K_RIGHT: self.user_crud_opt_idx = (self.user_crud_opt_idx + 1) % len(config.USER_CRUD_ITEMS)
        elif key == pygame.K_LEFT: self.user_crud_opt_idx = (self.user_crud_opt_idx - 1) % len(config.USER_CRUD_ITEMS)
        elif key == pygame.K_ESCAPE: self.game_state = 'menu'
        elif key == pygame.K_RETURN:
            selected_user = user_names[self.user_crud_user_idx]
            selected_action = config.USER_CRUD_ITEMS[self.user_crud_opt_idx]
            
            if selected_action == 'Editar Perfil':
                root = ctk.CTk(); root.withdraw()
                form = ProfileStatEditForm(root, lambda: None, selected_user)
                root.wait_window(form); root.destroy()
            elif selected_action == 'Resetear Perfil':
                if messagebox.askyesno("Confirmar", f"¿Resetear estadísticas de perfil de {selected_user}?"):
                    users = load_users(); users[selected_user]['profile_stats'] = {'play_time_seconds': 0, 'matches_played': 0, 'matches_won': 0, 'matches_lost': 0}
                    save_users(users); messagebox.showinfo("Éxito", "Estadísticas de perfil reseteadas.")
            elif selected_action == 'Editar Ranked':
                root = ctk.CTk(); root.withdraw()
                form = RankedStatEditForm(root, lambda: None, selected_user)
                root.wait_window(form); root.destroy()
            elif selected_action == 'Resetear Ranked':
                if messagebox.askyesno("Confirmar", f"¿Resetear estadísticas de ranked de {selected_user}?"):
                    users = load_users(); users[selected_user]['ranked_stats'] = {'league_points': 0, 'rank': 'Bronce'}
                    save_users(users); messagebox.showinfo("Éxito", "Estadísticas de ranked reseteadas.")
            elif selected_action == 'Volver': self.game_state = 'menu'
    
    def handle_mission_crud_keys(self, key):
        missions = list(self.missions_master_list.keys())
        if not missions: self.mission_crud_idx = 0
        
        if key == pygame.K_UP: self.mission_crud_idx = (self.mission_crud_idx - 1) % len(missions) if missions else 0
        elif key == pygame.K_DOWN: self.mission_crud_idx = (self.mission_crud_idx + 1) % len(missions) if missions else 0
        elif key == pygame.K_RIGHT: self.mission_crud_opt_idx = (self.mission_crud_opt_idx + 1) % len(config.MISSION_CRUD_ITEMS)
        elif key == pygame.K_LEFT: self.mission_crud_opt_idx = (self.mission_crud_opt_idx - 1) % len(config.MISSION_CRUD_ITEMS)
        elif key == pygame.K_ESCAPE: self.game_state = 'menu'
        elif key == pygame.K_RETURN:
            selected_action = config.MISSION_CRUD_ITEMS[self.mission_crud_opt_idx]
            
            if selected_action == 'Añadir Misión':
                root = ctk.CTk(); root.withdraw()
                form = MissionEditForm(root, lambda: setattr(self, 'missions_master_list', load_missions_master_list()))
                root.wait_window(form); root.destroy()
            
            elif selected_action in ['Editar Misión', 'Eliminar Misión'] and missions:
                selected_mission_id = missions[self.mission_crud_idx]
                
                if selected_action == 'Editar Misión':
                    root = ctk.CTk(); root.withdraw()
                    form = MissionEditForm(root, lambda: setattr(self, 'missions_master_list', load_missions_master_list()), self.missions_master_list[selected_mission_id], selected_mission_id)
                    root.wait_window(form); root.destroy()
                
                elif selected_action == 'Eliminar Misión':
                    if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar la misión '{selected_mission_id}'?"):
                        del self.missions_master_list[selected_mission_id]
                        save_json_data(config.MISSIONS_FILE, self.missions_master_list)
                        self.mission_crud_idx = min(self.mission_crud_idx, len(self.missions_master_list) - 1) if self.missions_master_list else 0
            
            elif selected_action == 'Volver':
                self.game_state = 'menu'

    def handle_ajustes_keys(self, key):
        if key == pygame.K_UP: self.ajustes_idx = (self.ajustes_idx - 1) % len(config.AJUSTES_ITEMS)
        elif key == pygame.K_DOWN: self.ajustes_idx = (self.ajustes_idx + 1) % len(config.AJUSTES_ITEMS)
        opt = config.AJUSTES_ITEMS[self.ajustes_idx]
        if key == pygame.K_LEFT:
            if opt == 'Resolución': self.res_index = (self.res_index - 1) % len(config.RESOLUTIONS); self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = max(0, self.music_volume - 10); self.update_volumes()
            elif opt == 'Volumen FX': self.fx_volume = max(0, self.fx_volume - 10); self.update_volumes()
        elif key == pygame.K_RIGHT:
            if opt == 'Resolución': self.res_index = (self.res_index + 1) % len(config.RESOLUTIONS); self.screen = pygame.display.set_mode(config.RESOLUTIONS[self.res_index], pygame.RESIZABLE)
            elif opt == 'Volumen Música': self.music_volume = min(100, self.music_volume + 10); self.update_volumes()
            elif opt == 'Volumen FX': self.fx_volume = min(100, self.fx_volume + 10); self.update_volumes()
        elif key == pygame.K_RETURN:
            if opt == 'Ver Perfil': self.game_state = 'profile'
            elif opt == 'Eliminar Cuenta':
                self.save_user_playtime()
                if messagebox.askyesno('Confirmar', '¿Seguro?'):
                    delete_user(self.username); pygame.quit(); sys.exit()
            elif opt == 'Volver': self.game_state = 'menu'

    def handle_profile_keys(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_RETURN:
            self.game_state = 'ajustes'

    def handle_character_select_keys(self, key):
        char_names = list(self.all_characters_data.keys())
        if not char_names: return
        if key == pygame.K_UP: self.char_select_idx = (self.char_select_idx - 1) % len(char_names); self._update_preview_fighter()
        elif key == pygame.K_DOWN: self.char_select_idx = (self.char_select_idx + 1) % len(char_names); self._update_preview_fighter()
        elif key == pygame.K_RETURN:
            self.character_class = char_names[self.char_select_idx]
            users = load_users(); users[self.username]['character_class'] = self.character_class; save_users(users)
            self.game_state = 'menu'; self.preview_fighter = None

    def handle_missions_keys(self, key):
        if key == pygame.K_ESCAPE: self.game_state = 'menu'
        elif key == pygame.K_UP and self.current_daily_missions.get('missions'):
            self.missions_selected_idx = (self.missions_selected_idx - 1) % len(self.current_daily_missions['missions'])
        elif key == pygame.K_DOWN and self.current_daily_missions.get('missions'):
            self.missions_selected_idx = (self.missions_selected_idx + 1) % len(self.current_daily_missions['missions'])
        elif key == pygame.K_RETURN:
            claim_mission_reward(self.username, self.missions_selected_idx)
            self.current_daily_missions = get_or_generate_daily_missions(self.username)
            
    def handle_round_over_keys(self, key):
        if key == pygame.K_UP: self.round_sel_idx = (self.round_sel_idx - 1) % len(config.ROUND_OPTIONS)
        elif key == pygame.K_DOWN: self.round_sel_idx = (self.round_sel_idx + 1) % len(config.ROUND_OPTIONS)
        elif key == pygame.K_RETURN:
            self.last_lp_change = 0
            if config.ROUND_OPTIONS[self.round_sel_idx] == 'Reintentar':
                if self.is_ranked_match: self.game_state = 'menu'
                else: self.reset_round()
            else: self.game_state = 'menu'

    def handle_leaderboard_keys(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_RETURN:
            self.game_state = 'menu'

    def handle_battle_history_keys(self, event):
        key = event.key; mods = pygame.key.get_mods()
        if key == pygame.K_ESCAPE: self.game_state = 'menu'
        elif key == pygame.K_UP and self.battle_history: self.history_selected_idx = max(0, self.history_selected_idx - 1)
        elif key == pygame.K_DOWN and self.battle_history: self.history_selected_idx = min(len(self.battle_history) - 1, self.history_selected_idx + 1)
        elif key == pygame.K_a or (key == pygame.K_e and self.battle_history):
            root = ctk.CTk(); root.withdraw()
            form_to_open = None
            if key == pygame.K_a: form_to_open = BattleHistoryForm(root, self.refresh_battle_history)
            elif key == pygame.K_e:
                selected_record = self.battle_history[self.history_selected_idx]
                form_to_open = BattleHistoryForm(root, self.refresh_battle_history, battle_data=selected_record, record_index=self.history_selected_idx)
            if form_to_open: root.wait_window(form_to_open)
            root.destroy()
        elif key == pygame.K_DELETE and self.battle_history:
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar este registro?"):
                self.battle_history.pop(self.history_selected_idx)
                save_json_data("battle_history.json", self.battle_history)
                self.history_selected_idx = min(len(self.battle_history) - 1, self.history_selected_idx) if self.battle_history else 0
        elif key == pygame.K_d and (mods & pygame.KMOD_LSHIFT or mods & pygame.KMOD_RSHIFT):
            if self.battle_history and messagebox.askyesno("Confirmar Borrado Total", "ADVERTENCIA: ¿ESTÁS SEGURO?\nEsto borrará TODO el historial."):
                self.battle_history = []; save_json_data("battle_history.json", self.battle_history); self.history_selected_idx = 0

    def handle_playing_keys(self, key):
        if key == pygame.K_w: self.fighter_1.jump()
        for move_key_str in self.fighter_1.special_moves:
            if hasattr(pygame, move_key_str) and key == getattr(pygame, move_key_str):
                self.fighter_1.attack(self.fighter_2, move_key_str); break

    def draw_scenes(self):
        state_draw_functions = {
            'menu': lambda: ui.draw_menu(self.screen, self.menu_font, config.MENU_ITEMS, self.menu_idx),
            'map_select': lambda: ui.draw_map_select(self.screen, self.title_font, self.menu_font, config.MAPS, self.map_thumbnails, self.map_select_idx),
            'character_crud': lambda: ui.draw_character_crud(self.screen, self.bg_image, self.menu_font, self.title_font, list(self.all_characters_data.keys()), config.CRUD_MENU_ITEMS, self.crud_char_idx, self.crud_opt_idx),
            'move_crud': lambda: ui.draw_move_crud(self.screen, self.bg_image, self.menu_font, self.title_font, self.crud_selected_char, self.all_characters_data.get(self.crud_selected_char, {}).get("special_moves", {}), self.move_crud_move_idx, self.is_listening_for_key),
            'character_select': self.draw_character_select_scene,
            'ajustes': lambda: ui.draw_ajustes(self.screen, self.menu_font, config.AJUSTES_ITEMS, self.ajustes_idx, {'Resolución': f"{config.RESOLUTIONS[self.res_index][0]}x{config.RESOLUTIONS[self.res_index][1]}", 'Volumen Música': str(self.music_volume), 'Volumen FX': str(self.fx_volume)}),
            'profile': self.draw_profile_scene,
            'daily_missions': self.draw_missions_scene,
            'leaderboard': self.draw_leaderboard_scene,
            'user_crud': self.draw_user_crud_scene,
            'battle_history': lambda: ui.draw_battle_history(self.screen, self.bg_image, self.score_font, self.title_font, self.battle_history, self.history_selected_idx),
            'playing': self.run_game_logic
        }
        draw_func = state_draw_functions.get(self.game_state)
        if draw_func: draw_func()

    def draw_character_select_scene(self):
        if self.preview_fighter: self.preview_fighter.update()
        ui.draw_character_select(self.screen, self.bg_image, self.menu_font, self.title_font, list(self.all_characters_data.keys()), self.char_select_idx, self.preview_fighter)
    
    def draw_profile_scene(self):
        current_user_data = load_users().get(self.username, {})
        profile_stats = current_user_data.get('profile_stats', {})
        saved_seconds = profile_stats.get('play_time_seconds', 0)
        live_seconds = saved_seconds + int(self.time_accumulator / 1000)
        hours, rem = divmod(live_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        play_time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        char_name = current_user_data.get('character_class')
        char_image = None
        if char_name in self.all_characters_data:
            assets = self.get_character_assets(char_name)
            if assets['animation_list'] and assets['animation_list'][0]:
                char_image = assets['animation_list'][0][0]
        ui.draw_bg(self.screen, self.bg_image)
        ui.draw_profile_screen(self.screen, self.title_font, self.menu_font, self.username, profile_stats, play_time_str, char_image)

    def draw_missions_scene(self):
        missions_with_details = []
        for m_progress in self.current_daily_missions.get('missions', []):
            m_info = self.missions_master_list.get(m_progress['id'])
            if m_info: missions_with_details.append({'info': m_info, 'progress': m_progress})
        user_currency = load_users()[self.username].get('currency', 0)
        ui.draw_daily_missions(self.screen, self.bg_image, self.menu_font, self.title_font, missions_with_details, self.missions_selected_idx, user_currency)

    def draw_leaderboard_scene(self):
        all_users = load_users()
        ranked_players = []
        for name, data in all_users.items():
            if "ranked_stats" in data:
                ranked_players.append({"name": name, "lp": data["ranked_stats"].get("league_points", 0), "rank": data["ranked_stats"].get("rank", "Bronce")})
        sorted_players = sorted(ranked_players, key=lambda p: p['lp'], reverse=True)
        ui.draw_leaderboard(self.screen, self.title_font, self.menu_font, sorted_players)

    def draw_user_crud_scene(self):
        user_names = list(load_users().keys())
        ui.draw_user_crud_screen(self.screen, self.bg_image, self.menu_font, self.title_font, user_names, self.user_crud_user_idx, self.user_crud_opt_idx)

    def run_game_logic(self):
        ui.draw_bg(self.screen, self.bg_image)
        ui.draw_health_bar(self.screen, self.fighter_1.health, 20, 20)
        ui.draw_health_bar(self.screen, self.fighter_2.health, self.screen.get_width() - 420, 20)
        ui.draw_text(self.screen, f'{self.fighter_1.username}: {self.score[0]}', self.score_font, config.RED, 20, 60)
        ui.draw_text(self.screen, f'{self.fighter_2.username}: {self.score[1]}', self.score_font, config.RED, self.screen.get_width() - 200, 60)
        if self.intro_count <= 0:
            self.fighter_1.move(self.screen.get_width(), self.screen.get_height(), self.fighter_2, self.round_over)
            self.fighter_2.move(self.screen.get_width(), self.screen.get_height(), self.fighter_1, self.round_over)
        else:
            ui.draw_text(self.screen, str(self.intro_count), self.count_font, config.RED, self.screen.get_width() / 2 - 20, self.screen.get_height() / 3)
            if pygame.time.get_ticks() - self.last_count_update >= 1000:
                self.intro_count -= 1; self.last_count_update = pygame.time.get_ticks()
        self.fighter_1.update(); self.fighter_2.update()
        self.fighter_1.draw(self.screen); self.fighter_2.draw(self.screen)
        if not self.round_over:
            winner, loser = None, None
            if not self.fighter_1.alive: winner, loser = self.fighter_2, self.fighter_1
            elif not self.fighter_2.alive: winner, loser = self.fighter_1, self.fighter_2
            if winner:
                self.round_over = True; self.round_over_time = pygame.time.get_ticks()
                self.player1_won_round = (winner.player == 1)
                if self.player1_won_round: self.score[0] += 1
                else: self.score[1] += 1
                record_battle_result(winner.username, self.p1_char_name, self.p2_char_name)
                if self.is_ranked_match:
                    self.last_lp_change = update_rank(self.username, config.LP_WIN if self.player1_won_round else config.LP_LOSS)
                update_user_match_stats(self.username, won_match=self.player1_won_round)
                update_mission_progress(self.username, 'play_games')
                update_mission_progress(self.username, 'play_with_char', character=self.fighter_1.username)
                update_mission_progress(self.username, 'use_specials', count=self.fighter_1.specials_used_in_match)
                if self.player1_won_round:
                    is_perfect = loser.health == 0 and winner.health == winner.base_health
                    update_mission_progress(self.username, 'win_games')
                    update_mission_progress(self.username, 'win_with_char', character=self.fighter_1.username)
                    update_mission_progress(self.username, 'win_perfect', is_perfect=is_perfect)
        else:
            if pygame.time.get_ticks() - self.round_over_time > config.ROUND_COOLDOWN:
                image_to_show = self.victory_img if self.player1_won_round else self.defeat_img
                ui.draw_round_over_menu(self.screen, self.menu_font, config.ROUND_OPTIONS, self.round_sel_idx, image_to_show, self.last_lp_change)
    
    def run(self):
        self.play_music(config.MUSIC_PATH)
        while True:
            time_passed_ms = self.clock.tick(config.FPS)
            self.time_accumulator += time_passed_ms
            if self.time_accumulator >= self.time_save_interval:
                self.save_user_playtime()
            self.handle_events()
            self.draw_scenes()
            pygame.display.update()