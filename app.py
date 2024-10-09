from flask import Flask, render_template, request, redirect, url_for, session
import MySQLdb
import cv2
import numpy as np
import imutils
import requests
app = Flask(__name__)
app.secret_key = "11111"  # For session management

# Connect to the MySQL database
db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="12345",
    db="parking_system"
)
cursor = db.cursor()

# Route for home (login) page
@app.route('/')
def home():
    return render_template('login.html')

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Query to check user credentials
    cursor.execute("SELECT * FROM users WHERE empid = %s AND password = %s", (username, password))
    manager = cursor.fetchone()
    
    if manager:
        session['manager_name'] = manager[1]  # Store the manager's name in session
        return redirect(url_for('dashboard'))
    else:
        return "Invalid credentials, please try again."

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'manager_name' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html')

# Route to manage staff parking
@app.route('/staff', methods=['GET', 'POST'])
def manage_staff():
    if 'manager_name' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        name = request.form['name']
        parking_spot = request.form['parking_spot']

        # Check if the staff exists, if so update, otherwise insert new staff
        cursor.execute("SELECT * FROM staff WHERE staff_id = %s", (staff_id,))
        staff = cursor.fetchone()
        if staff:
            cursor.execute(
                "UPDATE staff SET name = %s, parking_spot = %s WHERE staff_id = %s",
                (name, parking_spot, staff_id)
            )
        else:
            cursor.execute(
                "INSERT INTO staff (staff_id, name, parking_spot) VALUES (%s, %s, %s)",
                (staff_id, name, parking_spot)
            )
        db.commit()
        return redirect(url_for('manage_staff'))

    # Fetch the list of current staff
    cursor.execute("SELECT staff_id, name, parking_spot FROM staff")
    staff_list = cursor.fetchall()

    return render_template('staff.html', staff_list=staff_list)

# Route to delete staff
@app.route('/delete_staff', methods=['POST'])
def delete_staff():
    staff_id = request.form['staff_id']
    cursor.execute("DELETE FROM staff WHERE staff_id = %s", (staff_id,))
    db.commit()
    return redirect(url_for('manage_staff'))

# Route to view and manage fines
@app.route('/fine', methods=['GET', 'POST'])
def manage_fines():
    if 'manager_name' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        fine_amount = request.form['fine_amount']
        
        # Insert new fine record
        cursor.execute("INSERT INTO fines (roll_no, fine_amount) VALUES (%s, %s)", (roll_no, fine_amount))
        db.commit()
        return redirect(url_for('manage_fines'))

    # Fetch existing fines
    cursor.execute("SELECT roll_no, fine_amount FROM fines")
    fines_list = cursor.fetchall()

    return render_template('fine.html', fines_list=fines_list)

# Route to delete a fine
@app.route('/delete_fine', methods=['POST'])
def delete_fine():
    if 'manager_name' not in session:
        return redirect(url_for('home'))

    roll_no = request.form['roll_no']
    
    # Delete the fine from the database
    cursor.execute("DELETE FROM fines WHERE roll_no = %s", (roll_no,))
    db.commit()
    
    return redirect(url_for('manage_fines'))

# Route to launch IP camera stream
@app.route('/view_ip_camera')
def view_ip_camera():
    def stream_ip_camera():
        url = "http://192.168.55.55:8080/shot.jpg"
        
        # While loop to continuously fetching data from the Url
        while True:
            img_resp = requests.get(url)
            img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
            img = cv2.imdecode(img_arr, -1)
            img = imutils.resize(img, width=800, height=600)
            cv2.imshow("Android Cam", img)
        
            # Press Esc key to exit
            if cv2.waitKey(1) == 27:
                break

        cv2.destroyAllWindows()
    stream_ip_camera()
    return redirect(url_for('dashboard'))

# Parking spaces left (runs app.py)
@app.route('/parking_spaces_left')
def parking_spaces_left():
    import subprocess
    subprocess.run(['python', 'main.py'])
    return redirect(url_for('dashboard'))

# Manual fine entry (runs app2.py)
@app.route('/start_auto_violation_checker')
def start_auto_violation_checker():
    import subprocess
    subprocess.run(['python', 'app2.py'])
    return redirect(url_for('dashboard'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('manager_name', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
