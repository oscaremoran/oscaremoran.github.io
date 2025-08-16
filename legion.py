import asyncio
import random
import platform
import pygame
import sys 
from pygame.locals import *

# Player class for Conquest and Custom modes
class Player:
    def __init__(self, name):
        self.name = name
        self.conquered = 0
        self.war_cry_cooldown = -1  # -1 means not unlocked, 0 means available

# Territory class for Conquest
class Territory:
    def __init__(self, name, is_neutral=False):
        self.name = name
        self.units = {"swordsman": 0, "spearman": 0, "archer": 0}
        self.owner = None
        self.adjacent = []
        self.is_neutral = is_neutral

# Helper function to format units for unit display
def format_units(units):
    return ", ".join([f"{count} {unit}{'s' if count > 1 else ''}" for unit, count in units.items() if count > 0]) or "0 units"

# Helper function to remove random units from territories
# Helper function to remove random units
def remove_random_units(units, count):
    total_removed = 0
    while total_removed < count and sum(units.values()) > 0:
        available = [unit for unit in units if units[unit] > 0]
        if not available:
            break
        unit_to_remove = random.choice(available)
        units[unit_to_remove] -= 1
        total_removed += 1
    return total_removed

# Helper function to clear all units
def clear_units(units_dict):
    for key in units_dict:
        units_dict[key] = 0

# Helper function to distribute units proportionally
def distribute_units(original_units, total):
    if total <= 0:
        return {"swordsman": 0, "spearman": 0, "archer": 0}
    original_total = sum(original_units.values())
    if original_total == 0:
        return {"swordsman": total, "spearman": 0, "archer": 0}
    new_units = {"swordsman": 0, "spearman": 0, "archer": 0}
    for unit, count in original_units.items():
        new_units[unit] = round(count * total / original_total)
    current_total = sum(new_units.values())
    if current_total > total:
        remove_random_units(new_units, current_total - total)
    elif current_total < total:
        available = [unit for unit in new_units if original_units[unit] > 0]
        if available:
            new_units[random.choice(available)] += total - current_total
    return new_units

# Battle resolution function for Conquest and Custom modes
def battle(attacker_territory, defender_territory, k, use_war_cry=False, territories=None, ai=None):
    beats = {"swordsman": "spearman", "spearman": "archer", "archer": "swordsman"}
    
    all_units = [unit for unit, count in attacker_territory.units.items() for _ in range(count)]
    if k > len(all_units) - 1:
        return False
    committed = random.sample(all_units, k)
    committed_units = {"swordsman": 0, "spearman": 0, "archer": 0}
    for unit in committed:
        committed_units[unit] += 1
    for unit, count in committed_units.items():
        attacker_territory.units[unit] -= count
    
    defender_original_units = defender_territory.units.copy()
    
    attack_base = k
    defense_base = sum(defender_territory.units.values())
    
    committed_types = [unit for unit in committed_units if committed_units[unit] > 0]
    defender_types = [unit for unit in defender_territory.units if defender_territory.units[unit] > 0]
    attacker_advantage = sum(1 for attacker_type in committed_types if beats[attacker_type] in defender_types)
    defender_advantage = sum(1 for defender_type in defender_types if beats[defender_type] in committed_types)
    
    A = attack_base + attacker_advantage + (1 if use_war_cry else 0)
    D = defense_base + defender_advantage
    
    if A > D:
        clear_units(defender_territory.units)
        remaining = max(1, A - D)
        if sum(committed_units.values()) > 0:
            for unit in committed_units:
                defender_territory.units[unit] = committed_units[unit]
            total_remaining = sum(defender_territory.units.values())
            if total_remaining > remaining:
                excess = total_remaining - remaining
                remove_random_units(defender_territory.units, excess)
        else:
            defender_territory.units["swordsman"] = 1
        defender_territory.owner = attacker_territory.owner
        defender_territory.is_neutral = False
        attacker_territory.owner.conquered += 1
        if attacker_territory.owner.conquered >= 3 and attacker_territory.owner.war_cry_cooldown == -1:
            attacker_territory.owner.war_cry_cooldown = 0
        if defender_territory.is_neutral and territories and ai:
            neutral_territories = [t for t in territories.values() if t.is_neutral]
            if neutral_territories:
                neutral_to_ai = random.choice(neutral_territories)
                neutral_to_ai.owner = ai
                neutral_to_ai.is_neutral = False
                ai.conquered += 1
                print(f"AI gains {neutral_to_ai.name} due to neutral territory attack.")
    elif A < D:
        clear_units(attacker_territory.units)
        for unit, count in committed_units.items():
            attacker_territory.units[unit] += count
        clear_units(defender_territory.units)
        remaining_defense = max(1, D - A)
        defender_territory.units = distribute_units(defender_original_units, remaining_defense)
    else:
        clear_units(attacker_territory.units)
        for unit, count in committed_units.items():
            attacker_territory.units[unit] += count
        clear_units(defender_territory.units)
        if use_war_cry:
            defender_territory.units["swordsman"] = 1
            defender_territory.owner = attacker_territory.owner
            defender_territory.is_neutral = False
            attacker_territory.owner.conquered += 1
            if attacker_territory.owner.conquered >= 3 and attacker_territory.owner.war_cry_cooldown == -1:
                attacker_territory.owner.war_cry_cooldown = 0
            if defender_territory.is_neutral and territories and ai:
                neutral_territories = [t for t in territories.values() if t.is_neutral]
                if neutral_territories:
                    neutral_to_ai = random.choice(neutral_territories)
                    neutral_to_ai.owner = ai
                    neutral_to_ai.is_neutral = False
                    ai.conquered += 1
                    print(f"AI gains {neutral_to_ai.name} due to neutral territory attack.")
        else:
            defender_territory.units = distribute_units(defender_original_units, 1)
    
    return True

# Diplomacy questions for Conquest and Custom modes
questions = [
    {"question": "Which god is the patron of this city?", "answers": ["Athena", "Apollo"], "correct": random.choice([0, 1])},
    {"question": "What is the main export of this region?", "answers": ["Olives", "Pottery"], "correct": random.choice([0, 1])},
    {"question": "Who founded this city according to legend?", "answers": ["Cadmus", "Theseus"], "correct": random.choice([0, 1])},
    {"question": "Which festival is most celebrated here?", "answers": ["Panathenaea", "Dionysia"], "correct": random.choice([0, 1])},
    {"question": "What is the city's famous landmark?", "answers": ["Temple", "Theater"], "correct": random.choice([0, 1])}
]

# Custom input function to check for 'q'
def get_input(prompt, validate=None):
    while True:
        user_input = input(prompt).strip()
        if user_input.lower() == 'q':
            print("Quitting game...")
            sys.exit()
        if validate is None or validate(user_input):
            return user_input
        print("Invalid input. Please try again.")

# Diplomacy meeting function for Conquest and Custom modes
def diplomacy_meeting(player, ai, territories):
    if random.random() < 1/3:
        neutral_territories = [t for t in territories.values() if t.is_neutral]
        if not neutral_territories:
            return
        target_territory = random.choice(neutral_territories)
        is_player_meeting = random.random() < 0.5
        recipient = player if is_player_meeting else ai
        print(f"Diplomacy Meeting with {target_territory.name} for {recipient.name}!")
        question_data = random.choice(questions)
        print(f"Question: {question_data['question']}")
        print(f"Options: 1) {question_data['answers'][0]}, 2) {question_data['answers'][1]}")
        if is_player_meeting:
            answer = get_input("Choose answer (1 or 2): ", lambda x: x in ['1', '2'])
            answer = int(answer) - 1
        else:
            answer = random.choice([0, 1])
        if answer == question_data['correct']:
            print(f"Correct! {target_territory.name} joins {recipient.name}.")
            target_territory.owner = recipient
            target_territory.is_neutral = False
            recipient.conquered += 1
            if recipient.conquered >= 3 and recipient.war_cry_cooldown == -1:
                recipient.war_cry_cooldown = 0
        else:
            print(f"Incorrect! {target_territory.name} joins {ai.name if is_player_meeting else player.name}.")
            target_territory.owner = ai if is_player_meeting else player
            target_territory.is_neutral = False
            (ai if is_player_meeting else player).conquered += 1
            if (ai if is_player_meeting else player).conquered >= 3 and (ai if is_player_meeting else player).war_cry_cooldown == -1:
                (ai if is_player_meeting else player).war_cry_cooldown = 0

# Naval Assault function for Conquest and Custom modes
def naval_assault(player, territories):
    if random.random() < 1/3:
        spartan_territories = [t for t in territories.values() if t.owner == player]
        if spartan_territories:
            target = random.choice(spartan_territories)
            total_units = sum(target.units.values())
            if total_units > 1:
                units_to_remove = min(3, total_units - 1)
                removed = remove_random_units(target.units, units_to_remove)
                print(f"AI launches Naval Assault on {target.name}! {removed} units lost.")
                display_state()

# European invasion function for Conquest and Custom modes
def european_invasion(player, ai, europeans, territories):
    if random.random() < 0.1:
        outcome = random.choice([1, 2, 3])
        if outcome == 1:
            print("The Europeans have conquered Greece. The Europeans have triumphed")
            return False
        elif outcome == 2:
            spartan_territories = [t for t in territories.values() if t.owner == player]
            if spartan_territories:
                target = random.choice(spartan_territories)
                print(f"Europeans conquer {target.name}!")
                target.owner = europeans
                target.is_neutral = False
                target.units = {
                    "swordsman": random.randint(1, 5),
                    "spearman": random.randint(1, 5),
                    "archer": random.randint(1, 5)
                }
        else:
            athenian_territories = [t for t in territories.values() if t.owner == ai]
            if athenian_territories:
                target = random.choice(athenian_territories)
                print(f"Europeans conquer {target.name}!")
                target.owner = europeans
                target.is_neutral = False
                target.units = {
                    "swordsman": random.randint(1, 5),
                    "spearman": random.randint(1, 5),
                    "archer": random.randint(1, 5)
                }
    return True

# European turn function for Conquest and Custom modes
def european_turn(europeans, player, ai, territories):
    if any(t.owner == europeans for t in territories.values()):
        print("Europeans' turn")
        possible_attacks = [(t, adj) for t in territories.values() if t.owner == europeans and sum(t.units.values()) > 1 
                            for adj in t.adjacent if adj.owner in [player, ai]]
        if possible_attacks:
            attack_from, target = random.choice(possible_attacks)
            k = random.randint(1, sum(attack_from.units.values()) - 1)
            print(f"Europeans attack from {attack_from.name} to {target.name} with {k} units")
            if battle(attack_from, target, k, False, territories, ai):
                if target.owner == europeans:
                    print(f"{attack_from.name} (Europeans) Wins! {format_units(target.units)} remaining on {target.name}.")
                else:
                    print(f"Attack from {attack_from.name} failed. {format_units(target.units)} on {target.name}.")
                display_state()
        else:
            print("Europeans have no valid attacks this turn.")

# Warrior Mode Implementation
def warrior_mode():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Warrior Mode")
    clock = pygame.time.Clock()
    FPS = 60

    # Colors
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (128, 128, 128)

    # Entity class for player, enemies, teammates
    class Entity:
        def __init__(self, x, y, color, size=20, player_controlled=False):
            self.x = x
            self.y = y
            self.color = color
            self.size = size
            self.speed = 0.8
            self.player_controlled = player_controlled
            self.alive = True

        def draw(self, screen):
            if self.alive:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

        def move_towards(self, target_x, target_y, terrain):
            if not self.alive:
                return
            new_x = self.x
            new_y = self.y
            if self.x < target_x:
                new_x += min(self.speed, target_x - self.x)
            elif self.x > target_x:
                new_x -= min(self.speed, self.x - target_x)
            if self.y < target_y:
                new_y += min(self.speed, target_y - self.y)
            elif self.y > target_y:
                new_y -= min(self.speed, self.y - target_y)
            
            # Check terrain collision
            for t in terrain:
                if (new_x < t.x + t.size and new_x + self.size > t.x and
                    new_y < t.y + t.size and new_y + self.size > t.y):
                    # Try moving only x or only y
                    if not any(t.x < new_x + self.size and new_x < t.x + t.size and
                               t.y < self.y + self.size and self.y < t.y + t.size for t in terrain):
                        self.x = new_x
                    elif not any(t.x < self.x + self.size and self.x < t.x + t.size and
                                 t.y < new_y + self.size and new_y < t.y + t.size for t in terrain):
                        self.y = new_y
                    return
            self.x = new_x
            self.y = new_y

    # Terrain class for impassable obstacles
    class Terrain:
        def __init__(self, x, y, size=30):
            self.x = x
            self.y = y
            self.size = size
            self.color = GRAY

        def draw(self, screen):
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

    # Initialize entities
    player = Entity(400, 300, GREEN, player_controlled=True)
    enemies = [Entity(random.randint(0, 780), random.randint(0, 580), RED) for _ in range(20)]
    teammates = [Entity(random.randint(0, 780), random.randint(0, 580), BLUE) for _ in range(4)]

    # Initialize terrain
    terrain = []
    for _ in range(10):
        while True:
            x = random.randint(0, 770)
            y = random.randint(0, 570)
            if not (380 < x + 30 and x < 420 and 280 < y + 30 and y < 320):
                terrain.append(Terrain(x, y))
                break

    # Health bars
    max_enemy_health = 5
    max_teammate_health = 4
    enemy_health = len(enemies)
    teammate_health = len([t for t in teammates if t.alive]) + 1  # Include player initially

    # Timers and cooldowns
    block_cooldown = 0
    invulnerability_timer = 0
    enemy_contact_timer = None
    contact_enemy = None

    # Font for instructions
    font = pygame.font.SysFont(None, 36)

    running = True
    while running:
        screen.fill(BLACK)

        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_q:
                    print("Quitting game...")
                    pygame.quit()
                    sys.exit()
                elif event.key == K_1 and contact_enemy:
                    enemies.remove(contact_enemy)
                    enemy_health -= 1
                    contact_enemy = None
                    enemy_contact_timer = None
                elif event.key == K_2 and block_cooldown <= 0:
                    invulnerability_timer = 3 * FPS
                    block_cooldown = 10 * FPS

        # Find current player-controlled entity
        controlled_entity = next((e for e in [player] + teammates if e.player_controlled and e.alive), None)

        # Player movement
        if controlled_entity:
            keys = pygame.key.get_pressed()
            new_x = controlled_entity.x
            new_y = controlled_entity.y
            if keys[K_LEFT]:
                new_x -= controlled_entity.speed
            if keys[K_RIGHT]:
                new_x += controlled_entity.speed
            if keys[K_UP]:
                new_y -= controlled_entity.speed
            if keys[K_DOWN]:
                new_y += controlled_entity.speed

            # Boundary and terrain checks
            new_x = max(0, min(new_x, 800 - controlled_entity.size))
            new_y = max(0, min(new_y, 600 - controlled_entity.size))
            if not any(t.x < new_x + controlled_entity.size and new_x < t.x + t.size and
                       t.y < new_y + controlled_entity.size and new_y < t.y + t.size for t in terrain):
                controlled_entity.x = new_x
                controlled_entity.y = new_y

        # AI movement
        for enemy in enemies[:]:
            if not enemy.alive:
                continue
            target = controlled_entity if random.random() < 0.5 and controlled_entity else random.choice([t for t in teammates if t.alive]) if any(t.alive for t in teammates) else controlled_entity
            enemy.move_towards(target.x, target.y, terrain)

        for teammate in teammates[:]:
            if not teammate.alive or teammate.player_controlled:
                continue
            if enemies:
                target = random.choice([e for e in enemies if e.alive])
                teammate.move_towards(target.x, target.y, terrain)

        # Collision detection
        if controlled_entity:
            for enemy in enemies[:]:
                if not enemy.alive:
                    continue
                if abs(enemy.x - controlled_entity.x) < controlled_entity.size and abs(enemy.y - controlled_entity.y) < controlled_entity.size:
                    if not contact_enemy:
                        contact_enemy = enemy
                        enemy_contact_timer = random.randint(int(0.3 * FPS), int(2 * FPS))

        if contact_enemy and controlled_entity:
            enemy_contact_timer -= 1
            if enemy_contact_timer <= 0:
                controlled_entity.alive = False
                controlled_entity.player_controlled = False
                teammate_health -= 1
                contact_enemy = None
                enemy_contact_timer = None
                # Switch to a teammate if available
                alive_teammates = [t for t in teammates if t.alive and not t.player_controlled]
                if alive_teammates:
                    new_controlled = random.choice(alive_teammates)
                    new_controlled.player_controlled = True
                    new_controlled.color = GREEN

        for teammate in teammates[:]:
            if not teammate.alive:
                continue
            for enemy in enemies[:]:
                if not enemy.alive:
                    continue
                if abs(teammate.x - enemy.x) < teammate.size and abs(teammate.y - enemy.y) < teammate.size:
                    if invulnerability_timer > 0:
                        enemies.remove(enemy)
                        enemy_health -= 1
                    else:
                        if random.random() < 0.5:
                            teammate.alive = False
                            if teammate.player_controlled:
                                teammate.player_controlled = False
                                alive_teammates = [t for t in teammates if t.alive and not t.player_controlled]
                                if alive_teammates:
                                    new_controlled = random.choice(alive_teammates)
                                    new_controlled.player_controlled = True
                                    new_controlled.color = GREEN
                            teammate_health -= 1
                            break
                        else:
                            enemies.remove(enemy)
                            enemy_health -= 1

        # Update timers
        if block_cooldown > 0:
            block_cooldown -= 1
        if invulnerability_timer > 0:
            invulnerability_timer -= 1

        # Draw entities and terrain
        for t in terrain:
            t.draw(screen)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for teammate in teammates:
            teammate.draw(screen)

        # Draw health bars
        pygame.draw.rect(screen, RED, (50, 50, 200 * (enemy_health / max_enemy_health), 20))
        pygame.draw.rect(screen, BLUE, (50, 80, 200 * (teammate_health / max_teammate_health), 20))

        # Draw instructions
        text = font.render("Press 1 to attack. Press 2 to block.", True, WHITE)
        screen.blit(text, (50, 10))

        # Check win/lose conditions
        if enemy_health <= 0:
            print("You win!")
            running = False
        elif teammate_health <= 0:
            print("Game over!")
            running = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# Game mode selection
def select_game_mode():
    def validate_mode(choice):
        return choice in ['1', '2', '3']
    choice = get_input("Select game mode:\n1. Conquest (default map)\n2. Custom (build your own map)\n3. Warrior (battle mode)\nEnter 1, 2, or 3: ", validate_mode)
    return "Conquest" if choice == '1' else "Custom" if choice == '2' else "Warrior"

# Custom map building for Custom mode
def build_custom_map():
    territories = {}
    adjacencies = {}
    def validate_num(x):
        try:
            num = int(x)
            return 4 <= num <= 20
        except ValueError:
            return False
    num_territories = int(get_input("Enter the number of territories (4-20): ", validate_num))
    territory_names = []
    print("Enter the names of the territories (unique, no commas).")
    for i in range(num_territories):
        def validate_name(name):
            return name and name not in territory_names and "," not in name
        name = get_input(f"Territory {i+1} name: ", validate_name)
        territory_names.append(name)
    for name in territory_names:
        territories[name] = Territory(name, is_neutral=False)
    for name in territory_names:
        print(f"\nEnter territories adjacent to {name} (comma-separated, e.g., 'Territory1,Territory2').")
        print("Enter nothing for no adjacencies.")
        def validate_adj(adj_input):
            if not adj_input:
                return True
            adj_names = [n.strip() for n in adj_input.split(",") if n.strip()]
            return all(n in territory_names for n in adj_names)
        adj_input = get_input(f"Adjacent to {name}: ", validate_adj)
        adjacencies[name] = [n.strip() for n in adj_input.split(",") if n.strip()] if adj_input else []
    return territories, adjacencies, territory_names

# Game setup for Conquest and Custom modes
def setup_game(mode):
    global player, ai, neutral, europeans, territories, adjacencies
    player = Player("player")
    ai = Player("AI")
    neutral = Player("neutral")
    europeans = Player("europeans")
    if mode == "Conquest":
        territories = {name: Territory(name, is_neutral=(name in ["Pylos", "Larissa"])) 
                       for name in ["Sparta", "Athens", "Thebes", "Corinth", "Olympia", "Delphi", "Pylos", "Larissa"]}
        adjacencies = {
            "Sparta": ["Corinth", "Olympia"],
            "Athens": ["Thebes", "Corinth"],
            "Thebes": ["Athens", "Delphi", "Larissa"],
            "Corinth": ["Sparta", "Athens", "Olympia"],
            "Olympia": ["Sparta", "Corinth", "Delphi", "Pylos"],
            "Delphi": ["Thebes", "Olympia", "Larissa"],
            "Pylos": ["Olympia"],
            "Larissa": ["Thebes", "Delphi"]
        }
        territories["Sparta"].owner = player
        territories["Sparta"].units = {"swordsman": 5, "spearman": 5, "archer": 0}
        territories["Corinth"].owner = player
        territories["Corinth"].units = {"swordsman": 3, "spearman": 3, "archer": 3}
        territories["Olympia"].owner = player
        territories["Olympia"].units = {"swordsman": 4, "spearman": 2, "archer": 1}
        territories["Athens"].owner = ai
        territories["Athens"].units = {"swordsman": 0, "spearman": 5, "archer": 5}
        territories["Thebes"].owner = ai
        territories["Thebes"].units = {"swordsman": 2, "spearman": 4, "archer": 3}
        territories["Delphi"].owner = ai
        territories["Delphi"].units = {"swordsman": 1, "spearman": 3, "archer": 4}
        for name in ["Pylos", "Larissa"]:
            territories[name].owner = neutral
            territories[name].units = {
                "swordsman": random.randint(1, 5),
                "spearman": random.randint(1, 5),
                "archer": random.randint(1, 5)
            }
    else:  # Custom mode
        territories, adjacencies, territory_names = build_custom_map()
        num_territories = len(territory_names)
        if num_territories >= 7:
            third = num_territories // 3
            remainder = num_territories % 3
            player_count = third + (1 if remainder > 0 else 0)
            ai_count = third + (1 if remainder > 1 else 0)
            neutral_count = third
        else:
            player_count = (num_territories + 1) // 2
            ai_count = num_territories // 2
            neutral_count = 0
        random.shuffle(territory_names)
        for name in territory_names[:player_count]:
            territories[name].owner = player
            territories[name].is_neutral = False
            territories[name].units = {"swordsman": 5, "spearman": 5, "archer": 0}
        for name in territory_names[player_count:player_count + ai_count]:
            territories[name].owner = ai
            territories[name].is_neutral = False
            territories[name].units = {"swordsman": 0, "spearman": 5, "archer": 5}
        for name in territory_names[player_count + ai_count:]:
            territories[name].owner = neutral
            territories[name].is_neutral = True
            territories[name].units = {
                "swordsman": random.randint(1, 5),
                "spearman": random.randint(1, 5),
                "archer": random.randint(1, 5)
            }
    for name, adj_names in adjacencies.items():
        territories[name].adjacent = [territories[adj_name] for adj_name in adj_names]

# Game state for Conquest and Custom modes
game_running = True
FPS = 60

def display_state():
    state = "\n".join([f"{t.name}: {format_units(t.units)}, owned by {t.owner.name}" for t in territories.values()])
    print(state)
    return state

async def player_turn():
    global game_running
    print("Player's turn")
    display_state()
    while True:
        attack_from = get_input("Select territory to attack from (or 'done'): ")
        if attack_from.lower() == "done":
            break
        if attack_from not in territories or territories[attack_from].owner != player:
            print("Invalid selection")
            continue
        total_units = sum(territories[attack_from].units.values())
        if total_units < 2:
            print("Not enough units to attack")
            continue
        adjacent_targets = [t for t in territories[attack_from].adjacent if t.owner != player]
        if not adjacent_targets:
            print("No enemy or neutral territories adjacent")
            continue
        print(f"Adjacent targets: {[t.name for t in adjacent_targets]}")
        target = get_input("Select target territory: ")
        if target not in territories or territories[target] not in adjacent_targets:
            print("Invalid target")
            continue
        max_k = total_units - 1
        def validate_k(k):
            try:
                k = int(k)
                return 1 <= k <= max_k
            except ValueError:
                return False
        k = int(get_input(f"Choose number of units to commit (1 to {max_k}): ", validate_k))
        use_war_cry = False
        if player.war_cry_cooldown == 0:
            choice = get_input("Use War Cry? (y/n): ", lambda x: x.lower() in ['y', 'n'])
            if choice.lower() == 'y':
                use_war_cry = True
        if battle(territories[attack_from], territories[target], k, use_war_cry, territories, ai):
            if territories[target].owner == player:
                print(f"{attack_from} (Player) Wins! {format_units(territories[target].units)} remaining on {target}.")
            else:
                print(f"Attack from {attack_from} failed. {format_units(territories[target].units)} on {target}.")
            display_state()
        if use_war_cry:
            player.war_cry_cooldown = 2
        if player.war_cry_cooldown > 0:
            player.war_cry_cooldown -= 1
        if all(territory.owner in [player, neutral] for territory in territories.values()):
            print("Player wins!")
            game_running = False
            break

async def ai_turn():
    global game_running
    print("AI's turn")
    possible_attacks = [(t, adj) for t in territories.values() if t.owner == ai and sum(t.units.values()) > 1 
                        for adj in t.adjacent if adj.owner == player]
    if possible_attacks:
        num_attacks = random.randint(0, len(possible_attacks))
        if num_attacks > 0:
            selected_attacks = random.sample(possible_attacks, num_attacks)
            for attack_from, target in selected_attacks:
                k = random.randint(1, sum(attack_from.units.values()) - 1)
                print(f"AI attacks from {attack_from.name} to {target.name} with {k} units")
                if battle(attack_from, target, k, False, territories, ai):
                    if target.owner == ai:
                        print(f"{attack_from.name} (AI) Wins! {format_units(target.units)} remaining on {target.name}.")
                    else:
                        print(f"Attack from {attack_from.name} failed. {format_units(target.units)} on {target.name}.")
                    display_state()
    else:
        print("AI has no valid attacks this turn.")
    naval_assault(player, territories)
    if all(territory.owner in [ai, neutral] for territory in territories.values()):
        print("AI wins!")
        game_running = False

async def main():
    global game_running
    while True:
        game_mode = select_game_mode()
        if game_mode == "Warrior":
            warrior_mode()
        else:
            game_running = True
            setup_game(game_mode)
            while game_running:
                await player_turn()
                if not game_running:
                    break
                await ai_turn()
                if not game_running:
                    break
                diplomacy_meeting(player, ai, territories)
                if not game_running:
                    break
                european_turn(europeans, player, ai, territories)
                if not european_invasion(player, ai, europeans, territories):
                    game_running = False
                    break
                await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())