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
    def __init__(self, name, title, description, health, damage, info=None, gold_drop=10, difficulty="normal"):
        self.name = name
        self.title = title
        self.description = description
        self.base_health = health
        self.base_damage = damage
        self.info = info
        self.gold_drop = gold_drop
        self.health = self._apply_difficulty(health, difficulty, "health")
        self.damage = self._apply_difficulty(damage, difficulty, "damage")

    def _apply_difficulty(self, value, difficulty, attribute_type):
        multipliers = {
            "easy": {"health": 0.5, "damage": 0.5},
            "normal": {"health": 1.0, "damage": 1.0},
            "hard": {"health": 1.5, "damage": 1.5},
            "expert": {"health": 2.0, "damage": 2.0}
        }
        return int(value * multipliers.get(difficulty.lower(), {"health": 1.0, "damage": 1.0})[attribute_type])

    def to_dict(self):
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "health": self.health,
            "damage": self.damage,
            "base_health": self.base_health,
            "base_damage": self.base_damage,
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
        self.corruption_monster_defeated = False
        self.defeated_bosses = []
        self.difficulty = "normal"

    def to_dict(self):
        return {
            "health": self.health,
            "mana": self.mana,
            "gold": self.gold,
            "spells": self.spells,
            "inventory": [item.to_dict() for item in self.inventory],
            "current_room_name": self.current_room.name if self.current_room else None,
            "unlocked_destinations": self.unlocked_destinations,
            "corruption_monster_defeated": self.corruption_monster_defeated,
            "defeated_bosses": self.defeated_bosses,
            "difficulty": self.difficulty
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
        locked_exits={"north": "castle_hall"}
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
            80, 50,
            "The dragon roars: 'Razukan the Lich has returned after a thousand years. He cursed you to sleep!'"
        )],
        exits={"south": "castle_hall"},
        locked_exits={"out": "town_square"}
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
            "The Hydra, Venomous Terror of the Deep",
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
            Item("better sword", "A better sword.", usable=True, price=40)
        ],
        exits={"north": "town_square"},
        is_shop=True
    )
    #stuff
    rooms["shop"].original_items = rooms["shop"].items[:]   # ← PASTE THIS LINE
    #stuff
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
        exits={"north": "lokendar_ne", "west": "lokendar_sw", "junkyard": "junkyard", "dock": "lokendar_dock"},
        locked_exits={"gate": "black_keep_gate"}
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
            "Corruption Monster, Blight of Lokendar",
            "A grotesque mass of writhing shadows, its form pulsating with dark tendrils and glowing red eyes.",
            150, 30,
            "As it falls, the Corruption Monster wheezes: 'Razukan awaits at the Black Keep, a dungeon beyond Lokendar’s borders!'"
        )],
        exits={"south": "lokendar_nw"}
    )

    # Junkyard
    rooms["junkyard"] = Room(
        "The Junkyard",
        "A desolate expanse filled with broken machinery and refuse. A merchant here sells rare items.",
        items=[
            Item("grenade", "A one-use explosive device that deals heavy damage.", usable=True, price=40),
            Item("airship", "A magnificent airship to fly to the Sky Castle.", usable=True, price=50)
        ],
        exits={"southeast": "lokendar_se"},
        is_shop=True
    )
    #stuff
    rooms["junkyard"].original_items = rooms["junkyard"].items[:]   # ← PASTE THIS LINE
    #stuff
    # Black Keep
    rooms["black_keep_gate"] = Room(
        "Black Keep Gate",
        "The imposing gate of the Black Keep, a dark fortress shrouded in mist. Ancient runes pulse faintly on the stone.",
        exits={"southeast": "lokendar_se", "north": "black_keep_courtyard"},
        items=[Item("keep key 1", "A heavy iron key, one of three needed to unlock the inner chamber.", usable=True)]
    )
    rooms["black_keep_courtyard"] = Room(
        "Black Keep Courtyard",
        "A cracked stone courtyard surrounded by crumbling towers. Shadows move in the corners.",
        enemies=[Enemy(
            "Spectral Knight",
            "",
            "",
            60, 25
        )],
        exits={"south": "black_keep_gate", "east": "black_keep_hall", "west": "black_keep_armory"}
    )
    rooms["black_keep_hall"] = Room(
        "Black Keep Hall",
        "A long hall lined with faded tapestries. The air feels heavy with dread.",
        enemies=[Enemy(
            "Shadow Hound",
            "",
            "",
            50, 20
        )],
        items=[Item("keep key 2", "A silver key etched with cryptic symbols, one of three needed to unlock the inner chamber.", usable=True)],
        exits={"west": "black_keep_courtyard"}
    )
    rooms["black_keep_armory"] = Room(
        "Black Keep Armory",
        "Rusted weapons and armor lie scattered, remnants of a forgotten garrison.",
        items=[Item("keep key 3", "A bronze key with a skull motif, one of three needed to unlock the inner chamber.", usable=True)],
        enemies=[Enemy(
            "Cursed Sentinel",
            "",
            "",
            70, 30
        )],
        exits={"east": "black_keep_courtyard"},
        locked_exits={"north": "razukan_lair"}
    )
    rooms["razukan_lair"] = Room(
        "Razukan's Lair",
        "A foreboding chamber pulsing with dark energy.",
        enemies=[Enemy(
            "Razukan",
            "Razukan, The Eternal Lich",
            "A skeletal figure cloaked in tattered robes, his eyes burning with unholy fire.",
            1, 0
        )],
        exits={"south": "black_keep_armory"}
    )

    # Spring of Courage
    rooms["spring_of_courage"] = Room(
        "Spring of Courage",
        "A sacred spring surrounded by ancient statues. A formidable guardian tests your courage!",
        enemies=[
            Enemy(
                "Sacred Guardian",
                "Sacred Guardian, Protector of the Spring",
                "A towering figure clad in radiant armor, wielding a blade infused with holy light.",
                150, 25
            )
        ],
        exits={}
    )

    # Whirlpool
    rooms["whirlpool"] = Room(
        "Whirlpool",
        "A swirling vortex of water.",
        enemies=[Enemy(
            "Kraken",
            "Kraken, Terror of the Seas",
            "A massive octopus-like beast with tentacles whipping through the waves, its beak snapping hungrily.",
            400, 40
        )],
        exits={}
    )

    # Lokendar Dock
    rooms["lokendar_dock"] = Room(
        "Lokendar Dock",
        "A sturdy dock in Lokendar's harbor. From here, you can sail back to other islands if you have a boat.",
        exits={"north": "lokendar_se"}
    )

    # Sky Castle Entry
    rooms["sky_castle_entry"] = Room(
        "Sky Castle Entry",
        "The entrance to a huge, floating castle among the clouds.",
        exits={"north": "sky_castle_courtyard"}
    )
    rooms["sky_castle_courtyard"] = Room(
        "Sky Castle Courtyard",
        "A huge room in the center of the magnificent Sky Castle, with an engraving on a wall saying 'Bring me riches!'",
        enemies=[Enemy(
            "Sky Giant",
            "Sky Giant, Defender of the Castle",
            "A huge giant with a massive spiked club.",
            180, 35    
        )],
        exits={"south": "sky_castle_entry", "east": "sky_castle_secret"},
        locked_exits={"north": "sky_castle_arena"}
    )
    # Modify the "treasure" item in sky_castle_secret to make it usable
    rooms["sky_castle_secret"] = Room(
    "Sky Castle Treasure Room",
    "A hidden room in the Sky Castle, filled with treasure.",
    items=[Item("treasure", "Gleaming gold coins. Perhaps they can be used to unlock something sacred.", usable=True)],
    exits={"west": "sky_castle_courtyard"},
    )
    rooms["sky_castle_arena"] = Room(
    "Sky Castle Arena",
    "A vast, ethereal arena floating among the clouds. The air hums with ancient power.",
    enemies=[Enemy(
        "Remnant",
        "The Remnant, Fragment of Razukan's Soul",
        "A black skeleton with rifts in the air around it, a servant of Razukan's will.",
        230, 45,
        "The Remnant breaks into black bones that dissipate before your eyes.",
    )],
    exits={"south": "sky_castle_courtyard"},
    locked_exits={"north": "sky_castle_arena_two"}
    )
    rooms["sky_castle_arena_two"] = Room(
    "Sky Castle Throne Room",
    "A huge throne room with a steel throne.", 
    enemies=[Enemy(
        "Skeletal Razukan",
        "Razukan, Destroyer of Mankind",
        "The evil sorcerer of legend, poised to destroy the world.",
        250, 50,
        "Razukan groans and falls back. Then, strangely, he begins to laugh. He begins talking: 'You haven't gotten close to stopping me! All you've done is slow me down!' Razukan grabs his staff and begins to chant, in a low voice: 'Thanatos... Awaken... FOREVERMORE!' A huge shape bursts out of the ground, destroying the castle. Razukan teleports away, laughing manaically."

    )],
    exits={"south": "sky_castle_arena"}
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
    elif action == "set_difficulty":
        return set_difficulty(player, rooms, target)
    elif action == "help":
        help_text = "Commands: get [item], attack [enemy], cast [spell], use [item], buy [item], save, load, look, inventory, go [direction], talk [npc], memorize (at shrine), set_difficulty [easy|normal|hard|expert]"
        if "airship" in [item.name for item in player.inventory] and player.current_room.name in ["Razukan's Lair", "Sky Castle Entry", "The Junkyard"]:
            help_text += ", use airship"
        return help_text
    else:
        return "Unknown command. Try 'help'."

def get_item(player, item_name):
    for item in player.current_room.items:
        if item.name.lower() == item_name:
            if player.current_room.is_shop and item.price > 0:
                return f"You can't pick up {item.name}. Try 'buy {item.name}'."
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
                return npc.dialogue
            elif rand < 0.75:
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
                monster = Enemy("Hidden Monster", "Shadowed Deceiver", "A cloaked figure with glowing eyes, its form shimmering unnaturally.", 60, 25)
                player.current_room.enemies.append(monster)
                player.current_room.npcs.remove(npc)
                return "The townsperson reveals itself as a monster! Prepare to fight!"
            elif rand < 0.95:
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
                player.health -= 10
                if player.health <= 0:
                    print("You died! Game over.")
                    sys.exit()
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
    print("\r" + " " * 20, end="\r", flush=True)
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
    bosses = ["Dragon", "Hydra", "Corruption Monster", "Crystal Mech", "Kraken", "Sacred Guardian", "Remnant", "Skeletal Razukan", "Thanatos"]
    for enemy in player.current_room.enemies:
        if enemy.name.lower() == enemy_name:
            if enemy.name == "Razukan":
                print("Razukan laughs: 'My secret plan to destroy the world is nearly complete... But you won't be there to see it. CRYSTAL MECH? Destroy him.'")
                print("He continues: 'I’m heading to the Sky Castle to unleash my ultimate power!'")
                print("Razukan flies off, summoning the Crystal Mech!")
                player.current_room.enemies.remove(enemy)
                crystal_mech = Enemy(
                    "Crystal Mech",
                    "Crystal Mech, Guardian of Annihilation",
                    "A towering construct of shimmering crystals, its limbs crackling with destructive energy.",
                    220, 40, difficulty=player.difficulty
                )
                player.current_room.enemies.append(crystal_mech)
                return "The Crystal Mech activates! Prepare for battle."
            if enemy.title and enemy.description:
                print(f"{enemy.title}: {enemy.description}")
            frozen = False
            while enemy.health > 0 and player.health > 0:
                print(f"Combat with {enemy.name}! Enemy health: {enemy.health}, Your health: {player.health}, Mana: {player.mana}")
                if enemy.name == "Kraken":
                    print("What do you do? (shoot cannon)")
                else:
                    print("What do you do? (attack, cast [spell], use [item], flee)")
                cmd = input("> ").lower()
                parts = cmd.split()
                action = parts[0]
                target = " ".join(parts[1:]) if len(parts) > 1 else None
                if action == "flee" and enemy.name != "Kraken":
                    return "You fled the combat."
                elif action == "attack" and enemy.name != "Kraken":
                    damage = 30 if any(item.name == "better sword" for item in player.inventory) else 20 if any(item.name == "sword" for item in player.inventory) else 10
                    enemy.health -= damage
                    if enemy.health <= 0:
                        break
                    print(f"You hit {enemy.name}! Now health: {enemy.health}")
                elif action == "shoot" and target == "cannon" and enemy.name == "Kraken":
                    print("Prepare to fire the cannon! Type 'fire' within 1.5 seconds!")
                    start_time = time.time()
                    inp = ""
                    while time.time() - start_time < 1.5:
                        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                        if rlist:
                            inp = sys.stdin.readline().strip().lower()
                            break
                    if inp == "fire":
                        damage = 50
                        enemy.health -= damage
                        if enemy.health <= 0:
                            break
                        print(f"You fire the cannon at {enemy.name}! Now health: {enemy.health}")
                    else:
                        print("You failed to fire the cannon in time!")
                elif action == "cast" and target and enemy.name != "Kraken":
                    if target in player.spells and player.mana >= 25:
                        player.mana -= 25
                        if target == "heal":
                            player.health += 30
                            print(f"You cast {target}! Health restored to {player.health}")
                        elif target == "icebolt":
                            enemy.health -= 15
                            frozen = True
                            print(f"You cast {target}! Enemy health: {enemy.health}. The enemy is frozen for a turn!")
                            if enemy.health <= 0:
                                break
                        else:
                            enemy.health -= 40
                            if enemy.health <= 0:
                                break
                            print(f"You cast {target}! Enemy health: {enemy.health}")
                    else:
                        print("Can't cast that.")
                        continue
                elif action == "use" and target and enemy.name != "Kraken":
                    res = use_item(player, target, rooms, in_combat=True)
                    print(res)
                    if res.startswith("Grenade thrown!"):
                        enemy.health -= 50
                        print(f"The grenade deals 50 damage to {enemy.name}! Enemy health: {enemy.health}")
                        if enemy.health <= 0:
                            break
                else:
                    print("Invalid action." if enemy.name != "Kraken" else "Only 'shoot cannon' is allowed against the Kraken.")
                    continue
                if enemy.health > 0:
                    if frozen:
                        print("The enemy is frozen and skips its turn!")
                        frozen = False
                        continue
                    attack_count = 4 if enemy.name == "Sacred Guardian" else 2 if enemy.name == "Kraken" and enemy.health <= enemy._apply_difficulty(200, player.difficulty, "health") else 2 if enemy.name == "Crystal Mech" and enemy.health <= enemy._apply_difficulty(110, player.difficulty, "health") else 5 if enemy.name == "Remnant" else 6 if enemy.name == "Skeletal Razukan" else 5 if enemy.name == "Thanatos" else 1
                    for attack_num in range(attack_count):
                        if enemy.health <= 0 or player.health <= 0:
                            break
                        if attack_num > 0:
                            print(f"{enemy.name} attacks again! ({attack_num + 1}/{attack_count})")
                        attack_types = ["light", "heavy"]
                        if enemy.name in bosses:
                            attack_types.append("special")
                        attack = random.choice(attack_types)
                        time_limits = {
                            "easy": {"light": 3.0, "heavy": 4.0, "special": 3.5},
                            "normal": {"light": 2.0, "heavy": 3.0, "special": 2.5},
                            "hard": {"light": 1.5, "heavy": 2.5, "special": 2.0},
                            "expert": {"light": 1.0, "heavy": 2.0, "special": 1.5}
                        }
                        time_limit = time_limits.get(player.difficulty.lower(), {"light": 2.0, "heavy": 3.0, "special": 2.5})[attack]
                        if attack == "light":
                            prompt = f"Enemy light attack! Type 'jump' within {time_limit} seconds!"
                            correct = ["jump"]
                            dmg = random.randint(10 + enemy.damage // 10, 20 + enemy.damage // 10)
                        elif attack == "heavy":
                            prompt = f"Enemy heavy attack! Type 'dodge' within {time_limit} seconds!"
                            correct = ["dodge"]
                            dmg = random.randint(15 + enemy.damage // 10, 25 + enemy.damage // 10)
                        elif attack == "special":
                            if enemy.name == "Dragon":
                                prompt = f"Dragon breathes fire! Type 'roll' within {time_limit} seconds!"
                                correct = ["roll"]
                                dmg = 35 + enemy.damage // 10
                            elif enemy.name == "Hydra":
                                prompt = f"Hydra spits poison! Type 'block' within {time_limit} seconds!"
                                correct = ["block"]
                                dmg = 30 + enemy.damage // 10
                            elif enemy.name == "Corruption Monster":
                                prompt = f"Corruption Monster fires a corrupt beam! Type 'reflect' within {time_limit} seconds!"
                                correct = ["reflect"]
                                dmg = 40 + enemy.damage // 10
                            elif enemy.name == "Crystal Mech":
                                prompt = f"Crystal Mech charges a laser! Type 'duck' within {time_limit} seconds!"
                                correct = ["duck"]
                                dmg = 45 + enemy.damage // 10
                            elif enemy.name == "Kraken":
                                prompt = f"Kraken unleashes a crushing tentacle slam! Type 'swerve' within {time_limit} seconds!"
                                correct = ["swerve"]
                                dmg = 50 + enemy.damage // 10
                            elif enemy.name == "Sacred Guardian":
                                prompt = f"Sacred Guardian swings its holy blade! Type 'parry' within {time_limit} seconds!"
                                correct = ["parry"]
                                dmg = 35 + enemy.damage // 10
                            elif enemy.name == "Remnant":
                                prompt = f"Remnant attempts to rip your soul! Type 'thrust' within {time_limit} seconds!"
                                correct = ["thrust"]
                                dmg = 50 + enemy.damage // 10
                            elif enemy.name == "Skeletal Razukan":
                                prompt = f"Skeletal Razukan blasts you with an Obliteration spell! Type 'deflect' within {time_limit} seconds!"
                                correct = ["deflect"]
                                dmg = 50 + enemy.damage // 10
                            elif enemy.name == "Thanatos":
                                prompt = f"Thanatos slams you with his scythe! Type 'dive' within {time_limit} seconds!"
                                correct = ["dive"]
                                dmg = 50 + enemy.damage // 10
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
                                print("You died! Game over.")
                                sys.exit()
            if player.health > 0:
                player.current_room.enemies.remove(enemy)
                player.mana = 100
                player.gold += enemy.gold_drop
                if enemy.name in bosses:
                    player.defeated_bosses.append(enemy.name)
                info = enemy.info if enemy.info else ""
                if enemy.name == "Hydra":
                    if "boat" not in [item.name for item in player.inventory]:
                        player.inventory.append(Item("boat", "A boat to reach Lokendar.", usable=True))
                        info += " You received a boat!"
                    if "lokendar_dock" not in player.unlocked_destinations:
                        player.unlocked_destinations.append("lokendar_dock")
                        info += " Lokendar is now unlocked for sailing!"
                if enemy.name == "Dragon" and player.current_room.name == "Dragon Chamber":
                    if "out" not in player.current_room.exits:
                        player.current_room.exits["out"] = player.current_room.locked_exits["out"]
                        del player.current_room.locked_exits["out"]
                        player.unlocked_destinations.append("dock")
                        info += " The path to the outside is now open! Isolated Island unlocked for sailing."
                if enemy.name == "Corruption Monster":
                    player.corruption_monster_defeated = True
                    rooms["lokendar_se"].exits["gate"] = rooms["lokendar_se"].locked_exits["gate"]
                    del rooms["lokendar_se"].locked_exits["gate"]
                    player.unlocked_destinations.append("spring_of_courage")
                    info += " The gate to the Black Keep is now accessible! Spring of Courage unlocked for sailing."
                if enemy.name == "Crystal Mech":
                    player.unlocked_destinations.append("whirlpool")
                    info += " Whirlpool unlocked for sailing."
                if enemy.name == "Remnant" and player.current_room.name == "Sky Castle Arena":
                    if "north" not in player.current_room.exits:
                        player.current_room.exits["north"] = player.current_room.locked_exits["north"]
                        del player.current_room.locked_exits["north"]
                        player.unlocked_destinations.append("sky_castle_arena_two")
                if enemy.name == "Skeletal Razukan":
                    player.current_room = Room("The Void", "Absolute nothingness. Thanatos has destroyed everything but you. Stop him before it's too late!", enemies=[Enemy("Thanatos", "Thanatos, Bringer of Death", "A colossal titan summoned by Razukan as his last gambit to destroy the world.", 400, 55, "Thanatos collapses and vanishes in a blur of black light. The world is saved! Made by Oscar with the help of xAI. Special thanks go to: Our playtesters on Recess, and anyone who played this game. Thank you, and get ready to play TALES OF RAZUKAN II, coming in 2026!")], exits={})
                return f"You defeated {enemy.name}! {info} Gained {enemy.gold_drop} gold. Refilled mana to full."
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
                if player.current_room.name not in ["Dock", "Lokendar Dock", "Spring of Courage", "Whirlpool"]:
                    return "You can only use the boat at a dock or in Spring of Courage or Whirlpool."
                destinations = {
                    "dock": "Isolated Island",
                    "lokendar_dock": "Lokendar",
                    "spring_of_courage": "Spring of Courage",
                    "whirlpool": "Whirlpool"
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
            elif item_name == "grenade":
                if in_combat:
                    player.inventory.remove(item)
                    return "Grenade thrown! It deals 50 damage to the enemy."
                return "Grenades can only be used in combat."
            elif item_name == "airship":
                if player.current_room.name not in ["Razukan's Lair", "Sky Castle Entry", "The Junkyard"]:
                    return "You can only use the airship in Razukan's Lair, Sky Castle Entry, or The Junkyard."
                destinations = {
                    "razukan_lair": "Razukan's Lair",
                    "sky_castle_entry": "Sky Castle Entry"
                }
                unlocked = [k for k in destinations.keys() if k in player.unlocked_destinations or k == "sky_castle_entry" or "north" in rooms["black_keep_armory"].exits or "Crystal Mech" in player.defeated_bosses]
                print("Available destinations:")
                for key in destinations:
                    name = destinations[key] if key in unlocked else "???"
                    print(f"- {name}")
                print("Where would you like to fly?")
                choice = input("> ").lower()
                for key, name in destinations.items():
                    if choice == name.lower() or choice == key:
                        if key in unlocked:
                            player.current_room = rooms[key]
                            if key not in player.unlocked_destinations:
                                player.unlocked_destinations.append(key)
                            return f"You fly to {player.current_room.name}. " + get_room_info(player.current_room)
                        else:
                            return "That destination is locked."
                return "Invalid destination."
            elif item_name in ["keep key 1", "keep key 2", "keep key 3"]:
                if player.current_room.name == "Black Keep Armory" and "north" in player.current_room.locked_exits:
                    required_keys = ["keep key 1", "keep key 2", "keep key 3"]
                    if all(key in [item.name for item in player.inventory] for key in required_keys):
                        player.current_room.exits["north"] = player.current_room.locked_exits["north"]
                        del player.current_room.locked_exits["north"]
                        for key in required_keys:
                            for inv_item in player.inventory[:]:
                                if inv_item.name == key:
                                    player.inventory.remove(inv_item)
                        if "razukan_lair" not in player.unlocked_destinations:
                            player.unlocked_destinations.append("razukan_lair")
                        return "You used the three keys to unlock the lair door. They vanish."
                    return "You need all three keys to unlock the lair."
                return "You can't use the key here."

                # Add this block inside the use_item() function, under the existing elif chains for specific items
            elif item_name == "treasure":
                if player.current_room.name == "Sky Castle Courtyard":
                    if "north" in player.current_room.locked_exits:
                        player.current_room.exits["north"] = player.current_room.locked_exits["north"]
                        del player.current_room.locked_exits["north"]
                        player.inventory.remove(item)  # Consume the treasure as an offering
                        if "sky_castle_arena" not in player.unlocked_destinations:
                            player.unlocked_destinations.append("sky_castle_arena")
                            return "You offer the gleaming gold coins to an ancient altar in the courtyard. The ground trembles as a hidden path to the north opens, revealing the Sky Castle Arena!"
                        return "The path is already unlocked."
                    return "The treasure doesn't seem useful here."
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
                if item.name == "airship":
                    print("You bought the airship! THERE IS A HIDDEN CODE HERE IF YOU HAVEN'T FINISHED THE KEEP YET!! TRY TO FIND IT - Oscar")
                    command = input("> ").lower()
                    if command == "skipkeep":
                        if "razukan_lair" not in player.unlocked_destinations:
                            player.unlocked_destinations.append("razukan_lair")
                            return "You bought airship for 80 gold. Razukan's Lair unlocked for airship travel! YOU FOUND THE EASTER EGG - Oscar"
                        return "You bought airship for 80 gold. Razukan's Lair was already unlocked. YOU FOUND THE EASTER EGG - Oscar"
                    return "You bought airship for 80 gold."
                return f"You bought {item.name} for {item.price} gold."
            else:
                return "Not enough gold."
    return "No such item for sale."

def set_difficulty(player, rooms, difficulty):
    valid_difficulties = ["easy", "normal", "hard", "expert"]
    if difficulty.lower() not in valid_difficulties:
        return f"Invalid difficulty. Choose from: {', '.join(valid_difficulties)}"
    player.difficulty = difficulty.lower()
    # Update all enemies in all rooms based on new difficulty
    for room in rooms.values():
        for enemy in room.enemies:
            enemy.health = enemy._apply_difficulty(enemy.base_health, player.difficulty, "health")
            enemy.damage = enemy._apply_difficulty(enemy.base_damage, player.difficulty, "damage")
    return f"Difficulty set to {player.difficulty.capitalize()}."

def save_game(player, rooms):
    data = {
        "player": player.to_dict(),
        "rooms": {key: room.to_dict() for key, room in rooms.items()}
    }
    with open("save.json", "w") as f:
        json.dump(data, f, indent=2)
    return "Game saved."

def load_game(player, rooms):
    if not os.path.exists("save.json"):
        return "No save file found."
    try:
        with open("save.json", "r") as f:
            data = json.load(f)
        new_rooms, _ = setup_world()
        rooms.clear()
        for room_key, room_data in data["rooms"].items():
            room = new_rooms.get(room_key)
            if room:
                room.items = [Item(**item_data) for item_data in room_data.get("items", [])]
                room.enemies = [
                    Enemy(
                        name=enemy_data["name"],
                        title=enemy_data["title"],
                        description=enemy_data["description"],
                        health=enemy_data.get("base_health", enemy_data["health"]),
                        damage=enemy_data.get("base_damage", enemy_data["damage"]),
                        info=enemy_data.get("info"),
                        gold_drop=enemy_data.get("gold_drop", 10),
                        difficulty=data["player"].get("difficulty", "normal")
                    ) for enemy_data in room_data.get("enemies", [])
                    if "defeated_bosses" not in data["player"] or enemy_data["name"] not in data["player"].get("defeated_bosses", [])
                ]
                room.exits = room_data.get("exits", {})
                room.locked_exits = room_data.get("locked_exits", {})
                room.npcs = [NPC(**npc_data) for npc_data in room_data.get("npcs", [])]
                if "puzzle_solved" in room_data:
                    room.puzzle_solved = room_data["puzzle_solved"]
                rooms[room_key] = room
        player.health = data["player"].get("health", 100)
        player.mana = data["player"].get("mana", 100)
        player.gold = data["player"].get("gold", 100)
        player.spells = data["player"].get("spells", [])
        player.inventory = [Item(**item_data) for item_data in data["player"].get("inventory", [])]
        player.unlocked_destinations = data["player"].get("unlocked_destinations", ["lokendar_se"])
        player.corruption_monster_defeated = data["player"].get("corruption_monster_defeated", False)
        player.defeated_bosses = data["player"].get("defeated_bosses", [])
        player.difficulty = data["player"].get("difficulty", "normal")
        current_room_name = data["player"].get("current_room_name", "castle_start")
        for room in rooms.values():
            if room.name == current_room_name:
                player.current_room = room
                break
        else:
            player.current_room = rooms["castle_start"]
            print("Warning: Saved room not found. Starting in Castle Starting Room.")
        if player.corruption_monster_defeated:
            rooms["lokendar_se"].exits["gate"] = rooms["lokendar_se"].locked_exits.get("gate", "black_keep_gate")
            if "gate" in rooms["lokendar_se"].locked_exits:
                del rooms["lokendar_se"].locked_exits["gate"]
            rooms["central_chamber"].enemies = [
                enemy for enemy in rooms["central_chamber"].enemies if enemy.name != "Corruption Monster"
            ]

        # Rebuild original shop inventories from the fresh world template
        fresh_rooms, _ = setup_world()  # create a clean copy of the world
        for room_key, room in rooms.items():
            if room.is_shop and hasattr(fresh_rooms[room_key], "original_items"):
                # Deep-copy the original items so buying removes them again
                room.items = [Item(
                    name=i.name,
                    description=i.description,
                    usable=i.usable,
                    price=i.price
                ) for i in fresh_rooms[room_key].original_items]


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
        player.unlocked_destinations = ["lokendar_se"]
        player.corruption_monster_defeated = False
        player.defeated_bosses = []
        player.difficulty = "normal"
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
    print("Tales of Razukan")
    print("Choose difficulty: easy, normal, hard, expert")
    while True:
        difficulty = input("> ").lower()
        response = set_difficulty(player, rooms, difficulty)
        print(response)
        if "Difficulty set" in response:
            break
    print(get_room_info(player.current_room))
    while True:
        command = input("> ")
        if command.lower() == "quit":
            break
        response = parse_command(command, player, rooms)
        print(response)

if __name__ == "__main__":
    main()