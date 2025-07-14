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

def update_user_character(username, new_character_class):
    users = load_users()
    if username in users:
        users[username]['character_class'] = new_character_class
        save_users(users)
        return True
    return False

def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return True
    return False

def validate_login_field(field_name, field_value, is_email=False):
    if not field_value.strip():
        return 'campo_vacio'

    if ' ' in field_value:
        return 'no_espacios'

    if is_email:
        if '@' not in field_value:
            return 'invalid_email'
        
        nombre_email, dominio = field_value.split('@', 1)

        if not nombre_email.strip():
            return 'campo_vacio'
        elif len(nombre_email) < 6:
            return 'nombre_usuario_corto'
        
        dominio_completo = f"@{dominio}"
        if not any(dominio_completo == dominio_valido for dominio_valido in config.VALID_DOMAINS):
            return 'invalid_email'
    
    for c in field_value:
        if not (c.isalnum() or c in '._-,#'):
            return 'campo_invalido'

    alfanumericos = sum(c.isalnum() for c in field_value)
    if alfanumericos < 4:
        return 'campo_invalido'

    for i in range(len(field_value) - 1):
        if field_value[i] in '._-,#' and field_value[i+1] in '._-,#':
            return 'mucho_caracteres_especiales'
    
    return 'ok'

class AuthUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title('DARKHI GAME')
        self.root.geometry('1280x720')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(False, False)

        self.cap = None
        self.current_frame = None
        self.stop_video_thread = False
        self.video_thread = None

        side_panel = ctk.CTkFrame(self.root, fg_color=("#1C1C1C", "#1C1C1C"), corner_radius=0, width=420)
        side_panel.pack(side="left", fill="y")
        side_panel.pack_propagate(False)

        logo_image = ctk.CTkImage(Image.open("assets/images/icons/darkhi_logo.png"), size=(200, 200))
        ctk.CTkLabel(side_panel, image=logo_image, text="").pack(pady=(50, 20))

        self.video_label = ctk.CTkLabel(self.root, text="")
        self.video_label.pack(side="right", fill="both", expand=True)

        self.content_frame = ctk.CTkFrame(side_panel, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.views = {}
        self.current_view_frame = None
        self.create_login_view()
        self.create_register_view()
        self.create_delete_account_view()

        self.switch_view('login')

    def start_video(self):
        self.cap = cv2.VideoCapture("assets/video/Login_Background.mp4")
        if not self.cap.isOpened():
            print("Error: No se pudo abrir el archivo de video.")
            return

        self.stop_video_thread = False
        self.video_thread = threading.Thread(target=self.play_video)
        self.video_thread.daemon = True
        self.video_thread.start()

    def play_video(self):
        while not self.stop_video_thread:
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)

            self.video_label.configure(image=img_tk)
            self.video_label.image = img_tk
            time.sleep(0.01)

    def stop_video(self):
        self.stop_video_thread = True
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join()
        if self.cap:
            self.cap.release()
        self.video_label.configure(image=None)

    def on_closing(self):
        self.stop_video()
        self.root.destroy()

    def switch_view(self, view_name):
        if self.current_view_frame:
            self.current_view_frame.pack_forget()
        self.current_view_frame = self.views[view_name]
        self.current_view_frame.pack(fill="both", expand=True)

    def create_login_view(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views['login'] = frame

        ctk.CTkLabel(frame, text="INICIAR SESIÓN", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 30))

        self.username_entry = ctk.CTkEntry(frame, placeholder_text="Nombre de Usuario", width=300, height=40)
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*", width=300, height=40)
        self.password_entry.pack(pady=10)

        ctk.CTkButton(frame, text="Entrar", command=self._login, width=300, height=40).pack(pady=20)
        ctk.CTkButton(frame, text="Registrarse", command=lambda: self.switch_view('register'), width=300, height=40, fg_color="gray", hover_color="dimgray").pack(pady=5)

    def create_register_view(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views['register'] = frame

        ctk.CTkLabel(frame, text="REGISTRARSE", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 30))

        self.reg_username_entry = ctk.CTkEntry(frame, placeholder_text="Nombre de Usuario", width=300, height=40)
        self.reg_username_entry.pack(pady=10)
        self.reg_email_entry = ctk.CTkEntry(frame, placeholder_text="Correo Electrónico", width=300, height=40)
        self.reg_email_entry.pack(pady=10)
        self.reg_password_entry = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*", width=300, height=40)
        self.reg_password_entry.pack(pady=10)

        self.character_class_var = ctk.StringVar(value="Guerrero")
        character_options = ["Guerrero", "Mago", "Knight2"]
        ctk.CTkOptionMenu(frame, variable=self.character_class_var, values=character_options, width=300, height=40).pack(pady=10)

        ctk.CTkButton(frame, text="Crear Cuenta", command=self._register, width=300, height=40).pack(pady=20)
        ctk.CTkButton(frame, text="Volver al Inicio de Sesión", command=lambda: self.switch_view('login'), width=300, height=40, fg_color="gray", hover_color="dimgray").pack(pady=5)

    def create_delete_account_view(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views['delete_account'] = frame

        ctk.CTkLabel(frame, text="ELIMINAR CUENTA", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 30))

        self.del_username_entry = ctk.CTkEntry(frame, placeholder_text="Nombre de Usuario", width=300, height=40)
        self.del_username_entry.pack(pady=10)
        self.del_password_entry = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*", width=300, height=40)
        self.del_password_entry.pack(pady=10)

        ctk.CTkButton(frame, text="Eliminar mi Cuenta", command=self._delete_account, width=300, height=40, fg_color="red", hover_color="darkred").pack(pady=20)
        ctk.CTkButton(frame, text="Volver", command=lambda: self.switch_view('login'), width=300, height=40, fg_color="gray", hover_color="dimgray").pack(pady=5)

    def _login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        resultado_user = validate_login_field('username', username)
        resultado_pass = validate_login_field('password', password)

        if resultado_user != 'ok':
            messagebox.showerror('Error', f'Nombre de usuario: {resultado_user}', parent=self.root)
            return
        if resultado_pass != 'ok':
            messagebox.showerror('Error', f'Contraseña: {resultado_pass}', parent=self.root)
            return

        if login_user(username, password):
            messagebox.showinfo('Éxito', 'Inicio de sesión exitoso', parent=self.root)
            self.stop_video()
            self.root.destroy()
            self.logged_in_user = username
        else:
            messagebox.showerror('Error', 'Nombre de usuario o contraseña incorrectos', parent=self.root)
            self.logged_in_user = None

    def _register(self):
        username = self.reg_username_entry.get()
        correo = self.reg_email_entry.get()
        password = self.reg_password_entry.get()
        character_class = self.character_class_var.get()

        resultado = register_user(username, correo, password, character_class)
        
        if resultado == 'exists':
            messagebox.showerror('Error', 'El nombre de usuario ya existe.', parent=self.root)
        elif resultado == 'campo_vacio':
            messagebox.showerror('Error', 'Todos los campos son obligatorios.', parent=self.root)
        elif resultado == 'nombre_usuario_corto':
            messagebox.showerror('Error', 'El nombre de usuario debe tener al menos 6 caracteres.', parent=self.root)
        elif resultado == 'invalid_email':
            messagebox.showerror('Error', 'Correo inválido. Solo dominios permitidos.', parent=self.root)
        elif resultado == 'no_espacios':
            messagebox.showerror('Error', 'No puede contener espacios.', parent=self.root)
        elif resultado == 'mucho_caracteres_especiales':
            messagebox.showerror('Error', 'El campo contiene demasiados caracteres especiales consecutivos.', parent=self.root)
        elif resultado == 'campo_invalido':
            messagebox.showerror('Error', 'El campo debe contener al menos 4 letras o números.', parent=self.root)
        elif resultado == 'contraseña_corta':
            messagebox.showerror('Error', 'La contraseña debe tener al menos 6 caracteres.', parent=self.root)
        elif resultado == 'contraseña_larga':
            messagebox.showerror('Error', 'La contraseña no puede tener más de 8 caracteres.', parent=self.root)
        elif resultado == 'ok':
            messagebox.showinfo('Éxito', 'Registro exitoso. Ahora puedes iniciar sesión.', parent=self.root)
            self.switch_view('login')

    def _delete_account(self):
        username = self.del_username_entry.get()
        password = self.del_password_entry.get()

        if login_user(username, password):
            if messagebox.askyesno("Confirmar Eliminación", "¿Estás seguro de que quieres eliminar tu cuenta? Esta acción es irreversible.", parent=self.root):
                if delete_user(username):
                    messagebox.showinfo('Éxito', 'Cuenta eliminada exitosamente.', parent=self.root)
                    self.switch_view('login')
                else:
                    messagebox.showerror('Error', 'No se pudo eliminar la cuenta.', parent=self.root)
            else:
                messagebox.showinfo('Cancelado', 'La eliminación de la cuenta ha sido cancelada.', parent=self.root)
        else:
            messagebox.showerror('Error', 'Nombre de usuario o contraseña incorrectos.', parent=self.root)

    def start_login(self):
        self.start_video()
        self.root.mainloop()
        return getattr(self, 'logged_in_user', None)

# --- Instancia de la interfaz de usuario de autenticación ---
# auth_ui = AuthUI()
# auth_ui.start_login()