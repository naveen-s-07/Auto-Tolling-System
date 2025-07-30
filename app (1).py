from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number_plate TEXT,
            owner TEXT,
            phone TEXT,
            toll INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def dashboard():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    logs = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    total_toll = conn.execute("SELECT SUM(toll) FROM logs").fetchone()[0]
    conn.close()
    return render_template("dashboard.html", logs=logs, total_toll=total_toll or 0)

@app.route('/api/log', methods=['POST'])
def log_entry():
    data = request.json
    conn = sqlite3.connect('database.db')
    conn.execute('''
        INSERT INTO logs (number_plate, owner, phone, toll, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['number_plate'],
        data['owner'],
        data['phone'],
        data['toll'],
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)
