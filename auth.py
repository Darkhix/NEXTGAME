# auth.py
import os
import json
import customtkinter as ctk
from tkinter import messagebox
import config

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

def register_user(username, correo, password, character_class):
    users = load_users()
    if username in users:
        return 'exists'
    if not any(correo.endswith(domain) for domain in config.VALID_DOMAINS):
        return 'invalid_email'
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

    def start_login(self):
        self.iniciar_tkinter_login()
        return self.current_user

    def iniciar_tkinter_login(self):
        def validar_login():
            usuario = username_entry.get()
            clave = contraseña_entry.get()
            if login_user(usuario, clave):
                self.current_user = usuario
                self.root.destroy()
            else:
                messagebox.showerror('Error', 'Usuario o contraseña incorrectos.')

        def ir_a_registro():
            self.root.destroy()
            self.iniciar_tkinter_registro()

        self.root = ctk.CTk()
        self.root.title('Inicio de sesión')
        self.root.geometry('400x400')
        frame = ctk.CTkFrame(self.root)
        frame.pack(expand=True)

        ctk.CTkLabel(frame, text='Iniciar sesión', font=('Arial', 22)).pack(pady=10)
        ctk.CTkLabel(frame, text='Nombre de usuario').pack()
        username_entry = ctk.CTkEntry(frame)
        username_entry.pack(pady=5)
        ctk.CTkLabel(frame, text='Contraseña').pack()
        contraseña_entry = ctk.CTkEntry(frame, show='*')
        contraseña_entry.pack(pady=5)
        ctk.CTkButton(frame, text='Entrar', command=validar_login).pack(pady=10)
        ctk.CTkButton(frame, text='Registrarse', command=ir_a_registro, fg_color='#444').pack()
        self.root.mainloop()

    def iniciar_tkinter_registro(self):
        from game import load_characters

        def registrar():
            username = usuario_entry.get()
            correo = correo_entry.get()
            password = contraseña_entry.get()
            confirm = confirmar_entry.get()
            character_class = character_var.get()

            if not all([username, correo, password, confirm, character_class]):
                messagebox.showerror('Error', 'Completa todos los campos.')
                return
            if password != confirm:
                messagebox.showerror('Error', 'Las contraseñas no coinciden.')
                return

            resultado = register_user(username, correo, password, character_class)
            if resultado == 'exists':
                messagebox.showerror('Error', 'Ese nombre de usuario ya existe.')
            elif resultado == 'invalid_email':
                messagebox.showerror('Error', 'Correo inválido. Solo dominios permitidos.')
            else:
                messagebox.showinfo('Éxito', 'Registro exitoso. Ahora puedes iniciar sesión.')
                self.root.destroy()
                self.iniciar_tkinter_login()

        def volver():
            self.root.destroy()
            self.iniciar_tkinter_login()

        self.root = ctk.CTk()
        self.root.title('Registro')
        self.root.geometry('400x550')
        frame = ctk.CTkFrame(self.root)
        frame.pack(expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text='Registro', font=('Arial', 22)).pack(pady=10)
        usuario_entry = ctk.CTkEntry(frame, placeholder_text='Nombre de usuario')
        usuario_entry.pack(pady=5, fill='x')
        correo_entry = ctk.CTkEntry(frame, placeholder_text='Correo electrónico')
        correo_entry.pack(pady=5, fill='x')
        contraseña_entry = ctk.CTkEntry(frame, placeholder_text='Contraseña', show='*')
        contraseña_entry.pack(pady=5, fill='x')
        confirmar_entry = ctk.CTkEntry(frame, placeholder_text='Confirmar contraseña', show='*')
        confirmar_entry.pack(pady=5, fill='x')
        ctk.CTkLabel(frame, text='Selecciona tu personaje').pack(pady=(10, 5))
        character_var = ctk.StringVar(value=None)
        
        try:
            available_characters = load_characters()
            for char_name in available_characters:
                ctk.CTkRadioButton(frame, text=char_name, variable=character_var, value=char_name).pack(anchor='w', padx=50)
        except FileNotFoundError:
            ctk.CTkLabel(frame, text="Error: No se encontró characters.json").pack()
        
        ctk.CTkButton(frame, text='Registrarse', command=registrar).pack(pady=(20, 5), fill='x')
        ctk.CTkButton(frame, text='Volver', command=volver, fg_color='#444').pack(pady=5, fill='x')
        
        self.root.mainloop()