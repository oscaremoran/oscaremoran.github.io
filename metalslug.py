import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Metal Slug - Level 1")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH // 4
        self.rect.y = SCREEN_HEIGHT - 60
        self.speed = 5
        self.jump_speed = -18  # Increased for higher jump
        self.gravity = 0.8
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = True
        self.bullets = 10
        self.shots_fired = 0
        self.reloading = False
        self.reload_timer = 0
        self.health = 100

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        # Horizontal movement
        target_velocity_x = 0
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            target_velocity_x = -self.speed
        if keys[pygame.K_RIGHT] and self.rect.x < SCREEN_WIDTH - 40:
            target_velocity_x = self.speed
        self.velocity_x = target_velocity_x

        # Jump
        if keys[pygame.K_UP] and self.on_ground:
            self.velocity_y = self.jump_speed
            self.on_ground = False

        # Apply gravity
        self.velocity_y += self.gravity

        # Move horizontally and check collisions
        self.rect.x += self.velocity_x
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                elif self.velocity_x < 0:  # Moving left
                    self.rect.left = platform.rect.right
                self.velocity_x = 0

        # Move vertically and check collisions
        self.rect.y += self.velocity_y
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:  # Falling
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                elif self.velocity_y < 0:  # Jumping up
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0

        # Ground collision
        if self.rect.y >= SCREEN_HEIGHT - 60:
            self.rect.y = SCREEN_HEIGHT - 60
            self.velocity_y = 0
            self.on_ground = True

        if self.reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.bullets = 10
                self.reloading = False

    def shoot(self):
        if self.bullets > 0 and not self.reloading:
            bullet = Bullet(self.rect.right, self.rect.centery)
            all_sprites.add(bullet)
            bullets.add(bullet)
            self.bullets -= 1
            self.shots_fired += 1
            if self.shots_fired >= 10:
                self.shots_fired = 0
                self.bullets = 0

    def reload(self):
        if not self.reloading and self.bullets < 10:
            self.reloading = True
            self.reload_timer = 60  # 1 second at 60 FPS

# Bullet class (Player's bullets)
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 5))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 10

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > SCREEN_WIDTH:
            self.kill()

# Enemy Bullet class (Regular enemies)
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((10, 5))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = -8 if direction == "left" else 8

    def update(self):
        self.rect.x += self.speed
        if self.rect.x < 0 or self.rect.x > SCREEN_WIDTH:
            self.kill()

# Boss Bullet class (Larger bullets)
class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = -8

    def update(self):
        self.rect.x += self.speed
        if self.rect.x < 0:
            self.kill()

# Enemy class (Turn around, no movement)
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.Surface((30, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = SCREEN_HEIGHT - 50
        self.direction = "left"
        self.shoot_timer = random.randint(60, 120)
        self.turn_timer = 120

    def update(self):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot()
            self.shoot_timer = random.randint(60, 120)

        self.turn_timer -= 1
        if self.turn_timer <= 0:
            self.direction = "right" if self.direction == "left" else "left"
            self.turn_timer = 120

    def shoot(self):
        bullet = EnemyBullet(self.rect.left if self.direction == "left" else self.rect.right, 
                             self.rect.centery, self.direction)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

# Boss class (Jumping and big bullets)
class Boss(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.Surface((100, 100))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = SCREEN_HEIGHT - 100
        self.health = 100
        self.jump_speed = -15
        self.gravity = 0.8
        self.velocity_y = 0
        self.on_ground = True
        self.shoot_timer = 30
        self.jump_timer = 60

    def update(self):
        self.jump_timer -= 1
        if self.jump_timer <= 0 and self.on_ground:
            self.velocity_y = self.jump_speed
            self.on_ground = False
            self.jump_timer = 60

        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y
        if self.rect.y >= SCREEN_HEIGHT - 100:
            self.rect.y = SCREEN_HEIGHT - 100
            self.velocity_y = 0
            self.on_ground = True

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot()
            self.shoot_timer = 30

    def shoot(self):
        bullet = BossBullet(self.rect.left, self.rect.centery)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.Surface((width, 20))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Background scrolling
class Background:
    def __init__(self):
        self.image = pygame.Surface((SCREEN_WIDTH * 2, SCREEN_HEIGHT))
        self.image.fill((100, 150, 100))
        self.x = 0
        self.speed = 2

    def update(self):
        self.x -= self.speed
        if self.x <= -SCREEN_WIDTH:
            self.x = 0

    def draw(self, surface):
        surface.blit(self.image, (self.x, 0))
        surface.blit(self.image, (self.x + SCREEN_WIDTH, 0))

# Sprite groups
all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
platforms = pygame.sprite.Group()

# Create player and background
player = Player()
all_sprites.add(player)
background = Background()

# HUD bullet symbols
bullet_icon = pygame.Surface((10, 10))
bullet_icon.fill(RED)

# Generate initial platforms (no overlap, higher)
platform_list = []
platform_positions = []
for i in range(0, SCREEN_WIDTH * 3, 300):
    height = random.choice([SCREEN_HEIGHT - 180, SCREEN_HEIGHT - 200, SCREEN_HEIGHT - 220])  # Higher platforms
    platform = Platform(i, height, 200)
    platform_list.append(platform)
    platform_positions.append((i, i + 200))
    platforms.add(platform)
    all_sprites.add(platform)

# Game loop
clock = pygame.time.Clock()
running = True
enemy_spawn_timer = 0
enemies_killed = 0
boss_spawned = False
scroll_offset = 0

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()
            if event.key == pygame.K_r:
                player.reload()

    # Update
    background.update()
    player.update(platforms)
    
    # Scroll platforms and enemies
    scroll_offset -= background.speed
    for platform in platforms:
        platform.rect.x -= background.speed
        if platform.rect.right < 0:
            new_x = SCREEN_WIDTH + random.randint(100, 300)
            while any(new_x < pos[1] + 50 and new_x + 200 > pos[0] - 50 for pos in platform_positions):
                new_x += 250
            platform.rect.x = new_x
            platform.rect.y = random.choice([SCREEN_HEIGHT - 180, SCREEN_HEIGHT - 200, SCREEN_HEIGHT - 220])  # Higher platforms
            platform_positions = [(p.rect.x, p.rect.x + 200) for p in platforms]

    for enemy in enemies:
        enemy.rect.x -= background.speed

    # Update all other sprites (excluding player)
    for sprite in all_sprites:
        if sprite != player:
            sprite.update()

    # Spawn enemies or boss
    if not boss_spawned:
        enemy_spawn_timer += 1
        if enemy_spawn_timer > 60:
            enemy = Enemy(SCREEN_WIDTH + random.randint(0, 100))
            all_sprites.add(enemy)
            enemies.add(enemy)
            enemy_spawn_timer = 0

    # Collision detection
    hits = pygame.sprite.groupcollide(bullets, enemies, True, True)
    if hits:
        enemies_killed += len(hits)
        if enemies_killed >= 20 and not boss_spawned:
            boss = Boss(SCREEN_WIDTH + 50)
            all_sprites.add(boss)
            enemies.add(boss)
            boss_spawned = True

    boss_hits = pygame.sprite.groupcollide(bullets, enemies, True, False)
    if boss_hits and boss_spawned:
        for boss in enemies:
            boss.health -= len(boss_hits)
            if boss.health <= 0:
                boss.kill()
                print("Boss defeated!")

    player_hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
    if player_hits:
        for bullet in player_hits:
            if isinstance(bullet, BossBullet):
                player.health -= 25
            else:
                player.health -= 5
        if player.health <= 0:
            print("Player dead!")
            running = False

    # Draw
    screen.fill(WHITE)
    background.draw(screen)
    all_sprites.draw(screen)

    # Draw bullet HUD
    for i in range(player.bullets):
        screen.blit(bullet_icon, (10 + i * 15, 10))

    # Draw health bar
    pygame.draw.rect(screen, RED, (10, 30, 100, 10))
    pygame.draw.rect(screen, GREEN, (10, 30, player.health, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()