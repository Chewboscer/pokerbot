from flask import request, render_template, redirect, url_for, session
import os
import sys

# Add models directory to path
fpath = os.path.join(os.path.dirname(__file__), '../models')
sys.path.append(fpath)

from models.user_model import User_Model, User

class UserController:
    @staticmethod
    def login():
        """
        Handles the login page rendering
        """
        # Create a default user with empty values for the login template
        default_user = User(id=0, username="", email="", password="")
        return render_template("login.html", user=default_user)
    
    @staticmethod
    def validate_login():
        """
        Validates login credentials
        """
        username = request.form["username"]
        password = request.form["password"]
        user = User_Model.get(username=username)
        
        if user and user.password == password:
            session["username"] = username
            return redirect(url_for("user_details"))
        else:
            default_user = User(id=0, username=username, email="", password="")
            return render_template("login.html", error="Invalid username or password", user=default_user)
    
    @staticmethod
    def register():
        """
        Handles user registration
        """
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        
        if User_Model.exists(username=username):
            default_user = User(id=0, username=username, email=email, password="")
            return render_template("login.html", error="Username already exists", user=default_user)
        
        try:
            new_user = User_Model.create({"username": username, "email": email, "password": password})
            session["username"] = username
            return redirect(url_for("user_details"))
        except ValueError as e:
            default_user = User(id=0, username=username, email=email, password="")
            return render_template("login.html", error=str(e), user=default_user)
    
    @staticmethod
    def user_details():
        """
        Shows user profile details
        """
        if "username" not in session:
            return redirect(url_for("login"))
            
        username = session["username"]
        user = User_Model.get(username=username)
        
        if not user:
            session.pop("username", None)
            return redirect(url_for("login"))
            
        return render_template("user_details.html", user=user)
    
    @staticmethod
    def update_user():
        """
        Updates user profile
        """
        if "username" not in session:
            return redirect(url_for("login"))
            
        username = session["username"]
        user = User_Model.get(username=username)
        
        if not user:
            return redirect(url_for("login"))
        
        email = request.form["email"]
        password = request.form["password"]
        updated_user = User_Model.update({"id": user.id, "username": username, "email": email, "password": password})
        
        return redirect(url_for("user_details"))
    
    @staticmethod
    def logout():
        """
        Handles user logout
        """
        session.pop("username", None)
        return redirect(url_for("login")) 