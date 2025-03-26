from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from tinydb import TinyDB, Query

app = Flask(__name__)

db = TinyDB('klepet.json')
users = db.table('uporabniki')
User = Query()

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            # Check if the user exists in the database
            user = users.get(User.username == username)
            
            if user:
                # If user exists, check password
                if user['password'] == password:
                    session['username'] = username
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'error': 'Incorrect password'})
            else:
                # If user doesn't exist, create a new user
                users.insert({'username': username, 'password': password})
                session['username'] = username
                return jsonify({'success': True})
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({'success': False, 'error': 'An error occurred'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)