# auth.py
import os
import json
import customtkinter as ctk
from tkinter import messagebox
import config
from PIL import Image, ImageTk
import threading
import cv2
import time

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

def load_users():
    if os.path.exists(config.USERS_FILE):
        with open(config.USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(config.USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# --- NUEVA FUNCIÓN register_user ---
def register_user(username, correo, password, character_class):
    users = load_users()
    if username in users:
        return 'exists'
    if '@' not in correo:
        return 'invalid_email'
    
    nombre_email, dominio = correo.split('@', 1)

    if ' ' in nombre_email:
        return 'no_espacios'
    
    if not nombre_email.strip():
        return 'campo_vacio'
    elif len(nombre_email) < 6: 
        return 'nombre_usuario_corto'
    
    dominio_completo = f"@{dominio}"
    if not any(dominio_completo == dominio_valido for dominio_valido in config.VALID_DOMAINS):
        return 'invalid_email'
    
    for c in nombre_email:
        if not (c.isalnum() or c in '._-,#'):
            return 'campo_invalido'

    alfanumericos = sum(c.isalnum() for c in nombre_email)
    if alfanumericos < 4:
        return 'campo_invalido'

    for i in range(len(nombre_email) - 1):
        if nombre_email[i] in '._-,#' and nombre_email[i+1] in '._-,#':
            return 'mucho_caracteres_especiales'

    if ' ' in password:
        return 'no_espacios'
    if len(password) < 6:
        return 'contraseña_corta'
    if len(password) > 8:
        return 'contraseña_larga'
        
    for c in password:
        if not (c.isalnum() or c in '._-,#'):
            return 'campo_invalido'

    alfanumericos_pass = sum(c.isalnum() for c in password)
    if alfanumericos_pass < 4:
        return 'campo_invalido'

    for i in range(len(password) - 1):
        if password[i] in '._-,#' and password[i+1] in '._-,#':
            return 'mucho_caracteres_especiales'

    users[username] = {
        'password': password,
        'correo': correo,
        'character_class': character_class,
        'stats': {'health': 100, 'attacks_done': 0, 'is_alive': True}
    }
    save_users(users)
    return 'ok'

def login_user(username, password):
    users = load_users()
    return username in users and users[username]['password'] == password

def get_user(username):
    users = load_users()
    return users.get(username)

def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return True
    return False

class AuthUI:
    def __init__(self):
        self.current_user = None
        self.root = None
        self.is_running = True

    def video_stream(self, video_label):
        video_path = "assets/videos/login_bg.mp4"
        if not os.path.exists(video_path):
            print(f"Video no encontrado en {video_path}")
            return
        cap = cv2.VideoCapture(video_path)
        while self.is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.configure(image=imgtk)
            video_label.imgtk = imgtk
            time.sleep(0.033)
        cap.release()

    def on_closing(self):
        self.is_running = False
        time.sleep(0.1)
        if self.root:
            self.root.destroy()

    def start_login(self):
        self.iniciar_auth_screen()
        return self.current_user

    def iniciar_auth_screen(self):
        self.root = ctk.CTk()
        self.root.title('DARKHI GAME')
        self.root.geometry('1280x720')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(False, False)

        side_panel = ctk.CTkFrame(self.root, fg_color=("#1C1C1C", "#1C1C1C"), corner_radius=0, width=420)
        side_panel.pack(side="left", fill="y")
        side_panel.pack_propagate(False)

        video_label = ctk.CTkLabel(self.root, text="")
        video_label.pack(side="left", fill="both", expand=True)

        video_thread = threading.Thread(target=self.video_stream, args=(video_label,), daemon=True)
        video_thread.start()

        login_frame = ctk.CTkFrame(side_panel, fg_color="transparent")
        
        login_widget_container = ctk.CTkFrame(login_frame, fg_color="transparent")
        login_widget_container.place(relx=0.5, rely=0.5, anchor="c")
        
        ctk.CTkLabel(login_widget_container, text='BIENVENIDO', font=ctk.CTkFont(family="Arial", size=32, weight="bold")).pack(pady=(20, 50), padx=20)
        login_user_entry = ctk.CTkEntry(login_widget_container, placeholder_text="Nombre de Usuario", width=300, height=45, font=ctk.CTkFont(size=14))
        login_user_entry.pack(pady=10, padx=40)
        login_pass_entry = ctk.CTkEntry(login_widget_container, placeholder_text="Contraseña", show='*', width=300, height=45, font=ctk.CTkFont(size=14))
        login_pass_entry.pack(pady=10, padx=40)
        ctk.CTkButton(login_widget_container, text='INICIAR SESIÓN', command=lambda: validar_login(), width=300, height=50, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(40, 10), padx=40)
        ctk.CTkButton(login_widget_container, text='Crear una cuenta', command=lambda: switch_view('register'), fg_color="transparent", text_color=("gray70", "gray60"), hover_color=("#2B2B2B", "#2B2B2B")).pack(pady=10, padx=40)

        register_frame = ctk.CTkFrame(side_panel, fg_color="transparent")

        ctk.CTkLabel(register_frame, text='CREAR CUENTA', font=ctk.CTkFont(family="Arial", size=32, weight="bold")).pack(pady=(40, 30))
        reg_user_entry = ctk.CTkEntry(register_frame, placeholder_text="Nombre de usuario", width=300, height=40)
        reg_user_entry.pack(pady=5, padx=40)
        reg_correo_entry = ctk.CTkEntry(register_frame, placeholder_text="Correo electrónico", width=300, height=40)
        reg_correo_entry.pack(pady=5, padx=40)
        reg_pass_entry = ctk.CTkEntry(register_frame, placeholder_text="Contraseña", show='*', width=300, height=40)
        reg_pass_entry.pack(pady=5, padx=40)
        reg_confirm_entry = ctk.CTkEntry(register_frame, placeholder_text="Confirmar contraseña", show='*', width=300, height=40)
        reg_confirm_entry.pack(pady=5, padx=40)
        
        ctk.CTkLabel(register_frame, text='Selecciona tu personaje').pack(pady=(15, 5))
        character_var = ctk.StringVar(value=None)
        
        try:
            from game import load_characters
            available_characters = load_characters()
            for char_name in available_characters:
                ctk.CTkRadioButton(register_frame, text=char_name, variable=character_var, value=char_name).pack(anchor='w', padx=100, pady=2)
        except (FileNotFoundError, ImportError):
            ctk.CTkLabel(register_frame, text="Error: No se encontró characters.json").pack()

        ctk.CTkButton(register_frame, text='Registrarse', command=lambda: registrar(), width=300, height=45).pack(pady=(20, 5), padx=40)
        ctk.CTkButton(register_frame, text='Volver al inicio de sesión', command=lambda: switch_view('login'), fg_color="transparent", text_color=("gray70", "gray60"), hover_color=("#2B2B2B", "#2B2B2B")).pack(pady=5, padx=40)

        def switch_view(view):
            if view == 'register':
                login_frame.pack_forget()
                register_frame.pack(expand=True, fill="both")
            else:
                register_frame.pack_forget()
                login_frame.pack(expand=True, fill="both")

        def validar_login():
            if login_user(login_user_entry.get(), login_pass_entry.get()):
                self.current_user = login_user_entry.get()
                self.on_closing()
            else:
                messagebox.showerror('Error', 'Usuario o contraseña incorrectos.', parent=self.root)
        
        def registrar():
            username, correo = reg_user_entry.get(), reg_correo_entry.get()
            password, confirm = reg_pass_entry.get(), reg_confirm_entry.get()
            char_class = character_var.get()

            if not all([username, correo, password, confirm, char_class]):
                messagebox.showerror('Error', 'Completa todos los campos.', parent=self.root)
                return
            if password != confirm:
                messagebox.showerror('Error', 'Las contraseñas no coinciden.', parent=self.root)
                return

            # --- NUEVO BLOQUE DE MANEJO DE ERRORES ---
            resultado = register_user(username, correo, password, char_class)
            if resultado == 'exists':
                messagebox.showerror('Error', 'Ese nombre de usuario ya existe.', parent=self.root)
            elif resultado == 'campo_vacio':
                messagebox.showerror('Error', 'El campo de correo electrónico no puede estar vacío.', parent=self.root)
            elif resultado == 'mucho_caracteres_especiales':
                messagebox.showerror('Error', 'El campo contiene demasiados caracteres especiales consecutivos.', parent=self.root)
            elif resultado == 'campo_invalido':
                messagebox.showerror('Error', 'El campo debe contener al menos 4 letras o números.', parent=self.root)
            elif resultado == 'contraseña_corta':
                messagebox.showerror('Error', 'La contraseña debe tener al menos 6 caracteres.', parent=self.root)
            elif resultado == 'contraseña_larga':
                messagebox.showerror('Error', 'La contraseña no puede tener más de 8 caracteres.', parent=self.root)
            elif resultado == 'no_espacios':
                messagebox.showerror('Error', 'No puede contener espacios.', parent=self.root)
            elif resultado == 'nombre_usuario_corto':
                messagebox.showerror('Error', 'El nombre en el correo electrónico debe tener al menos 6 caracteres.', parent=self.root)
            elif resultado == 'invalid_email':
                messagebox.showerror('Error', 'Correo inválido. Solo dominios permitidos.', parent=self.root)
            elif resultado == 'ok':
                messagebox.showinfo('Éxito', 'Registro exitoso. Ahora puedes iniciar sesión.', parent=self.root)
                switch_view('login') # Vuelve a la vista de login

        switch_view('login')
        self.root.mainloop()