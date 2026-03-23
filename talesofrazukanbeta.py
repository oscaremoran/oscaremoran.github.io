import json
import os
import time
import select
import sys
import random

# Game Data Structures
class Room:
    def __init__(self, name, description, items=None, enemies=None, exits=None, locked_exits=None):
        self.name = name
        self.description = description
        self.items = items or []
        self.enemies = enemies or []
        self.exits = exits or {}
        self.locked_exits = locked_exits or {}

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "items": [item.to_dict() for item in self.items],
            "enemies": [enemy.to_dict() for enemy in self.enemies],
            "exits": self.exits,
            "locked_exits": self.locked_exits
        }

class Item:
    def __init__(self, name, description, usable=False):
        self.name = name
        self.description = description
        self.usable = usable

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "usable": self.usable
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

class Player:
    def __init__(self):
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

    def to_dict(self):
        return {
            "health": self.health,
            "mana": self.mana,
            "gold": self.gold,
            "spells": self.spells,
            "inventory": [item.to_dict() for item in self.inventory],
            "current_room_name": self.current_room.name if self.current_room else None
        }

# Game World Setup
def setup_world():
    rooms = {}

    # Castle Areas
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
        "A massive chamber with ancient carvings. The dragon blocks the path to the outside.",
        enemies=[Enemy(
            "Dragon",
            "The Dragon, Flame-Wreathed Sovereign",
            "A colossal beast with scales of molten crimson, its eyes glowing like embers and wings casting ominous shadows.",
            80, 50,
            "The dragon roars: 'Razukan the Lich has returned after a thousand years. He cursed you to sleep!'"
        )],
        exits={"south": "castle_hall"}
    )

    return rooms, "castle_start"

# Helper to get room info
def get_room_info(room):
    info = room.description + "\n"
    if room.items:
        info += "Items here: " + ", ".join([item.name for item in room.items]) + "\n"
    if room.enemies:
        info += "Enemies here: " + ", ".join([enemy.name for enemy in room.enemies]) + "\n"
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
    elif action == "help":
        return "Commands: get [item], attack [enemy], cast [spell], use [item], save, load, look, inventory, go [direction]"
    else:
        return "Unknown command. Try 'help'."

def get_item(player, item_name):
    for item in player.current_room.items:
        if item.name.lower() == item_name:
            player.inventory.append(item)
            player.current_room.items.remove(item)
            return f"You picked up {item.name}."
    return "No such item here."

def attack_enemy(player, enemy_name, rooms):
    for enemy in player.current_room.enemies:
        if enemy.name.lower() == enemy_name:
            if enemy.title and enemy.description:
                print(f"{enemy.title}: {enemy.description}")
            frozen = False
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
                    damage = 30 if any(item.name == "sword" for item in player.inventory) else 20
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
                        elif target == "icebolt":
                            enemy.health -= 20
                            frozen = True
                            print(f"You cast {target}! Enemy health: {enemy.health}. The enemy is frozen for a turn!")
                            if enemy.health <= 0:
                                break
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
                    if frozen:
                        print("The enemy is frozen and skips its turn!")
                        frozen = False
                        continue
                    attack_types = ["light", "heavy", "special"]
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
                        prompt = "Dragon breathes fire! Type 'roll' within 3 seconds!"
                        correct = ["roll"]
                        time_limit = 3
                        dmg = 30 + enemy.damage // 10

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
                if enemy.name == "Dragon":
                    return f"You defeated {enemy.name}! {info} Beta Version Complete!!"
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
            elif item_name == "strange symbol":
                return "It doesn't seem to do anything."
            return f"Used {item.name}."
    return "Can't use that."

def save_game(player, rooms):
    data = {
        "player": player.to_dict(),
        "rooms": {key: room.to_dict() for key, room in rooms.items()}
    }
    with open("save_beta.json", "w") as f:
        json.dump(data, f)
    return "Game saved."

def load_game(player, rooms):
    if not os.path.exists("save_beta.json"):
        return "No save file found."
    try:
        with open("save_beta.json", "r") as f:
            data = json.load(f)
        # Reset rooms to ensure consistency
        new_rooms, _ = setup_world()
        rooms.clear()
        rooms.update(new_rooms)
        # Load player data
        player.health = data["player"].get("health", 100)
        player.mana = data["player"].get("mana", 100)
        player.gold = data["player"].get("gold", 100)
        player.spells = data["player"].get("spells", [])
        player.inventory = [Item(**item_data) for item_data in data["player"].get("inventory", [])]
        current_room_name = data["player"].get("current_room_name", "castle_start")
        # Update room data
        for room_key, room_data in data.get("rooms", {}).items():
            if room_key in rooms:
                rooms[room_key].items = [Item(**item) for item in room_data.get("items", [])]
                rooms[room_key].enemies = [Enemy(**enemy) for enemy in room_data.get("enemies", [])]
                rooms[room_key].exits = room_data.get("exits", {})
                rooms[room_key].locked_exits = room_data.get("locked_exits", {})
        # Set current room
        for room in rooms.values():
            if room.name == current_room_name:
                player.current_room = room
                break
        else:
            player.current_room = rooms["castle_start"]
            print("Warning: Saved room not found. Starting in Castle Starting Room.")
        return "Game loaded successfully."
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error loading save file: {e}. Starting fresh.")
        rooms.clear()
        new_rooms, start_key = setup_world()
        rooms.update(new_rooms)
        player.current_room = rooms[start_key]
        player.health = 100
        player.mana = 100
        player.gold = 100
        player.spells = []
        player.inventory = [
            Item("leather tunic", "Basic leather tunic for protection."),
            Item("old torn leather boots", "Worn boots for walking."),
            Item("leather helmet", "A simple helmet."),
            Item("strange symbol", "A circle inside another circle. It doesn't seem to do anything.", usable=True)
        ]
        return "Save file corrupted. Started new game."

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
    print("Tales of Razukan - Beta Version")
    print("Explore the Castle and defeat the Dragon to complete the beta!")
    print(get_room_info(player.current_room))

    while True:
        command = input("> ")
        if command.lower() == "quit":
            break
        response = parse_command(command, player, rooms)
        print(response)
        if "Beta Version Complete!!" in response:
            print("Thank you for playing the beta version!")
            break

if __name__ == "__main__":
    main()