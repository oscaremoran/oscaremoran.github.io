import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PLAYER_SIZE = 40
ENEMY_SIZE = 40
HEAL_SIZE = 60
SPEED = 5
RED_ENEMY_SPEED = 2
GREEN_ENEMY_SPEED = 1
BLUE_ENEMY_SPEED = 0.5
NUM_RED_ENEMIES = 3
NUM_GREEN_ENEMIES = 2
NUM_BLUE_ENEMIES = 1
BOSS_SPAWN_INTERVAL = 5000
TEXT_SCROLL_SPEED = 2

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RPG Game")

# Player setup
player_x, player_y = WIDTH // 2, HEIGHT // 2
player_health = 100
player_gold = 0
player_potions = 5
total_enemies_killed = 0
has_paused_at_10 = False  # New flag to prevent repeated pausing

# Static healing squares positions
heal_square_1 = [WIDTH - HEAL_SIZE - 10, HEIGHT // 4 - HEAL_SIZE // 2]
heal_square_2 = [WIDTH - HEAL_SIZE - 10, 3 * HEIGHT // 4 - HEAL_SIZE // 2]

# Time tracking for BOSS spawn
last_boss_spawn_time = pygame.time.get_ticks()

# Intro text setup
intro_texts = [
    "NECROMANCER'S REIGN",
    "You have been appointed by the King,",
    "to slay the fearsome Necromancer!",
    "He is the blue enemy, and spawns his",
    "red and green skeleton brethren",
    "to overthrow you!"
]
intro_y_positions = [HEIGHT + i * 60 for i in range(len(intro_texts))]

def spawn_red_enemies(num):
    return [[random.randint(0, WIDTH - ENEMY_SIZE), random.randint(0, HEIGHT - ENEMY_SIZE), 100, 'red'] for _ in range(num)]

def spawn_green_enemies(num):
    return [[random.randint(0, WIDTH - ENEMY_SIZE), random.randint(0, HEIGHT - ENEMY_SIZE), 200, 'green'] for _ in range(num)]

def spawn_blue_enemies(num):
    return [[random.randint(0, WIDTH - ENEMY_SIZE), random.randint(0, HEIGHT - ENEMY_SIZE), 350, 'blue'] for _ in range(num)]

# Initialize all enemy types
red_enemies = spawn_red_enemies(NUM_RED_ENEMIES)
green_enemies = spawn_green_enemies(NUM_GREEN_ENEMIES)
blue_enemies = spawn_blue_enemies(NUM_BLUE_ENEMIES)
all_enemies = red_enemies + green_enemies + blue_enemies

def battle_scene(enemy_index):
    global player_health, player_gold, player_potions, all_enemies, total_enemies_killed
    in_battle = True
    enemy_health = all_enemies[enemy_index][2]
    enemy_type = all_enemies[enemy_index][3]
    
    while in_battle:
        potion_used = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:  # Magic
                    enemy_health -= 0 if random.random() < 0.5 else 40
                elif event.key == pygame.K_b:  # Attack
                    enemy_health -= 20
                elif event.key == pygame.K_c and player_potions > 0 and player_health <= 100:
                    player_health = min(100, player_health + 15)
                    player_potions -= 1
                    potion_used = True
                
                if enemy_health <= 0:
                    player_gold += 20 if enemy_type == 'green' else (50 if enemy_type == 'blue' else 10)
                    all_enemies.pop(enemy_index)
                    total_enemies_killed += 1
                    in_battle = False
                
                if in_battle and not potion_used:
                    damage = 15 if enemy_type == 'blue' else (10 if enemy_type == 'green' else 5)
                    player_health -= damage
                    if player_health <= 0:
                        in_battle = False
                        return "game_over"
        
        screen.fill(BLACK)
        font = pygame.font.Font(None, 50)
        player_health_text = font.render(f"Player Health: {player_health}", True, WHITE)
        enemy_name = "BOSS" if enemy_type == 'blue' else f"{enemy_type.capitalize()} Enemy"
        enemy_health_text = font.render(f"{enemy_name} Health: {enemy_health}", True, WHITE)
        potions_text = font.render(f"Potions: {player_potions}", True, WHITE)
        screen.blit(player_health_text, (50, 50))
        screen.blit(enemy_health_text, (50, 100))
        screen.blit(potions_text, (50, 150))
        
        command_font = pygame.font.Font(None, 40)
        commands = ["Press A for Magic", "Press B for Attack", "Press C for Potion"]
        for i, command in enumerate(commands):
            command_text = command_font.render(command, True, WHITE)
            screen.blit(command_text, (50, 200 + i * 50))
        
        pygame.display.flip()
        pygame.time.delay(100)
    
    return None

def game_over_screen():
    screen.fill(BLACK)
    font = pygame.font.Font(None, 74)
    game_over_text = font.render("GAME OVER", True, RED)
    retry_text = font.render("PRESS SPACE TO TRY AGAIN", True, RED)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 50))
    pygame.display.flip()

def intro_screen():
    font = pygame.font.Font(None, 60)
    title_font = pygame.font.Font(None, 80)
    global intro_y_positions
    
    while intro_y_positions[-1] > -60:
        screen.fill(BLACK)
        
        for i, (text, y) in enumerate(zip(intro_texts, intro_y_positions)):
            if i == 0:  # Title
                text_surface = title_font.render(text, True, WHITE)
                x = WIDTH // 2 - text_surface.get_width() // 2
            else:  # Other lines
                text_surface = font.render(text, True, WHITE)
                x = 50
            screen.blit(text_surface, (x, y))
        
        intro_y_positions = [y - TEXT_SCROLL_SPEED for y in intro_y_positions]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
        pygame.display.flip()
        pygame.time.delay(30)

def pause_screen():
    screen.fill(BLACK)
    font = pygame.font.Font(None, 74)
    pause_text = font.render("PAUSED", True, WHITE)
    resume_text = font.render("PRESS SPACE TO RESUME", True, WHITE)
    example_text = font.render("The Necromancer has been angered.", True, WHITE)
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 100))
    screen.blit(example_text, (WIDTH // 2 - example_text.get_width() // 2, HEIGHT // 2))
    screen.blit(resume_text, (WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2 + 100))
    pygame.display.flip()

# Game loop
running = True
inventory_open = False
game_state = "intro"

while running:
    screen.fill(BLACK)
    
    if game_state == "intro":
        intro_screen()
        game_state = "playing"
        continue
    
    if game_state == "game_over":
        game_over_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player_x, player_y = WIDTH // 2, HEIGHT // 2
                player_health = 100
                player_gold = 0
                player_potions = 5
                total_enemies_killed = 0
                has_paused_at_10 = False  # Reset pause flag
                red_enemies = spawn_red_enemies(NUM_RED_ENEMIES)
                green_enemies = spawn_green_enemies(NUM_GREEN_ENEMIES)
                blue_enemies = spawn_blue_enemies(NUM_BLUE_ENEMIES)
                all_enemies = red_enemies + green_enemies + blue_enemies
                last_boss_spawn_time = pygame.time.get_ticks()
                game_state = "intro"
        continue
    
    if game_state == "paused":
        pause_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_state = "playing"
        continue
    
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                inventory_open = not inventory_open
            if event.key == pygame.K_ESCAPE:
                inventory_open = False
    
    if inventory_open:
        screen.fill(BLACK)
        font = pygame.font.Font(None, 50)
        inventory_text = font.render("INVENTORY", True, WHITE)
        screen.blit(inventory_text, (WIDTH // 2 - 100, 50))
        potions_text = font.render(f"Potions: {player_potions}", True, WHITE)
        gold_text = font.render(f"Gold: {player_gold}", True, WHITE)
        buy_potion_text = font.render("Press B to buy a potion (20 Gold)", True, WHITE)
        buy_health_text = font.render("Press A to buy max health (50 Gold)", True, WHITE)
        screen.blit(potions_text, (50, 150))
        screen.blit(gold_text, (50, 200))
        screen.blit(buy_potion_text, (50, 250))
        screen.blit(buy_health_text, (50, 300))
        exit_text = font.render("PRESS D TO EXIT", True, WHITE)
        screen.blit(exit_text, (50, 350))
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_b] and player_gold >= 20:
            player_gold -= 20
            player_potions += 1
        if keys[pygame.K_a] and player_gold >= 50:
            player_gold -= 50
            player_health = 150
    
    else:
        font = pygame.font.Font(None, 36)
        inventory_hint = font.render("PRESS D FOR INVENTORY", True, WHITE)
        screen.blit(inventory_hint, (10, 10))
        
        keys = pygame.key.get_pressed()
        new_player_x, new_player_y = player_x, player_y
        if keys[pygame.K_LEFT]:
            new_player_x -= SPEED
        if keys[pygame.K_RIGHT]:
            new_player_x += SPEED
        if keys[pygame.K_UP]:
            new_player_y -= SPEED
        if keys[pygame.K_DOWN]:
            new_player_y += SPEED
        
        player_x, player_y = new_player_x, new_player_y
        
        pygame.draw.rect(screen, WHITE, (player_x, player_y, PLAYER_SIZE, PLAYER_SIZE))
        
        pygame.draw.rect(screen, YELLOW, (heal_square_1[0], heal_square_1[1], HEAL_SIZE, HEAL_SIZE))
        pygame.draw.rect(screen, YELLOW, (heal_square_2[0], heal_square_2[1], HEAL_SIZE, HEAL_SIZE))
        
        player_rect = pygame.Rect(player_x, player_y, PLAYER_SIZE, PLAYER_SIZE)
        if player_rect.colliderect(pygame.Rect(heal_square_1[0], heal_square_1[1], HEAL_SIZE, HEAL_SIZE)) or \
           player_rect.colliderect(pygame.Rect(heal_square_2[0], heal_square_2[1], HEAL_SIZE, HEAL_SIZE)):
            if player_health <= 100:
                player_health = 100
        
        boss_present = any(enemy[3] == 'blue' for enemy in all_enemies)
        if boss_present:
            current_time = pygame.time.get_ticks()
            if current_time - last_boss_spawn_time >= BOSS_SPAWN_INTERVAL:
                all_enemies.extend(spawn_red_enemies(1))
                all_enemies.extend(spawn_green_enemies(1))
                last_boss_spawn_time = current_time
        
        for i, enemy in enumerate(all_enemies):
            speed = BLUE_ENEMY_SPEED if enemy[3] == 'blue' else (GREEN_ENEMY_SPEED if enemy[3] == 'green' else RED_ENEMY_SPEED)
            enemy[1] += speed
            if enemy[1] > HEIGHT:
                enemy[1] = 0
            color = BLUE if enemy[3] == 'blue' else (GREEN if enemy[3] == 'green' else RED)
            pygame.draw.rect(screen, color, (enemy[0], enemy[1], ENEMY_SIZE, ENEMY_SIZE))
            
            if player_rect.colliderect(pygame.Rect(enemy[0], enemy[1], ENEMY_SIZE, ENEMY_SIZE)):
                result = battle_scene(i)
                if result == "game_over":
                    game_state = "game_over"
                break
        
        # Check for pause condition only once
        if total_enemies_killed == 10 and not has_paused_at_10 and game_state == "playing":
            game_state = "paused"
            has_paused_at_10 = True  # Set flag to prevent re-triggering
        
        font = pygame.font.Font(None, 36)
        health_text = font.render(f"Health: {player_health}", True, WHITE)
        gold_text = font.render(f"Gold: {player_gold}", True, WHITE)
        kills_text = font.render(f"Enemies Killed: {total_enemies_killed}", True, WHITE)
        screen.blit(health_text, (WIDTH - 150, 10))
        screen.blit(gold_text, (WIDTH - 150, 50))
        screen.blit(kills_text, (WIDTH - 250, 90))
        
        if not all_enemies:
            red_enemies = spawn_red_enemies(NUM_RED_ENEMIES)
            green_enemies = spawn_green_enemies(NUM_GREEN_ENEMIES)
            blue_enemies = spawn_blue_enemies(NUM_BLUE_ENEMIES)
            all_enemies = red_enemies + green_enemies + blue_enemies
            last_boss_spawn_time = pygame.time.get_ticks()
    
    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()