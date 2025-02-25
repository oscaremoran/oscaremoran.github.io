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
YELLOW = (255, 255, 0)  # Cannonball color

# Game variables
clock = pygame.time.Clock()
FPS = 60

# Cannon and target properties
cannon_pos = [WIDTH // 2, HEIGHT - 50]  # Cannon can move horizontally
cannon_speed = 5  # Pixels per frame
target_pos = [random.randint(0, WIDTH), 0]
target_speed = 2

# Cannonball properties
cannonball_pos = None  # [x, y] when active, None when inactive
cannonball_speed = -5  # Moves upward

# Player combo states
loader_combo = ['a', 's', 'd']  # Player 1 combo
gunner_combo = ['j', 'k', 'l']  # Player 2 combo
loader_input = []
gunner_input = []
loader_ready = False
gunner_ready = False
last_combo_time = 0  # Track when combos started
combo_timeout = 2  # 2 seconds to sync combos

# Game loop
running = True
while running:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            current_time = time.time()
            # Player 1 (Loader) inputs
            if event.key in [pygame.K_a, pygame.K_s, pygame.K_d]:
                if not loader_input:  # Start timer on first key
                    last_combo_time = current_time
                loader_input.append(pygame.key.name(event.key))
                if loader_input == loader_combo:
                    loader_ready = True
                    loader_input = []  # Reset after success
            # Player 2 (Gunner) inputs
            elif event.key in [pygame.K_j, pygame.K_k, pygame.K_l]:
                if not gunner_input:  # Start timer on first key
                    last_combo_time = current_time
                gunner_input.append(pygame.key.name(event.key))
                if gunner_input == gunner_combo:
                    gunner_ready = True
                    gunner_input = []  # Reset after success

    # Move cannon with arrow keys (Player 2)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and cannon_pos[0] > 20:  # Keep cannon in bounds
        cannon_pos[0] -= cannon_speed
    if keys[pygame.K_RIGHT] and cannon_pos[0] < WIDTH - 20:
        cannon_pos[0] += cannon_speed

    # Timeout check for combos
    current_time = time.time()
    if current_time - last_combo_time > combo_timeout and (loader_input or gunner_input):
        loader_ready = False
        gunner_ready = False
        loader_input = []
        gunner_input = []

    # Fire cannonball if both players are ready and no cannonball is active
    if loader_ready and gunner_ready and cannonball_pos is None:
        cannonball_pos = [cannon_pos[0], cannon_pos[1] - 20]  # Spawn at cannon's current position
        loader_ready = False
        gunner_ready = False
        last_combo_time = current_time  # Reset timer after firing

    # Move cannonball
    if cannonball_pos:
        cannonball_pos[1] += cannonball_speed
        # Check if cannonball hits target
        if (abs(cannonball_pos[0] - target_pos[0]) < 20 and 
            abs(cannonball_pos[1] - target_pos[1]) < 20):
            target_pos = [random.randint(0, WIDTH), 0]  # Reset target on hit
            cannonball_pos = None  # Remove cannonball
        # Remove cannonball if it goes off-screen
        elif cannonball_pos[1] < 0:
            cannonball_pos = None

    # Move target and check for game over
    target_pos[1] += target_speed
    if target_pos[1] > HEIGHT:
        running = False  # Quit game if target reaches bottom

    # Draw cannon, target, and cannonball
    pygame.draw.rect(screen, BLACK, (cannon_pos[0] - 20, cannon_pos[1] - 10, 40, 20))  # Cannon
    pygame.draw.circle(screen, RED, target_pos, 10)  # Target
    if cannonball_pos:
        pygame.draw.circle(screen, YELLOW, cannonball_pos, 5)  # Cannonball

    # Display combo status for debugging
    font = pygame.font.Font(None, 36)
    loader_text = font.render("Loader: " + " ".join(loader_input) + f" Ready: {loader_ready}", True, BLACK)
    gunner_text = font.render("Gunner: " + " ".join(gunner_input) + f" Ready: {gunner_ready}", True, BLACK)
    screen.blit(loader_text, (10, 10))
    screen.blit(gunner_text, (10, 50))

    # Update display
    pygame.display.flip()
    clock.tick(FPS)

# Quit Pygame
pygame.quit()