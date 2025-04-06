from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from tinydb import TinyDB, Query

app = Flask(__name__)
db = TinyDB("users.json")
users = db.table("uporabniki")
User = Query()

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/")
def links():
    return render_template("links.html")

@app.route("/login", methods=["GET", "POST"])
def login():
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
                        return jsonify({"success": True})
                    else:
                        return jsonify({"success": False, "error": "Incorrect password"})
                else:
                    return jsonify({"success": False, "error": "User doesn't exist"})

            elif mode == "signup":
                email = request.form.get("email")

                if not email:
                    return jsonify({"success": False, "error": "Email is required for signup"})

                if user:
                    return jsonify({"success": False, "error": "User already exists"})
                else:
                    users.insert({
                        "username": username,
                        "password": password,
                        "email": email
                    })
                    session["username"] = username
                    return jsonify({"success": True})

        except Exception as e:
            print(f"Login/Signup error: {str(e)}")
            return jsonify({"success": False, "error": "An error occurred"})

    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)