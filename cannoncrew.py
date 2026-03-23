import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cannon Crew")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)

# Game variables
clock = pygame.time.Clock()
FPS = 60

# Cannon and target properties
cannon_pos = [WIDTH // 2, HEIGHT - 50]
cannon_speed = 5
target_pos = [random.randint(0, WIDTH), 0]
target_speed = 1

# Cannonball properties
cannonball_pos = None
cannonball_speed = -5
cannonball_radius = 20

# Player combo states
loader_keys = ['a', 's', 'd']
gunner_keys = ['j', 'k', 'l']
loader_combo = random.sample(loader_keys, 3)
gunner_combo = random.sample(gunner_keys, 3)
loader_input = []
gunner_input = []
loader_ready = False
gunner_ready = False
last_combo_time = 0
combo_timeout = 2

# Round state
paused = False
pause_start_time = 0
pause_duration = 2  # 2 seconds pause

# Game loop
running = True
while running:
    screen.fill(WHITE)

    if not paused:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                current_time = time.time()
                if event.key in [pygame.K_a, pygame.K_s, pygame.K_d]:
                    if not loader_input:
                        last_combo_time = current_time
                    loader_input.append(pygame.key.name(event.key))
                    if loader_input == loader_combo:
                        loader_ready = True
                        loader_input = []
                        loader_combo = random.sample(loader_keys, 3)
                elif event.key in [pygame.K_j, pygame.K_k, pygame.K_l]:
                    if not gunner_input:
                        last_combo_time = current_time
                    gunner_input.append(pygame.key.name(event.key))
                    if gunner_input == gunner_combo:
                        gunner_ready = True
                        gunner_input = []
                        gunner_combo = random.sample(gunner_keys, 3)

        # Move cannon
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and cannon_pos[0] > 20:
            cannon_pos[0] -= cannon_speed
        if keys[pygame.K_RIGHT] and cannon_pos[0] < WIDTH - 20:
            cannon_pos[0] += cannon_speed

        # Combo timeout
        current_time = time.time()
        if current_time - last_combo_time > combo_timeout and (loader_input or gunner_input):
            loader_ready = False
            gunner_ready = False
            loader_input = []
            gunner_input = []

        # Fire cannonball
        if loader_ready and gunner_ready and cannonball_pos is None:
            cannonball_pos = [cannon_pos[0], cannon_pos[1] - 20]
            loader_ready = False
            gunner_ready = False
            last_combo_time = current_time

        # Move cannonball
        if cannonball_pos:
            cannonball_pos[1] += cannonball_speed
            if (abs(cannonball_pos[0] - target_pos[0]) < 20 and 
                abs(cannonball_pos[1] - target_pos[1]) < 20):
                target_pos = [random.randint(0, WIDTH), 0]
                cannonball_pos = None
            elif cannonball_pos[1] < 0:
                cannonball_pos = None

        # Move target and check for round end
        target_pos[1] += target_speed
        if target_pos[1] > HEIGHT:
            paused = True
            pause_start_time = time.time()
            cannonball_pos = None  # Clear any active cannonball

    # Handle pause and new round
    if paused:
        current_time = time.time()
        if current_time - pause_start_time >= pause_duration:
            paused = False
            target_pos = [random.randint(0, WIDTH), 0]  # Start new round
        else:
            # Display "Round Over" during pause
            font = pygame.font.Font(None, 48)
            pause_text = font.render("Round Over", True, BLACK)
            screen.blit(pause_text, (WIDTH // 2 - 100, HEIGHT // 2 - 24))

    # Draw game elements
    pygame.draw.rect(screen, BLACK, (cannon_pos[0] - 20, cannon_pos[1] - 10, 40, 20))
    pygame.draw.circle(screen, RED, target_pos, 10)
    if cannonball_pos:
        pygame.draw.circle(screen, YELLOW, cannonball_pos, cannonball_radius)

    # Display combos and status
    font = pygame.font.Font(None, 36)
    loader_combo_text = font.render(f"Loader Combo: {' -> '.join(loader_combo)}", True, BLACK)
    gunner_combo_text = font.render(f"Gunner Combo: {' -> '.join(gunner_combo)}", True, BLACK)
    loader_input_text = font.render("Loader: " + " ".join(loader_input) + f" Ready: {loader_ready}", True, BLACK)
    gunner_input_text = font.render("Gunner: " + " ".join(gunner_input) + f" Ready: {gunner_ready}", True, BLACK)
    screen.blit(loader_combo_text, (10, 10))
    screen.blit(gunner_combo_text, (10, 50))
    screen.blit(loader_input_text, (10, 90))
    screen.blit(gunner_input_text, (10, 130))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()