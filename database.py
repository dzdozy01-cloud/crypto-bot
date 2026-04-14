import sqlite3

def init_db():
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            coin_id TEXT NOT NULL,
            target_price REAL NOT NULL,
            condition TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            triggered INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            coin_id TEXT NOT NULL,
            UNIQUE(chat_id, coin_id)
        )
    """)
    conn.commit()
    conn.close()

def add_alert(chat_id, coin_id, target_price, condition):
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alerts (chat_id, coin_id, target_price, condition) VALUES (?, ?, ?, ?)",
        (chat_id, coin_id, target_price, condition)
    )
    conn.commit()
    conn.close()

def get_alerts(chat_id=None):
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    if chat_id:
        cursor.execute(
            "SELECT * FROM alerts WHERE chat_id = ? AND triggered = 0",
            (chat_id,)
        )
    else:
        cursor.execute("SELECT * FROM alerts WHERE triggered = 0")
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def mark_alert_triggered(alert_id):
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alerts SET triggered = 1 WHERE id = ?",
        (alert_id,)
    )
    conn.commit()
    conn.close()

def delete_alert(alert_id, chat_id):
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM alerts WHERE id = ? AND chat_id = ?",
        (alert_id, chat_id)
    )
    conn.commit()
    conn.close()

def add_to_watchlist(chat_id, coin_id):
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO watchlist (chat_id, coin_id) VALUES (?, ?)",
            (chat_id, coin_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_watchlist(chat_id):
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT coin_id FROM watchlist WHERE chat_id = ?",
        (chat_id,)
    )
    coins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return coins

def remove_from_watchlist(chat_id, coin_id):
    conn = sqlite3.connect("crypto_alerts.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM watchlist WHERE chat_id = ? AND coin_id = ?",
        (chat_id, coin_id)
    )
    conn.commit()
    conn.close()
