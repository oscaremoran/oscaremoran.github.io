import json
import os
import time
import select
import sys
import random

# Game Data Structures
class Room:
    def __init__(self, name, description, items=None, enemies=None, exits=None, is_shop=False, locked_exits=None, npcs=None):
        self.name = name
        self.description = description
        self.items = items or []
        self.enemies = enemies or []
        self.exits = exits or {}
        self.is_shop = is_shop
        self.locked_exits = locked_exits or {}
        self.npcs = npcs or []

    def to_dict(self):
        d = {
            "name": self.name,
            "description": self.description,
            "items": [item.to_dict() for item in self.items],
            "enemies": [enemy.to_dict() for enemy in self.enemies],
            "exits": self.exits,
            "is_shop": self.is_shop,
            "locked_exits": self.locked_exits,
            "npcs": [npc.to_dict() for npc in self.npcs]
        }
        if hasattr(self, "puzzle_solved"):
            d["puzzle_solved"] = self.puzzle_solved
        return d

class Item:
    def __init__(self, name, description, usable=False, price=0):
        self.name = name
        self.description = description
        self.usable = usable
        self.price = price

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "usable": self.usable,
            "price": self.price
        }

class Enemy:
    def __init__(self, name, title, description, health, damage, info=None, gold_drop=10):
        self.name = name
        self.title = title
        self.description = description
        self.health = health
        self.damage = damage
        self.info = info
        self.gold_drop = gold_drop

    def to_dict(self):
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "health": self.health,
            "damage": self.damage,
            "info": self.info,
            "gold_drop": self.gold_drop
        }

class NPC:
    def __init__(self, name, dialogue):
        self.name = name
        self.dialogue = dialogue

    def to_dict(self):
        return {
            "name": self.name,
            "dialogue": self.dialogue
        }

class Player:
    def __init__(self):
        self.age = "around 25-35 years old"
        self.gender = "man"
        self.health = 100
        self.mana = 100
        self.gold = 100
        self.spells = []
        self.inventory = [
            Item("leather tunic", "Basic leather tunic for protection."),
            Item("old torn leather boots", "Worn boots for walking."),
            Item("leather helmet", "A simple helmet."),
            Item("strange symbol", "A circle inside another circle. It doesn't seem to do anything.", usable=True)
        ]
        self.current_room = None
        self.memory = "You don’t know what happened to yourself and you need to find out. I am in a strange castle and don’t know where I am. There is a locked door in the room I am in. The room is lit by candles on the walls. I want to get out of here to find out what happened."
        self.unlocked_destinations = ["lokendar_se"]

    def to_dict(self):
        return {
            "health": self.health,
            "mana": self.mana,
            "gold": self.gold,
            "spells": self.spells,
            "inventory": [item.to_dict() for item in self.inventory],
            "current_room_name": self.current_room.name if self.current_room else None,
            "unlocked_destinations": self.unlocked_destinations
        }

# Game World Setup
def setup_world():
    rooms = {}

    # Isolated Island - Castle
    rooms["castle_start"] = Room(
        "Castle Starting Room",
        "You wake up in a dimly lit room lit by candles on the walls. There's a locked door ahead. You have no memory of how you got here.",
        items=[Item("key", "A rusty key to unlock doors.", usable=True)],
        exits={},
        locked_exits={"north": "castle_hall"}  # Locked until key is used
    )
    rooms["castle_hall"] = Room(
        "Castle Hall",
        "A grand hall with echoing footsteps. Paths lead to various rooms.",
        exits={"south": "castle_start", "east": "castle_library", "west": "castle_armory", "north": "castle_kitchen", "chamber": "dragon_chamber"}
    )
    rooms["castle_library"] = Room(
        "Castle Library",
        "Shelves filled with ancient books. Maybe some clues here.",
        items=[Item("book on liches", "A book mentioning Razukan, a powerful lich defeated long ago.")],
        exits={"west": "castle_hall"}
    )
    rooms["castle_armory"] = Room(
        "Castle Armory",
        "Weapons and armor racks. Some might be useful.",
        items=[Item("sword", "A sharp sword for fighting.", usable=True)],
        exits={"east": "castle_hall"}
    )
    rooms["castle_kitchen"] = Room(
        "Castle Kitchen",
        "Pots and pans, some food scraps. Nothing fancy.",
        items=[Item("health potion", "Restores health.", usable=True)],
        exits={"south": "castle_hall"}
    )
    rooms["dragon_chamber"] = Room(
        "Dragon Chamber",
        "A massive chamber with ancient carvings.",
        enemies=[Enemy(
            "Dragon",
            "The Dragon, Flame-Wreathed Sovereign",
            "A colossal beast with scales of molten crimson, its eyes glowing like embers and wings casting ominous shadows.",
            150, 50,
            "The dragon roars: 'Razukan the Lich has returned after a thousand years. He cursed you to sleep!'"
        )],
        exits={"south": "castle_hall", "out": "town_square"}
    )

    # Town Areas
    rooms["town_square"] = Room(
        "Town Square",
        "A small town terrified by a nearby hydra. Villagers look scared.",
        exits={"north": "forest", "east": "shrine", "west": "hydra_lair", "south": "shop", "dock": "dock"}
    )
    rooms["forest"] = Room(
        "Forest",
        "Dense woods with paths leading deeper.",
        exits={"south": "town_square"}
    )
    rooms["shrine"] = Room(
        "Shrine",
        "An ancient shrine with mystical aura. A memorization puzzle guards the magic scroll.",
        items=[Item("magic scroll", "Allows learning spells.", usable=True)],
        exits={"west": "town_square"}
    )
    rooms["shrine"].puzzle_solved = False
    rooms["hydra_lair"] = Room(
        "Hydra’s Lair",
        "A dark and eerie lair.",
        enemies=[Enemy(
            "Hydra",
            "Venomous Terror of the Deep",
            "A multi-headed serpent with glistening green scales, each head hissing with dripping venom.",
            120, 35,
            "The hydra hisses: 'Razukan is on Lokendar Island, plotting with Thanatos to corrupt the world!'"
        )],
        exits={"east": "town_square"}
    )
    rooms["shop"] = Room(
        "Town Shop",
        "A shop where you can buy items.",
        items=[
            Item("health potion", "Restores health.", usable=True, price=40),
            Item("mana potion", "Restores mana.", usable=True, price=40),
            Item("better sword", "A better sword.", usable=True, price=50)
        ],
        exits={"north": "town_square"},
        is_shop=True
    )
    rooms["dock"] = Room(
        "Dock",
        "A wooden dock extending into the sea. From here, you can sail to other islands if you have a boat.",
        exits={"town": "town_square"}
    )

    # Lokendar Quadrants
    rooms["lokendar_se"] = Room(
        "Lokendar - Southeast Quadrant",
        "An area with suspicious officials.",
        npcs=[NPC("Townsperson A", "Welcome to Lokendar, traveler. The city has seen better days.")],
        exits={"north": "lokendar_ne", "west": "lokendar_sw"}
    )
    rooms["lokendar_sw"] = Room(
        "Lokendar - Southwest Quadrant",
        "Government buildings loom here.",
        npcs=[NPC("Townsperson B", "Keep your wits about you; rumors of monsters in disguise abound.")],
        exits={"east": "lokendar_se", "north": "lokendar_nw"}
    )
    rooms["lokendar_ne"] = Room(
        "Lokendar - Northeast Quadrant",
        "Shadows linger in this quadrant.",
        npcs=[NPC("Townsperson C", "Nothing to see here, just going about my day.")],
        exits={"south": "lokendar_se", "west": "lokendar_nw"}
    )
    rooms["lokendar_nw"] = Room(
        "Lokendar - Northwest Quadrant",
        "The capital's center.",
        npcs=[NPC("Townsperson D", "What brings you to this part of town? Looking for trouble?")],
        exits={"east": "lokendar_ne", "south": "lokendar_sw", "chamber": "central_chamber"}
    )
    rooms["central_chamber"] = Room(
        "Central Chamber",
        "The central chamber of the capital.",
        enemies=[Enemy(
            "Corruption Monster",
            "Blight of the Eternal Void",
            "A grotesque mass of writhing shadows, its form pulsating with dark tendrils and glowing red eyes.",
            80, 30
        )],
        exits={"south": "lokendar_nw"}
    )

    return rooms, "castle_start"

# Helper to get room info
def get_room_info(room):
    info = room.description + "\n"
    if room.items:
        info += "Items here: " + ", ".join([item.name for item in room.items]) + "\n"
    if room.enemies:
        info += "Enemies here: " + ", ".join([enemy.name for enemy in room.enemies]) + "\n"
    if room.npcs:
        info += "NPCs here: " + ", ".join([npc.name for npc in room.npcs]) + "\n"
    if room.exits:
        info += "Available directions: " + ", ".join(room.exits.keys()) + "\n"
    if room.locked_exits:
        info += "Locked directions: " + ", ".join(room.locked_exits.keys()) + "\n"
    return info

# Game Functions
def parse_command(command, player, rooms):
    parts = command.lower().split()
    if not parts:
        return "Unrecognizable command. Try 'help'."

    action = parts[0]
    target = " ".join(parts[1:]) if len(parts) > 1 else None

    if action == "get":
        return get_item(player, target)
    elif action == "attack":
        return attack_enemy(player, target, rooms)
    elif action == "cast":
        return cast_spell(player, target)
    elif action == "use":
        return use_item(player, target, rooms)
    elif action == "buy":
        return buy_item(player, target)
    elif action == "save":
        return save_game(player, rooms)
    elif action == "load":
        return load_game(player, rooms)
    elif action == "look":
        return get_room_info(player.current_room)
    elif action == "inventory":
        return "Inventory: " + ", ".join([item.name for item in player.inventory]) + f"\nGold: {player.gold}\nMana: {player.mana}\nSpells: {', '.join(player.spells)}"
    elif action == "go":
        return go_to(player, target, rooms)
    elif action == "talk":
        return talk_npc(player, target, rooms)
    elif action == "memorize":
        return memorize_puzzle(player)
    elif action == "help":
        return "Commands: get [item], attack [enemy], cast [spell on enemy], use [item], buy [item], save, load, look, inventory, go [direction], talk [npc], memorize (at shrine)"
    else:
        return "Unknown command. Try 'help'."

def get_item(player, item_name):
    for item in player.current_room.items:
        if item.name.lower() == item_name:
            if item.name == "magic scroll" and player.current_room.name == "Shrine":
                if not hasattr(player.current_room, "puzzle_solved") or not player.current_room.puzzle_solved:
                    return "You must solve the memorization puzzle first. Use 'memorize' command."
            player.inventory.append(item)
            player.current_room.items.remove(item)
            if item.name == "magic scroll":
                player.spells.append("firebolt")
                return f"You picked up {item.name} and learned firebolt spell!"
            return f"You picked up {item.name}."
    return "No such item here."

def talk_npc(player, npc_name, rooms):
    for npc in player.current_room.npcs:
        if npc.name.lower() == npc_name:
            rand = random.random()
            if rand < 0.5:
                # Boring dialogue
                return npc.dialogue
            elif rand < 0.75:
                # Gambling game
                print("Want to play a gambling game?")
                response = input("> ").lower()
                if response in ["y", "yes"]:
                    if player.gold >= 50:
                        player.gold -= 50
                        return "The Game Begins! Oh... wait... where did he go? Oh no, I can't find 50 of my gold!"
                    else:
                        return "You don't have enough gold."
                else:
                    return "Maybe next time."
            elif rand < 0.85:
                # Monster reveal
                monster = Enemy("Hidden Monster", "Shadowed Deceiver", "A cloaked figure with glowing eyes, its form shimmering unnaturally.", 60, 25)
                player.current_room.enemies.append(monster)
                player.current_room.npcs.remove(npc)
                return "The townsperson reveals itself as a monster! Prepare to fight!"
            elif rand < 0.95:
                # Offer spell scroll
                spell = random.choice(["firebolt", "icebolt", "heal"])
                print(f"Want to buy a {spell} scroll for 100 gold?")
                response = input("> ").lower()
                if response in ["y", "yes"]:
                    if player.gold >= 100:
                        player.gold -= 100
                        player.spells.append(spell)
                        return f"You bought the {spell} scroll!"
                    else:
                        return "Not enough gold."
                else:
                    return "Offer declined."
            else:
                # Punch
                player.health -= 10
                if player.health <= 0:
                    return "You died! Game over."
                return f"The townsperson punches you in the face! -10 health. Your health: {player.health}"
    return "No such NPC here."

def memorize_puzzle(player):
    if player.current_room.name != "Shrine":
        return "No puzzle here."
    if hasattr(player.current_room, "puzzle_solved") and player.current_room.puzzle_solved:
        return "Puzzle already solved."
    sequence = [random.randint(1, 9) for _ in range(5)]
    print("Memorize the sequence:")
    for num in sequence:
        print(num, end=" ", flush=True)
        time.sleep(0.75)
    print("\r" + " " * 20, end="\r", flush=True)  # Clear the line
    print("Now, enter the sequence separated by spaces:")
    inp = input("> ").strip().split()
    try:
        user_seq = [int(x) for x in inp]
        if user_seq == sequence:
            player.current_room.puzzle_solved = True
            return "Correct! You can now get the magic scroll."
        else:
            return "Wrong. Try again."
    except ValueError:
        return "Invalid input."

def attack_enemy(player, enemy_name, rooms):
    bosses = ["Dragon", "Hydra", "Corruption Monster"]
    for enemy in player.current_room.enemies:
        if enemy.name.lower() == enemy_name:
            print(f"{enemy.title}: {enemy.description}")
            while enemy.health > 0 and player.health > 0:
                print(f"Combat with {enemy.name}! Enemy health: {enemy.health}, Your health: {player.health}, Mana: {player.mana}")
                print("What do you do? (attack, cast [spell], use [item], flee)")
                cmd = input("> ").lower()
                parts = cmd.split()
                action = parts[0]
                target = " ".join(parts[1:]) if len(parts) > 1 else None

                if action == "flee":
                    return "You fled the combat."
                elif action == "attack":
                    damage = 30 if any(item.name == "better sword" for item in player.inventory) else 20
                    enemy.health -= damage
                    if enemy.health <= 0:
                        break
                    print(f"You hit {enemy.name}! Now health: {enemy.health}")
                elif action == "cast" and target:
                    if target in player.spells and player.mana >= 20:
                        player.mana -= 20
                        if target == "heal":
                            player.health += 30
                            print(f"You cast {target}! Health restored to {player.health}")
                        else:
                            enemy.health -= 20
                            if enemy.health <= 0:
                                break
                            print(f"You cast {target}! Enemy health: {enemy.health}")
                    else:
                        print("Can't cast that.")
                        continue
                elif action == "use" and target:
                    res = use_item(player, target, rooms, in_combat=True)
                    print(res)
                else:
                    print("Invalid action.")
                    continue

                if enemy.health > 0:
                    attack_types = ["light", "heavy"]
                    if enemy.name in bosses:
                        attack_types.append("special")
                    attack = random.choice(attack_types)
                    if attack == "light":
                        prompt = f"Enemy light attack! Type 'jump' within 2 seconds!"
                        correct = ["jump"]
                        time_limit = 2
                        dmg = random.randint(5 + enemy.damage // 10, 15 + enemy.damage // 10)
                    elif attack == "heavy":
                        prompt = f"Enemy heavy attack! Type 'dodge' within 4 seconds!"
                        correct = ["dodge"]
                        time_limit = 4
                        dmg = random.randint(10 + enemy.damage // 10, 20 + enemy.damage // 10)
                    elif attack == "special":
                        if enemy.name == "Dragon":
                            prompt = "Dragon breathes fire! Type 'roll' within 3 seconds!"
                            correct = ["roll"]
                            time_limit = 3
                            dmg = 30 + enemy.damage // 10
                        elif enemy.name == "Hydra":
                            prompt = "Hydra spits poison! Type 'block' within 3 seconds!"
                            correct = ["block"]
                            time_limit = 3
                            dmg = 25 + enemy.damage // 10
                        elif enemy.name == "Corruption Monster":
                            prompt = "Corruption Monster fires a corrupt beam! Type 'reflect' within 3 seconds!"
                            correct = ["reflect"]
                            time_limit = 3
                            dmg = 35 + enemy.damage // 10

                    print(prompt)
                    start_time = time.time()
                    inp = ""
                    while time.time() - start_time < time_limit:
                        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                        if rlist:
                            inp = sys.stdin.readline().strip().lower()
                            break
                    if inp in correct:
                        print("You dodged!")
                    else:
                        player.health -= dmg
                        print(f"You took {dmg} damage! Your health: {player.health}")
                        if player.health <= 0:
                            return "You died! Game over."

            if player.health > 0:
                player.current_room.enemies.remove(enemy)
                player.gold += enemy.gold_drop
                info = enemy.info if enemy.info else ""
                if enemy.name == "Hydra":
                    player.inventory.append(Item("boat", "A boat to reach Lokendar.", usable=True))
                    info += " You received a boat!"
                return f"You defeated {enemy.name}! {info} Gained {enemy.gold_drop} gold."
    return "No such enemy here."

def cast_spell(player, target):
    return "Cast during combat."

def use_item(player, item_name, rooms, in_combat=False):
    for item in player.inventory:
        if item.name.lower() == item_name and item.usable:
            if item_name == "key":
                if player.current_room.name == "Castle Starting Room":
                    if "north" in player.current_room.locked_exits:
                        player.current_room.exits["north"] = player.current_room.locked_exits["north"]
                        del player.current_room.locked_exits["north"]
                        player.inventory.remove(item)
                        return "You used the key to unlock the door and it vanishes."
                    return "Door already unlocked."
            elif item_name == "health potion":
                player.health += 50
                if not in_combat:
                    player.inventory.remove(item)
                return "Health restored."
            elif item_name == "mana potion":
                player.mana += 50
                if not in_combat:
                    player.inventory.remove(item)
                return "Mana restored."
            elif item_name == "strange symbol":
                return "It doesn't seem to do anything."
            elif item_name == "boat":
                if player.current_room.name != "Dock":
                    return "You can only use the boat at a dock."
                destinations = {
                    "lokendar_se": "Lokendar",
                    "spring_of_courage": "???",
                    "whirlpool": "???"
                }
                unlocked = [k for k in destinations.keys() if k in player.unlocked_destinations]
                print("Available destinations:")
                for key in destinations:
                    name = destinations[key] if key in player.unlocked_destinations else "???"
                    print(f"- {name}")
                print("Where would you like to sail?")
                choice = input("> ").lower()
                for key, name in destinations.items():
                    if choice == name.lower() or (key in player.unlocked_destinations and choice == key):
                        if key in player.unlocked_destinations:
                            player.current_room = rooms[key]
                            return f"You sail to {player.current_room.name}. " + get_room_info(player.current_room)
                        else:
                            return "That destination is locked."
                return "Invalid destination."
            return f"Used {item.name}."
    return "Can't use that."

def buy_item(player, item_name):
    if not player.current_room.is_shop:
        return "No shop here."
    for item in player.current_room.items:
        if item.name.lower() == item_name and item.price > 0:
            if player.gold >= item.price:
                player.gold -= item.price
                player.inventory.append(item)
                player.current_room.items.remove(item)
                return f"You bought {item.name} for {item.price} gold."
            else:
                return "Not enough gold."
    return "No such item for sale."

def save_game(player, rooms):
    data = {
        "player": player.to_dict(),
        "rooms": {key: room.to_dict() for key, room in rooms.items()}
    }
    with open("save.json", "w") as f:
        json.dump(data, f)
    return "Game saved."

def load_game(player, rooms):
    if os.path.exists("save.json"):
        with open("save.json", "r") as f:
            data = json.load(f)
        player.health = data["player"]["health"]
        player.mana = data["player"]["mana"]
        player.gold = data["player"]["gold"]
        player.spells = data["player"]["spells"]
        player.inventory = [Item(**item_data) for item_data in data["player"]["inventory"]]
        player.unlocked_destinations = data["player"].get("unlocked_destinations", ["lokendar_se"])
        current_room_name = data["player"]["current_room_name"]
        # Reconstruct rooms
        for room_key, room_data in data["rooms"].items():
            rooms[room_key].items = [Item(**item) for item in room_data["items"]]
            rooms[room_key].enemies = [Enemy(**enemy) for enemy in room_data["enemies"]]
            rooms[room_key].exits = room_data["exits"]
            rooms[room_key].locked_exits = room_data["locked_exits"]
            rooms[room_key].npcs = [
                NPC(npc["name"], npc["dialogue"]) for npc in room_data.get("npcs", [])
            ]
            if "puzzle_solved" in room_data:
                setattr(rooms[room_key], "puzzle_solved", room_data["puzzle_solved"])
        # Set current room by name
        for room in rooms.values():
            if room.name == current_room_name:
                player.current_room = room
                break
        return "Game loaded."
    return "No save file."

def go_to(player, direction, rooms):
    if direction in player.current_room.exits:
        next_room_key = player.current_room.exits[direction]
        if next_room_key:
            player.current_room = rooms[next_room_key]
            return f"You go {direction}. Now in {player.current_room.name}. " + get_room_info(player.current_room)
    elif direction in player.current_room.locked_exits:
        return f"The {direction} exit is locked."
    return "Can't go there."

# Main Game Loop
def main():
    rooms, start_key = setup_world()
    player = Player()
    player.current_room = rooms[start_key]
    print("Tales of Razukan")
    print(get_room_info(player.current_room))

    while True:
        command = input("> ")
        if command.lower() == "quit":
            break
        response = parse_command(command, player, rooms)
        print(response)

if __name__ == "__main__":
    main()