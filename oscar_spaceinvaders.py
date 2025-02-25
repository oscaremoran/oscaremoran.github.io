import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, is_mimic=False):
        super().__init__()
        self.image = pygame.Surface([50, 30])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH // 2
        self.rect.y = HEIGHT - 50
        self.speed = 5
        self.is_mimic = is_mimic

    def update(self, primary_player=None):
        if self.is_mimic and primary_player:
            self.rect.x = primary_player.rect.x - 60  # Position to the left of primary
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and self.rect.x > 0:
                self.rect.x -= self.speed
            if keys[pygame.K_RIGHT] and self.rect.x < WIDTH - 50:
                self.rect.x += self.speed

# Player Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([5, 10])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.y < 0:
            self.kill()

# Enemy Bullet class
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([5, 10])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 7

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > HEIGHT:
            self.kill()

# Invader class
class Invader(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = pygame.Surface([40, 30])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.direction = 1

    def update(self):
        self.rect.x += self.speed * self.direction

# Power-up Pellet class
class PowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([15, 15])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - 15)
        self.rect.y = 0
        self.speed = 10

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > HEIGHT:
            self.kill()

# Game states
HOME_SCREEN = 0
PLAYING = 1
game_state = HOME_SCREEN

# Game variables
score = 0
has_mimic = False
all_sprites = pygame.sprite.Group()
invaders = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
power_ups = pygame.sprite.Group()
player = None
mimic_player = None

def init_game(invader_speed=2, reset_score=True):
    global all_sprites, invaders, bullets, enemy_bullets, power_ups, player, mimic_player, invader_direction, move_down, score, has_mimic
    if reset_score:
        score = 0
        has_mimic = False
        all_sprites.empty()
        invaders.empty()
        bullets.empty()
        enemy_bullets.empty()
        power_ups.empty()
    else:  # When respawning invaders
        
        # Remove and disable mimic if it exists when starting new wave
        if has_mimic and mimic_player:
            all_sprites.remove(mimic_player)
            has_mimic = False
            mimic_player = None
        invaders.empty()
    
    player = Player()
    all_sprites.add(player)
    
    for i in range(5):
        for j in range(8):
            invader = Invader(100 + j * 60, 50 + i * 50, invader_speed)
            all_sprites.add(invader)
            invaders.add(invader)
    
    invader_direction = 1
    move_down = False

# Font setup
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)

# Clock
clock = pygame.time.Clock()

# Initial invader speed
current_invader_speed = 2

# Main game loop
running = True
while running:
    if game_state == HOME_SCREEN:
        # Home screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_invader_speed = 2
                    init_game(current_invader_speed, reset_score=True)
                    game_state = PLAYING
        
        screen.fill(BLACK)
        start_text = font.render("PRESS SPACE TO START", True, WHITE)
        start_rect = start_text.get_rect(center=(WIDTH/2, HEIGHT/2))
        screen.blit(start_text, start_rect)
        pygame.display.flip()
        
    elif game_state == PLAYING:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bullet = Bullet(player.rect.centerx, player.rect.y)
                    all_sprites.add(bullet)
                    bullets.add(bullet)
                    if has_mimic and mimic_player:
                        mimic_bullet = Bullet(mimic_player.rect.centerx, mimic_player.rect.y)
                        all_sprites.add(mimic_bullet)
                        bullets.add(mimic_bullet)

        # Random power-up spawn
        if random.random() < 0.005 and not has_mimic:  # 0.5% chance per frame
            power_up = PowerUp()
            all_sprites.add(power_up)
            power_ups.add(power_up)

        # Random enemy shooting
        if random.random() < 0.01 and invaders:
            shooter = random.choice([inv for inv in invaders])
            enemy_bullet = EnemyBullet(shooter.rect.centerx, shooter.rect.bottom)
            all_sprites.add(enemy_bullet)
            enemy_bullets.add(enemy_bullet)

        # Update
        all_sprites.update()
        if has_mimic and mimic_player:
            mimic_player.update(player)

        # Check for power-up collection
        if pygame.sprite.spritecollide(player, power_ups, True) and not has_mimic:
            has_mimic = True
            mimic_player = Player(is_mimic=True)
            all_sprites.add(mimic_player)

        # Check for bullet-invader collisions
        hits = pygame.sprite.groupcollide(invaders, bullets, True, True)
        for hit in hits:
            score += 10

        # Check if all invaders are dead
        if not invaders:
            current_invader_speed += 1
            init_game(current_invader_speed, reset_score=False)

        # Check for enemy bullet-player collision or invaders reaching bottom
        game_over = False
        if (pygame.sprite.spritecollide(player, enemy_bullets, True) or 
            (has_mimic and mimic_player and pygame.sprite.spritecollide(mimic_player, enemy_bullets, True))):
            game_over = True
        for invader in invaders:
            if invader.rect.bottom >= HEIGHT:
                game_over = True

        if game_over:
            screen.fill(BLACK)
            game_over_text = font.render(f"Game Over! Score: {score}", True, WHITE)
            text_rect = game_over_text.get_rect(center=(WIDTH/2, HEIGHT/2))
            screen.blit(game_over_text, text_rect)
            pygame.display.flip()
            pygame.time.wait(2000)
            game_state = HOME_SCREEN
            continue

        # Invader movement logic
        for invader in invaders:
            if invader.rect.right >= WIDTH or invader.rect.left <= 0:
                invader_direction *= -1
                move_down = True
                break

        if move_down:
            for invader in invaders:
                invader.rect.y += 20
                invader.direction = invader_direction
            move_down = False

        # Draw
        screen.fill(BLACK)
        all_sprites.draw(screen)

        # Draw score
        score_text = small_font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
    
    clock.tick(60)

pygame.quit()