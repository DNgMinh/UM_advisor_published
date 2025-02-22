import sqlite3

class SQLitePageStore:
    def __init__(self, db_file: str = "pages.db", table_name: str = "pages"):
        self.db_file = db_file
        self.table_name = table_name
        self._db_initialized = False    # False if not initialized

    def _initialize_db(self):
        """Initialize the SQLite database to store page content."""
        if self._db_initialized:
            return

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create table to store page number and content
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        self._db_initialized = True

    def save_pages(self, documents, source_file):
        """Save extracted pages to the database."""
        self._initialize_db()
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        for i, doc in enumerate(documents, 1):
            cursor.execute(f'''
                INSERT INTO {self.table_name} (page_number, content, source_file)
                VALUES (?, ?, ?)
            ''', (i, doc.page_content, source_file))

        conn.commit()
        conn.close()

    def get_page_content(self, page_number: int, source_file: str) -> str:
        """Get content for a specific page from a specific source PDF."""

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Query the page content from the specified source file and page number
        cursor.execute(f'''
            SELECT content FROM {self.table_name} 
            WHERE page_number = ? AND source_file = ?
        ''', (page_number, source_file))

        # Fetch result and handle if no content is found
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]  # Return the content of the page
        else:
            return None  # No page found with the given parameters
        

    def remove_source(self, source_file: str) -> None:
        """Remove all pages from a specific source."""
        self._initialize_db()
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Remove documents
        cursor.execute(f'''
            DELETE FROM {self.table_name}
            WHERE source_file = ?
        ''', (source_file,))

        conn.commit()
        conn.close()