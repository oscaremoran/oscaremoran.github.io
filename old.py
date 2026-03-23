import time
import random
import sys
import select

def display_welcome():
    print("Welcome to Choose Your Own Adventure ('CYOA')! Please pick your adventure: The Dragon's Cave (type 1). After beginning, type Help.")
    choice = input().strip()
    if choice == '1':
        print("Welcome to the Dragon's Cave! You are in the entrance. There is a bush on the left and a rustling bush on the right. There are also two chests behind the rustling bush and a sturdy door ahead. You can interact with BUSH, RUSTLINGBUSH, CHEST1, CHEST2, DOOR.")
    else:
        print("Invalid choice. Exiting.")
        exit()

def display_room_description(player):
    if player['room'] == 1:
        print("You are in the entrance. There is a bush on the left and a rustling bush on the right. There are also two chests behind the rustling bush and a sturdy door ahead. You can interact with BUSH, RUSTLINGBUSH, CHEST1, CHEST2, DOOR.")
    elif player['room'] == 2:
        objects = ["BUSH1", "BUSH2", "BUSH3", "LOOTCHEST", "DOOR", "TRADER", "CHEST3"]
        if rooms[2].get("WALLPORTAL", {}).get("unlocked", False):
            objects.append("WALLPORTAL")
        print(f"You are in Room 2, a dimly lit chamber. There are three suspicious bushes in the corners, a loot chest, a door leading back, a trader, and a gem chest. You can interact with {', '.join(objects)}.")
    elif player['room'] == 3:
        print("You are in Room 3, a fiery arena. A Flame Boar awaits!")
    elif player['room'] == 4:
        objects = ["TRAP1", "TRAP2", "SHRINE"]
        print(f"You are in Room 4, a treacherous chamber with traps and a glowing shrine. You can interact with {', '.join(objects)}.")
        if player.get('curse_active', False):
            player['curse_active'] = False
            player['curse_start_time'] = 0
            print("The dark spirit vanishes!")
        if not rooms[4].get("event_triggered", False):
            event = random.choice(["Treasure Cache", "Mystic Voice", "Hidden Gem"])
            rooms[4]["event_triggered"] = True
            if event == "Treasure Cache":
                player['gold'] += 2
                print("A Treasure Cache appears! You gain 2 Gold.")
            elif event == "Mystic Voice":
                player['max_hp'] = player.get('max_hp', 20) + 5
                player['hp'] = min(player['hp'] + 5, player['max_hp'])
                print("A Mystic Voice strengthens you! Max HP +5.")
            elif event == "Hidden Gem":
                player['gems'] += 1
                print("You find a Hidden Gem! +1 Gem.")

def check_curse_timer(player):
    if player.get('curse_active', False) and player.get('curse_start_time', 0) > 0:
        elapsed = time.time() - player['curse_start_time']
        if elapsed > 300:  # 5 minutes
            print("The dark spirit consumes you! You collapse.")
            game_over()

def save_game(player, rooms):
    chest1_opened = int(rooms[1]['CHEST1']['opened'])
    chest2_opened = int(rooms[1]['CHEST2']['opened'])
    door1_broken = int(rooms[1]['DOOR']['broken'])
    bush1_attacked = int(rooms[2]['BUSH1']['attacked'])
    bush2_attacked = int(rooms[2]['BUSH2']['attacked'])
    bush3_attacked = int(rooms[2]['BUSH3']['attacked'])
    has_armor = int(player['has_armor'])
    lootchest_opened = int(rooms[2]['LOOTCHEST']['opened'])
    door2_broken = int(rooms[2]['DOOR']['broken'])
    trader_dead = int(rooms[2]['TRADER']['dead'])
    wallportal_unlocked = int(rooms[2].get("WALLPORTAL", {}).get("unlocked", False))
    has_frost_horn = int(player['has_frost_horn'])
    chest3_opened = int(rooms[2]['CHEST3']['opened'])
    trap1_disarmed = int(rooms[4].get('TRAP1', {}).get('disarmed', False))
    trap2_disarmed = int(rooms[4].get('TRAP2', {}).get('disarmed', False))
    has_orb = int(player.get('has_orb', False))
    curse_start_time = int(player.get('curse_start_time', 0))
    room4_event_triggered = int(rooms[4].get('event_triggered', False))
    curse_active = int(player.get('curse_active', False))
    save_code = f"{player['room']}-{player['hp']}-{player['gold']}-{player['gems']}-{chest1_opened}-{chest2_opened}-{door1_broken}-{bush1_attacked}-{bush2_attacked}-{bush3_attacked}-{has_armor}-{lootchest_opened}-{door2_broken}-{trader_dead}-{wallportal_unlocked}-{has_frost_horn}-{chest3_opened}-{trap1_disarmed}-{trap2_disarmed}-{has_orb}-{curse_start_time}-{room4_event_triggered}-{curse_active}"
    print(f"Save code: {save_code}")
    slot = input("Enter save slot (1-10): ").strip()
    try:
        slot_num = int(slot)
        if not 1 <= slot_num <= 10:
            raise ValueError
    except ValueError:
        print("Invalid slot. Must be 1-10.")
        return
    try:
        try:
            with open("saves.txt", "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = [""] * 10
        lines = [line.strip() for line in lines] + [""] * (10 - len(lines))
        lines[slot_num - 1] = f"{slot_num}. {save_code}"
        with open("saves.txt", "w") as f:
            f.write("\n".join(lines))
        print(f"Saved to slot {slot_num}.")
    except Exception as e:
        print(f"Error saving: {e}")

def load_game(player):
    if player['room'] != 1:
        print("Can only load in Room 1.")
        return None
    slot = input("Enter save slot (1-10): ").strip()
    try:
        slot_num = int(slot)
        if not 1 <= slot_num <= 10:
            raise ValueError
    except ValueError:
        print("Invalid slot. Must be 1-10.")
        return None
    try:
        with open("saves.txt", "r") as f:
            lines = f.readlines()
        if slot_num > len(lines) or not lines[slot_num - 1].strip():
            print("No save in this slot.")
            return None
        save_code = lines[slot_num - 1].strip().split(". ", 1)[1]
        parts = save_code.split('-')
        if len(parts) != 23:
            raise ValueError
        room, hp, gold, gems, chest1_opened, chest2_opened, door1_broken, bush1_attacked, bush2_attacked, bush3_attacked, has_armor, lootchest_opened, door2_broken, trader_dead, wallportal_unlocked, has_frost_horn, chest3_opened, trap1_disarmed, trap2_disarmed, has_orb, curse_start_time, room4_event_triggered, curse_active = map(int, parts)
        return (room, hp, gold, gems, bool(chest1_opened), bool(chest2_opened), bool(door1_broken), bool(bush1_attacked), bool(bush2_attacked), bool(bush3_attacked), bool(has_armor), bool(lootchest_opened), bool(door2_broken), bool(trader_dead), bool(wallportal_unlocked), bool(has_frost_horn), bool(chest3_opened), bool(trap1_disarmed), bool(trap2_disarmed), bool(has_orb), curse_start_time, bool(room4_event_triggered), bool(curse_active))
    except FileNotFoundError:
        print("Save file not found.")
        return None
    except Exception as e:
        print(f"Invalid save code: {e}")
        return None

def combat_with_goblin(player):
    goblin_hp = 7
    player_damage = 5
    goblin_damage = 3
    drain_used = False
    print("Combat starts! Choose (A)ttack, (F)lee, (D)rain (once per battle), or (H)orn (if you have it.")
    combat_start = time.time()
    while True:
        choice = input("Enter A, F, D, or H: ").strip().upper()
        if choice == 'A':
            goblin_hp -= player_damage
            print(f"You attack the Goblin for {player_damage} damage. Goblin HP: {goblin_hp}")
            if goblin_hp <= 0:
                print("You defeated the Goblin!")
                if player.get('curse_active', False):
                    player['curse_start_time'] += time.time() - combat_start
                return True
            damage_taken = max(0, goblin_damage - (2 if player['has_armor'] else 0))
            player['hp'] -= damage_taken
            print(f"The Goblin attacks you for {damage_taken} damage. Your HP: {player['hp']}")
            if player['hp'] <= 0:
                print("You have been defeated.")
                if player.get('curse_active', False):
                    player['curse_start_time'] += time.time() - combat_start
                return False
        elif choice == 'F':
            print("You fled.")
            if player.get('curse_active', False):
                player['curse_start_time'] += time.time() - combat_start
            return False
        elif choice == 'D':
            if not drain_used:
                goblin_hp -= 10
                player['hp'] -= 10
                drain_used = True
                print(f"You use Drain, dealing 10 damage to both! Goblin HP: {goblin_hp}, Your HP: {player['hp']}")
                if goblin_hp <= 0:
                    print("You defeated the Goblin!")
                    if player.get('curse_active', False):
                        player['curse_start_time'] += time.time() - combat_start
                    return True
                if player['hp'] <= 0:
                    print("You have been defeated.")
                    if player.get('curse_active', False):
                        player['curse_start_time'] += time.time() - combat_start
                    return False
            else:
                print("Drain can only be used once per battle.")
        elif choice == 'H':
            if player['has_frost_horn']:
                print("You use the Frost Horn, freezing the Goblin instantly!")
                if player.get('curse_active', False):
                    player['curse_start_time'] += time.time() - combat_start
                return True
            else:
                print("You don't have the Frost Horn.")
        else:
            print("Invalid choice. Please enter A, F, D, or H.")

def combat_with_flame_boar(player):
    boar_hp = 30
    player_damage = 5
    inferno_damage = 11
    drain_used = False
    weather = random.choice(["Firestorm", "Mist"])
    inferno_prob = ["nothing", "nothing", "inferno"] if weather == "Mist" else ["nothing", "nothing", "inferno"]
    print(f"As you enter this strange area, you hear the sound of a crackling flame. A {weather} rages! Suddenly, a huge creature leaps towards you! It is a huge Boar with a crackling flame horn. BOSS FIGHT: Flame Boar.")
    if weather == "Mist":
        boar_hp -= 10
        print(f"The Mist weakens the Flame Boar, dealing 10 damage! Boar HP: {boar_hp}")
    print("Combat starts! Choose (A)ttack, (F)lee, (D)rain (once per battle), or (H)orn (if you have Frost Horn).")
    combat_start = time.time()
    while True:
        choice = input("Enter A, F, D, or H: ").strip().upper()
        if choice == 'A':
            boar_hp -= player_damage
            print(f"You attack the Flame Boar for {player_damage} damage. Boar HP: {boar_hp}")
            if boar_hp <= 0:
                print("You defeated the Flame Boar!")
                if player.get('curse_active', False):
                    player['curse_start_time'] += time.time() - combat_start
                return True
        elif choice == 'F':
            print("You fled from the Flame Boar.")
            if player.get('curse_active', False):
                player['curse_start_time'] += time.time() - combat_start
            return False
        elif choice == 'D':
            if not drain_used:
                boar_hp -= 10
                player['hp'] -= 10
                drain_used = True
                print(f"You use Drain, dealing 10 damage to both! Boar HP: {boar_hp}, Your HP: {player['hp']}")
                if boar_hp <= 0:
                    print("You defeated the Flame Boar!")
                    if player.get('curse_active', False):
                        player['curse_start_time'] += time.time() - combat_start
                    return True
                if player['hp'] <= 0:
                    print("You have been defeated.")
                    if player.get('curse_active', False):
                        player['curse_start_time'] += time.time() - combat_start
                    return False
            else:
                print("Drain can only be used once per battle.")
        elif choice == 'H':
            if player['has_frost_horn']:
                boar_hp -= 10
                print(f"You use the Frost Horn, dealing 10 damage to the Flame Boar! Boar HP: {boar_hp}")
                if boar_hp <= 0:
                    print("You defeated the Flame Boar!")
                    if player.get('curse_active', False):
                        player['curse_start_time'] += time.time() - combat_start
                    return True
            else:
                print("You don't have the Frost Horn.")
        else:
            print("Invalid choice. Please enter A, F, D, or H.")
            continue
        if boar_hp > 0:
            action = random.choice(inferno_prob)
            if action == "inferno":
                damage_taken = max(0, inferno_damage - (2 if player['has_armor'] else 0))
                player['hp'] -= damage_taken
                print(f"The Flame Boar uses Inferno, dealing {damage_taken} damage. Your HP: {player['hp']}")
                if player['hp'] <= 0:
                    print("You have been defeated.")
                    if player.get('curse_active', False):
                        player['curse_start_time'] += time.time() - combat_start
                    return False
            else:
                print("The Flame Boar glares but does nothing.")

def number_pressing_phase(player):
    print("The Flame Boar's body crackles, demanding a test of speed! Press the correct numbers in time!")
    phase_start = time.time()
    for _ in range(4):
        target = str(random.randint(0, 9))
        print(f"Press {target}!")
        sys.stdin.flush()
        rlist, _, _ = select.select([sys.stdin], [], [], 2.5)
        if rlist:
            user_input = sys.stdin.readline().strip()
            if user_input != target:
                player['hp'] -= 5
                print(f"Wrong or too slow! You take 5 damage. Your HP: {player['hp']}")
                if player['hp'] <= 0:
                    print("You have been defeated.")
                    if player.get('curse_active', False):
                        player['curse_start_time'] += time.time() - phase_start
                    return False
                print("Try again!")
                if player.get('curse_active', False):
                    player['curse_start_time'] += time.time() - phase_start
                return number_pressing_phase(player)
        else:
            player['hp'] -= 5
            print(f"Time's up! You take 5 damage. Your HP: {player['hp']}")
            if player['hp'] <= 0:
                print("You have been defeated.")
                if player.get('curse_active', False):
                    player['curse_start_time'] += time.time() - phase_start
                return False
            print("Try again!")
            if player.get('curse_active', False):
                player['curse_start_time'] += time.time() - phase_start
            return number_pressing_phase(player)
    print("Success! You passed the test!")
    if player.get('curse_active', False):
        player['curse_start_time'] += time.time() - phase_start
    return True

def disable_trap(player, trap_name):
    if trap_name == 'TRAP1':
        question = "What is 2 + 7?"
        answer = "9"
    elif trap_name == 'TRAP2':
        question = "What is 5 * 2?"
        answer = "10"
    print(question)
    user_answer = input().strip().lower()
    if user_answer == answer:
        print("Correct! Trap disarmed.")
        rooms[4][trap_name]['disarmed'] = True
    else:
        player['hp'] -= 3
        print(f"Wrong! You take 3 damage. Your HP: {player['hp']}")
        if player['hp'] <= 0:
            print("You have been defeated.")
            game_over()

def game_over():
    print("GAME OVER.")
    time.sleep(5)
    exit()

def attack_object(object_name, player, rooms):
    room = rooms[player['room']]
    if object_name not in room:
        print("No such object.")
        return
    obj = room[object_name]
    if object_name == 'BUSH':
        if not obj['attacked']:
            print("You chopped the bush. There's nothing inside.")
            obj['attacked'] = True
        else:
            print("The bush is already chopped.")
    elif object_name == 'RUSTLINGBUSH':
        if not obj['attacked']:
            print("A Goblin jumps out!")
            if combat_with_goblin(player):
                print("You defeated the Goblin and found 1 Gold.")
                player['gold'] += 1
                obj['attacked'] = True
            else:
                display_room_description(player)
        else:
            print("The bush is already chopped.")
    elif object_name in ['BUSH1', 'BUSH2', 'BUSH3']:
        if not obj['attacked']:
            print("A Goblin jumps out!")
            if combat_with_goblin(player):
                print("You found 1 Gold!")
                player['gold'] += 1
                if object_name == 'BUSH2':
                    print("You found a Gem hidden in the bush!")
                    player['gems'] += 1
                obj['attacked'] = True
            else:
                display_room_description(player)
        else:
            print("The bush is already chopped.")
    elif object_name == 'DOOR':
        if not obj['broken']:
            print("You smash the door and enter another room!")
            obj['broken'] = True
            player['room'] = 2 if player['room'] == 1 else 1
            display_room_description(player)
        else:
            print("The door is already broken.")
    elif object_name == 'TRADER':
        if not obj['dead']:
            print("The trader falls, and a dark spirit rises! You feel your life draining.")
            obj['dead'] = True
            player['curse_active'] = True
            player['curse_start_time'] = time.time()
        else:
            print("The trader is already dead.")
    elif object_name in ['CHEST1', 'CHEST2', 'LOOTCHEST', 'CHEST3']:
        print("You dented the chest!")

def interact_with_object(object_name, player, rooms):
    room = rooms[player['room']]
    if object_name not in room:
        print("No such object.")
        return
    obj = room[object_name]
    if object_name in ['BUSH', 'RUSTLINGBUSH', 'BUSH1', 'BUSH2', 'BUSH3']:
        print("You walk into the bush. There's nothing here.")
    elif object_name == 'DOOR':
        if obj['broken']:
            print("The door is broken. You pass through.")
            player['room'] = 2 if player['room'] == 1 else 1
            display_room_description(player)
        else:
            print("The door is sturdy and won't budge.")
    elif object_name == 'WALLPORTAL':
        if obj['unlocked']:
            player['room'] = 3
            if combat_with_flame_boar(player):
                if number_pressing_phase(player):
                    player['room'] = 4
                    display_room_description(player)
                else:
                    game_over()
            else:
                player['room'] = 2
                display_room_description(player)
        else:
            print("The wall is sealed.")
    elif object_name in ['CHEST1', 'CHEST2', 'CHEST3', 'LOOTCHEST']:
        if player.get('has_orb', False):
            print("The Mystic Orb prevents you from opening chests until delivered!")
            return
        if object_name in ['CHEST1', 'CHEST2', 'CHEST3']:
            if not obj['opened']:
                content = obj['content']
                if content == 'Gold':
                    player['gold'] += 1
                    print("You found 1 Gold in the chest.")
                elif content == 'Gem':
                    player['gems'] += 1
                    print("You found a Gem in the chest.")
                obj['opened'] = True
            else:
                print("The chest is already empty.")
        elif object_name == 'LOOTCHEST':
            if not obj['opened']:
                print("You found Armor in the loot chest! Damage taken is reduced by 2.")
                player['has_armor'] = True
                obj['opened'] = True
            else:
                print("The loot chest is already empty.")
    elif object_name == 'TRADER':
        if obj['dead']:
            print("The trader is dead and cannot trade.")
        else:
            all_goblins_dead = (rooms[2]['BUSH1']['attacked'] and
                               rooms[2]['BUSH2']['attacked'] and
                               rooms[2]['BUSH3']['attacked'])
            if all_goblins_dead and not player.get('has_orb', False):
                print("You’ve cleared the goblins! The trader offers a quest: Deliver a Mystic Orb to Room 4’s shrine for 5 Gems. Accept? (Y/N)")
                choice = input().strip().upper()
                if choice == 'Y':
                    player['has_orb'] = True
                    print("You take the Mystic Orb. Chests are locked until delivered.")
                else:
                    print("You decline the quest.")
            else:
                print("You can trade Gems and Gold for new abilities! Want to get a key to the next room? It'll cost ya 3 Gold. Type 1 to buy it. Want to get the Frost Horn for freezin' those Goblins? I charge 3 Gems. Type 2 to get that.")
                choice = input("Enter 1 or 2: ").strip()
                if choice == '1':
                    if player['gold'] >= 3:
                        player['gold'] -= 3
                        print("The wall to a new area vanishes! You may now interact with WALLPORTAL.")
                        rooms[2]['WALLPORTAL'] = {'unlocked': True}
                    else:
                        print("Not enough Gold!")
                elif choice == '2':
                    if player['gems'] >= 3:
                        player['gems'] -= 3
                        print("You received the Frost Horn! Use H in combat to freeze enemies.")
                        player['has_frost_horn'] = True
                    else:
                        print("Not enough Gems!")
                else:
                    print("Invalid choice.")
    elif object_name in ['TRAP1', 'TRAP2']:
        if obj.get('disarmed', False):
            print("This trap is already disarmed.")
        else:
            disable_trap(player, object_name)
    elif object_name == 'SHRINE':
        if player.get('has_orb', False):
            player['has_orb'] = False
            player['gems'] += 5
            print("You deliver the Mystic Orb to the shrine! +5 Gems.")
        else:
            print("The shrine glows faintly, awaiting something.")

def main():
    global rooms
    display_welcome()
    player = {'room': 1, 'hp': 20, 'gold': 0, 'gems': 0, 'has_armor': False, 'has_frost_horn': False, 'has_orb': False, 'curse_start_time': 0, 'max_hp': 20, 'curse_active': False}
    rooms = {
        1: {
            'BUSH': {'attacked': False, 'content': None},
            'RUSTLINGBUSH': {'attacked': False, 'content': 'Goblin'},
            'CHEST1': {'opened': False, 'content': 'Gold'},
            'CHEST2': {'opened': False, 'content': 'Gem'},
            'DOOR': {'broken': False}
        },
        2: {
            'BUSH1': {'attacked': False, 'content': 'Goblin'},
            'BUSH2': {'attacked': False, 'content': 'Goblin'},
            'BUSH3': {'attacked': False, 'content': 'Goblin'},
            'LOOTCHEST': {'opened': False, 'content': 'Armor'},
            'DOOR': {'broken': False},
            'TRADER': {'dead': False},
            'CHEST3': {'opened': False, 'content': 'Gem'}
        },
        3: {},
        4: {
            'TRAP1': {'disarmed': False},
            'TRAP2': {'disarmed': False},
            'SHRINE': {}
        }
    }
    print(f"HP: {player['hp']}, Gold: {player['gold']}, Gems: {player['gems']}, Lootchest Item: {'Yes' if player['has_armor'] else 'No'}, Trader's Artifact: {'Yes' if player['has_frost_horn'] else 'No'}")
    while True:
        check_curse_timer(player)
        command_input = input("Enter command: ").strip().upper()
        parts = command_input.split()
        if len(parts) == 0:
            continue
        command = parts[0]
        object_name = parts[1] if len(parts) > 1 else None
        if command == 'Q':
            print("Quitting the game.")
            break
        elif command == 'A':
            if object_name:
                attack_object(object_name, player, rooms)
            else:
                print("Attack what?")
        elif command == 'G':
            if object_name:
                interact_with_object(object_name, player, rooms)
            else:
                print("Interact with what?")
        elif command == 'S':
            save_game(player, rooms)
        elif command == 'L':
            loaded_data = load_game(player)
            if loaded_data:
                (room, hp, gold, gems, chest1_opened, chest2_opened, door1_broken, bush1_attacked, bush2_attacked, bush3_attacked, has_armor, lootchest_opened, door2_broken, trader_dead, wallportal_unlocked, has_frost_horn, chest3_opened, trap1_disarmed, trap2_disarmed, has_orb, curse_start_time, room4_event_triggered, curse_active) = loaded_data
                player['room'] = room
                player['hp'] = hp
                player['gold'] = gold
                player['gems'] = gems
                player['has_armor'] = has_armor
                player['has_frost_horn'] = has_frost_horn
                player['has_orb'] = has_orb
                player['curse_start_time'] = curse_start_time
                player['curse_active'] = curse_active
                player['max_hp'] = 20 + (5 if room4_event_triggered and rooms[4].get('event_triggered', False) else 0)
                rooms[1]['CHEST1']['opened'] = chest1_opened
                rooms[1]['CHEST2']['opened'] = chest2_opened
                rooms[1]['DOOR']['broken'] = door1_broken
                rooms[2]['BUSH1']['attacked'] = bush1_attacked
                rooms[2]['BUSH2']['attacked'] = bush2_attacked
                rooms[2]['BUSH3']['attacked'] = bush3_attacked
                rooms[2]['LOOTCHEST']['opened'] = lootchest_opened
                rooms[2]['DOOR']['broken'] = door2_broken
                rooms[2]['TRADER']['dead'] = trader_dead
                rooms[2]['CHEST3']['opened'] = chest3_opened
                rooms[4]['TRAP1']['disarmed'] = trap1_disarmed
                rooms[4]['TRAP2']['disarmed'] = trap2_disarmed
                rooms[4]['event_triggered'] = room4_event_triggered
                if wallportal_unlocked:
                    rooms[2]['WALLPORTAL'] = {'unlocked': True}
                print("Game loaded successfully.")
                display_room_description(player)
        elif command == 'HELP':
            print("Use G then the name of an object to use it. Use A then an object to slice it. Use Q to quit. Use S to get a save code. Use L to load the code. Use F to flee from battle. Use D during battle to drain 10 HP from both sides.")
        else:
            print("Invalid command.")
        print(f"HP: {player['hp']}, Gold: {player['gold']}, Gems: {player['gems']}, Lootchest Item: {'Yes' if player['has_armor'] else 'No'}, Trader's Artifact: {'Yes' if player['has_frost_horn'] else 'No'}")

if __name__ == "__main__":
    main()