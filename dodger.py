import pygame
import random
import asyncio
import platform
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disaster Avoider")

# Colors
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Player properties
player_size = 20
player_x = WIDTH // 2
player_y = 50
player_speed = 5
player_rect = pygame.Rect(player_x, player_y, player_size, player_size)

# Building blocks
building_size = 50
buildings = [
    pygame.Rect(50, 50, building_size, building_size),  # Top-left
    pygame.Rect(WIDTH - 50 - building_size, 50, building_size, building_size),  # Top-right
    pygame.Rect(50, HEIGHT - 50 - building_size, building_size, building_size),  # Bottom-left
    pygame.Rect(WIDTH - 50 - building_size, HEIGHT - 50 - building_size, building_size, building_size),  # Bottom-right
    pygame.Rect(WIDTH // 2 - building_size // 2, HEIGHT // 2 - building_size // 2, building_size, building_size),  # Center
]

# Disaster properties
disaster_interval = 10  # Initial interval in seconds
disaster_timer = 0
disaster_type = None
disaster_active = False
tornado_blocks = []
tornado_speed = 5
tornado_direction = 1
tornado_passes = 0
earthquake_shake = 0
earthquake_duration = 0
flood_blocks = []
flood_triangle = None
flood_spawned = False
game_over = False

# Clock for frame rate
FPS = 60
clock = pygame.time.Clock()

def reset_game():
    global player_rect, buildings, disaster_interval, disaster_timer, disaster_type, disaster_active
    global tornado_blocks, tornado_direction, tornado_passes, earthquake_shake, earthquake_duration
    global flood_blocks, flood_triangle, flood_spawned, game_over
    player_rect = pygame.Rect(WIDTH // 2, 50, player_size, player_size)
    buildings = [
        pygame.Rect(50, 50, building_size, building_size),
        pygame.Rect(WIDTH - 50 - building_size, 50, building_size, building_size),
        pygame.Rect(50, HEIGHT - 50 - building_size, building_size, building_size),
        pygame.Rect(WIDTH - 50 - building_size, HEIGHT - 50 - building_size, building_size, building_size),
        pygame.Rect(WIDTH // 2 - building_size // 2, HEIGHT // 2 - building_size // 2, building_size, building_size),
    ]
    disaster_interval = 10
    disaster_timer = 0
    disaster_type = None
    disaster_active = False
    tornado_blocks = []
    tornado_direction = 1
    tornado_passes = 0
    earthquake_shake = 0
    earthquake_duration = 0
    flood_blocks = []
    flood_triangle = None
    flood_spawned = False
    game_over = False

def spawn_tornado():
    global tornado_blocks, disaster_active, tornado_direction, tornado_passes
    tornado_blocks = []
    block_size = 30
    num_blocks = 20
    start_x = -block_size if tornado_direction == 1 else WIDTH
    for i in range(num_blocks):
        offset_y = random.randint(0, HEIGHT - block_size)
        tornado_blocks.append(pygame.Rect(start_x, offset_y, block_size, block_size))
    disaster_active = True
    tornado_passes = 0

def spawn_earthquake():
    global earthquake_shake, earthquake_duration, disaster_active
    earthquake_shake = 10
    earthquake_duration = FPS * 5  # 5 seconds
    disaster_active = True

def spawn_flood():
    global flood_triangle, disaster_active, flood_spawned
    flood_triangle = (WIDTH // 2, 0)
    disaster_active = True
    flood_spawned = False

def update_tornado():
    global tornado_blocks, disaster_active, tornado_direction, tornado_passes
    all_offscreen = True
    for block in tornado_blocks[:]:
        block.x += tornado_speed * tornado_direction
        if 0 <= block.x <= WIDTH:
            all_offscreen = False
        # Check collision with player
        if block.colliderect(player_rect):
            return True  # Player dies
        # Check collision with buildings
        for building in buildings[:]:
            if block.colliderect(building):
                tornado_blocks.remove(block)
                buildings.remove(building)
                break
    # Check if tornado is offscreen
    if all_offscreen:
        tornado_passes += 1
        if tornado_passes < 2:
            tornado_direction *= -1
            start_x = -30 if tornado_direction == 1 else WIDTH
            for block in tornado_blocks:
                block.x = start_x
        else:
            disaster_active = False
            tornado_blocks = []
    return False

def update_earthquake():
    global earthquake_shake, earthquake_duration, disaster_active
    earthquake_duration -= 1
    if earthquake_duration <= 0:
        earthquake_shake = 0
        disaster_active = False
    # Check if player is offscreen
    if (player_rect.left < 0 or player_rect.right > WIDTH or
        player_rect.top < 0 or player_rect.bottom > HEIGHT):
        return True  # Player dies
    return False

def update_flood():
    global flood_blocks, flood_triangle, disaster_active, flood_spawned
    if flood_triangle:
        if pygame.time.get_ticks() % 1000 < 16:  # Approx 1 second
            flood_triangle = None
            flood_spawned = True
            # Spawn flood blocks at bottom
            for _ in range(50):
                x = random.randint(0, WIDTH - 20)
                flood_blocks.append(pygame.Rect(x, HEIGHT - 20, 20, 20))
    if flood_spawned:
        # Check if player is on a building
        on_building = False
        for building in buildings:
            if player_rect.colliderect(building):
                on_building = True
                break
        # Check collision with flood blocks
        for block in flood_blocks:
            if block.colliderect(player_rect) and not on_building:
                return True  # Player dies
        # End flood after 5 seconds
        if pygame.time.get_ticks() % 5000 < 16:
            flood_blocks = []
            disaster_active = False
            flood_spawned = False
    return False

def setup():
    reset_game()

def update_loop():
    global disaster_timer, disaster_type, disaster_active, game_over, disaster_interval
    if game_over:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()
        return

    # Handle input
    keys = pygame.key.get_pressed()
    new_rect = player_rect.copy()
    if keys[pygame.K_LEFT]:
        new_rect.x -= player_speed
    if keys[pygame.K_RIGHT]:
        new_rect.x += player_speed
    if keys[pygame.K_UP]:
        new_rect.y -= player_speed
    if keys[pygame.K_DOWN]:
        new_rect.y += player_speed

    # Check collision with buildings
    can_move = True
    for building in buildings:
        if new_rect.colliderect(building):
            can_move = False
            break
    if can_move:
        player_rect.x = new_rect.x
        player_rect.y = new_rect.y

    # Keep player in bounds
    player_rect.clamp_ip(screen.get_rect())

    # Update disaster timer
    disaster_timer += 1 / FPS
    if not disaster_active and disaster_timer >= disaster_interval:
        disaster_type = random.choice(["tornado", "earthquake", "flood"])
        if disaster_type == "tornado":
            spawn_tornado()
        elif disaster_type == "earthquake":
            spawn_earthquake()
        elif disaster_type == "flood":
            spawn_flood()
        disaster_timer = 0
        disaster_interval = max(2, disaster_interval - 0.5)

    # Update disasters
    player_dies = False
    if disaster_active:
        if disaster_type == "tornado":
            player_dies = update_tornado()
        elif disaster_type == "earthquake":
            player_dies = update_earthquake()
        elif disaster_type == "flood":
            player_dies = update_flood()

    if player_dies:
        game_over = True

    # Draw everything
    screen.fill(BLACK)
    shake_x = random.randint(-earthquake_shake, earthquake_shake) if earthquake_shake else 0
    shake_y = random.randint(-earthquake_shake, earthquake_shake) if earthquake_shake else 0

    # Draw buildings
    for building in buildings:
        pygame.draw.rect(screen, WHITE, building.move(shake_x, shake_y))

    # Draw player
    pygame.draw.rect(screen, WHITE, player_rect.move(shake_x, shake_y))

    # Draw disasters
    if disaster_type == "tornado":
        for block in tornado_blocks:
            pygame.draw.rect(screen, GRAY, block.move(shake_x, shake_y))
    elif disaster_type == "flood":
        if flood_triangle:
            pygame.draw.polygon(screen, RED, [
                (flood_triangle[0], flood_triangle[1]),
                (flood_triangle[0] - 20, flood_triangle[1] + 40),
                (flood_triangle[0] + 20, flood_triangle[1] + 40)
            ])
        for block in flood_blocks:
            pygame.draw.rect(screen, BLUE, block.move(shake_x, shake_y))

    # Draw game over screen
    if game_over:
        font = pygame.font.SysFont("arial", 36)
        text = font.render("Game Over! Press R to Restart", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))

    pygame.display.flip()
    clock.tick(FPS)

async def main():
    setup()
    while True:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())