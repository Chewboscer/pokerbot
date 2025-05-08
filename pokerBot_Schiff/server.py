from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import sys

# Add controllers and models to the path
fpath = os.path.join(os.path.dirname(__file__), 'controllers')
sys.path.append(fpath)
fpath = os.path.join(os.path.dirname(__file__), 'models')
sys.path.append(fpath)

# Import controllers
from controllers.UserController import UserController
from controllers.GameController import GameController

# Import models
from models.user_model import User_Model

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = "secret_key"  # Change this in a production environment

# Initialize the database
User_Model.initialize_DB()

# Ensure the 'data' directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Default route redirects to login
@app.route('/')
def index():
    return redirect(url_for('login'))

# User Management Routes
app.add_url_rule('/login', 'login', view_func=UserController.login, methods=['GET'])
app.add_url_rule('/validate_login', 'validate_login', view_func=UserController.validate_login, methods=['POST'])
app.add_url_rule('/register', 'register', view_func=UserController.register, methods=['POST'])
app.add_url_rule('/user_details', 'user_details', view_func=UserController.user_details, methods=['GET'])
app.add_url_rule('/update_user', 'update_user', view_func=UserController.update_user, methods=['POST'])
app.add_url_rule('/logout', 'logout', view_func=UserController.logout, methods=['GET'])

# Game Management Routes
app.add_url_rule('/game_setup', 'game_setup', view_func=GameController.user_games, methods=['GET'])
app.add_url_rule('/start_game', 'start_game', view_func=GameController.create_game, methods=['POST'])
app.add_url_rule('/game/<game_id>', 'view_game', view_func=GameController.view_game, methods=['GET'])
app.add_url_rule('/gamesettings/<game_id>', 'game_settings', view_func=GameController.game_settings, methods=['GET'])
app.add_url_rule('/update_bot_settings/<game_id>', 'update_game_settings', view_func=GameController.update_game_settings, methods=['POST'])
app.add_url_rule('/api/game/<game_id>/action', 'handle_game_action', view_func=GameController.handle_game_action, methods=['POST'])
app.add_url_rule('/api/game/<game_id>/deal', 'deal_cards', view_func=GameController.deal_cards, methods=['POST'])
app.add_url_rule('/api/game/<game_id>/advance', 'advance_round', view_func=GameController.advance_round, methods=['POST'])

if __name__ == "__main__":
    # To run this application, you need to install Flask:
    # pip install flask
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, port=port)
