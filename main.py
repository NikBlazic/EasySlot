from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from tinydb import TinyDB, Query
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
user_db = TinyDB("users.json")
business_db = TinyDB("businesses.json")

users = user_db.table("users")
businesses = business_db.table("businesses")

User = Query()
Business = Query()

@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect(url_for('auth'))
    return render_template("dashboard.html", username=session['username'])

@app.route("/")
def links():
    return render_template("links.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/business")
def business():
    return render_template("/businesses/business.html")

@app.route("/create_business")
def create_business():
    return render_template("/businesses/create_business.html")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            mode = request.form["mode"]

            user = users.get(User.username == username)

            if mode == "login":
                if user:
                    if user["password"] == password:
                        session["username"] = username
                        return redirect(url_for('dashboard'))
                    else:
                        return render_template("auth.html", error="Incorrect password")
                else:
                    return render_template("auth.html", error="User doesn't exist")

            elif mode == "signup":
                email = request.form.get("email")

                if not email:
                    return render_template("auth.html", error="Email is required for signup")

                if user:
                    return render_template("auth.html", error="User already exists")
                else:
                    users.insert({
                        "username": username,
                        "password": password,
                        "email": email
                    })
                    session["username"] = username
                    return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"Login/Signup error: {str(e)}")
            return render_template("auth.html", error="An error occurred")

    return render_template("auth.html")

if __name__ == "__main__":
    app.run(debug=True)