#!/usr/bin/env python3
"""
Check database columns for title system
"""
import sqlite3
import os

def check_database():
    """Check if database has title columns"""
    try:
        db_files = ['new_player.db', 'player.db']
        
        for db_file in db_files:
            if os.path.exists(db_file):
                print(f"Checking database: {db_file}")
                
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table schema
                cursor.execute("PRAGMA table_info(players)")
                columns = cursor.fetchall()
                
                column_names = [col[1] for col in columns]
                print(f"Total columns: {len(column_names)}")
                
                # Check for title columns
                has_titles = 'titles' in column_names
                has_active_title = 'active_title' in column_names
                
                print(f"Has 'titles' column: {has_titles}")
                print(f"Has 'active_title' column: {has_active_title}")
                
                if not has_titles or not has_active_title:
                    print("Adding missing title columns...")
                    
                    if not has_titles:
                        cursor.execute('ALTER TABLE players ADD COLUMN titles TEXT DEFAULT "{}"')
                        print("Added 'titles' column")
                    
                    if not has_active_title:
                        cursor.execute('ALTER TABLE players ADD COLUMN active_title TEXT DEFAULT NULL')
                        print("Added 'active_title' column")
                    
                    conn.commit()
                    print("Database updated!")
                else:
                    print("✅ All title columns present")
                
                conn.close()
                return True
        
        print("❌ No database files found")
        return False
        
    except Exception as e:
        print(f"❌ Database check error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database()
