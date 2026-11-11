import random
import string
import os
import psycopg2
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'shortener')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'shortener_pass')
DB_NAME = os.environ.get('DB_NAME', 'shortener_db')

def get_db_connection():
    return psycopg2.connect(
        host = DB_HOST,
        port = DB_PORT,
        user = DB_USER,
        password = DB_PASSWORD,
        dbname = DB_NAME,
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                code VARCHAR(16) PRIMARY KEY,
                long_url TEXT NOT NULL);
    """)
    conn.commit()
    cur.close()
    conn.close()

def gen_code(len=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(len))

@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'url is required'}), 400

    long_url = data['url']

    conn = get_db_connection()
    cur = conn.cursor()

    while True:
        code = gen_code()
        cur.execute("SELECT 1 FROM urls WHERE code = %s", (code,))
        if cur.fetchone() is None:
            break

    cur.execute(
        "INSERT INTO urls (code, long_url) VALUES (%s, %s)",
        (code, long_url),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'short_code': code, 'short_url': f'http:localhost:5000/{code}'}), 201


@app.route('/<code>')
def redirect_to_url(code):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT long_url FROM urls WHERE code = %s", (code,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return jsonify({'error': 'not found'}), 404
    return redirect(row[0])

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)