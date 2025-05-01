import pygame
import os
import sys
import json
import customtkinter as ctk
from tkinter import messagebox
from pygame import mixer
from fighter import Fighter


os.chdir(os.path.dirname(os.path.abspath(__file__)))
pygame.init()
mixer.init()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

USERS_FILE = "users.json"
current_user = None
VALID_DOMAINS = ["@gmail.com", "@yahoo.cl", "@hotmail.com"]

#Funciones usuario

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def register_user(username, correo, password):
    users = load_users()
    if username in users:
        return "exists"
    if not any(correo.endswith(domain) for domain in VALID_DOMAINS):
        return "invalid_email"
    users[username] = {"password": password, "correo": correo}
    save_users(users)
    return "ok"

def login_user(username, password):
    users = load_users()
    return username in users and users[username]["password"] == password

# Crud

def get_user(username):
    users = load_users()
    return users.get(username)

def get_all_users():
    return load_users()

def update_user(username, new_data):
    users = load_users()
    if username in users:
        users[username].update(new_data)
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

#login y registro

def iniciar_tkinter_login():
    def validar_login():
        usuario = username_entry.get()
        clave = contraseña_entry.get()
        if login_user(usuario, clave):
            global current_user
            current_user = usuario
            root.destroy()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    def ir_a_registro():
        root.destroy()
        iniciar_tkinter_registro()

    root = ctk.CTk()
    root.title("Inicio de sesión")
    root.geometry("400x400")

    frame = ctk.CTkFrame(root)
    frame.pack(expand=True)

    ctk.CTkLabel(frame, text="Iniciar sesión", font=("Arial", 22)).pack(pady=10)
    ctk.CTkLabel(frame, text="Nombre de usuario").pack()
    username_entry = ctk.CTkEntry(frame)
    username_entry.pack(pady=5)

    ctk.CTkLabel(frame, text="Contraseña").pack()
    contraseña_entry = ctk.CTkEntry(frame, show="*")
    contraseña_entry.pack(pady=5)

    ctk.CTkButton(frame, text="Entrar", command=validar_login).pack(pady=10)
    ctk.CTkButton(frame, text="Registrarse", command=ir_a_registro, fg_color="#444").pack()

    root.mainloop()

def iniciar_tkinter_registro():
    def registrar():
        username = usuario_entry.get()
        correo = correo_entry.get()
        password = contraseña_entry.get()
        confirm = confirmar_entry.get()

        if not username or not correo or not password or not confirm:
            messagebox.showerror("Error", "Completa todos los campos.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        resultado = register_user(username, correo, password)
        if resultado == "exists":
            messagebox.showerror("Error", "Ese nombre de usuario ya existe.")
        elif resultado == "invalid_email":
            messagebox.showerror("Error", "Correo inválido. Solo se permiten @gmail.com, @yahoo.cl o @hotmail.com.")
        else:
            messagebox.showinfo("Éxito", "Registro exitoso. Inicia sesión.")
            registro.destroy()
            iniciar_tkinter_login()

    def volver():
        registro.destroy()
        iniciar_tkinter_login()

    registro = ctk.CTk()
    registro.title("Registro")
    registro.geometry("400x500")

    frame = ctk.CTkFrame(registro)
    frame.pack(expand=True)

    ctk.CTkLabel(frame, text="Registro", font=("Arial", 22)).pack(pady=10)
    usuario_entry = ctk.CTkEntry(frame, placeholder_text="Nombre de usuario")
    usuario_entry.pack(pady=5)

    correo_entry = ctk.CTkEntry(frame, placeholder_text="Correo electrónico")
    correo_entry.pack(pady=5)

    contraseña_entry = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*")
    contraseña_entry.pack(pady=5)

    confirmar_entry = ctk.CTkEntry(frame, placeholder_text="Confirmar contraseña", show="*")
    confirmar_entry.pack(pady=5)

    ctk.CTkButton(frame, text="Registrarse", command=registrar).pack(pady=10)
    ctk.CTkButton(frame, text="Volver", command=volver, fg_color="#444").pack()

    registro.mainloop()

#inicio de sesion

iniciar_tkinter_login()
if not current_user:
    sys.exit()

#Ajustes del juego

resolutions = [(800, 600)]
res_index = 0
music_volume = 50
fx_volume = 50

screen = pygame.display.set_mode(resolutions[res_index])
pygame.display.set_caption("Brawler")
clock = pygame.time.Clock()
FPS = 60

count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)
menu_font = pygame.font.SysFont(None, 60)

WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
HIGHLIGHT = (50, 150, 255)

sword_fx = pygame.mixer.Sound("assets/audio/sword.wav")
sword_fx.set_volume(fx_volume / 100)
magic_fx = pygame.mixer.Sound("assets/audio/magic.wav")
magic_fx.set_volume(fx_volume / 100)

bg_image = pygame.image.load("assets/images/background/background.jpg").convert_alpha()
victory_img = pygame.image.load("assets/images/icons/victory.png").convert_alpha()
warrior_sheet = pygame.image.load("assets/images/warrior/Sprites/warrior.png").convert_alpha()
wizard_sheet = pygame.image.load("assets/images/wizard/Sprites/wizard.png").convert_alpha()

WARRIOR_DATA = [162, 4, [72, 56]]
WIZARD_DATA = [250, 3, [112, 107]]
WARRIOR_ANIM = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIM = [8, 8, 1, 8, 8, 3, 7]

intro_count = 3
last_count_update = pygame.time.get_ticks()
score = [0, 0]
round_over = False
ROUND_OVER_COOLDOWN = 2000
game_state = "menu"

menu_items = ["Jugar", "Opciones", "Salir"]
selected_index = 0
options_items = ["Resolución", "Volumen Música", "Volumen FX", "Volver"]
options_index = 0

#partes de del juego(barra de vida, titulo, etc)

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def draw_bg():
    bg = pygame.transform.scale(bg_image, screen.get_size())
    screen.blit(bg, (0, 0))

def draw_health_bar(health, x, y):
    ratio = health / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))

def draw_menu():
    screen.fill(BLACK)
    title = menu_font.render("Joseadores el juego", True, WHITE)
    screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 100))
    for i, item in enumerate(menu_items):
        color = HIGHLIGHT if i == selected_index else GRAY
        text = menu_font.render(item, True, color)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 220 + i*80))
    pygame.display.flip()

def draw_options():
    screen.fill(BLACK)
    title = menu_font.render("Configuración", True, WHITE)
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 100))
    for i, item in enumerate(options_items):
        color = HIGHLIGHT if i == options_index else GRAY
        value = ""
        if item == "Resolución":
            value = f"{resolutions[res_index][0]}x{resolutions[res_index][1]}"
        elif item == "Volumen Música":
            value = f"{music_volume}"
        elif item == "Volumen FX":
            value = f"{fx_volume}"
        text = menu_font.render(f"{item}: {value}", True, color)
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, 200 + i * 80))
    pygame.display.flip()

def create_fighters():
    return (
        Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIM, sword_fx, username=current_user),
        Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIM, magic_fx, ai=True)
    )

fighter_1, fighter_2 = create_fighters()

#Loop para que funcione el juego

run = True
while run:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(menu_items)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(menu_items)
                elif event.key == pygame.K_RETURN:
                    if menu_items[selected_index] == "Jugar":
                        fighter_1, fighter_2 = create_fighters()
                        intro_count = 3
                        score = [0, 0]
                        game_state = "playing"
                    elif menu_items[selected_index] == "Opciones":
                        game_state = "options"
                    elif menu_items[selected_index] == "Salir":
                        run = False
            elif game_state == "options":
                if event.key == pygame.K_RETURN and options_items[options_index] == "Volver":
                    game_state = "menu"

    if game_state == "menu":
        draw_menu()
    elif game_state == "options":
        draw_options()
    elif game_state == "playing":
        draw_bg()
        draw_health_bar(fighter_1.health, 20, 20)
        draw_health_bar(fighter_2.health, screen.get_width()-420, 20)
        draw_text("P1: " + str(score[0]), score_font, RED, 20, 60)
        draw_text("P2: " + str(score[1]), score_font, RED, screen.get_width()-120, 60)

        if intro_count <= 0:
            fighter_1.move(screen.get_width(), screen.get_height(), screen, fighter_2, round_over)
            fighter_2.move(screen.get_width(), screen.get_height(), screen, fighter_1, round_over)
        else:
            draw_text(str(intro_count), count_font, RED, screen.get_width() / 2 - 20, screen.get_height() / 3)
            if pygame.time.get_ticks() - last_count_update >= 1000:
                intro_count -= 1
                last_count_update = pygame.time.get_ticks()

        fighter_1.update()
        fighter_2.update()
        fighter_1.draw(screen)
        fighter_2.draw(screen)

        if not round_over:
            if not fighter_1.alive:
                score[1] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
            elif not fighter_2.alive:
                score[0] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
        else:
            screen.blit(victory_img, (screen.get_width() // 2 - victory_img.get_width() // 2, 150))
            if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
                round_over = False
                game_state = "menu"

    pygame.display.update()

pygame.quit()
