import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Storm Pilot")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GREY = (100, 100, 100)
BLACK = (0, 0, 0)

# Player (Plane)
plane_size = 20
plane_x = 50
plane_y = HEIGHT // 2 - plane_size // 2
plane_speed = 5

# Cities
city_size = 30
city_a_x = 0
city_a_y = HEIGHT // 2 - city_size // 2
city_b_x = WIDTH - city_size  # Fixed at right edge
city_b_y = HEIGHT // 2 - city_size // 2
city_b_visible = False  # City B starts invisible

# Storms
storm_width = 40
storm_height = 80
storms = []
scroll_speed = 3

# Timer
time_left = 60  # 60 seconds
font = pygame.font.Font(None, 36)  # Default font, size 36

def spawn_storm():
    storm_x = WIDTH + random.randint(0, 200)  # Spawn off-screen to the right
    storm_y = random.randint(0, HEIGHT - storm_height)
    storms.append(pygame.Rect(storm_x, storm_y, storm_width, storm_height))

# Game loop variables
clock = pygame.time.Clock()
running = True
storm_spawn_timer = 0
timer_tick = 0  # To track seconds

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Player movement with arrow keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] and plane_y > 0:
        plane_y -= plane_speed
    if keys[pygame.K_DOWN] and plane_y < HEIGHT - plane_size:
        plane_y += plane_speed
    if keys[pygame.K_LEFT] and plane_x > 0:
        plane_x -= plane_speed
    if keys[pygame.K_RIGHT] and plane_x < WIDTH - plane_size:
        plane_x += plane_speed

    # Scroll the world (move storms and City A to the left)
    city_a_x -= scroll_speed
    for storm in storms[:]:
        storm.x -= scroll_speed
        if storm.x + storm_width < 0:  # Remove storms that go off-screen
            storms.remove(storm)

    # Spawn new storms periodically
    storm_spawn_timer += 1
    if storm_spawn_timer > 30:  # Spawn every 60 frames (~1 second)
        spawn_storm()
        storm_spawn_timer = 0

    # Update timer (decrement every second)
    timer_tick += 1
    if timer_tick >= 60:  # 60 frames = ~1 second at 60 FPS
        time_left -= 1
        timer_tick = 0
    if time_left <= 0:
        time_left = 0
        city_b_visible = True  # Show City B when timer hits 0

    # Collision detection
    plane_rect = pygame.Rect(plane_x, plane_y, plane_size, plane_size)
    for storm in storms:
        if plane_rect.colliderect(storm):
            print("Crash! Game Over!")
            running = False

    if city_b_visible and plane_rect.colliderect(pygame.Rect(city_b_x, city_b_y, city_size, city_size)):
        print("You reached City B! You win!")
        running = False

    # Draw everything
    screen.fill(BLACK)  # Background
    pygame.draw.rect(screen, GREEN, (city_a_x, city_a_y, city_size, city_size))  # City A (scrolls)
    if city_b_visible:  # City B only draws when timer hits 0
        pygame.draw.rect(screen, BLUE, (city_b_x, city_b_y, city_size, city_size))
    pygame.draw.rect(screen, WHITE, (plane_x, plane_y, plane_size, plane_size))  # Plane
    for storm in storms:  # Storms
        pygame.draw.rect(screen, GREY, storm)

    # Draw timer
    timer_text = font.render(f"Time: {time_left}", True, WHITE)
    screen.blit(timer_text, (10, 10))  # Top-left corner

    # Update the display
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

# Quit Pygame
pygame.quit()