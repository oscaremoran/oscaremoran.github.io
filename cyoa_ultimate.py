import time

def display_welcome():
    print("Welcome to Choose Your Own Adventure ('CYOA')! To play the Dragon's Cave, enter 1. After beginning the game, you can type Help if you are confused.")
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
        print("You are in Room 2, a dimly lit chamber. There are three suspicious bushes in the corners. You can interact with BUSH1, BUSH2, BUSH3.")

def save_game(player, rooms):
    chest1_opened = int(rooms[1]['CHEST1']['opened'])
    chest2_opened = int(rooms[1]['CHEST2']['opened'])
    door_broken = int(rooms[1]['DOOR']['broken'])
    bush1_attacked = int(rooms[2]['BUSH1']['attacked'])
    bush2_attacked = int(rooms[2]['BUSH2']['attacked'])
    bush3_attacked = int(rooms[2]['BUSH3']['attacked'])
    save_code = f"{player['room']}-{player['hp']}-{player['gold']}-{player['gems']}-{chest1_opened}-{chest2_opened}-{door_broken}-{bush1_attacked}-{bush2_attacked}-{bush3_attacked}"
    print(f"Save code: {save_code}")

def load_game():
    save_code = input("Enter save code: ").strip()
    try:
        parts = save_code.split('-')
        if len(parts) != 10:
            raise ValueError
        room, hp, gold, gems, chest1_opened, chest2_opened, door_broken, bush1_attacked, bush2_attacked, bush3_attacked = map(int, parts)
        return room, hp, gold, gems, bool(chest1_opened), bool(chest2_opened), bool(door_broken), bool(bush1_attacked), bool(bush2_attacked), bool(bush3_attacked)
    except ValueError:
        print("Invalid save code.")
        return None

def combat_with_goblin(player):
    goblin_hp = 7
    player_damage = 5
    goblin_damage = 3
    print("Combat starts! Choose (A)ttack or (F)lee.")
    while True:
        choice = input("Enter A or F: ").strip().upper()
        if choice == 'A':
            goblin_hp -= player_damage
            print(f"You attack the Goblin for {player_damage} damage. Goblin HP: {goblin_hp}")
            if goblin_hp <= 0:
                print("You defeated the Goblin!")
                return True
            player['hp'] -= goblin_damage
            print(f"The Goblin attacks you for {goblin_damage} damage. Your HP: {player['hp']}")
            if player['hp'] <= 0:
                print("You have been defeated.")
                return False
        elif choice == 'F':
            print("You fled.")
            return False
        else:
            print("Invalid choice. Please enter A or F.")

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
                print("You found 1 Gold.")
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
            print("You smash the door and enter a new room!")
            obj['broken'] = True
            player['room'] = 2
            display_room_description(player)
        else:
            print("The door is already broken.")
    elif object_name in ['CHEST1', 'CHEST2']:
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
            print("The door is broken. You can pass through to Room 2.")
            player['room'] = 2
            display_room_description(player)
        else:
            print("The door is sturdy and won't budge.")
    elif object_name in ['CHEST1', 'CHEST2']:
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

def main():
    display_welcome()
    player = {'room': 1, 'hp': 20, 'gold': 0, 'gems': 0}
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
            'BUSH3': {'attacked': False, 'content': 'Goblin'}
        }
    }
    print(f"HP: {player['hp']}, Gold: {player['gold']}, Gems: {player['gems']}")
    while True:
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
            loaded_data = load_game()
            if loaded_data:
                room, hp, gold, gems, chest1_opened, chest2_opened, door_broken, bush1_attacked, bush2_attacked, bush3_attacked = loaded_data
                player['room'] = room
                player['hp'] = hp
                player['gold'] = gold
                player['gems'] = gems
                rooms[1]['CHEST1']['opened'] = chest1_opened
                rooms[1]['CHEST2']['opened'] = chest2_opened
                rooms[1]['DOOR']['broken'] = door_broken
                rooms[2]['BUSH1']['attacked'] = bush1_attacked
                rooms[2]['BUSH2']['attacked'] = bush2_attacked
                rooms[2]['BUSH3']['attacked'] = bush3_attacked
                print("Game loaded successfully.")
                display_room_description(player)
        elif command == 'HELP':
            print("Type G, which means Get/interact, then an object to use it. Type A, which means Attack, to slice something. Type Q, which means Quit, to quit. Type S, which means Save, to get a code. Type L which means Load to enter that code.")
        else:
            print("Invalid command.")
        print(f"HP: {player['hp']}, Gold: {player['gold']}, Gems: {player['gems']}")

if __name__ == "__main__":
    main()