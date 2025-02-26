import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("X-Wing vs Death Star")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

# X-Wing properties
xwing_pos = [WIDTH // 2, HEIGHT - 60]
xwing_speed = 5
xwing_width = 50
xwing_height = 40

# Laser properties
lasers = []
laser_speed = -10
laser_width = 4
laser_height = 20

# TIE Fighter properties
tie_fighters = []
tie_speed = 2
tie_width = 30
tie_height = 30
tie_spawn_timer = 0
tie_lasers = []
tie_laser_speed = 5

# Death Star properties
deathstar_pos = [WIDTH // 2, 100]
deathstar_radius = 80
deathstar_health = 100

# Score and Timers
score = 0
font = pygame.font.Font(None, 36)
start_time = pygame.time.get_ticks()
initial_timer_limit = 20 * 1000
wipeout_timer_limit = 30 * 1000
wipeout_start_time = None

# Maneuver properties
maneuver = random.randint(1, 2)
maneuver_timer = 0
maneuver_switch_interval = 180  # 3 seconds at 60 FPS
yellow_circle_pos = [random.randint(0, WIDTH), random.randint(0, HEIGHT)]
green_line_start = [random.randint(0, WIDTH), random.randint(0, HEIGHT)]
green_line_end = [random.randint(0, WIDTH), random.randint(0, HEIGHT)]

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                lasers.append([xwing_pos[0] + xwing_width // 2 - laser_width // 2, xwing_pos[1]])

    # X-Wing movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and xwing_pos[0] > 0:
        xwing_pos[0] -= xwing_speed
    if keys[pygame.K_RIGHT] and xwing_pos[0] < WIDTH - xwing_width:
        xwing_pos[0] += xwing_speed
    if keys[pygame.K_UP] and xwing_pos[1] > 0:
        xwing_pos[1] -= xwing_speed
    if keys[pygame.K_DOWN] and xwing_pos[1] < HEIGHT - xwing_height:
        xwing_pos[1] += xwing_speed

    # Spawn TIE Fighters
    tie_spawn_timer += 1
    if tie_spawn_timer >= 60 and len(tie_fighters) < 5:
        angle = random.uniform(0, 2 * math.pi)
        distance = deathstar_radius + 50
        tie_x = deathstar_pos[0] + math.cos(angle) * distance
        tie_y = deathstar_pos[1] + math.sin(angle) * distance
        tie_fighters.append([tie_x, tie_y, angle])
        tie_spawn_timer = 0

    # Update TIE Fighters
    for tie in tie_fighters[:]:
        tie[2] += 0.05
        tie[0] = deathstar_pos[0] + math.cos(tie[2]) * (deathstar_radius + 50)
        tie[1] = deathstar_pos[1] + math.sin(tie[2]) * (deathstar_radius + 50)
        if random.randint(0, 100) < 5:
            tie_lasers.append([tie[0] + tie_width // 2, tie[1] + tie_height])

    # Timer logic
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - start_time
    initial_time_remaining = max(0, (initial_timer_limit - elapsed_time) // 1000)
    
    if elapsed_time >= initial_timer_limit and wipeout_start_time is None:
        wipeout_start_time = current_time
    
    wipeout_time_remaining = 0
    if wipeout_start_time:
        wipeout_elapsed = current_time - wipeout_start_time
        wipeout_time_remaining = max(0, (wipeout_timer_limit - wipeout_elapsed) // 1000)
        if wipeout_elapsed >= wipeout_timer_limit:
            screen.fill(BLACK)
            game_over_text = font.render("DEATH STAR BLEW UP THE REBEL BASE. GAME OVER.", True, WHITE)
            screen.blit(game_over_text, (WIDTH // 2 - 250, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(2000)
            running = False

    # Maneuver logic and completion check
    maneuver_timer += 1
    if maneuver_timer >= maneuver_switch_interval:
        maneuver = random.randint(1, 2)
        if maneuver == 1:
            yellow_circle_pos = [random.randint(0, WIDTH), random.randint(0, HEIGHT)]
        else:
            green_line_start = [random.randint(0, WIDTH), random.randint(0, HEIGHT)]
            green_line_end = [random.randint(0, WIDTH), random.randint(0, HEIGHT)]
        maneuver_timer = 0
    else:
        # Check Maneuver 1 completion (reach yellow circle)
        if maneuver == 1:
            xwing_center = [xwing_pos[0] + xwing_width // 2, xwing_pos[1] + xwing_height // 2]
            distance_to_circle = math.hypot(xwing_center[0] - yellow_circle_pos[0], 
                                          xwing_center[1] - yellow_circle_pos[1])
            if distance_to_circle < 20 + xwing_width // 2:  # Within circle radius + X-Wing size
                score += 15
                maneuver_timer = maneuver_switch_interval  # Force immediate switch
        # Check Maneuver 2 completion (reach green line end)
        elif maneuver == 2:
            xwing_center = [xwing_pos[0] + xwing_width // 2, xwing_pos[1] + xwing_height // 2]
            distance_to_end = math.hypot(xwing_center[0] - green_line_end[0], 
                                       xwing_center[1] - green_line_end[1])
            if distance_to_end < xwing_width // 2:  # Within X-Wing size of end point
                score += 175
                maneuver_timer = maneuver_switch_interval  # Force immediate switch

    # Update lasers
    for laser in lasers[:]:
        laser[1] += laser_speed
        if (wipeout_start_time and
            deathstar_pos[0] - deathstar_radius < laser[0] < deathstar_pos[0] + deathstar_radius and
            deathstar_pos[1] - deathstar_radius < laser[1] < deathstar_pos[1] + deathstar_radius):
            lasers.remove(laser)
            deathstar_health -= 10
            score += 10
            continue
        hit_tie = False
        for tie in tie_fighters[:]:
            if (tie[0] < laser[0] < tie[0] + tie_width and
                tie[1] < laser[1] < tie[1] + tie_height):
                lasers.remove(laser)
                tie_fighters.remove(tie)
                score += 5
                hit_tie = True
                break
        if hit_tie:
            continue
        if laser[1] < 0:
            lasers.remove(laser)

    # Update TIE lasers
    for t_laser in tie_lasers[:]:
        t_laser[1] += tie_laser_speed
        if (xwing_pos[0] < t_laser[0] < xwing_pos[0] + xwing_width and
            xwing_pos[1] < t_laser[1] < xwing_pos[1] + xwing_height):
            screen.fill(BLACK)
            lose_text = font.render("You Lost!", True, WHITE)
            screen.blit(lose_text, (WIDTH // 2 - 70, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(2000)
            running = False
        elif t_laser[1] > HEIGHT:
            tie_lasers.remove(t_laser)

    # Clear screen
    screen.fill(BLACK)

    # Draw Death Star
    pygame.draw.circle(screen, GRAY, deathstar_pos, deathstar_radius)
    pygame.draw.rect(screen, RED, (deathstar_pos[0] - 50, deathstar_pos[1] - deathstar_radius - 20, 
                                   deathstar_health, 10))

    # Draw X-Wing
    pygame.draw.polygon(screen, WHITE, [
        (xwing_pos[0] + xwing_width // 2, xwing_pos[1]),
        (xwing_pos[0], xwing_pos[1] + xwing_height),
        (xwing_pos[0] + xwing_width, xwing_pos[1] + xwing_height)
    ])

    # Draw TIE Fighters
    for tie in tie_fighters:
        pygame.draw.rect(screen, GRAY, (tie[0], tie[1], tie_width, tie_height))

    # Draw maneuvers
    if maneuver == 1:
        pygame.draw.circle(screen, YELLOW, yellow_circle_pos, 20, 2)
    else:
        pygame.draw.line(screen, GREEN, green_line_start, green_line_end, 3)

    # Draw lasers
    for laser in lasers:
        pygame.draw.rect(screen, RED, (laser[0], laser[1], laser_width, laser_height))
    for t_laser in tie_lasers:
        pygame.draw.rect(screen, RED, (t_laser[0], t_laser[1], laser_width, laser_height))

    # Draw score and timers
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    wipeout_text = font.render(f"Wipeout: {wipeout_time_remaining}", True, WHITE)
    screen.blit(wipeout_text, (10, 40))
    initial_text = font.render(f"Shields: {initial_time_remaining}", True, WHITE)
    screen.blit(initial_text, (WIDTH - 150, 10))
    maneuver_text = font.render(f"Maneuver: {maneuver}", True, WHITE)
    screen.blit(maneuver_text, (WIDTH - 150, 40))

    # Check win condition
    if deathstar_health <= 0:
        win_text = font.render("Death Star Destroyed! You Win!", True, WHITE)
        screen.blit(win_text, (WIDTH // 2 - 150, HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False

    # Update display
    pygame.display.flip()
    clock.tick(60)

# Quit game
pygame.quit()