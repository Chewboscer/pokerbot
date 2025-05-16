from flask import request, render_template, redirect, url_for, session, jsonify
import os
import sys
import random

# Add models directory to path
fpath = os.path.join(os.path.dirname(__file__), '../models')
sys.path.append(fpath)

from models.user_model import User_Model

# Poker game global state - in a real application, this would be stored in a database
games = {}

def get_card_value(card):
    """Convert card name to numeric value"""
    parts = card.split('_of_')
    value = parts[0]
    suit = parts[1]
    
    value_map = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'jack': 11, 'queen': 12, 'king': 13, 'ace': 14
    }
    
    return (value_map.get(value, 0), suit)

def evaluate_hand(hole_cards, community_cards):
    """
    Evaluate a poker hand (7 cards) and return the hand ranking.
    
    Rankings:
    9: Royal Flush
    8: Straight Flush
    7: Four of a Kind
    6: Full House
    5: Flush
    4: Straight
    3: Three of a Kind
    2: Two Pair
    1: One Pair
    0: High Card
    """
    all_cards = hole_cards + community_cards
    values = [get_card_value(card)[0] for card in all_cards]
    suits = [get_card_value(card)[1] for card in all_cards]
    
    # Count value frequencies
    value_counts = {}
    for value in values:
        value_counts[value] = value_counts.get(value, 0) + 1
    
    # Count suit frequencies
    suit_counts = {}
    for suit in suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    
    # Sort values by frequency (high to low) and then by value (high to low)
    sorted_values = sorted(value_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    
    # Check for flush
    flush = any(count >= 5 for count in suit_counts.values())
    flush_suit = next((suit for suit, count in suit_counts.items() if count >= 5), None)
    
    # Check for straight
    unique_values = sorted(set(values))
    straight = False
    straight_high = 0
    
    # Special case: Ace can be low (A-2-3-4-5)
    if 14 in unique_values and 2 in unique_values and 3 in unique_values and 4 in unique_values and 5 in unique_values:
        straight = True
        straight_high = 5  # 5 is the high card in A-2-3-4-5
    
    # Check for regular straights
    for i in range(len(unique_values) - 4):
        if unique_values[i+4] - unique_values[i] == 4:
            straight = True
            straight_high = unique_values[i+4]
    
    # Categorize hand
    if flush and straight:
        # Check for royal flush (10-J-Q-K-A of same suit)
        royal_values = [10, 11, 12, 13, 14]
        is_royal = all(any(get_card_value(card) == (value, flush_suit) for card in all_cards) for value in royal_values)
        if is_royal:
            return (9, [14, 13, 12, 11, 10])  # Royal Flush
        else:
            # Find highest straight flush
            flush_cards = [get_card_value(card)[0] for card in all_cards if get_card_value(card)[1] == flush_suit]
            flush_cards = sorted(set(flush_cards), reverse=True)
            for i in range(len(flush_cards) - 4):
                if flush_cards[i] - flush_cards[i+4] == 4:
                    return (8, [flush_cards[i]])  # Straight Flush
    
    # Four of a Kind
    if sorted_values[0][1] == 4:
        kicker = next((v for v, c in sorted_values if v != sorted_values[0][0]), 0)
        return (7, [sorted_values[0][0], kicker])
    
    # Full House
    if sorted_values[0][1] == 3 and (len(sorted_values) > 1 and sorted_values[1][1] >= 2):
        return (6, [sorted_values[0][0], sorted_values[1][0]])
    
    # Flush
    if flush:
        flush_values = [get_card_value(card)[0] for card in all_cards if get_card_value(card)[1] == flush_suit]
        flush_values.sort(reverse=True)
        return (5, flush_values[:5])
    
    # Straight
    if straight:
        return (4, [straight_high])
    
    # Three of a Kind
    if sorted_values[0][1] == 3:
        kickers = [v for v, c in sorted_values if v != sorted_values[0][0]]
        kickers = sorted(kickers, reverse=True)[:2]
        return (3, [sorted_values[0][0]] + kickers)
    
    # Two Pair
    if sorted_values[0][1] == 2 and (len(sorted_values) > 1 and sorted_values[1][1] == 2):
        kicker = next((v for v, c in sorted_values if v != sorted_values[0][0] and v != sorted_values[1][0]), 0)
        return (2, [sorted_values[0][0], sorted_values[1][0], kicker])
    
    # One Pair
    if sorted_values[0][1] == 2:
        kickers = [v for v, c in sorted_values if v != sorted_values[0][0]]
        kickers = sorted(kickers, reverse=True)[:3]
        return (1, [sorted_values[0][0]] + kickers)
    
    # High Card
    high_cards = sorted(values, reverse=True)[:5]
    return (0, high_cards)

def determine_winner(player_cards, bot_cards, community_cards):
    """
    Determine the winner between player and bot.
    Returns: 'player', 'bot', or 'tie'
    """
    player_hand = evaluate_hand(player_cards, community_cards)
    bot_hand = evaluate_hand(bot_cards, community_cards)
    
    # Compare hand ranks
    if player_hand[0] > bot_hand[0]:
        return 'player'
    elif bot_hand[0] > player_hand[0]:
        return 'bot'
    
    # If ranks are equal, compare kickers
    player_kickers = player_hand[1]
    bot_kickers = bot_hand[1]
    
    for i in range(min(len(player_kickers), len(bot_kickers))):
        if player_kickers[i] > bot_kickers[i]:
            return 'player'
        elif bot_kickers[i] > player_kickers[i]:
            return 'bot'
    
    return 'tie'

def get_hand_description(hand_rank):
    """Return a description of the hand based on the rank"""
    rank_names = {
        9: "Royal Flush",
        8: "Straight Flush",
        7: "Four of a Kind",
        6: "Full House", 
        5: "Flush",
        4: "Straight",
        3: "Three of a Kind",
        2: "Two Pair",
        1: "Pair",
        0: "High Card"
    }
    return rank_names.get(hand_rank[0], "Unknown")

class GameController:
    @staticmethod
    def user_games():
        """
        Display the user's games
        """
        if "username" not in session:
            return redirect(url_for("login"))
            
        username = session["username"]
        user = User_Model.get(username=username)
        
        # Get filtered games for this user
        user_games = []
        for game_id, game in games.items():
            if username in game.get("players", []):
                user_games.append({
                    "id": game_id,
                    "name": game.get("name", f"Game {game_id}"),
                    "bot_difficulty": game.get("bot_difficulty", "medium"),
                    "game_started": game.get("game_started", False)
                })
                
        return render_template("game_setup.html", games=games, username=username, user_games=user_games)
    
    @staticmethod
    def create_game():
        """
        Creates a new poker game
        """
        if "username" not in session:
            return redirect(url_for("login"))
            
        game_name = request.form["game_name"]
        bot_difficulty = request.form["bot_difficulty"]
        username = session["username"]
        
        # Create a unique game ID
        game_id = random.randint(1000, 9999)
        
        # Store the game in our global state
        games[game_id] = {
            "name": game_name,
            "bot_difficulty": bot_difficulty,
            "players": [username, "bot"],
            "game_started": True,
            "community_cards": [],
            "player_hands": {},
            "pot": 0,
            "current_bet": 0,
            "chips": {
                username: 1000,  # Starting chips for player
                "bot": 1000      # Starting chips for bot
            },
            "bets": {
                username: 0,
                "bot": 0
            },
            "round": "pre-flop"  # Options: pre-flop, flop, turn, river, showdown
        }
        
        session['game_id'] = game_id
        return redirect(url_for("view_game", game_id=game_id))
    
    @staticmethod
    def view_game(game_id):
        """
        View a specific game
        """
        if "username" not in session:
            return redirect(url_for("login"))
            
        game_id = int(game_id)
        game = games.get(game_id)
        if not game:
            return "Game not found", 404
            
        username = session["username"]
        return render_template("game.html", game_id=game_id, game=game, username=username)
    
    @staticmethod
    def game_settings(game_id):
        """
        Configure game settings
        """
        if "username" not in session:
            return redirect(url_for("login"))
            
        game_id = int(game_id)
        game = games.get(game_id)
        if not game:
            return "Game not found", 404
            
        username = session["username"]
        return render_template("gamesettings.html", game_id=game_id, bot_difficulty=game['bot_difficulty'], username=username)
    
    @staticmethod
    def update_game_settings(game_id):
        """
        Update game settings
        """
        if "username" not in session:
            return redirect(url_for("login"))
            
        game_id = int(game_id)
        if game_id not in games:
            return "Game not found", 404
            
        games[game_id]['bot_difficulty'] = request.form['bot_difficulty']
        return redirect(url_for('view_game', game_id=game_id))
    
    @staticmethod
    def handle_game_action(game_id):
        """
        Handle player actions (fold, call, raise)
        """
        if "username" not in session:
            return jsonify({'error': 'Not logged in'}), 401
            
        game_id = int(game_id)
        if game_id not in games:
            return jsonify({'error': 'Game not found'}), 404
        
        action = request.form['action']
        bet_amount = int(request.form.get('bet_amount', 0))
        username = session["username"]
        game = games[game_id]
        
        # Get the current cards
        bot_cards = game['player_hands'].get('bot', [])
        community_cards = game['community_cards'][:game.get('visible_cards', 0)]
        
        # Evaluate bot's hand strength
        bot_hand = None
        hand_strength = 0
        
        if community_cards:
            bot_hand = evaluate_hand(bot_cards, community_cards)
            hand_strength = bot_hand[0]  # Hand rank (0-9, higher is better)
        
        # Define bot behavior based on difficulty and hand strength
        if game['bot_difficulty'] == 'easy':
            # Easy bot: More likely to fold with weak hands, rarely raises
            if hand_strength <= 1:  # High card or pair
                bot_actions = ['fold'] * 60 + ['call'] * 40  # 60% fold, 40% call
            elif hand_strength <= 3:  # Two pair or three of a kind
                bot_actions = ['fold'] * 20 + ['call'] * 70 + ['raise'] * 10  # 20% fold, 70% call, 10% raise
            else:  # Strong hand
                bot_actions = ['call'] * 80 + ['raise'] * 20  # 80% call, 20% raise
                
            bot_action = random.choice(bot_actions)
            bot_raise = random.randint(5, 15)  # Small raises
            
        elif game['bot_difficulty'] == 'medium':
            # Medium bot: More balanced, raises with good hands
            if hand_strength <= 1:  # High card or pair
                bot_actions = ['fold'] * 30 + ['call'] * 60 + ['raise'] * 10  # 30% fold, 60% call, 10% raise
            elif hand_strength <= 3:  # Two pair or three of a kind
                bot_actions = ['fold'] * 10 + ['call'] * 60 + ['raise'] * 30  # 10% fold, 60% call, 30% raise
            else:  # Strong hand
                bot_actions = ['call'] * 40 + ['raise'] * 60  # 40% call, 60% raise
                
            bot_action = random.choice(bot_actions)
            bot_raise = random.randint(10, 30)  # Medium raises
            
        else:  # hard
            # Hard bot: Aggressive, rarely folds, bluffs occasionally
            if hand_strength <= 1:  # High card or pair
                # Even with weak hands, sometimes bluff
                bot_actions = ['fold'] * 10 + ['call'] * 50 + ['raise'] * 40  # 10% fold, 50% call, 40% raise
            elif hand_strength <= 3:  # Two pair or three of a kind
                bot_actions = ['call'] * 40 + ['raise'] * 60  # 40% call, 60% raise
            else:  # Strong hand
                bot_actions = ['call'] * 20 + ['raise'] * 80  # 20% call, 80% raise
                
            bot_action = random.choice(bot_actions)
            bot_raise = random.randint(20, 50)  # Large raises
        
        # Add additional randomness - bot occasionally switches strategy to prevent being predictable
        if random.random() < 0.1:  # 10% chance
            bot_action = random.choice(['fold', 'call', 'raise'])
        
        # If there are no community cards yet (pre-flop), make decisions based on hole cards only
        if not community_cards:
            # Check if bot has a high pair in hand
            card1_value = get_card_value(bot_cards[0])[0]
            card2_value = get_card_value(bot_cards[1])[0]
            
            if card1_value == card2_value and card1_value >= 10:  # High pair (10s or better)
                if game['bot_difficulty'] == 'easy':
                    bot_action = random.choice(['call', 'raise'])
                else:
                    bot_action = 'raise'
            elif card1_value >= 12 or card2_value >= 12:  # Face card
                if game['bot_difficulty'] == 'hard':
                    bot_action = random.choice(['call', 'raise'])
                else:
                    bot_action = 'call'
        
        # Process player action
        if action == 'fold':
            # Bot wins the pot
            game['chips']['bot'] += game['pot']
            game['pot'] = 0
            game['bets'][username] = 0
            game['bets']['bot'] = 0
            game['current_bet'] = 0
            
            response_data = {
                'message': f'You folded. Bot wins the pot!',
                'player_chips': game['chips'][username],
                'bot_chips': game['chips']['bot'],
                'pot': game['pot']
            }
            
        elif action == 'call':
            # Player matches the current bet
            call_amount = game['current_bet'] - game['bets'][username]
            if call_amount > game['chips'][username]:
                call_amount = game['chips'][username]  # All-in
            
            game['chips'][username] -= call_amount
            game['bets'][username] += call_amount
            game['pot'] += call_amount
            
            # Bot's action
            if bot_action == 'fold':
                # Player wins the pot
                game['chips'][username] += game['pot']
                game['pot'] = 0
                response_data = {
                    'message': f'Bot folded. You win the pot!',
                    'player_chips': game['chips'][username],
                    'bot_chips': game['chips']['bot'],
                    'pot': game['pot']
                }
                game['bets'][username] = 0
                game['bets']['bot'] = 0
                game['current_bet'] = 0
                
            else:  # Bot calls
                # Bot matches the player's bet
                bot_call_amount = game['current_bet'] - game['bets']['bot']
                if bot_call_amount > game['chips']['bot']:
                    bot_call_amount = game['chips']['bot']  # Bot all-in
                    
                game['chips']['bot'] -= bot_call_amount
                game['bets']['bot'] += bot_call_amount
                game['pot'] += bot_call_amount
                
                response_data = {
                    'message': f'You called ${call_amount}. Bot called.',
                    'player_chips': game['chips'][username],
                    'bot_chips': game['chips']['bot'],
                    'pot': game['pot']
                }
            
        elif action == 'raise':
            # Player raises
            raise_amount = bet_amount
            if raise_amount <= 0:
                raise_amount = 10  # Default raise amount
                
            total_bet = game['current_bet'] + raise_amount
            
            # Check if player has enough chips
            if total_bet - game['bets'][username] > game['chips'][username]:
                total_bet = game['bets'][username] + game['chips'][username]  # All-in
                
            player_additional = total_bet - game['bets'][username]
            game['chips'][username] -= player_additional
            game['pot'] += player_additional
            game['bets'][username] = total_bet
            game['current_bet'] = total_bet
            
            # Bot's action
            if bot_action == 'fold':
                # Player wins the pot
                game['chips'][username] += game['pot']
                game['pot'] = 0
                response_data = {
                    'message': f'You raised to ${total_bet}. Bot folded. You win the pot!',
                    'player_chips': game['chips'][username],
                    'bot_chips': game['chips']['bot'],
                    'pot': game['pot']
                }
                game['bets'][username] = 0
                game['bets']['bot'] = 0
                game['current_bet'] = 0
                
            elif bot_action == 'call':
                # Bot calls the player's raise
                bot_call_amount = total_bet - game['bets']['bot']
                if bot_call_amount > game['chips']['bot']:
                    bot_call_amount = game['chips']['bot']  # Bot all-in
                    
                game['chips']['bot'] -= bot_call_amount
                game['bets']['bot'] += bot_call_amount
                game['pot'] += bot_call_amount
                
                response_data = {
                    'message': f'You raised to ${total_bet}. Bot called.',
                    'player_chips': game['chips'][username],
                    'bot_chips': game['chips']['bot'],
                    'pot': game['pot']
                }
            
            else:  # Bot raises
                # Bot re-raises
                bot_total_bet = total_bet + bot_raise
                bot_additional = bot_total_bet - game['bets']['bot']
                
                if bot_additional > game['chips']['bot']:
                    bot_additional = game['chips']['bot']  # Bot all-in
                    bot_total_bet = game['bets']['bot'] + bot_additional
                    
                game['chips']['bot'] -= bot_additional
                game['bets']['bot'] = bot_total_bet
                game['pot'] += bot_additional
                game['current_bet'] = bot_total_bet
                
                response_data = {
                    'message': f'You raised to ${total_bet}. Bot re-raised to ${bot_total_bet}!',
                    'player_chips': game['chips'][username],
                    'bot_chips': game['chips']['bot'],
                    'pot': game['pot'],
                    'current_bet': game['current_bet']
                }
        else:
            response_data = {'message': 'Invalid action'}
        
        return jsonify(response_data)
    
    @staticmethod
    def deal_cards(game_id):
        """
        Deal cards for a poker game
        """
        game_id = int(game_id)
        if game_id not in games:
            return jsonify({'error': 'Game not found'}), 404
            
        username = session["username"]
        game = games[game_id]
        
        # Reset bets and add blinds
        small_blind = 5
        big_blind = 10
        
        # Reset the pot and bets
        game['pot'] = 0
        game['bets'] = {
            username: 0,
            "bot": 0
        }
        
        # Add small blind (player) and big blind (bot)
        player_blind = min(small_blind, game['chips'][username])
        bot_blind = min(big_blind, game['chips']['bot'])
        
        game['chips'][username] -= player_blind
        game['chips']['bot'] -= bot_blind
        game['pot'] = player_blind + bot_blind
        game['bets'][username] = player_blind
        game['bets']['bot'] = bot_blind
        game['current_bet'] = big_blind
        
        # Define a deck of cards
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
        
        deck = [f"{value}_of_{suit}" for suit in suits for value in values]
        random.shuffle(deck)
        
        # Deal player cards
        game['player_hands'] = {}
        
        # Deal player cards
        player_cards = [deck.pop(), deck.pop()]
        game['player_hands'][username] = player_cards
        
        # Deal bot cards
        bot_cards = [deck.pop(), deck.pop()]
        game['player_hands']["bot"] = bot_cards
        
        # Deal community cards (face down initially)
        game['community_cards'] = [deck.pop() for _ in range(5)]
        game['visible_cards'] = 0  # No community cards visible initially
        game['round'] = 'pre-flop'
        
        # Return the player's cards to the frontend
        return jsonify({
            'status': 'success', 
            'message': f'Cards dealt. You posted small blind (${player_blind}), Bot posted big blind (${bot_blind})',
            'player_cards': player_cards,
            'community_cards': game['community_cards'],
            'player_chips': game['chips'][username],
            'bot_chips': game['chips']['bot'],
            'pot': game['pot'],
            'current_bet': game['current_bet']
        })
    
    @staticmethod
    def advance_round(game_id):
        """
        Advance to the next round (flop, turn, river)
        """
        game_id = int(game_id)
        if game_id not in games:
            return jsonify({'error': 'Game not found'}), 404
            
        game = games[game_id]
        username = session["username"]
        bot_name = "bot"
        
        # Reset bets for the new round but keep the pot
        game['bets'][username] = 0
        game['bets'][bot_name] = 0
        game['current_bet'] = 0
        
        visible_community_cards = []
        bot_cards = None
        winner = None
        player_hand_description = None
        bot_hand_description = None
        
        if game['round'] == 'pre-flop':
            game['round'] = 'flop'
            game['visible_cards'] = 3
            visible_community_cards = game['community_cards'][:3]
        elif game['round'] == 'flop':
            game['round'] = 'turn'
            game['visible_cards'] = 4
            visible_community_cards = game['community_cards'][:4]
        elif game['round'] == 'turn':
            game['round'] = 'river'
            game['visible_cards'] = 5
            visible_community_cards = game['community_cards'][:5]
        elif game['round'] == 'river':
            game['round'] = 'showdown'
            visible_community_cards = game['community_cards']
            # In showdown, we also reveal the bot's cards
            bot_cards = game['player_hands'].get(bot_name, [])
            player_cards = game['player_hands'].get(username, [])
            
            # Evaluate hands and determine winner using poker rules
            player_hand = evaluate_hand(player_cards, game['community_cards'])
            bot_hand = evaluate_hand(bot_cards, game['community_cards'])
            player_hand_description = get_hand_description(player_hand)
            bot_hand_description = get_hand_description(bot_hand)
            
            winner_result = determine_winner(player_cards, bot_cards, game['community_cards'])
            
            if winner_result == 'player':
                winner = username
            elif winner_result == 'bot':
                winner = bot_name
            else:
                # In case of a tie, split the pot
                game['chips'][username] += game['pot'] // 2
                game['chips'][bot_name] += game['pot'] // 2
                game['pot'] = 0
                winner = "tie"
            
            # Award pot to winner if not a tie
            if winner and winner != "tie":
                game['chips'][winner] += game['pot']
                game['pot'] = 0
        
        response = {
            'status': 'success', 
            'round': game['round'], 
            'visible_cards': game['visible_cards'],
            'community_cards': visible_community_cards,
            'player_chips': game['chips'][username],
            'bot_chips': game['chips'][bot_name],
            'pot': game['pot']
        }
        
        if bot_cards:
            response['bot_cards'] = bot_cards
        
        if winner:
            response['winner'] = winner
            
            if winner == "tie":
                response['message'] = f"It's a tie! The pot is split."
                response['player_hand'] = player_hand_description
                response['bot_hand'] = bot_hand_description
            else:
                winner_name = 'You' if winner == username else 'Bot'
                if winner == username:
                    response['message'] = f"You win with {player_hand_description}! Bot had {bot_hand_description}."
                else:
                    response['message'] = f"Bot wins with {bot_hand_description}! You had {player_hand_description}."
                
                response['player_hand'] = player_hand_description
                response['bot_hand'] = bot_hand_description
        
        return jsonify(response) 