import asyncio
import platform
import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH = 1600
HEIGHT = 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spacewar!")


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)

# Fonts
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)


# Game states
MENU = 0
AI_DIFFICULTY = 1
ASTEROID_INPUT = 2
GAME = 3
game_state = MENU
mode = None  # 'pvp' or 'ai'
ai_difficulty = None  # 'easy', 'hard', 'master', 'ultra_master'
asteroid_count = 3
asteroid_input = ""
winner = None
cheat_unlocked = False
cheat_message = None
cheat_message_timer = 0

# Konami Code
konami_code = [
    pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN,
    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT,
    pygame.K_b, pygame.K_a, pygame.K_RETURN
]
konami_index = 0

# Ship class
class Ship:
    def __init__(self, x, y, color, angle=0):
        self.x = x
        self.y = y
        self.color = color
        self.angle = angle
        self.speed_x = 0
        self.speed_y = 0
        self.size = 20
        self.shoot_cooldown = 0
        self.alive = True
        self.invincible = False  # Added for invincibility feature
        self.invincibility_timer = 0  # Added for invincibility feature

    def rotate(self, direction):
        self.angle += direction * 5

    def move(self):
        self.speed_x += math.cos(math.radians(self.angle)) * 0.02
        self.speed_y -= math.sin(math.radians(self.angle)) * 0.02
        self.x += self.speed_x
        self.y += self.speed_y
        self.x = self.x % WIDTH
        self.y = self.y % HEIGHT

    def draw(self, screen):
        if self.alive:
            color = (255, 255, 0) if self.invincible else self.color  # Yellow if invincible, else normal color
            points = [
                (self.x + self.size * math.cos(math.radians(self.angle)),
                 self.y - self.size * math.sin(math.radians(self.angle))),
                (self.x + self.size * math.cos(math.radians(self.angle + 135)),
                 self.y - self.size * math.sin(math.radians(self.angle + 135))),
                (self.x + self.size * math.cos(math.radians(self.angle - 135)),
                 self.y - self.size * math.sin(math.radians(self.angle - 135)))
            ]
            pygame.draw.polygon(screen, color, points)

    def shoot(self, bullets):
        if self.shoot_cooldown <= 0 and self.alive:
            bullets.append(Bullet(self.x, self.y, self.angle, self.color))
            self.shoot_cooldown = 20

# Bullet class
class Bullet:
     def __init__(self, x, y, angle, color, speed=5, life=60, size=2):
         self.x = x
         self.y = y
         self.speed = speed
         self.angle = angle
         self.color = color
         self.life = life
         self.size = size

     def move(self):
         self.x += math.cos(math.radians(self.angle)) * self.speed
         self.y -= math.sin(math.radians(self.angle)) * self.speed
         self.life -= 1
         self.x = self.x % WIDTH
         self.y = self.y % HEIGHT

     def draw(self, screen):
         pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

# Asteroid class
class Asteroid:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = 10
        self.speed_x = random.uniform(-0.5, 0.5)
        self.speed_y = random.uniform(-0.5, 0.5)

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.x = self.x % WIDTH
        self.y = self.y % HEIGHT

    def draw(self, screen):
        pygame.draw.circle(screen, GRAY, (int(self.x), int(self.y)), self.size)

# AI logic
def ai_control(player, opponent, bullets, asteroids, difficulty):
    if not opponent.alive:
        return

    # Calculate angle to player
    dx = player.x - opponent.x
    dy = player.y - opponent.y
    angle_to_player = math.degrees(math.atan2(-dy, dx)) % 360

    # Difficulty-based parameters
    if difficulty == 'easy':
        rotation_speed = 2
        shoot_chance = 0.01
        move_chance = 0.06
        accuracy = 40
        speed_boost = 0.02  # Slower thrust for Easy
        special_chance = 0.0
    elif difficulty == 'hard':
        rotation_speed = 5
        shoot_chance = 0.06
        move_chance = 0.3
        accuracy = 20
        speed_boost = 0.02  # Standard thrust
        special_chance = 0.01  # Small chance for specials
    elif difficulty == 'master':
        rotation_speed = 8
        shoot_chance = 0.15
        move_chance = 0.6
        accuracy = 8
        speed_boost = 0.02  # Standard thrust
        special_chance = 0.05  # Medium chance for specials
    else:  # ultra_master
        rotation_speed = 12
        shoot_chance = 0.3
        move_chance = 0.6
        accuracy = 3
        speed_boost = 0.02  # Standard thrust
        special_chance = 0.05  # Medium chance for specials

    # Update invincibility timer
    if opponent.invincibility_timer > 0:
        opponent.invincibility_timer -= 1
        if opponent.invincibility_timer <= 0:
            opponent.invincible = False

    # Rotate towards player
    angle_diff = (angle_to_player - opponent.angle) % 360
    if angle_diff > 180:
        angle_diff -= 360
    if abs(angle_diff) > accuracy:
        opponent.rotate(1 if angle_diff > 0 else -1)

    # Move with standardized thrust
    if random.random() < move_chance:
        opponent.speed_x += math.cos(math.radians(opponent.angle)) * speed_boost
        opponent.speed_y -= math.sin(math.radians(opponent.angle)) * speed_boost
        opponent.x += opponent.speed_x
        opponent.y += opponent.speed_y
        opponent.x = opponent.x % WIDTH
        opponent.y = opponent.y % HEIGHT

    # Regular shoot when aligned
    if random.random() < shoot_chance and abs(angle_diff) < accuracy:
        opponent.shoot(bullets)

    # Special attacks
    if random.random() < special_chance:
        if difficulty == 'hard':
            choice = random.choice(['rapid', 'big'])
            if choice == 'rapid':
                # Rapid-fire: 3 bullets with slight angle variance
                for _ in range(3):
                    var_angle = opponent.angle + random.uniform(-5, 5)
                    bullets.append(Bullet(opponent.x, opponent.y, var_angle, opponent.color))
            elif choice == 'big':
                # Big bullet: Slower, larger size
                bullets.append(Bullet(opponent.x, opponent.y, opponent.angle, opponent.color, speed=3, size=10))
        elif difficulty == 'master':
            choice = random.choice(['ultrarapid', 'invincible'])
            if choice == 'ultrarapid':
                # Ultra-rapid-fire: 10 bullets with wider variance
                for _ in range(10):
                    var_angle = opponent.angle + random.uniform(-10, 10)
                    bullets.append(Bullet(opponent.x, opponent.y, var_angle, opponent.color))
            elif choice == 'invincible':
                # Temporary invincibility with yellow glow
                opponent.invincible = True
                opponent.invincibility_timer = 45  # 2 seconds at 60 FPS
        elif difficulty == 'ultra_master':
            choice = random.choice(['sparks', 'laser', 'invincible'])
            if choice == 'sparks':
                # Fire blue sparks all over the arena (20 small random bullets)
                for _ in range(20):
                    rand_angle = random.uniform(0, 360)
                    bullets.append(Bullet(opponent.x, opponent.y, rand_angle, BLUE, speed=3, life=30, size=1))
            elif choice == 'laser':
                # Red laser crackling bolt: Fast, medium size, red color
                bullets.append(Bullet(opponent.x, opponent.y, opponent.angle, BLUE, speed=10, life=40, size=20))
            elif choice == 'invincible':
                # Temporary invincibility with yellow glow
                opponent.invincible = True
                opponent.invincibility_timer = 90  # 3 seconds at 60 FPS

    # Avoid asteroids
    for asteroid in asteroids:
        dist = math.hypot(asteroid.x - opponent.x, asteroid.y - opponent.y)
        if dist < 50:
            angle_to_asteroid = math.degrees(math.atan2(-(asteroid.y - opponent.y), asteroid.x - opponent.x)) % 360
            angle_diff = (angle_to_asteroid - opponent.angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            avoidance_chance = 0.5 if difficulty == 'easy' else 0.8 if difficulty == 'hard' else 0.95 if difficulty == 'master' else 1.0
            if random.random() < avoidance_chance:
                opponent.rotate(-1 if angle_diff > 0 else 1)

    # Move more frequently
    if random.random() < move_chance:
        opponent.move()

    # Shoot when aligned
    if random.random() < shoot_chance and abs(angle_diff) < accuracy:
        opponent.shoot(bullets)

    # Avoid asteroids
    for asteroid in asteroids:
        dist = math.hypot(asteroid.x - opponent.x, asteroid.y - opponent.y)
        if dist < 50:
            angle_to_asteroid = math.degrees(math.atan2(-(asteroid.y - opponent.y), asteroid.x - opponent.x)) % 360
            angle_diff = (angle_to_asteroid - opponent.angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            if difficulty in ['hard', 'master', 'ultra_master'] or random.random() < 0.5:
                opponent.rotate(-1 if angle_diff > 0 else 1)

# Button class
class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = WHITE

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text = small_font.render(self.text, True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Game setup
player1 = None
player2 = None
bullets = []
asteroids = []
clock = pygame.time.Clock()
FPS = 60

# Menu buttons
pvp_button = Button("PvP Mode", WIDTH//2 - 100, HEIGHT//2 - 50, 200, 50)
ai_button = Button("AI Mode", WIDTH//2 - 100, HEIGHT//2 + 10, 200, 50)
easy_button = Button("Easy", WIDTH//2 - 100, HEIGHT//2 - 110, 200, 50)
hard_button = Button("Hard", WIDTH//2 - 100, HEIGHT//2 - 50, 200, 50)
master_button = Button("Master", WIDTH//2 - 100, HEIGHT//2 + 10, 200, 50)
ultra_master_button = Button("Ultra Master", WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50)
submit_button = Button("Submit", WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50)
back_button = Button("Back to Menu", WIDTH//2 - 100, HEIGHT//2 + 50, 200, 50)

async def main():
    global game_state, mode, ai_difficulty, asteroid_count, asteroid_input, player1, player2, bullets, asteroids, winner, cheat_unlocked, cheat_message, cheat_message_timer, konami_index

    def setup():
        global player1, player2, bullets, asteroids, winner
        player1 = Ship(100, HEIGHT // 2, RED, 0)
        player2 = Ship(WIDTH - 100, HEIGHT // 2, BLUE, 180)
        bullets = []
        asteroids = [Asteroid() for _ in range(asteroid_count)]
        winner = None

    async def update_loop():
        global game_state, mode, ai_difficulty, asteroid_count, asteroid_input, player1, player2, bullets, asteroids, winner, cheat_unlocked, cheat_message, cheat_message_timer, konami_index
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if game_state == MENU:
                    if pvp_button.is_clicked(pos):
                        mode = 'pvp'
                        game_state = ASTEROID_INPUT
                    elif ai_button.is_clicked(pos):
                        game_state = AI_DIFFICULTY
                elif game_state == AI_DIFFICULTY:
                    if easy_button.is_clicked(pos):
                        ai_difficulty = 'easy'
                        game_state = ASTEROID_INPUT
                    elif hard_button.is_clicked(pos):
                        ai_difficulty = 'hard'
                        game_state = ASTEROID_INPUT
                    elif master_button.is_clicked(pos):
                        ai_difficulty = 'master'
                        game_state = ASTEROID_INPUT
                    elif cheat_unlocked and ultra_master_button.is_clicked(pos):
                        ai_difficulty = 'ultra_master'
                        game_state = ASTEROID_INPUT
                elif game_state == ASTEROID_INPUT and submit_button.is_clicked(pos):
                    try:
                        asteroid_count = max(0, int(asteroid_input))
                        game_state = GAME
                        setup()
                    except ValueError:
                        asteroid_input = ""
                elif game_state == GAME and winner and back_button.is_clicked(pos):
                    game_state = MENU
                    mode = None
                    ai_difficulty = None
                    asteroid_count = 3
                    asteroid_input = ""
                    winner = None
            elif event.type == pygame.KEYDOWN:
                if game_state == MENU:
                    if event.key == konami_code[konami_index]:
                        konami_index += 1
                        if konami_index == len(konami_code):
                            cheat_unlocked = True
                            cheat_message = "You are great!! Ultra Master difficulty unlocked!!"
                            cheat_message_timer = 180  # 3 seconds at 60 FPS
                            konami_index = 0
                    else:
                        konami_index = 0
                elif game_state == ASTEROID_INPUT:
                    if event.key == pygame.K_RETURN:
                        try:
                            asteroid_count = max(0, int(asteroid_input))
                            game_state = GAME
                            setup()
                        except ValueError:
                            asteroid_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        asteroid_input = asteroid_input[:-1]
                    elif event.unicode.isdigit():
                        asteroid_input += event.unicode

        if game_state == MENU:
            screen.fill(BLACK)
            pvp_button.draw(screen)
            ai_button.draw(screen)
            if cheat_message and cheat_message_timer > 0:
                text = small_font.render(cheat_message, True, WHITE)
                text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 110))
                screen.blit(text, text_rect)
                cheat_message_timer -= 1
                if cheat_message_timer <= 0:
                    cheat_message = None

        elif game_state == AI_DIFFICULTY:
            screen.fill(BLACK)
            easy_button.draw(screen)
            hard_button.draw(screen)
            master_button.draw(screen)
            if cheat_unlocked:
                ultra_master_button.draw(screen)
        elif game_state == ASTEROID_INPUT:
            screen.fill(BLACK)
            text = small_font.render("Enter number of asteroids:", True, WHITE)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            screen.blit(text, text_rect)
            input_text = small_font.render(asteroid_input, True, WHITE)
            input_rect = input_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(input_text, input_rect)
            submit_button.draw(screen)
        elif game_state == GAME:
            if player1 is None or player2 is None:
                setup()  # Ensure players are initialized
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

            # Player 2 controls or AI
            if mode == 'pvp':
                if keys[pygame.K_LEFT]:
                    player2.rotate(1)
                if keys[pygame.K_RIGHT]:
                    player2.rotate(-1)
                if keys[pygame.K_UP]:
                    player2.move()
                if keys[pygame.K_RETURN]:
                    player2.shoot(bullets)
            else:
                ai_control(player1, player2, bullets, asteroids, ai_difficulty)

            # Update positions
            if not keys[pygame.K_w]:
                player1.x += player1.speed_x
                player1.y += player1.speed_y
                player1.x = player1.x % WIDTH
                player1.y = player1.y % HEIGHT
            if mode == 'pvp' and not keys[pygame.K_UP]:
                player2.x += player2.speed_x
                player2.y += player2.speed_y
                player2.x = player2.x % WIDTH
                player2.y = player2.y % HEIGHT
            elif mode == 'ai':
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
                elif winner is None:
                    if player1.alive and math.hypot(bullet.x - player1.x, bullet.y - player1.y) < player1.size + bullet.size and bullet.color != RED:
                        player1.alive = False
                        winner = "PLAYER TWO WINS" if mode == 'pvp' else "AI WINS"
                    elif player2.alive and          math.hypot(bullet.x - player2.x, bullet.y - player2.y) < player2.size + bullet.size and bullet.color != BLUE:
                        player2.alive = False
                        winner = "PLAYER ONE WINS"

            # Update asteroids
            for asteroid in asteroids:
                asteroid.move()
                if winner is None:
                    if player1.alive and math.hypot(asteroid.x - player1.x, asteroid.y - player1.y) < (player1.size + asteroid.size):
                        player1.alive = False
                        winner = "PLAYER TWO WINS" if mode == 'pvp' else "AI WINS"
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
            if winner:
                text = font.render(winner, True, WHITE)
                text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(text, text_rect)
                back_button.draw(screen)

        pygame.display.flip()
        return True

    running = True
    while running:
        running = await update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())