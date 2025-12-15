from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'rootpassword'),
    'database': os.getenv('DB_NAME', 'devops_db')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY id DESC")
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', messages=messages)
    except Exception as e:
        return f"Database Error: {str(e)}"

@app.route('/add', methods=['POST'])
def add_message():
    message = request.form.get('message')
    if message:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            return f"Error: {str(e)}"
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)