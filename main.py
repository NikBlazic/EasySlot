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
appointments_db = TinyDB("appointments.json")

users = users_db.table("users")
businesses = business_db.table("businesses")
calendars = calendars_db.table("calendars")
appointments = appointments_db.table("appointments")

User = Query()
Business = Query()
Calendars = Query()
Appointments = Query()

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

    business_name = business['name']
    is_owner = business['owner'] == session.get('username')
    
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year+1}-01-01"
    else:
        end_date = f"{year}-{month+1:02d}-01"
    
    appointment_slots = calendars.search(
        (Calendars.business_id == int(business_id)) &
        (Calendars.date >= start_date) &
        (Calendars.date < end_date)
    )

    user_appointments = appointments.search(Appointments.user == session['username'])
    
    return render_template('businesses/calendar.html',
                         year=year,
                         month=month,
                         month_name=month_name,
                         calendar=cal,
                         today=today,
                         business_id=business_id,
                         business_name=business_name,
                         appointment_slots=appointment_slots,
                         user_appointments=user_appointments,
                         is_owner=is_owner)

@app.route("/businesses/<business_id>/add_slot", methods=["GET", "POST"])
def add_appointment_slot(business_id):
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    business = businesses.get(doc_id=int(business_id))
    if not business:
        return redirect(url_for('business_page'))
    
    if request.method == "POST":
        try:
            date_str = request.form.get('date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            duration = int(request.form.get('duration'))
            
            calendars.insert({
                'business_id': int(business_id),
                'date': date_str,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'available': True
            })
            
            return redirect(url_for('show_calendar', business_id=business_id))
        except Exception as e:
            return render_template('businesses/add_appointment_slot.html', 
                                business_id=business_id,
                                business_name=business['name'],
                                error=str(e))
    
    return render_template('businesses/add_appointment_slot.html',
                         business_id=business_id,
                         business_name=business['name'])

@app.route("/businesses/<business_id>/book_appointment", methods=["POST"])
def book_appointment(business_id):
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    try:
        slot_id = request.form.get('slot_id')
        date_str = request.form.get('date')
        
        if not slot_id or not date_str:
            return render_template('businesses/calendar.html',
                                error="Invalid appointment data",
                                business_id=business_id,
                                business_name=businesses.get(doc_id=int(business_id))['name'],
                                calendar=calendar.monthcalendar(datetime.now().year, datetime.now().month),
                                month=datetime.now().month,
                                year=datetime.now().year,
                                month_name=calendar.month_name[datetime.now().month],
                                today=date.today(),
                                appointment_slots=calendars.search(Calendars.business_id == int(business_id)),
                                user_appointments=appointments.search(Appointments.user == session['username']),
                                is_owner=businesses.get(doc_id=int(business_id))['owner'] == session['username'])
        
        slot = calendars.get(doc_id=int(slot_id))
        if not slot or not slot['available']:
            return render_template('businesses/calendar.html',
                                error="This slot is no longer available",
                                business_id=business_id,
                                business_name=businesses.get(doc_id=int(business_id))['name'],
                                calendar=calendar.monthcalendar(datetime.now().year, datetime.now().month),
                                month=datetime.now().month,
                                year=datetime.now().year,
                                month_name=calendar.month_name[datetime.now().month],
                                today=date.today(),
                                appointment_slots=calendars.search(Calendars.business_id == int(business_id)),
                                user_appointments=appointments.search(Appointments.user == session['username']),
                                is_owner=businesses.get(doc_id=int(business_id))['owner'] == session['username'])
        
        appointments.insert({
            'user': session['username'],
            'business_id': int(business_id),
            'slot_id': int(slot_id),
            'date': date_str,
            'start_time': slot['start_time'],
            'end_time': slot['end_time'],
            'duration': slot['duration']
        })
        
        calendars.update({'available': False}, doc_ids=[int(slot_id)])
        
        return redirect(url_for('show_calendar', business_id=business_id))
    except Exception as e:
        return render_template('businesses/calendar.html',
                            error=f"Failed to book appointment: {str(e)}",
                            business_id=business_id,
                            business_name=businesses.get(doc_id=int(business_id))['name'],
                            calendar=calendar.monthcalendar(datetime.now().year, datetime.now().month),
                            month=datetime.now().month,
                            year=datetime.now().year,
                            month_name=calendar.month_name[datetime.now().month],
                            today=date.today(),
                            appointment_slots=calendars.search(Calendars.business_id == int(business_id)),
                            user_appointments=appointments.search(Appointments.user == session['username']),
                            is_owner=businesses.get(doc_id=int(business_id))['owner'] == session['username'])

if __name__ == "__main__":
    app.run(debug=True)