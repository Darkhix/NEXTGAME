# fighter.py
import pygame
import json
import os

class Fighter():
    JSON_PATH = 'usuarios.json'

    def __init__(self, player, x, y, flip, data, sprite_sheet, animation_steps, sound, ai=False, username=None):
        self.player = player
        self.size = data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip
        self.ai = ai
        self.sprite_sheet = sprite_sheet
        self.animation_steps = animation_steps
        self.sound = sound
        self.username = username

        self.attacks_done = 0

        self.animation_list = self.load_images(sprite_sheet, animation_steps)

        self.action = 0
        self.frame_index = 0
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
        self.health = 100
        self.alive = True

        if self.username:
            self.init_user_data()

    def init_user_data(self):
        if not os.path.exists(Fighter.JSON_PATH):
            with open(Fighter.JSON_PATH, 'w') as f:
                json.dump({}, f)
        with open(Fighter.JSON_PATH, 'r') as f:
            data = json.load(f)
        if self.username not in data:
            data[self.username] = {"health": self.health, "attacks_done": self.attacks_done, "is_alive": self.alive}
            with open(Fighter.JSON_PATH, 'w') as f:
                json.dump(data, f, indent=4)

    def save_user_data(self):
        if not self.username:
            return
        with open(Fighter.JSON_PATH, 'r') as f:
            data = json.load(f)
        data[self.username] = {"health": self.health, "attacks_done": self.attacks_done, "is_alive": self.alive}
        with open(Fighter.JSON_PATH, 'w') as f:
            json.dump(data, f, indent=4)

    def load_images(self, sprite_sheet, animation_steps):
        animation_list = []
        sheet_width, sheet_height = sprite_sheet.get_width(), sprite_sheet.get_height()
        for y, frames in enumerate(animation_steps):
            temp_img_list = []
            for x in range(frames):
                frame_x, frame_y = x * self.size, y * self.size
                if frame_x + self.size <= sheet_width and frame_y + self.size <= sheet_height:
                    temp_img = sprite_sheet.subsurface(pygame.Rect(frame_x, frame_y, self.size, self.size))
                    temp_img = pygame.transform.scale(temp_img, (self.size * self.image_scale, self.size * self.image_scale))
                    temp_img_list.append(temp_img)
                else:
                    break
            animation_list.append(temp_img_list if temp_img_list else [pygame.Surface((1, 1))])
        return animation_list

    def move(self, screen_width, screen_height, target, round_over):
        SPEED = 10
        GRAVITY = 2
        dx = 0
        dy = 0
        self.running = False

        if not self.attacking and self.alive and not round_over:
            if self.ai:
                if self.rect.centerx < target.rect.centerx - 30: dx = SPEED
                elif self.rect.centerx > target.rect.centerx + 30: dx = -SPEED
                if abs(self.rect.centerx - target.rect.centerx) < 80 and not self.attacking:
                    self.attack(target, 1)
            else:
                key = pygame.key.get_pressed()
                if key[pygame.K_a]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_d]:
                    dx = SPEED
                    self.running = True

        self.vel_y += GRAVITY
        dy += self.vel_y

        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > screen_width: dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            self.jump_state = False
            dy = screen_height - 110 - self.rect.bottom

        self.flip = target.rect.centerx < self.rect.centerx
        if self.attack_cooldown > 0: self.attack_cooldown -= 1

        self.rect.x += dx
        self.rect.y += dy

    def jump(self):
        if not self.jump_state and self.alive:
            self.vel_y = -30
            self.jump_state = True

    def attack(self, target, attack_type):
        if self.attack_cooldown == 0 and not self.attacking and self.alive:
            self.attack_type = attack_type
            self.attacking = True
            self.attacks_done += 1
            self.sound.play()
            attacking_rect = pygame.Rect(self.rect.centerx - (2 * self.rect.width * self.flip), self.rect.y, 2 * self.rect.width, self.rect.height)
            if attacking_rect.colliderect(target.rect):
                target.health -= 10
                target.hit = True
    
    def update(self):
        if self.health <= 0:
            self.health, self.alive = 0, False
            self.update_action(6)
        elif self.hit: self.update_action(5)
        elif self.attacking:
            self.update_action(3 if self.attack_type == 1 else 4)
        elif self.jump_state: self.update_action(2)
        elif self.running: self.update_action(1)
        else: self.update_action(0)

        animation_cooldown = 50
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.animation_list[self.action]):
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                if self.action in [3, 4]: self.attacking, self.attack_cooldown = False, 20
                if self.action == 5: self.hit, self.attacking, self.attack_cooldown = False, False, 20
        self.save_user_data()

    def update_action(self, new_action):
        if new_action != self.action:
            self.action, self.frame_index, self.update_time = new_action, 0, pygame.time.get_ticks()

    def draw(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False)
        surface.blit(img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))
        if self.username:
            font = pygame.font.SysFont(None, 26)
            name_text = font.render(self.username, True, (255, 255, 255))
            name_x = self.rect.centerx - name_text.get_width() // 2
            name_y = self.rect.top - 20
            surface.blit(name_text, (name_x, name_y))