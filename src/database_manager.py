import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Create a new database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise
        
    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        try:
            # Family members table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS family_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    personal_info TEXT
                )
            ''')
            
            # Memories table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    family_member_id INTEGER,
                    text TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    category TEXT NOT NULL,
                    importance REAL NOT NULL,
                    embedding BLOB,
                    FOREIGN KEY (family_member_id) REFERENCES family_members (id)
                )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            raise

    def add_family_member(self, name, age, personal_info=None):
        """Add a new family member to the database."""
        try:
            self.cursor.execute('''
                INSERT INTO family_members (name, age, personal_info)
                VALUES (?, ?, ?)
            ''', (name, age, json.dumps(personal_info or {})))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        except sqlite3.Error as e:
            print(f"Error adding family member: {e}")
            return None

    def get_member_info(self, name):
        """Get family member information."""
        try:
            self.cursor.execute('''
                SELECT * FROM family_members 
                WHERE name = ?
            ''', (name,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error getting member info: {e}")
            return None

    def store_memory(self, family_member_name, text, category, importance=0.5):
        """Store a new memory entry in the database."""
        try:
            # Get family member ID
            self.cursor.execute('SELECT id FROM family_members WHERE name = ?', (family_member_name,))
            family_member_id = self.cursor.fetchone()
            
            if not family_member_id:
                raise ValueError(f"Family member {family_member_name} not found")
                
            family_member_id = family_member_id[0]
            
            # Store memory
            self.cursor.execute('''
                INSERT INTO memories (family_member_id, text, timestamp, category, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                family_member_id,
                text,
                datetime.now().isoformat(),
                category,
                importance
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error storing memory: {e}")
            return None

    def get_memories(self, family_member_name, limit=5):
        """Retrieve recent memories for a family member."""
        try:
            self.cursor.execute('''
                SELECT m.* FROM memories m
                JOIN family_members fm ON m.family_member_id = fm.id
                WHERE fm.name = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            ''', (family_member_name, limit))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving memories: {e}")
            return []

    def get_relevant_memories(self, name, categories, limit=2):
        """Get memories relevant to current categories."""
        try:
            placeholders = ','.join('?' * len(categories))
            query = f'''
                SELECT m.* FROM memories m
                JOIN family_members fm ON m.family_member_id = fm.id
                WHERE fm.name = ? 
                AND m.category IN ({placeholders})
                ORDER BY m.timestamp DESC, m.importance DESC
                LIMIT ?
            '''
            
            params = [name] + categories + [limit]
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving relevant memories: {e}")
            return []

    def get_member_categories(self, name):
        """Get all categories discussed with a family member."""
        try:
            self.cursor.execute('''
                SELECT DISTINCT category, COUNT(*) as count
                FROM memories m
                JOIN family_members fm ON m.family_member_id = fm.id
                WHERE fm.name = ?
                GROUP BY category
            ''', (name,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving member categories: {e}")
            return []

    def update_member_info(self, name, new_info):
        """Update a family member's personal information."""
        try:
            self.cursor.execute('''
                UPDATE family_members
                SET personal_info = ?
                WHERE name = ?
            ''', (json.dumps(new_info), name))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating member info: {e}")
            return False

    def delete_old_memories(self, days_old=30):
        """Delete memories older than specified days."""
        try:
            cutoff_date = (datetime.now() - datetime.timedelta(days=days_old)).isoformat()
            self.cursor.execute('''
                DELETE FROM memories
                WHERE timestamp < ?
            ''', (cutoff_date,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting old memories: {e}")
            return False

    def get_memory_stats(self, name):
        """Get statistics about stored memories for a family member."""
        try:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(importance) as avg_importance,
                    MAX(timestamp) as latest_interaction
                FROM memories m
                JOIN family_members fm ON m.family_member_id = fm.id
                WHERE fm.name = ?
            ''', (name,))
            result = self.cursor.fetchone()
            if not result or result[0] == 0:  # No memories found
                return (0, None, None)
            return result
        except sqlite3.Error as e:
            print(f"Error retrieving memory stats: {e}")
            return (0, None, None)

    def close_connection(self):
        """Properly close the database connection."""
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
                self.cursor = None
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.conn = None
        except sqlite3.Error as e:
            print(f"Error closing connection: {e}")

    def __enter__(self):
        """Context manager support."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when context ends."""
        self.close_connection()

    def __del__(self):
        """Ensure database connection is closed when object is destroyed."""
        try:
            self.close_connection()
        except:
            pass