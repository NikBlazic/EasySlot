from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from tinydb import TinyDB, Query
from dotenv import load_dotenv
import os
from datetime import datetime, date
import calendar

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

users_db = TinyDB("users.json")
business_db = TinyDB("businesses.json")
calendars_db = TinyDB("calendars.json")

users = users_db.table("users")
businesses = business_db.table("businesses")
calendars = calendars_db.table("calendars")

User = Query()
Business = Query()
Calendars = Query()

@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect(url_for('auth'))

    return render_template("dashboard.html", username=session['username'])

@app.route("/")
def links():
    return render_template("links.html")

@app.route("/profile")
def profile():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    user_businesses = businesses.search(Business.owner == session['username'])
    
    return render_template("profile.html", businesses=user_businesses)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('auth'))

@app.route("/settings", methods=["GET"])
def settings():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    user = users.get(User.username == session['username'])
    return render_template("settings.html", user=user)

@app.route('/update_profile', methods=["GET", "POST"])
def update_profile():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    try:
        data = request.get_json()
        email = data.get('email')
        phone = data.get('phone')
        location = data.get('location')
        
        users.update({
            'email': email,
            'phone': phone,
            'location': location
        }, User.username == session['username'])
        
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'error': 'Failed to update profile'})

@app.route("/businesses")
def business_page():
    if 'username' not in session:
        return redirect(url_for('auth'))

    all_businesses = businesses.all()
    return render_template("/businesses/businesses.html", businesses=all_businesses, current_user=session['username'])

@app.route('/businesses/create', methods=["GET", "POST"])
def create_business():
    if 'username' not in session:
        return redirect(url_for('auth'))

    if request.method == "POST":
        try:
            business_name = request.form["businessName"]
            business_type = request.form["businessType"]
            business_email = request.form["businessEmail"]
            phone_number = request.form["phoneNumber"]
            business_address = request.form["businessAddress"]
            business_description = request.form["businessDescription"]

            if not all([business_name, business_type, business_email, phone_number, business_address, business_description]):
                return render_template("/businesses/create.html", error="All fields are required")

            businesses.insert ({
                'name': business_name,
                'type': business_type,
                'email': business_email,
                'phone': phone_number,
                'address': business_address,
                'description': business_description,
                'owner': session['username']
            })
            return redirect(url_for('dashboard'))
        except Exception as e:
            return render_template("/businesses/create.html", error=f"Failed to create business: {str(e)}")

    return render_template("/businesses/create.html")

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

@app.route("/businesses/<business_id>/calendar", methods=["GET", "POST"])
def show_calendar(business_id):
    try:
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
    except (TypeError, ValueError):
        month = datetime.now().month
        year = datetime.now().year
    
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    today = date.today()
    business = businesses.get(doc_id=int(business_id))

    if business:
        business_name = business['name']
    else:
        business_name = 'Unknown Business'
    
    return render_template('businesses/calendar.html',
                         year=year,
                         month=month,
                         month_name=month_name,
                         calendar=cal,
                         today=today,
                         business_id=business_id,
                         business_name=business_name)

if __name__ == "__main__":
    app.run(debug=True)