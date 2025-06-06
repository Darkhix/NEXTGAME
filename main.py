# main.py
import pygame
import sys
import os
import auth
from game import Game

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    auth_ui = auth.AuthUI()
    current_user = auth_ui.start_login()

    if not current_user:
        sys.exit()

    user_data = auth.get_user(current_user)

    if not user_data:
        print(f"Error: No se pudieron cargar los datos para el usuario {current_user}")
        sys.exit()

    game_instance = Game(current_user, user_data)
    game_instance.run()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()  