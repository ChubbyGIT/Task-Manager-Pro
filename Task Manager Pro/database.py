import sqlite3
import pandas as pd
from datetime import date, datetime

DB_FILE = "task_tracker_v3.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            priority TEXT,
            start_date DATE,
            end_date DATE,
            progress INTEGER DEFAULT 0,
            task_type TEXT,        
            is_daily INTEGER DEFAULT 0,
            created_at DATE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            log_date DATE,
            is_complete INTEGER DEFAULT 0,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_package_dates():
    """
    Returns (start_date, end_date) of the CURRENT active package.
    Returns (None, None) if the current package has expired or doesn't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MIN(start_date), MAX(end_date) FROM tasks WHERE task_type != 'resolution'")
    res = c.fetchone()
    conn.close()
    
    if res and res[0] and res[1]:
        s_date = datetime.strptime(res[0], "%Y-%m-%d").date()
        e_date = datetime.strptime(res[1], "%Y-%m-%d").date()
        
        if e_date < date.today():
            return None, None
            
        return s_date, e_date
    return None, None

def add_task_to_db(name, desc, priority, start_dt, end_dt, t_type, is_daily):
    if isinstance(start_dt, str): start_dt = datetime.strptime(start_dt, "%Y-%m-%d").date()
    if isinstance(end_dt, str): end_dt = datetime.strptime(end_dt, "%Y-%m-%d").date()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (name, description, priority, start_date, end_date, task_type, is_daily, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, desc, priority, start_dt, end_dt, t_type, 1 if is_daily else 0, date.today()))
    conn.commit()
    conn.close()

def update_task_progress(task_id, new_progress):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE tasks SET progress = ? WHERE id = ?', (new_progress, task_id))
    conn.commit()
    conn.close()

def toggle_daily_status(task_id, log_date, is_checked):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    val = 1 if is_checked else 0
    c.execute('SELECT id FROM daily_logs WHERE task_id = ? AND log_date = ?', (task_id, log_date))
    exists = c.fetchone()
    if exists:
        c.execute('UPDATE daily_logs SET is_complete = ? WHERE id = ?', (val, exists[0]))
    else:
        c.execute('INSERT INTO daily_logs (task_id, log_date, is_complete) VALUES (?, ?, ?)', (task_id, log_date, val))
    conn.commit()
    
    # Auto-Calculate Parent Progress
    c.execute('SELECT start_date, end_date FROM tasks WHERE id = ?', (task_id,))
    res = c.fetchone()
    if res:
        s_date = datetime.strptime(res[0], "%Y-%m-%d").date()
        e_date = datetime.strptime(res[1], "%Y-%m-%d").date()
        total_days = (e_date - s_date).days + 1
        c.execute('''
            SELECT COUNT(*) FROM daily_logs 
            WHERE task_id = ? AND is_complete = 1 AND log_date >= ? AND log_date <= ?
        ''', (task_id, res[0], res[1]))
        completed_count = c.fetchone()[0]
        if total_days > 0:
            new_pct = int((completed_count / total_days) * 100)
            c.execute('UPDATE tasks SET progress = ? WHERE id = ?', (new_pct, task_id))
    conn.commit()
    conn.close()

def get_daily_status_map(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT log_date, is_complete FROM daily_logs WHERE task_id = ?', (task_id,))
    data = {row[0]: bool(row[1]) for row in c.fetchall()}
    conn.close()
    return data

def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    c.execute('DELETE FROM daily_logs WHERE task_id = ?', (task_id,))
    conn.commit()
    conn.close()

def get_tasks_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    if not df.empty:
        df['end_date'] = pd.to_datetime(df['end_date']).dt.date
        df['start_date'] = pd.to_datetime(df['start_date']).dt.date
    return df

def get_resolutions_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM tasks WHERE task_type = 'resolution'", conn)
    conn.close()
    return df