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
            "players": [username],
            "game_started": True,
            "community_cards": [],
            "player_hands": {},
            "pot": 0,
            "current_turn": 0,
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
        
        # Determine bot response based on difficulty
        if games[game_id]['bot_difficulty'] == 'easy':
            bot_action = random.choice(['fold', 'call'])
        elif games[game_id]['bot_difficulty'] == 'medium':
            bot_action = random.choice(['call', 'raise'])
        else:  # hard
            bot_action = 'raise'
        
        # Process game actions
        if action == 'fold':
            response_data = {'message': f'Player folded. Bot action: {bot_action}. Game Over'}
            games[game_id]['game_started'] = False
        elif action == 'call':
            response_data = {'message': f'Player called. Bot action: {bot_action}.'}
        elif action == 'raise':
            response_data = {'message': f'Player raised. Bot action: {bot_action}.'}
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
            
        # Define a deck of cards
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
        
        deck = [f"{value}_of_{suit}" for suit in suits for value in values]
        random.shuffle(deck)
        
        # Deal player cards
        games[game_id]['player_hands'] = {}
        for player in games[game_id]['players']:
            games[game_id]['player_hands'][player] = [deck.pop(), deck.pop()]
        
        # Deal community cards (face down initially)
        games[game_id]['community_cards'] = [deck.pop() for _ in range(5)]
        games[game_id]['visible_cards'] = 0  # No community cards visible initially
        games[game_id]['round'] = 'pre-flop'
        
        return jsonify({'status': 'success', 'message': 'Cards dealt'})
    
    @staticmethod
    def advance_round(game_id):
        """
        Advance to the next round (flop, turn, river)
        """
        game_id = int(game_id)
        if game_id not in games:
            return jsonify({'error': 'Game not found'}), 404
            
        game = games[game_id]
        if game['round'] == 'pre-flop':
            game['round'] = 'flop'
            game['visible_cards'] = 3
        elif game['round'] == 'flop':
            game['round'] = 'turn'
            game['visible_cards'] = 4
        elif game['round'] == 'turn':
            game['round'] = 'river'
            game['visible_cards'] = 5
        elif game['round'] == 'river':
            game['round'] = 'showdown'
        
        return jsonify({'status': 'success', 'round': game['round'], 'visible_cards': game['visible_cards']}) 