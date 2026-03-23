import asyncio
import platform
import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ice Cream Catch")

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
BLACK = (0, 0, 0)

# Game variables
FPS = 60
cone_width = 60
cone_height = 80
cone_x = WIDTH // 2 - cone_width // 2
cone_y = HEIGHT - cone_height - 10
cone_speed = 5
ice_cream_size = 30
ice_cream_speed = 3
ice_creams = []
score = 0
game_time = 15.0
start_time = time.time()
last_spawn_time = time.time()  # Track time for spawning ice creams
orders = []
current_order = 0
font = pygame.font.SysFont("arial", 24)
running = True  # Flag to control game loop

# Customer order
def new_order():
    return random.randint(1, 3)

# Ice cream object
class IceCream:
    def __init__(self):
        self.x = random.randint(0, WIDTH - ice_cream_size)
        self.y = -ice_cream_size
        self.caught = False

# Setup game
def setup():
    global orders, current_order, ice_creams, cone_x, score, start_time, last_spawn_time
    orders = [new_order()]
    current_order = orders[0]
    ice_creams = [IceCream()]
    cone_x = WIDTH // 2 - cone_width // 2
    score = 0
    start_time = time.time()
    last_spawn_time = time.time()

# Update game loop
def update_loop():
    global cone_x, ice_creams, score, game_time, orders, current_order, running, last_spawn_time, start_time

    # Spawn new ice cream every second
    current_time = time.time()
    if current_time - last_spawn_time >= 1.0:
        ice_creams.append(IceCream())
        last_spawn_time = current_time

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            caught_count = sum(1 for ic in ice_creams if ic.caught)
            if caught_count == current_order:
                score += 1
                game_time -= 0.5
                start_time = time.time()  # Reset timer after serving
                orders.append(new_order())
                orders.pop(0)
                current_order = orders[0]
                ice_creams = [IceCream()]  # Reset to one new ice cream after serving
                last_spawn_time = time.time()  # Reset spawn timer

    # Move cone
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and cone_x > 0:
        cone_x -= cone_speed
    if keys[pygame.K_RIGHT] and cone_x < WIDTH - cone_width:
        cone_x += cone_speed

    # Update ice creams
    for ic in ice_creams[:]:  # Iterate over a copy to allow removal
        if not ic.caught:
            ic.y += ice_cream_speed
            # Check collision with cone
            if (cone_x <= ic.x <= cone_x + cone_width and
                cone_y <= ic.y + ice_cream_size <= cone_y + cone_height):
                ic.caught = True
            # Remove if off screen
            if ic.y > HEIGHT:
                ice_creams.remove(ic)

    # Draw everything
    screen.fill(WHITE)
    
    # Draw cone
    pygame.draw.polygon(screen, BROWN, [
        (cone_x, cone_y + cone_height),
        (cone_x + cone_width // 2, cone_y),
        (cone_x + cone_width, cone_y + cone_height)
    ])
    
    # Draw ice creams
    caught_count = 0
    for ic in ice_creams:
        if ic.caught:
            y_offset = cone_y - (caught_count + 1) * ice_cream_size
            pygame.draw.circle(screen, BLUE, (cone_x + cone_width // 2, y_offset), ice_cream_size // 2)
            caught_count += 1
        else:
            pygame.draw.circle(screen, BLUE, (ic.x, ic.y), ice_cream_size // 2)
    
    # Draw orders and stats
    order_text = font.render(f"Order: {current_order} ice cream(s)", True, BLACK)
    score_text = font.render(f"Customers Served: {score}", True, BLACK)
    time_left = max(0, game_time - (time.time() - start_time))
    time_text = font.render(f"Time: {time_left:.1f}s", True, BLACK)
    screen.blit(order_text, (10, 10))
    screen.blit(score_text, (10, 40))
    screen.blit(time_text, (10, 70))
    
    # Check game over
    if time_left <= 0:
        game_over_text = font.render(f"Game Over! Score: {score}", True, BLACK)
        screen.blit(game_over_text, (WIDTH // 2 - 100, HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False
        return

    pygame.display.flip()

# Main async function
async def main():
    global running
    setup()
    while running:
        update_loop()
        await asyncio.sleep(1.0 / FPS)
    pygame.quit()

# Run game
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        try:
            asyncio.run(main())
        finally:
            pygame.quit()