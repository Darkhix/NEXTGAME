# fighter.py
import pygame
import json
import os

class Fighter():
    JSON_PATH = 'usuarios.json'

    def __init__(self, player, x, y, flip, data, animation_list, sound, stats, special_moves, ai=False, username=None):
        self.player = player
        # --- MODIFICADO: Lee el nuevo formato de 'data' con ancho y alto separados ---
        self.frame_w = data[0]
        self.frame_h = data[1]
        self.image_scale = data[2]
        self.offset = data[3]
        
        self.flip = flip
        self.animation_list = animation_list
        self.sound = sound
        self.ai = ai
        self.username = username
        
        # Carga de estadísticas desde el diccionario
        self.base_health = stats.get('health', 100)
        self.speed = stats.get('speed', 10)
        self.special_moves = special_moves
        
        self.action = 0
        self.frame_index = 0
        
        # Red de seguridad para evitar crashes si una animación no existe
        if not self.animation_list or self.action >= len(self.animation_list) or not self.animation_list[self.action]:
            print(f"ADVERTENCIA: Animación 'Idle' (acción 0) no encontrada o vacía para un personaje.")
            placeholder_surface = pygame.Surface((self.frame_w if self.frame_w > 0 else 50, self.frame_h if self.frame_h > 0 else 50))
            placeholder_surface.fill((255, 0, 255))
            while len(self.animation_list) <= self.action:
                self.animation_list.append([])
            self.animation_list[self.action] = [placeholder_surface]

        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        self.rect = pygame.Rect((x, y, 80, 180))
        self.vel_y = 0
        self.running = False
        self.jump_state = False
        self.attacking = False
        self.attack_type = 0
        self.attack_cooldown = 0
        self.hit = False
        self.health = self.base_health
        self.alive = True
        self.attacks_done = 0

        if self.username:
            self.init_user_data()

    def init_user_data(self):
        if not os.path.exists(Fighter.JSON_PATH):
            with open(Fighter.JSON_PATH, 'w') as f: json.dump({}, f)
        with open(Fighter.JSON_PATH, 'r') as f: data = json.load(f)
        if self.username not in data:
            data[self.username] = {"health": self.health, "attacks_done": self.attacks_done, "is_alive": self.alive}
            with open(Fighter.JSON_PATH, 'w') as f: json.dump(data, f, indent=4)

    def save_user_data(self):
        if self.username:
            if not os.path.exists(Fighter.JSON_PATH):
                with open(Fighter.JSON_PATH, 'w') as f:
                    json.dump({}, f)
            try:
                with open(Fighter.JSON_PATH, 'r+') as f:
                    data = json.load(f)
                    data[self.username] = {
                        "health": self.health,
                        "attacks_done": self.attacks_done,
                        "is_alive": self.alive
                    }
                    f.seek(0)  # Rewind to the beginning of the file
                    json.dump(data, f, indent=4)
                    f.truncate()  # Truncate any remaining old content
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error saving user data for {self.username}: {e}")

    def move(self, screen_width, screen_height, target, round_over):
        SPEED = self.speed
        GRAVITY = 2
        dx, dy = 0, 0
        if not self.alive or round_over: return
        key = pygame.key.get_pressed()
        if self.player == 1:
            if key[pygame.K_a]: dx = -SPEED; self.running = True
            if key[pygame.K_d]: dx = SPEED; self.running = True
            if key[pygame.K_w] and not self.jump_state: self.vel_y = -30; self.jump_state = True
            if key[pygame.K_t] and not self.attacking: self.attack(target, self.special_moves['K_t']['damage'], 'K_t')
            if key[pygame.K_y] and not self.attacking: self.attack(target, self.special_moves['K_y']['damage'], 'K_y')
        if self.player == 2:
            if key[pygame.K_LEFT]: dx = -SPEED; self.running = True
            if key[pygame.K_RIGHT]: dx = SPEED; self.running = True
            if key[pygame.K_UP] and not self.jump_state: self.vel_y = -30; self.jump_state = True
            if key[pygame.K_k] and not self.attacking: self.attack(target, self.special_moves['K_k']['damage'], 'K_k')
            if key[pygame.K_l] and not self.attacking: self.attack(target, self.special_moves['K_l']['damage'], 'K_l')

        self.vel_y += GRAVITY
        dy += self.vel_y
        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > screen_width: dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110: self.vel_y = 0; self.jump_state = False; dy = screen_height - 110 - self.rect.bottom
        self.flip = target.rect.centerx < self.rect.centerx
        self.rect.x += dx; self.rect.y += dy

    def attack(self, target, damage, move_key):
        if not self.attacking and self.attack_cooldown == 0:
            self.attack_type = move_key
            self.attacking = True
            self.attacks_done += 1
            self.update_action(self.special_moves[move_key]['animation_row'])
            self.sound.play()
            
            # Crear un rectángulo de ataque que se extiende desde el atacante
            attack_rect_width = self.rect.width * 1.5  # Ajusta según sea necesario
            attack_rect_height = self.rect.height / 2
            
            if self.flip: # Atacando a la izquierda
                attack_rect = pygame.Rect(self.rect.x - attack_rect_width, self.rect.y, attack_rect_width, attack_rect_height)
            else: # Atacando a la derecha
                attack_rect = pygame.Rect(self.rect.right, self.rect.y, attack_rect_width, attack_rect_height)

            if attack_rect.colliderect(target.rect):
                target.health -= damage
                target.hit = True
                if target.health <= 0:
                    target.health = 0
                    target.alive = False
                target.update_action(5) # Animación de golpe
            
            self.attack_cooldown = self.special_moves[move_key]['cooldown']

    def update(self):
        animation_cooldown = 100
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(6) # Death animation
        elif self.hit:
            self.update_action(5) # Take hit animation
        elif self.attacking:
            pass # Keep attack animation
        elif self.jump_state:
            self.update_action(2) # Jump animation
        elif self.running:
            self.update_action(1) # Run animation
        else:
            self.update_action(0) # Idle animation

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Si el índice de frame es válido para la acción actual, procede
        # Si no, significa que la animación actual terminó o se cambió, la resetea a Idle para evitar un crash
        if self.frame_index >= len(self.animation_list[self.action]):
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                if self.attacking: self.attacking = False
                if self.hit: self.hit = False
        
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        
        self.save_user_data()

    def update_action(self, new_action):
        if new_action != self.action:
            self.action, self.frame_index, self.update_time = new_action, 0, pygame.time.get_ticks()

    def draw(self, surface):
        # El offset ahora usa el cuarto elemento del array 'data'
        img = pygame.transform.flip(self.image, self.flip, False)
        surface.blit(img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))
        if self.username:
            font = pygame.font.SysFont(None, 26)
            name_text = font.render(self.username, True, (255, 255, 255))
            surface.blit(name_text, (self.rect.centerx - name_text.get_width() / 2, self.rect.y - 30))