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

# Fonts
title_font = pygame.font.Font(None, 74)
name_font = pygame.font.Font(None, 36)
countdown_font = pygame.font.Font(None, 100)

# Characters and their PNGs (assuming face PNGs; use full body if available)
characters = ["Cyclops", "Wolverine", "Apocalypse", "Sabretooth"]
sprites = [
    pygame.transform.scale(pygame.image.load("cyclops.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("wolverine.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("apocalypse.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("sabretooth.png"), (100, 100))
]

# Game states
MAIN_MENU = "main_menu"
CHARACTER_SELECT = "character_select"
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
player_jumping = False
player_health = 100
enemy_health = 100
player_punch_active = False
enemy_punch_active = False
punch_duration = 10  # frames
player_punch_timer = 0
enemy_punch_timer = 0
countdown_active = True
countdown_time = 3
fight_start_time = None

# Gravity and jump
GRAVITY = 1
JUMP_STRENGTH = -20

# Ground platform
ground_rect = pygame.Rect(0, 500, SCREEN_WIDTH, 100)  # Grey platform at bottom

# Function to draw character PNGs with borders in select
def draw_select_face(char_index, x, y, selected=False):
    screen.blit(sprites[char_index], (x, y))
    border_width = 3 if selected else 1
    pygame.draw.rect(screen, WHITE, (x, y, 100, 100), border_width)
    name_text = name_font.render(characters[char_index], True, WHITE)
    screen.blit(name_text, (x + 50 - name_text.get_width() // 2, y + 110))

# Function to draw characters in battle
def draw_battle_character(pos, sprite, facing_right=True):
    if not facing_right:
        sprite = pygame.transform.flip(sprite, True, False)
    screen.blit(sprite, pos)

# Function to draw punch
def draw_punch(pos, facing_right):
    if facing_right:
        punch_rect = pygame.Rect(pos[0] + 100, pos[1] + 40, 50, 20)  # Right punch
    else:
        punch_rect = pygame.Rect(pos[0] - 50, pos[1] + 40, 50, 20)  # Left punch
    pygame.draw.rect(screen, BROWN, punch_rect)
    return punch_rect

# Function to draw health bars
def draw_health_bars():
    # Player
    player_name_text = name_font.render(characters[player_char], True, WHITE)
    screen.blit(player_name_text, (10, 10))
    pygame.draw.rect(screen, GREEN, (10, 50, player_health * 2, 20))
    
    # Enemy
    enemy_name_text = name_font.render(characters[enemy_char], True, WHITE)
    screen.blit(enemy_name_text, (SCREEN_WIDTH - enemy_name_text.get_width() - 10, 10))
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 200 - 10, 50, enemy_health * 2, 20))

# Simple enemy AI
def enemy_ai():
    global enemy_punch_active, enemy_punch_timer
    # Move towards player
    if enemy_pos[0] > player_pos[0] + 150:
        enemy_pos[0] -= 2
    elif enemy_pos[0] < player_pos[0] - 150:
        enemy_pos[0] += 2
    
    # Random punch
    if random.randint(1, 50) == 1 and not enemy_punch_active:
        enemy_punch_active = True
        enemy_punch_timer = punch_duration

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
                if event.key == pygame.K_RETURN:
                    current_state = CHARACTER_SELECT
            elif current_state == CHARACTER_SELECT:
                if event.key == pygame.K_LEFT:
                    selected_char = (selected_char - 1) % len(characters)
                elif event.key == pygame.K_RIGHT:
                    selected_char = (selected_char + 1) % len(characters)
                elif event.key == pygame.K_RETURN:
                    player_char = selected_char
                    # Random enemy, different from player
                    enemy_char = random.choice([i for i in range(len(characters)) if i != player_char])
                    print(f"Selected {characters[player_char]}! Starting battle against {characters[enemy_char]}...")
                    current_state = BATTLE
                    countdown_active = True
                    countdown_time = 3
                    player_pos = [100, 400]
                    enemy_pos = [600, 400]
                    player_health = 100
                    enemy_health = 100
    
    if current_state == MAIN_MENU:
        title_text = title_font.render("X-Men Battle", True, RED)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        instr_text = name_font.render("Press Return to Start", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, 300))
    
    elif current_state == CHARACTER_SELECT:
        select_text = title_font.render("Select Your Fighter", True, RED)
        screen.blit(select_text, (SCREEN_WIDTH // 2 - select_text.get_width() // 2, 50))
        spacing = SCREEN_WIDTH // (len(characters) + 1)
        for i in range(len(characters)):
            draw_select_face(i, spacing * (i + 1) - 50, 200, selected=(i == selected_char))
    
    elif current_state == BATTLE:
        # Draw ground
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
                    fight_start_time = None
        else:
            # Player movement
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_pos[0] > 0:
                player_pos[0] -= 5
            if keys[pygame.K_RIGHT] and player_pos[0] < SCREEN_WIDTH - 100:
                player_pos[0] += 5
            if keys[pygame.K_UP] and not player_jumping:
                player_vel_y = JUMP_STRENGTH
                player_jumping = True
            if keys[pygame.K_1] and not player_punch_active:
                player_punch_active = True
                player_punch_timer = punch_duration
            
            # Apply gravity
            player_vel_y += GRAVITY
            player_pos[1] += player_vel_y
            if player_pos[1] >= 400:
                player_pos[1] = 400
                player_vel_y = 0
                player_jumping = False
            
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
            
            # Draw characters (player faces right, enemy faces left)
            draw_battle_character(player_pos, sprites[player_char], facing_right=True)
            draw_battle_character(enemy_pos, sprites[enemy_char], facing_right=False)
            
            # Draw punches and check collisions
            if player_punch_active:
                player_punch_rect = draw_punch(player_pos, facing_right=True)
                enemy_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], 100, 100)
                if player_punch_rect.colliderect(enemy_rect):
                    enemy_health -= 10
                    player_punch_active = False  # Hit, reset punch
                    if enemy_health < 0:
                        enemy_health = 0
            
            if enemy_punch_active:
                enemy_punch_rect = draw_punch(enemy_pos, facing_right=False)
                player_rect = pygame.Rect(player_pos[0], player_pos[1], 100, 100)
                if enemy_punch_rect.colliderect(player_rect):
                    player_health -= 10
                    enemy_punch_active = False
                    if player_health < 0:
                        player_health = 0
            
            # Draw health bars
            draw_health_bars()
            
            # Check for win/lose
            if player_health <= 0 or enemy_health <= 0:
                winner = characters[enemy_char] if player_health <= 0 else characters[player_char]
                print(f"{winner} wins!")
                running = False  # End game for now
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()