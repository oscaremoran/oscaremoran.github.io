import pygame
import sys
import random
import time

# Initialize Pygame
pygame.init()

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("X-Men Battle")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)  # For magnetic fields
YELLOW = (255, 255, 0)  # For healing orbs

# Fonts
title_font = pygame.font.Font(None, 74)
name_font = pygame.font.Font(None, 36)
countdown_font = pygame.font.Font(None, 100)

# Characters and their PNGs
characters = ["Cyclops", "Wolverine", "Apocalypse", "Sabretooth"]
sprites = [
    pygame.transform.scale(pygame.image.load("cyclops.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("wolverine.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("apocalypse.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("sabretooth.png"), (100, 100))
]

# Stages with gimmicks
stages = [
    "Danger Room",      # Static midair platform
    "Sentinel Factory", # Moving platforms
    "Muir Island",      # Healing zones (yellow orbs restore 10 HP)
    "Savage Land",      # Falling rocks (20 HP damage)
    "Genosha"           # Magnetic fields pull characters together
]
selected_stage = 0

# Game states
MAIN_MENU = "main_menu"
CHARACTER_SELECT = "character_select"
STAGE_SELECT = "stage_select"
BATTLE = "battle"
current_state = MAIN_MENU

# Selected character index
selected_char = 0
player_char = None
enemy_char = None

# Battle variables
player_pos = [100, 400]  # x, y (ground at y=400)
enemy_pos = [600, 400]
player_vel_y = 0
enemy_vel_y = 0
player_jumping = False
enemy_jumping = False
player_health = 500
enemy_health = 500
player_special_meter = 0
enemy_special_meter = 0
player_punch_active = False
enemy_punch_active = False
punch_duration = 10  # frames
player_punch_timer = 0
enemy_punch_timer = 0
countdown_active = True
countdown_time = 3
fight_start_time = None
battle_start_time = None

# Special move variables
player_special_active = False
player_special_charging = False
enemy_special_active = False
enemy_special_charging = False
special_charge_start = None
enemy_special_charge_start = None
special_charge_duration = 3  # seconds
specials = {
    0: "RAY BEAM",
    1: "FLURRY",
    2: "EXTERMINATION",
    3: "FLURRY"
}
# For Cyclops Ray Beam
ray_duration = 10
player_ray_timer = 0
enemy_ray_timer = 0
# For Flurry (Wolverine/Sabretooth)
flurry_hits = 5
player_flurry_timer = 0
enemy_flurry_timer = 0
flurry_duration = 30  # frames for all hits
# For Extermination (Apocalypse)
player_pellets = []
enemy_pellets = []
pellet_duration = 60  # frames for pellets to fall

# Lightning
lightning_active = False
lightning_pos = [0, 0]
lightning_timer = 0
lightning_duration = 5  # frames

# Gravity and jump
GRAVITY = 1
JUMP_STRENGTH = -25

# Platforms
ground_rect = pygame.Rect(0, 500, SCREEN_WIDTH, 100)
danger_midair_platform = pygame.Rect(300, 350, 200, 20)
sentinel_platform1 = pygame.Rect(200, 350, 150, 20)  # Moving left-right
sentinel_platform2 = pygame.Rect(500, 300, 150, 20)  # Moving up-down
sentinel_platform1_speed = 2
sentinel_platform2_speed = 1
sentinel_platform1_dir = 1
sentinel_platform2_dir = 1

# Gimmick variables
healing_orb_pos = None
healing_orb_timer = 0
healing_orb_interval = 600  # Every 10 seconds (60 FPS * 10)
rock_pos = None
rock_vel = 5
rock_timer = 0
rock_interval = 300  # Every 5 seconds
magnetic_active = False
magnetic_timer = 0
magnetic_interval = 900  # Every 15 seconds
magnetic_duration = 180  # 3 seconds

# Function to draw character PNGs with borders in select
def draw_select_face(char_index, x, y, selected=False):
    screen.blit(sprites[char_index], (x, y))
    border_width = 3 if selected else 1
    pygame.draw.rect(screen, WHITE, (x, y, 100, 100), border_width)
    name_text = name_font.render(characters[char_index], True, WHITE)
    screen.blit(name_text, (x + 50 - name_text.get_width() // 2, y + 110))

# Function to draw stage select
def draw_stage_select(stage_index, x, y, selected=False):
    stage_text = name_font.render(stages[stage_index], True, WHITE)
    screen.blit(stage_text, (x + 100 - stage_text.get_width() // 2, y + 40 - stage_text.get_height() // 2))
    border_width = 3 if selected else 1
    pygame.draw.rect(screen, WHITE, (x, y, 200, 80), border_width)

# Function to draw characters in battle
def draw_battle_character(pos, sprite, facing_right=True):
    if not facing_right:
        sprite = pygame.transform.flip(sprite, True, False)
    screen.blit(sprite, pos)

# Function to draw punch
def draw_punch(pos, facing_right):
    if facing_right:
        punch_rect = pygame.Rect(pos[0] + 100, pos[1] + 40, 50, 20)
    else:
        punch_rect = pygame.Rect(pos[0] - 50, pos[1] + 40, 50, 20)
    pygame.draw.rect(screen, BROWN, punch_rect)
    return punch_rect

# Function to draw health bars and special meters
def draw_health_bars():
    player_name_text = name_font.render(characters[player_char], True, WHITE)
    screen.blit(player_name_text, (10, 10))
    pygame.draw.rect(screen, GREEN, (10, 50, player_health * 0.4, 20))  # Scaled for 500 max
    pygame.draw.rect(screen, BLUE, (10, 80, player_special_meter * 40, 10))
    
    enemy_name_text = name_font.render(characters[enemy_char], True, WHITE)
    screen.blit(enemy_name_text, (SCREEN_WIDTH - enemy_name_text.get_width() - 10, 10))
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 200 - 10, 50, enemy_health * 0.4, 20))
    pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH - 200 - 10, 80, enemy_special_meter * 40, 10))

# Function to draw special moves
def draw_special(is_player=True):
    global player_special_active, enemy_special_active, player_flurry_timer, enemy_flurry_timer, player_pellets, enemy_pellets, enemy_health, player_health, player_ray_timer, enemy_ray_timer
    pos = player_pos if is_player else enemy_pos
    char_index = player_char if is_player else enemy_char
    health = enemy_health if is_player else player_health
    opponent_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], 100, 100) if is_player else pygame.Rect(player_pos[0], player_pos[1], 100, 100)
    pellets = player_pellets if is_player else enemy_pellets
    flurry_timer = player_flurry_timer if is_player else enemy_flurry_timer
    ray_timer = player_ray_timer if is_player else enemy_ray_timer
    
    if char_index == 0:  # Cyclops: Ray Beam
        if ray_timer > 0:
            ray_rect = pygame.Rect(pos[0] + 100 if is_player else pos[0] - 400, pos[1] + 40, 400, 40)
            pygame.draw.rect(screen, RED, ray_rect)
            if ray_rect.colliderect(opponent_rect):
                health -= 100
                if is_player:
                    enemy_health = max(0, health)
                else:
                    player_health = max(0, health)
            if is_player:
                player_ray_timer -= 1
                if player_ray_timer <= 0:
                    player_special_active = False
            else:
                enemy_ray_timer -= 1
                if enemy_ray_timer <= 0:
                    enemy_special_active = False
    elif char_index in [1, 3]:  # Wolverine/Sabretooth: Flurry
        flurry_timer -= 1
        if flurry_timer % 6 == 0:
            slash_rect = pygame.Rect(pos[0] + 100 if is_player else pos[0] - 30, pos[1] + 20, 30, 30)
            pygame.draw.rect(screen, GRAY, slash_rect)
            if slash_rect.colliderect(opponent_rect):
                health -= 10
                if is_player:
                    enemy_health = max(0, health)
                else:
                    player_health = max(0, health)
        if flurry_timer <= 0:
            if is_player:
                player_special_active = False
            else:
                enemy_special_active = False
    elif char_index == 2:  # Apocalypse: Extermination
        for pellet in pellets[:]:
            pellet[1] += 5
            pygame.draw.circle(screen, ORANGE, (pellet[0], pellet[1]), 10)
            pellet_rect = pygame.Rect(pellet[0] - 10, pellet[1] - 10, 20, 20)
            if pellet_rect.colliderect(opponent_rect):
                health -= 20
                pellets.remove(pellet)
                if is_player:
                    enemy_health = max(0, health)
                else:
                    player_health = max(0, health)
            elif pellet[1] > SCREEN_HEIGHT:
                pellets.remove(pellet)
        if not pellets:
            if is_player:
                player_special_active = False
            else:
                enemy_special_active = False

# Simple enemy AI
def enemy_ai():
    global enemy_punch_active, enemy_punch_timer, enemy_special_charging, enemy_special_active, enemy_special_charge_start, enemy_vel_y, enemy_jumping
    # Run away if health below half
    if enemy_health < 250:
        if enemy_pos[0] < player_pos[0]:
            enemy_pos[0] -= 3  # Move left
            if enemy_pos[0] < 0:
                enemy_pos[0] = 0
        else:
            enemy_pos[0] += 3  # Move right
            if enemy_pos[0] > SCREEN_WIDTH - 100:
                enemy_pos[0] = SCREEN_WIDTH - 100
    else:
        if enemy_pos[0] > player_pos[0] + 150:
            enemy_pos[0] -= 2
        elif enemy_pos[0] < player_pos[0] - 150:
            enemy_pos[0] += 2
    # Punch more frequently
    if random.randint(1, 30) == 1 and not enemy_punch_active and not enemy_special_charging and not enemy_special_active:
        enemy_punch_active = True
        enemy_punch_timer = punch_duration
    # Special more frequently when meter is full
    if random.randint(1, 75) == 1 and not enemy_punch_active and not enemy_special_charging and not enemy_special_active and enemy_special_meter >= 5:
        enemy_special_charging = True
        enemy_special_charge_start = time.time()
    # Jump strategically (if player is on platform and enemy is not)
    player_on_platform = player_pos[1] < 400
    enemy_on_platform = enemy_pos[1] < 400
    if random.randint(1, 50) == 1 and not enemy_jumping and not enemy_special_charging and not enemy_special_active and player_on_platform and not enemy_on_platform:
        enemy_vel_y = JUMP_STRENGTH
        enemy_jumping = True

# Check platform collision
def check_platform_collision(pos, vel_y, jumping, platforms):
    char_rect = pygame.Rect(pos[0], pos[1], 100, 100)
    for platform in platforms:
        if vel_y > 0 and char_rect.colliderect(platform) and pos[1] + 100 <= platform.top + vel_y:
            pos[1] = platform.top - 100
            return True
    if pos[1] >= 400:
        pos[1] = 400
        return True
    return False

# Update moving platforms for Sentinel Factory
def update_moving_platforms():
    global sentinel_platform1_dir, sentinel_platform2_dir
    sentinel_platform1.x += sentinel_platform1_speed * sentinel_platform1_dir
    if sentinel_platform1.x <= 100 or sentinel_platform1.x >= 500:
        sentinel_platform1_dir *= -1
    sentinel_platform2.y += sentinel_platform2_speed * sentinel_platform2_dir
    if sentinel_platform2.y <= 200 or sentinel_platform2.y >= 400:
        sentinel_platform2_dir *= -1

# Handle stage gimmicks
def handle_gimmicks(stage_name):
    global healing_orb_pos, healing_orb_timer, rock_pos, rock_timer, rock_vel, magnetic_active, magnetic_timer, player_health, enemy_health, player_pos, enemy_pos, magnetic_duration
    magnetic_duration = 180  # Initialize to avoid UnboundLocalError
    if stage_name == "Muir Island":
        healing_orb_timer += 1
        if healing_orb_timer >= healing_orb_interval:
            healing_orb_pos = [random.randint(100, SCREEN_WIDTH - 100), random.randint(100, 400)]
            healing_orb_timer = 0
        if healing_orb_pos:
            pygame.draw.circle(screen, YELLOW, healing_orb_pos, 20)
            player_rect = pygame.Rect(player_pos[0], player_pos[1], 100, 100)
            enemy_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], 100, 100)
            orb_rect = pygame.Rect(healing_orb_pos[0] - 20, healing_orb_pos[1] - 20, 40, 40)
            if orb_rect.colliderect(player_rect):
                player_health = min(500, player_health + 10)
                healing_orb_pos = None
            elif orb_rect.colliderect(enemy_rect):
                enemy_health = min(500, enemy_health + 10)
                healing_orb_pos = None
    elif stage_name == "Savage Land":
        rock_timer += 1
        if rock_timer >= rock_interval:
            rock_pos = [random.randint(0, SCREEN_WIDTH), 0]
            rock_timer = 0
        if rock_pos:
            rock_pos[1] += rock_vel
            pygame.draw.circle(screen, GRAY, rock_pos, 15)
            player_rect = pygame.Rect(player_pos[0], player_pos[1], 100, 100)
            enemy_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], 100, 100)
            rock_rect = pygame.Rect(rock_pos[0] - 15, rock_pos[1] - 15, 30, 30)
            if rock_rect.colliderect(player_rect):
                player_health = max(0, player_health - 20)
                rock_pos = None
            elif rock_rect.colliderect(enemy_rect):
                enemy_health = max(0, enemy_health - 20)
                rock_pos = None
            elif rock_pos[1] > SCREEN_HEIGHT:
                rock_pos = None
    elif stage_name == "Genosha":
        magnetic_timer += 1
        if magnetic_timer >= magnetic_interval:
            magnetic_active = True
            magnetic_timer = 0
        if magnetic_active:
            pygame.draw.rect(screen, PURPLE, (SCREEN_WIDTH // 2 - 50, 0, 100, SCREEN_HEIGHT), 2)
            center_x = SCREEN_WIDTH // 2
            if player_pos[0] < center_x:
                player_pos[0] += 2
            else:
                player_pos[0] -= 2
            if enemy_pos[0] < center_x:
                enemy_pos[0] += 2
            else:
                enemy_pos[0] -= 2
            magnetic_duration -= 1
            if magnetic_duration <= 0:
                magnetic_active = False
                magnetic_duration = 180

# Draw lightning
def draw_lightning():
    global lightning_timer, lightning_active, player_health, enemy_health
    if lightning_active:
        pygame.draw.line(screen, BLUE, (lightning_pos[0], 0), (lightning_pos[0], SCREEN_HEIGHT), 5)
        player_rect = pygame.Rect(player_pos[0], player_pos[1], 100, 100)
        enemy_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], 100, 100)
        lightning_rect = pygame.Rect(lightning_pos[0] - 2.5, 0, 5, SCREEN_HEIGHT)
        if lightning_rect.colliderect(player_rect):
            player_health = 0
        if lightning_rect.colliderect(enemy_rect):
            enemy_health = 0
        lightning_timer -= 1
        if lightning_timer <= 0:
            lightning_active = False

# Reset battle
def reset_battle():
    global current_state, selected_char, countdown_active, countdown_time, player_health, enemy_health, player_special_meter, enemy_special_meter, player_special_active, player_special_charging, enemy_special_active, enemy_special_charging, player_pellets, enemy_pellets, player_vel_y, enemy_vel_y, player_jumping, enemy_jumping, battle_start_time, healing_orb_pos, rock_pos, magnetic_active, magnetic_timer, magnetic_duration
    current_state = CHARACTER_SELECT
    selected_char = 0
    countdown_active = True
    countdown_time = 3
    player_health = 500
    enemy_health = 500
    player_special_meter = 0
    enemy_special_meter = 0
    player_special_active = False
    player_special_charging = False
    enemy_special_active = False
    enemy_special_charging = False
    player_pellets = []
    enemy_pellets = []
    player_vel_y = 0
    enemy_vel_y = 0
    player_jumping = False
    enemy_jumping = False
    battle_start_time = None
    healing_orb_pos = None
    healing_orb_timer = 0
    rock_pos = None
    rock_timer = 0
    magnetic_active = False
    magnetic_timer = 0
    magnetic_duration = 180

# Main game loop
running = True
while running:
    screen.fill(BLACK)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif current_state == MAIN_MENU:
                if event.key == pygame.K_1:
                    current_state = CHARACTER_SELECT
            elif current_state == CHARACTER_SELECT:
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    current_state = MAIN_MENU
                elif event.key == pygame.K_LEFT:
                    selected_char = (selected_char - 1) % len(characters)
                elif event.key == pygame.K_RIGHT:
                    selected_char = (selected_char + 1) % len(characters)
                elif event.key == pygame.K_RETURN:
                    player_char = selected_char
                    current_state = STAGE_SELECT
            elif current_state == STAGE_SELECT:
                if event.key == pygame.K_LEFT:
                    selected_stage = (selected_stage - 1) % len(stages)
                elif event.key == pygame.K_RIGHT:
                    selected_stage = (selected_stage + 1) % len(stages)
                elif event.key == pygame.K_RETURN:
                    enemy_char = random.choice([i for i in range(len(characters)) if i != player_char])
                    print(f"Selected {characters[player_char]}! Starting battle against {characters[enemy_char]} in {stages[selected_stage]}...")
                    current_state = BATTLE
                    countdown_active = True
                    countdown_time = 3
                    player_pos = [100, 400]
                    enemy_pos = [600, 400]
                    player_health = 500
                    enemy_health = 500
                    player_special_meter = 0
                    enemy_special_meter = 0
                    player_special_active = False
                    player_special_charging = False
                    enemy_special_active = False
                    enemy_special_charging = False
                    player_pellets = []
                    enemy_pellets = []
                    player_vel_y = 0
                    enemy_vel_y = 0
                    player_jumping = False
                    enemy_jumping = False
                    battle_start_time = None
                    healing_orb_pos = None
                    healing_orb_timer = 0
                    rock_pos = None
                    rock_timer = 0
                    magnetic_active = False
                    magnetic_timer = 0
                    magnetic_duration = 180
            elif current_state == BATTLE and not countdown_active and not player_special_charging:
                if event.key == pygame.K_UP and not player_jumping:
                    player_vel_y = JUMP_STRENGTH
                    player_jumping = True
                if event.key == pygame.K_1 and not player_punch_active:
                    player_punch_active = True
                    player_punch_timer = punch_duration
                if event.key == pygame.K_2 and not player_special_active and player_special_meter >= 5:
                    player_special_charging = True
                    special_charge_start = time.time()

    if current_state == MAIN_MENU:
        title_text = title_font.render("X-Men Battle", True, RED)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        instr_text = name_font.render("Press 1 for Single Match", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, 300))
    
    elif current_state == CHARACTER_SELECT:
        select_text = title_font.render("Select Your Fighter", True, RED)
        screen.blit(select_text, (SCREEN_WIDTH // 2 - select_text.get_width() // 2, 50))
        spacing = SCREEN_WIDTH // (len(characters) + 1)
        for i in range(len(characters)):
            draw_select_face(i, spacing * (i + 1) - 50, 200, selected=(i == selected_char))
    
    elif current_state == STAGE_SELECT:
        select_text = title_font.render("Select Your Stage", True, RED)
        screen.blit(select_text, (SCREEN_WIDTH // 2 - select_text.get_width() // 2, 50))
        for i in range(len(stages)):
            if i < 3:
                x = 100 + i * 250
                y = 200
            else:
                x = 225 + (i - 3) * 250
                y = 300
            draw_stage_select(i, x, y, selected=(i == selected_stage))
    
    elif current_state == BATTLE:
        # Determine platforms based on stage
        stage_name = stages[selected_stage]
        if stage_name == "Danger Room":
            platforms = [ground_rect, danger_midair_platform]
            pygame.draw.rect(screen, GRAY, ground_rect)
            pygame.draw.rect(screen, GRAY, danger_midair_platform)
        elif stage_name == "Sentinel Factory":
            update_moving_platforms()
            platforms = [ground_rect, sentinel_platform1, sentinel_platform2]
            pygame.draw.rect(screen, GRAY, ground_rect)
            pygame.draw.rect(screen, GRAY, sentinel_platform1)
            pygame.draw.rect(screen, GRAY, sentinel_platform2)
        else:
            platforms = [ground_rect]
            pygame.draw.rect(screen, GRAY, ground_rect)
        
        # Countdown
        if countdown_active:
            if countdown_time > 0:
                countdown_text = countdown_font.render(str(countdown_time), True, RED)
                screen.blit(countdown_text, (SCREEN_WIDTH // 2 - countdown_text.get_width() // 2, SCREEN_HEIGHT // 2 - countdown_text.get_height() // 2))
                if fight_start_time is None:
                    fight_start_time = time.time()
                elif time.time() - fight_start_time >= 1:
                    countdown_time -= 1
                    fight_start_time = time.time()
            else:
                countdown_text = countdown_font.render("Fight!", True, RED)
                screen.blit(countdown_text, (SCREEN_WIDTH // 2 - countdown_text.get_width() // 2, SCREEN_HEIGHT // 2 - countdown_text.get_height() // 2))
                if time.time() - fight_start_time >= 1:
                    countdown_active = False
                    battle_start_time = time.time()
                    fight_start_time = None
        else:
            # Special charging
            if player_special_charging:
                special_text = countdown_font.render(specials[player_char], True, RED)
                screen.blit(special_text, (SCREEN_WIDTH // 2 - special_text.get_width() // 2, SCREEN_HEIGHT // 2 - special_text.get_height() // 2))
                if time.time() - special_charge_start >= special_charge_duration:
                    player_special_charging = False
                    player_special_active = True
                    player_special_meter = 0
                    if player_char == 0:
                        player_ray_timer = ray_duration
                    if player_char == 2:
                        player_pellets = [[random.randint(0, SCREEN_WIDTH - 10), 0] for _ in range(20)]
                    elif player_char in [1, 3]:
                        player_flurry_timer = flurry_duration
            if enemy_special_charging:
                special_text = countdown_font.render(specials[enemy_char], True, RED)
                screen.blit(special_text, (SCREEN_WIDTH // 2 - special_text.get_width() // 2, SCREEN_HEIGHT // 2 - special_text.get_height() // 2))
                if time.time() - enemy_special_charge_start >= special_charge_duration:
                    enemy_special_charging = False
                    enemy_special_active = True
                    enemy_special_meter = 0
                    if enemy_char == 0:
                        enemy_ray_timer = ray_duration
                    if enemy_char == 2:
                        enemy_pellets = [[random.randint(0, SCREEN_WIDTH - 10), 0] for _ in range(20)]
                    elif enemy_char in [1, 3]:
                        enemy_flurry_timer = flurry_duration
            
            # Player movement (only if not charging)
            if not player_special_charging:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] and player_pos[0] > 0:
                    player_pos[0] -= 5
                if keys[pygame.K_RIGHT] and player_pos[0] < SCREEN_WIDTH - 100:
                    player_pos[0] += 5
            
            # Apply gravity and platform collision
            player_vel_y += GRAVITY
            player_pos[1] += player_vel_y
            if check_platform_collision(player_pos, player_vel_y, player_jumping, platforms):
                player_vel_y = 0
                player_jumping = False
            
            enemy_vel_y += GRAVITY
            enemy_pos[1] += enemy_vel_y
            if check_platform_collision(enemy_pos, enemy_vel_y, enemy_jumping, platforms):
                enemy_vel_y = 0
                enemy_jumping = False
            
            # Punch timers
            if player_punch_active:
                player_punch_timer -= 1
                if player_punch_timer <= 0:
                    player_punch_active = False
            
            if enemy_punch_active:
                enemy_punch_timer -= 1
                if enemy_punch_timer <= 0:
                    enemy_punch_active = False
            
            # Enemy AI
            enemy_ai()
            
            # Draw characters
            draw_battle_character(player_pos, sprites[player_char], facing_right=True)
            draw_battle_character(enemy_pos, sprites[enemy_char], facing_right=False)
            
            # Draw punches and check collisions
            if player_punch_active:
                player_punch_rect = draw_punch(player_pos, facing_right=True)
                enemy_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], 100, 100)
                if player_punch_rect.colliderect(enemy_rect):
                    enemy_health -= 20
                    player_special_meter = min(5, player_special_meter + 1)
                    player_punch_active = False
                    enemy_health = max(0, enemy_health)
            
            if enemy_punch_active:
                enemy_punch_rect = draw_punch(enemy_pos, facing_right=False)
                player_rect = pygame.Rect(player_pos[0], player_pos[1], 100, 100)
                if enemy_punch_rect.colliderect(player_rect):
                    player_health -= 20
                    enemy_special_meter = min(5, player_special_meter + 1)
                    enemy_punch_active = False
                    player_health = max(0, player_health)
            
            # Draw special moves
            if player_special_active:
                draw_special(is_player=True)
            if enemy_special_active:
                draw_special(is_player=False)
            
            # Handle stage gimmicks
            handle_gimmicks(stage_name)
            
            # Lightning after 30 seconds
            if battle_start_time and time.time() - battle_start_time > 30:
                if random.randint(1, 100) == 1 and not lightning_active:
                    lightning_active = True
                    lightning_pos[0] = random.randint(0, SCREEN_WIDTH)
                    lightning_timer = lightning_duration
            draw_lightning()
            
            # Draw health bars and meters
            draw_health_bars()
            
            # Check for win/lose
            if player_health <= 0 or enemy_health <= 0:
                winner = characters[enemy_char] if player_health <= 0 else characters[player_char]
                print(f"{winner} wins!")
                reset_battle()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()