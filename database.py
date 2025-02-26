import sqlite3
import os

db_path = "C:\\ProgramData\\resumeWizard"
db_file = os.path.join(db_path, "resume_data.db")

# Ensure the database directory exists
if not os.path.exists(db_path):
    os.makedirs(db_path)


def connect_db():
    """Connect to the SQLite database."""
    return sqlite3.connect(db_file)


def create_tables():
    """Create job experience table if it doesn't exist."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            responsibilities TEXT NOT NULL,
            skills TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

def add_job_experience(job_title, company, responsibilities, skills=""):
    """Add a new job experience entry to the database safely."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO job_experience (job_title, company, responsibilities, skills)
            VALUES (?, ?, ?, ?)
        ''', (job_title, company, responsibilities, skills or ""))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")  # Debugging info in case of an issue
        raise
    finally:
        conn.close()


def fetch_all_experiences():
    """Retrieve all job experiences from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT job_title, company, responsibilities FROM job_experience")
    experiences = cursor.fetchall()
    conn.close()
    return experiences

def search_experiences_by_skills(extracted_skills):
    """Find job experiences that match the extracted skills from the job description."""
    if not extracted_skills:
        return []  # No skills extracted, return empty list

    conn = connect_db()
    cursor = conn.cursor()

    # Convert skills list into a wildcard search format
    query = "SELECT job_title, company, responsibilities FROM job_experience WHERE "
    conditions = []
    params = []

    for skill in extracted_skills:
        conditions.append("skills LIKE ?")
        params.append(f"%{skill}%")

    if not conditions:
        return []

    query += " OR ".join(conditions)
    cursor.execute(query, params)

    matched_experiences = cursor.fetchall()
    conn.close()
    return matched_experiences

# Initialize database tables
create_tables()
