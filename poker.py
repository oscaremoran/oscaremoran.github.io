import asyncio
import platform
import pygame
import random
from enum import Enum

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
CARD_WIDTH, CARD_HEIGHT = 60, 80
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Card and game enums
class Suit(Enum):
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class AIDifficulty(Enum):
    BEGINNER = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    MASTER = 5

# Card class
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        rank_str = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}.get(self.rank.value, str(self.rank.value))
        return f"{rank_str}{self.suit.value}"

# Player class
class Player:
    def __init__(self, name, chips=1000):
        self.name = name
        self.chips = chips
        self.hand = []
        self.folded = False
        self.current_bet = 0

    def evaluate_hand(self, community_cards):
        cards = sorted(self.hand + community_cards, key=lambda c: c.rank.value, reverse=True)
        if not cards:
            return random.random() * 0.3
        ranks = [c.rank.value for c in cards]
        if len(set(ranks)) < len(ranks):  # Has pair or better
            return min(1.0, 0.5 + (14 - max(set(ranks))) / 14.0)
        else:
            return max(ranks) / 14.0 * 0.4

# AI Player class
class AIPlayer(Player):
    def __init__(self, name, difficulty, chips=1000):
        super().__init__(name, chips)
        self.difficulty = difficulty

    def decide_action(self, game_state, pot, current_bet):
        if current_bet > self.current_bet + self.chips:
            self.folded = True
            return 0, "folded (can't call)"

        hand_strength = self.evaluate_hand(game_state.community_cards)
        pot_odds = current_bet / (pot + current_bet) if pot + current_bet > 0 else 0
        early_round = len(game_state.community_cards) < 3
        
        if self.difficulty == AIDifficulty.BEGINNER:
            choice = random.choices(["fold", "call", "raise"], weights=[0.2, 0.6, 0.2])[0]
            raise_amount = random.randint(10, 100)
        elif self.difficulty == AIDifficulty.EASY:
            choice = "raise" if hand_strength > 0.5 else "call" if hand_strength > 0.2 else "fold"
            raise_amount = random.randint(20, 80)
        elif self.difficulty == AIDifficulty.MEDIUM:
            choice = "raise" if hand_strength > 0.5 and pot_odds < 0.3 else "call" if hand_strength > 0.3 else "fold"
            raise_amount = 50 + random.randint(0, int(hand_strength * 100))
        elif self.difficulty == AIDifficulty.HARD:
            bluff_chance = 0.2 if early_round else 0.1
            choice = random.choices(["raise", "call", "fold"], weights=[0.4, 0.5, 0.1])[0] if random.random() < bluff_chance else \
                    "raise" if hand_strength > 0.6 else "call" if hand_strength > 0.4 else "fold"
            raise_amount = 100 + random.randint(0, int(hand_strength * 150))
        else:  # Master
            bluff_chance = 0.25 if early_round else 0.15
            choice = random.choices(["raise", "call", "fold"], weights=[0.5, 0.4, 0.1])[0] if random.random() < bluff_chance else \
                    "raise" if hand_strength > 0.7 and pot_odds < 0.2 else "call" if hand_strength > 0.4 else "fold"
            raise_amount = 150 + random.randint(0, int(hand_strength * 200))

        if choice == "fold":
            self.folded = True
            return 0, "folded"
        elif choice == "call":
            amount = min(current_bet - self.current_bet, self.chips)
            self.current_bet += amount
            self.chips -= amount
            return amount, f"called {amount}"
        else:  # raise
            amount = min(current_bet - self.current_bet + raise_amount, self.chips)
            self.current_bet += amount
            self.chips -= amount
            return amount, f"raised to {self.current_bet}"

# Game class
class PokerGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Texas Hold'em Poker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.deck = []
        self.players = [Player("You", 1000)]
        self.difficulty = None
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.phase = "select_difficulty"
        self.running = True
        self.log = []
        self.current_turn = 0
        self.current_player_index = 0
        self.showdown_timer = 0
        self.showdown_duration = 5 * FPS
        self.input_active = False
        self.input_text = ""
        self.game_over = False

    def deal_cards(self):
        self.reset_deck()
        for player in self.players:
            player.hand = [self.deck.pop(), self.deck.pop()]
            player.folded = False
            player.current_bet = 0
        self.community_cards = []
        self.pot = 0
        self.current_bet = 10  # Small blind
        self.phase = "preflop"
        self.log = []
        self.current_turn = 0
        self.current_player_index = 0
        self.showdown_timer = 0
        self.input_active = False
        self.input_text = ""

    def reset_deck(self):
        self.deck = [Card(rank, suit) for suit in Suit for rank in Rank]
        random.shuffle(self.deck)

    def draw(self):
        self.screen.fill(GREEN)
        if self.phase == "select_difficulty":
            text = self.font.render("Select AI Difficulty:", True, BLACK)
            self.screen.blit(text, (WIDTH // 2 - 150, 50))
            difficulties = ["Beginner", "Easy", "Medium", "Hard", "Master"]
            for i, diff in enumerate(difficulties):
                pygame.draw.rect(self.screen, BLUE, (WIDTH // 2 - 100, 100 + i * 50, 200, 40))
                text = self.font.render(diff, True, WHITE)
                self.screen.blit(text, (WIDTH // 2 - 50, 105 + i * 50))
        elif self.phase == "select_num_ai":
            text = self.font.render("Select Number of AIs:", True, BLACK)
            self.screen.blit(text, (WIDTH // 2 - 150, 50))
            for i in range(1, 6):
                pygame.draw.rect(self.screen, BLUE, (WIDTH // 2 - 100, 100 + (i-1) * 50, 200, 40))
                text = self.font.render(str(i), True, WHITE)
                self.screen.blit(text, (WIDTH // 2 - 50, 105 + (i-1) * 50))
        else:
            # Community Cards
            text = self.font.render("Community Cards:", True, BLACK)
            self.screen.blit(text, (300, HEIGHT // 2 - 50))
            for i, card in enumerate(self.community_cards):
                text = self.font.render(str(card), True, BLACK)
                self.screen.blit(text, (200 + i * CARD_WIDTH, HEIGHT // 2))

            # Player Hand
            text = self.font.render("Your Hand:", True, BLACK)
            self.screen.blit(text, (50, HEIGHT - 150))
            for j, card in enumerate(self.players[0].hand):
                text = self.font.render(str(card), True, BLACK)
                self.screen.blit(text, (50 + j * CARD_WIDTH, HEIGHT - 100))

            # Pot and Phase
            text = self.font.render(f"Pot: {self.pot}", True, BLACK)
            self.screen.blit(text, (WIDTH - 150, 50))
            text = self.font.render(f"Phase: {self.phase.capitalize()}", True, BLACK)
            self.screen.blit(text, (50, 110))
            text = self.font.render(f"Current Bet: {self.current_bet}", True, BLACK)
            self.screen.blit(text, (50, 140))

            # Players Info (adjusted for multiple players)
            max_players_display = min(5, len(self.players))  # Limit to 5 visible players
            y_offset = 170  # Start below phase info
            for i in range(max_players_display):
                player = self.players[i]
                color = RED if player == self.players[0] else BLACK
                text = self.font.render(f"{player.name}: {player.chips} chips{' (folded)' if player.folded else ''}", True, color)
                self.screen.blit(text, (50, y_offset + i * 40))  # Increased spacing to 40 pixels

            if self.phase == "showdown":
                # Hands logged in showdown logic
                pass

            if self.game_over:
                text = self.font.render("Game Over! Click to restart.", True, RED)
                self.screen.blit(text, (WIDTH // 2 - 150, HEIGHT // 2))

            if self.input_active:
                pygame.draw.rect(self.screen, WHITE, (250, HEIGHT - 100, 100, 30))
                text = self.small_font.render(self.input_text, True, BLACK)
                self.screen.blit(text, (255, HEIGHT - 95))
                text = self.small_font.render("Enter Raise Amount", True, BLACK)
                self.screen.blit(text, (250, HEIGHT - 120))
            elif not self.game_over and self.current_player_index == 0 and not self.players[0].folded and self.players[0].chips > 0 and self.phase != "showdown":
                pygame.draw.rect(self.screen, BLACK, (50, HEIGHT - 50, 80, 40))
                pygame.draw.rect(self.screen, BLACK, (150, HEIGHT - 50, 80, 40))
                pygame.draw.rect(self.screen, BLACK, (250, HEIGHT - 50, 80, 40))
                text = self.small_font.render("Fold", True, WHITE)
                self.screen.blit(text, (60, HEIGHT - 45))
                text = self.small_font.render("Call", True, WHITE)
                self.screen.blit(text, (160, HEIGHT - 45))
                text = self.small_font.render("Raise", True, WHITE)
                self.screen.blit(text, (260, HEIGHT - 45))

            # Turn Analysis on right
            text = self.font.render("Turn Analysis:", True, BLACK)
            self.screen.blit(text, (WIDTH - 300, 100))
            for i, entry in enumerate(self.log[-10:]):
                text = self.small_font.render(entry, True, BLACK)
                self.screen.blit(text, (WIDTH - 300, 130 + i * 20))

        pygame.display.flip()

    def handle_player_action(self, action, raise_amount=None):
        player = self.players[0]
        if action == "fold":
            player.folded = True
            amount = 0
            self.log.append(f"Turn {self.current_turn}: You folded")
        elif action == "call":
            amount = min(self.current_bet - player.current_bet, player.chips)
            player.current_bet += amount
            player.chips -= amount
            self.log.append(f"Turn {self.current_turn}: You called {amount}")
        else:  # raise
            amount = min(raise_amount - player.current_bet, player.chips)
            player.current_bet += amount
            player.chips -= amount
            self.current_bet = player.current_bet
            self.log.append(f"Turn {self.current_turn}: You raised to {player.current_bet}")
        return amount

    def advance_player_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        while self.players[self.current_player_index].folded and len(self.get_active_players()) > 1:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def get_active_players(self):
        return [p for p in self.players if not p.folded]

    def is_betting_round_over(self):
        active = self.get_active_players()
        if len(active) <= 1:
            return True
        max_bet = max(p.current_bet for p in active)
        return all(p.current_bet == max_bet or p.chips == 0 for p in active)

    def advance_phase(self):
        if self.phase == "preflop":
            self.community_cards = [self.deck.pop() for _ in range(3)]
            self.phase = "flop"
        elif self.phase == "flop":
            self.community_cards.append(self.deck.pop())
            self.phase = "turn"
        elif self.phase == "turn":
            self.community_cards.append(self.deck.pop())
            self.phase = "river"
        elif self.phase == "river":
            self.phase = "showdown"
        self.current_bet = 0
        for player in self.players:
            player.current_bet = 0

async def main():
    game = PokerGame()

    while game.running:
        game.draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if game.game_over:
                    if WIDTH // 2 - 150 <= pos[0] <= WIDTH // 2 + 150 and HEIGHT // 2 - 20 <= pos[1] <= HEIGHT // 2 + 20:
                        game.players[0].chips = 1000
                        game.players = [game.players[0]]
                        game.phase = "select_difficulty"
                        game.game_over = False
                elif game.phase == "select_difficulty":
                    difficulties = [AIDifficulty.BEGINNER, AIDifficulty.EASY, AIDifficulty.MEDIUM, AIDifficulty.HARD, AIDifficulty.MASTER]
                    for i in range(5):
                        if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100 and 100 + i * 50 <= pos[1] <= 140 + i * 50:
                            game.difficulty = difficulties[i]
                            game.phase = "select_num_ai"
                            break
                elif game.phase == "select_num_ai":
                    for i in range(1, 6):
                        if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100 and 100 + (i-1) * 50 <= pos[1] <= 140 + (i-1) * 50:
                            game.players = [game.players[0]]
                            for j in range(i):
                                game.players.append(AIPlayer(f"AI{j+1} {game.difficulty.name.capitalize()}", game.difficulty, 1000))
                            game.deal_cards()
                            break
                elif not game.input_active and game.current_player_index == 0 and not game.players[0].folded and game.players[0].chips > 0 and game.phase != "showdown":
                    if 50 <= pos[0] <= 130 and HEIGHT - 50 <= pos[1] <= HEIGHT - 10:
                        game.pot += game.handle_player_action("fold")
                        game.advance_player_turn()
                        if game.is_betting_round_over():
                            game.advance_phase()
                    elif 150 <= pos[0] <= 230 and HEIGHT - 50 <= pos[1] <= HEIGHT - 10:
                        game.pot += game.handle_player_action("call")
                        game.advance_player_turn()
                        if game.is_betting_round_over():
                            game.advance_phase()
                    elif 250 <= pos[0] <= 330 and HEIGHT - 50 <= pos[1] <= HEIGHT - 10:
                        game.input_active = True
                        game.input_text = ""
                elif game.input_active:
                    try:
                        raise_amount = int(game.input_text)
                        if raise_amount > game.current_bet and raise_amount <= game.players[0].chips + game.players[0].current_bet:
                            game.pot += game.handle_player_action("raise", raise_amount)
                            game.advance_player_turn()
                            if game.is_betting_round_over():
                                game.advance_phase()
                    except ValueError:
                        pass
                    game.input_active = False
                    game.input_text = ""

            elif event.type == pygame.KEYDOWN and game.input_active:
                if event.key == pygame.K_RETURN:
                    try:
                        raise_amount = int(game.input_text)
                        if raise_amount > game.current_bet and raise_amount <= game.players[0].chips + game.players[0].current_bet:
                            game.pot += game.handle_player_action("raise", raise_amount)
                            game.advance_player_turn()
                            if game.is_betting_round_over():
                                game.advance_phase()
                    except ValueError:
                        pass
                    game.input_active = False
                    game.input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    game.input_text = game.input_text[:-1]
                elif event.unicode.isdigit():
                    game.input_text += event.unicode

        if game.phase != "select_difficulty" and game.phase != "select_num_ai" and game.players and len(game.players) > 1 and not game.input_active and game.phase != "showdown" and not game.game_over and game.current_player_index != 0:
            current_player = game.players[game.current_player_index]
            if current_player.chips == 0 and game.current_bet > current_player.current_bet:
                current_player.folded = True
                game.log.append(f"Turn {game.current_turn}: {current_player.name} folded (out of chips)")
            else:
                if not current_player.folded:
                    game.current_turn += 1
                    amount, action_str = current_player.decide_action(game, game.pot, game.current_bet)
                    game.pot += amount
                    game.current_bet = max(game.current_bet, current_player.current_bet)
                    game.log.append(f"Turn {game.current_turn}: {current_player.name} {action_str}")
                    await asyncio.sleep(1)  # Wait 5 seconds before advancing
            game.advance_player_turn()
            if game.is_betting_round_over():
                game.advance_phase()

        if game.phase == "showdown" and not game.game_over:
            game.showdown_timer += 1
            if game.showdown_timer == 1:
                active_players = game.get_active_players()
                if len(active_players) <= 1:
                    winner = active_players[0] if active_players else game.players[0]
                    winner.chips += game.pot
                    game.log.append(f"{winner.name} won the pot (opponents folded)!")
                else:
                    # Log hands
                    for p in active_players:
                        game.log.append(f"{p.name} hand: {p.hand[0]} {p.hand[1]}")
                    strengths = [p.evaluate_hand(game.community_cards) for p in active_players]
                    max_strength = max(strengths)
                    winners = [active_players[k] for k in range(len(active_players)) if strengths[k] == max_strength]
                    split = game.pot // len(winners)
                    for winner in winners:
                        winner.chips += split
                    if len(winners) > 1:
                        game.log.append("Pot split among winners!")
                    else:
                        game.log.append(f"{winners[0].name} won the pot!")
                # Check for game over
                if game.players[0].chips <= 0:
                    game.game_over = True
                    game.log.append("Game Over: You ran out of chips!")
                elif all(p.chips <= 0 for p in game.players[1:]):
                    game.game_over = True
                    game.log.append("Game Over: All AIs ran out of chips! You win!")
            if game.showdown_timer >= game.showdown_duration and not game.game_over:
                game.deal_cards()

        await asyncio.sleep(4.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())