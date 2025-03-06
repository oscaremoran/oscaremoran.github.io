import pygame
import sys
import math
import random

# Constants (unchanged)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MAP_WIDTH = 3200
MAP_HEIGHT = 2400
FPS = 60

PLAYER_SPEED = 5
ENEMY_SPEED = 2
GREEN_ENEMY_SPEED = 3  # Slightly faster than regular enemies
PROJECTILE_SPEED = 5

def get_camera_offset(player):
    # ... (unchanged)
    offset_x = player.rect.centerx - SCREEN_WIDTH // 2
    offset_y = player.rect.centery - SCREEN_HEIGHT // 2
    offset_x = max(0, min(offset_x, MAP_WIDTH - SCREEN_WIDTH))
    offset_y = max(0, min(offset_y, MAP_HEIGHT - SCREEN_HEIGHT))
    return (offset_x, offset_y)

# Player class (unchanged)
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 50)
        self.health = 300

    def move(self, dx, dy):
        # ... (unchanged)
        self.rect.x += dx
        self.rect.y += dy
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.y < 0:
            self.rect.y = 0
        if self.rect.x > MAP_WIDTH - self.rect.width:
            self.rect.x = MAP_WIDTH - self.rect.width
        if self.rect.y > MAP_HEIGHT - self.rect.height:
            self.rect.y = MAP_HEIGHT - self.rect.height

    def draw(self, screen, camera_offset):
        offset_rect = self.rect.move(-camera_offset[0], -camera_offset[1])
        pygame.draw.rect(screen, (255, 255, 255), offset_rect)

# Original Enemy class (unchanged)
class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.shoot_delay = random.randint(60, 120)
        self.shoot_timer = self.shoot_delay
        self.dx = random.choice([-ENEMY_SPEED, ENEMY_SPEED])
        self.dy = random.choice([-ENEMY_SPEED, ENEMY_SPEED])
        self.change_direction_timer = random.randint(60, 180)

    def update(self):
        # ... (unchanged)
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.x <= 0 or self.rect.x >= MAP_WIDTH - self.rect.width:
            self.dx *= -1
        if self.rect.y <= 0 or self.rect.y >= MAP_HEIGHT - self.rect.height:
            self.dy *= -1
        self.change_direction_timer -= 1
        if self.change_direction_timer <= 0:
            self.dx = random.choice([-ENEMY_SPEED, ENEMY_SPEED])
            self.dy = random.choice([-ENEMY_SPEED, ENEMY_SPEED])
            self.change_direction_timer = random.randint(60, 180)
        self.shoot_timer -= 1

    def can_shoot(self):
        # ... (unchanged)
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_delay
            return True
        return False

    def draw(self, screen, camera_offset):
        offset_rect = self.rect.move(-camera_offset[0], -camera_offset[1])
        pygame.draw.rect(screen, (255, 0, 0), offset_rect)

# New GreenEnemy class that homes in on the player
class GreenEnemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.shoot_delay = random.randint(90, 150)  # Shoots less frequently
        self.shoot_timer = self.shoot_delay

    def update(self, player):
        # Calculate direction towards player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:  # Avoid division by zero
            dx = (dx / dist) * GREEN_ENEMY_SPEED
            dy = (dy / dist) * GREEN_ENEMY_SPEED
            self.rect.x += dx
            self.rect.y += dy

        # Keep within world boundaries
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.y < 0:
            self.rect.y = 0
        if self.rect.x > MAP_WIDTH - self.rect.width:
            self.rect.x = MAP_WIDTH - self.rect.width
        if self.rect.y > MAP_HEIGHT - self.rect.height:
            self.rect.y = MAP_HEIGHT - self.rect.height

        self.shoot_timer -= 1

    def can_shoot(self):
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_delay
            return True
        return False

    def draw(self, screen, camera_offset):
        offset_rect = self.rect.move(-camera_offset[0], -camera_offset[1])
        pygame.draw.rect(screen, (0, 255, 0), offset_rect)  # Green color

# Projectile class (unchanged)
class Projectile:
    def __init__(self, x, y, target_x, target_y):
        # ... (unchanged)
        self.rect = pygame.Rect(x, y, 10, 10)
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        self.dx = (dx / dist) * PROJECTILE_SPEED
        self.dy = (dy / dist) * PROJECTILE_SPEED

    def update(self):
        # ... (unchanged)
        self.rect.x += self.dx
        self.rect.y += self.dy

    def draw(self, screen, camera_offset):
        offset_rect = self.rect.move(-camera_offset[0], -camera_offset[1])
        pygame.draw.rect(screen, (0, 0, 0), offset_rect)

# Building class and other functions (unchanged)
class Building:
    # ... (unchanged)
    def __init__(self, x, y, width, height, health=100):
        self.rect = pygame.Rect(x, y, width, height)
        self.health = health
        self.max_health = health
        self.damage_timer = 0

    def update(self):
        # ... (unchanged)
        if self.damage_timer > 0:
            self.damage_timer -= 1

    def take_damage(self, amount):
        # ... (unchanged)
        if self.damage_timer <= 0:
            self.health -= amount
            self.damage_timer = 10
            if self.health < 0:
                self.health = 0

    def draw(self, screen, camera_offset):
        # ... (unchanged)
        offset_rect = self.rect.move(-camera_offset[0], -camera_offset[1])
        health_ratio = self.health / self.max_health
        color_value = int(100 + 155 * health_ratio)
        pygame.draw.rect(screen, (color_value, color_value, color_value), offset_rect)

def draw_hp_bar(screen, x, y, width, height, current_health, max_health):
    # ... (unchanged)
    ratio = current_health / max_health
    pygame.draw.rect(screen, (255, 0, 0), (x, y, width, height))
    pygame.draw.rect(screen, (0, 255, 0), (x, y, width * ratio, height))

def draw_enemy_count(screen, enemy_count):
    # ... (unchanged)
    font = pygame.font.Font(None, 36)
    text = font.render(f"Enemies: {enemy_count}", True, (0, 0, 0))
    screen.blit(text, (SCREEN_WIDTH - 150, 10))

def generate_buildings(num_buildings):
    # ... (unchanged)
    buildings = []
    attempts = 0
    while len(buildings) < num_buildings and attempts < num_buildings * 10:
        width = random.randint(80, 150)
        height = random.randint(80, 150)
        x = random.randint(0, MAP_WIDTH - width)
        y = random.randint(0, MAP_HEIGHT - height)
        new_rect = pygame.Rect(x, y, width, height)
        overlap = False
        for b in buildings:
            if new_rect.colliderect(b.rect.inflate(20, 20)):
                overlap = True
                break
        if not overlap:
            health = random.choice([100, 150])
            buildings.append(Building(x, y, width, height, health))
        attempts += 1
    return buildings

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Top-Down Rampage - Street Map Style")
    clock = pygame.time.Clock()
    running = True

    player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2)
    enemies = []  # Red enemies
    green_enemies = []  # New green enemies
    projectiles = []
    buildings = generate_buildings(20)

    # Spawn initial enemies: 3 red enemies and 2 green enemies
    for i in range(3):
        enemy_x = random.randint(0, MAP_WIDTH - 40)
        enemy_y = random.randint(0, MAP_HEIGHT - 40)
        enemies.append(Enemy(enemy_x, enemy_y))
    for i in range(2):
        enemy_x = random.randint(0, MAP_WIDTH - 40)
        enemy_y = random.randint(0, MAP_HEIGHT - 40)
        green_enemies.append(GreenEnemy(enemy_x, enemy_y))

    last_spawn_time = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Player movement (unchanged)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += PLAYER_SPEED
        player.move(dx, dy)

        # Update buildings (unchanged)
        for building in buildings:
            building.update()
            if player.rect.colliderect(building.rect):
                building.take_damage(1)
        buildings = [b for b in buildings if b.health > 0]

        # Spawn enemies every 5 seconds: 3 red + 2 green
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= 5000:
            for i in range(3):
                enemy_x = random.randint(0, MAP_WIDTH - 40)
                enemy_y = random.randint(0, MAP_HEIGHT - 40)
                enemies.append(Enemy(enemy_x, enemy_y))
            for i in range(2):
                enemy_x = random.randint(0, MAP_WIDTH - 40)
                enemy_y = random.randint(0, MAP_HEIGHT - 40)
                green_enemies.append(GreenEnemy(enemy_x, enemy_y))
            last_spawn_time = current_time

        # Update red enemies
        for enemy in enemies[:]:
            enemy.update()
            if enemy.can_shoot():
                proj = Projectile(enemy.rect.centerx, enemy.rect.centery,
                                player.rect.centerx, player.rect.centery)
                projectiles.append(proj)
            if player.rect.colliderect(enemy.rect):
                enemies.remove(enemy)

        # Update green enemies
        for green_enemy in green_enemies[:]:
            green_enemy.update(player)  # Pass player for homing
            if green_enemy.can_shoot():
                proj = Projectile(green_enemy.rect.centerx, green_enemy.rect.centery,
                                player.rect.centerx, player.rect.centery)
                projectiles.append(proj)
            if player.rect.colliderect(green_enemy.rect):
                green_enemies.remove(green_enemy)

        # Update projectiles (unchanged)
        for proj in projectiles[:]:
            proj.update()
            if (proj.rect.x < 0 or proj.rect.x > MAP_WIDTH or
                proj.rect.y < 0 or proj.rect.y > MAP_HEIGHT):
                projectiles.remove(proj)
                continue
            if proj.rect.colliderect(player.rect):
                player.health -= 10
                projectiles.remove(proj)
                if player.health < 0:
                    player.health = 0
                continue
            for building in buildings:
                if proj.rect.colliderect(building.rect):
                    building.take_damage(10)
                    if proj in projectiles:
                        projectiles.remove(proj)
                    break

        camera_offset = get_camera_offset(player)

        # Draw everything
        screen.fill((120, 120, 120))
        draw_hp_bar(screen, 10, 10, 200, 20, player.health, 300)  # Updated max health to 300
        draw_enemy_count(screen, len(enemies) + len(green_enemies))  # Count both types

        for building in buildings:
            building.draw(screen, camera_offset)
        player.draw(screen, camera_offset)
        for enemy in enemies:
            enemy.draw(screen, camera_offset)
        for green_enemy in green_enemies:
            green_enemy.draw(screen, camera_offset)
        for proj in projectiles:
            proj.draw(screen, camera_offset)

        pygame.display.flip()
        clock.tick(FPS)

        if player.health <= 0:
            running = False

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()