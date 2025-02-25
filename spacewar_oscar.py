import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spacewar!")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)

# Ship class
class Ship:
    def __init__(self, x, y, color, angle=0):
        self.x = x
        self.y = y
        self.color = color
        self.angle = angle  # Initial angle parameter
        self.speed_x = 0
        self.speed_y = 0
        self.size = 20
        self.shoot_cooldown = 0
        self.alive = True

    def rotate(self, direction):
        self.angle += direction * 5

    def move(self):
        # Thrust (slow movement)
        self.speed_x += math.cos(math.radians(self.angle)) * 0.02
        self.speed_y -= math.sin(math.radians(self.angle)) * 0.02
        self.x += self.speed_x
        self.y += self.speed_y
        self.x = self.x % WIDTH
        self.y = self.y % HEIGHT

    def draw(self, screen):
        if self.alive:
            points = [
                (self.x + self.size * math.cos(math.radians(self.angle)),
                 self.y - self.size * math.sin(math.radians(self.angle))),
                (self.x + self.size * math.cos(math.radians(self.angle + 135)),
                 self.y - self.size * math.sin(math.radians(self.angle + 135))),
                (self.x + self.size * math.cos(math.radians(self.angle - 135)),
                 self.y - self.size * math.sin(math.radians(self.angle - 135)))
            ]
            pygame.draw.polygon(screen, self.color, points)

    def shoot(self, bullets):
        if self.shoot_cooldown <= 0 and self.alive:
            bullets.append(Bullet(self.x, self.y, self.angle, self.color))
            self.shoot_cooldown = 20

# Bullet class
class Bullet:
    def __init__(self, x, y, angle, color):
        self.x = x
        self.y = y
        self.speed = 5
        self.angle = angle
        self.color = color
        self.life = 60

    def move(self):
        self.x += math.cos(math.radians(self.angle)) * self.speed
        self.y -= math.sin(math.radians(self.angle)) * self.speed
        self.life -= 1
        self.x = self.x % WIDTH
        self.y = self.y % HEIGHT

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 2)

# Asteroid class
class Asteroid:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = 10  # Small asteroid
        self.speed_x = random.uniform(-0.5, 0.5)  # Slow drift
        self.speed_y = random.uniform(-0.5, 0.5)

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.x = self.x % WIDTH
        self.y = self.y % HEIGHT

    def draw(self, screen):
        pygame.draw.circle(screen, GRAY, (int(self.x), int(self.y)), self.size)

# Game setup
player1 = Ship(100, HEIGHT // 2, RED, 0)      # Red ship starts facing right (0 degrees)
player2 = Ship(WIDTH - 100, HEIGHT // 2, BLUE, 180)  # Blue ship starts facing left (180 degrees)
bullets = []
asteroids = [Asteroid() for _ in range(3)]  # Create 3 asteroids
clock = pygame.time.Clock()
font = pygame.font.Font(None, 74)
winner = None

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Controls
    keys = pygame.key.get_pressed()
    
    # Player 1 controls
    if keys[pygame.K_a]:
        player1.rotate(1)
    if keys[pygame.K_d]:
        player1.rotate(-1)
    if keys[pygame.K_w]:
        player1.move()
    if keys[pygame.K_SPACE]:
        player1.shoot(bullets)

    # Player 2 controls
    if keys[pygame.K_LEFT]:
        player2.rotate(1)
    if keys[pygame.K_RIGHT]:
        player2.rotate(-1)
    if keys[pygame.K_UP]:
        player2.move()
    if keys[pygame.K_RETURN]:
        player2.shoot(bullets)

    # Update positions (no gravity)
    if not keys[pygame.K_w]:
        player1.x += player1.speed_x
        player1.y += player1.speed_y
        player1.x = player1.x % WIDTH
        player1.y = player1.y % HEIGHT
    if not keys[pygame.K_UP]:
        player2.x += player2.speed_x
        player2.y += player2.speed_y
        player2.x = player2.x % WIDTH
        player2.y = player2.y % HEIGHT
    
    player1.shoot_cooldown = max(0, player1.shoot_cooldown - 1)
    player2.shoot_cooldown = max(0, player2.shoot_cooldown - 1)

    # Update bullets
    for bullet in bullets[:]:
        bullet.move()
        if bullet.life <= 0:
            bullets.remove(bullet)
        # Collision with bullets (only set winner if not already set)
        elif winner is None:  # Check if no winner has been declared yet
            if player1.alive and math.hypot(bullet.x - player1.x, bullet.y - player1.y) < player1.size and bullet.color != RED:
                player1.alive = False
                winner = "PLAYER TWO WINS"
            elif player2.alive and math.hypot(bullet.x - player2.x, bullet.y - player2.y) < player2.size and bullet.color != BLUE:
                player2.alive = False
                winner = "PLAYER ONE WINS"

    # Update asteroids
    for asteroid in asteroids:
        asteroid.move()
        
        # Collision with asteroids (only set winner if not already set)
        if winner is None:  # Check if no winner has been declared yet
            if player1.alive and math.hypot(asteroid.x - player1.x, asteroid.y - player1.y) < (player1.size + asteroid.size):
                player1.alive = False
                winner = "PLAYER TWO WINS"
            if player2.alive and math.hypot(asteroid.x - player2.x, asteroid.y - player2.y) < (player2.size + asteroid.size):
                player2.alive = False
                winner = "PLAYER ONE WINS"

    # Draw
    screen.fill(BLACK)
    player1.draw(screen)
    player2.draw(screen)
    for bullet in bullets:
        bullet.draw(screen)
    for asteroid in asteroids:
        asteroid.draw(screen)
    
    # Display winner
    if winner:
        text = font.render(winner, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, text_rect)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()