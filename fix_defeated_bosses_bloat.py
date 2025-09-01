#!/usr/bin/env python3
"""
Fix Defeated Bosses Bloat Issue
The defeated_bosses field is taking up 40.12 GB (99.9% of database)
This script will clean up this field and optimize the data structure
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime

def format_size(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def backup_database():
    """Create backup before making changes"""
    print("💾 Creating backup before defeated_bosses cleanup...")
    
    db_path = "new_player.db"
    backup_path = f"new_player_before_bosses_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    shutil.copy2(db_path, backup_path)
    
    original_size = os.path.getsize(db_path)
    print(f"✅ Backup created: {backup_path}")
    print(f"📊 Original size: {format_size(original_size)}")
    
    return backup_path

def analyze_defeated_bosses_data():
    """Analyze the defeated_bosses field to understand the data structure"""
    print("\n🔍 Analyzing defeated_bosses data structure...")
    
    db_path = "new_player.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get sample of defeated_bosses data
    cursor.execute("""
        SELECT id, LENGTH(defeated_bosses) as size, defeated_bosses 
        FROM players 
        WHERE defeated_bosses IS NOT NULL AND LENGTH(defeated_bosses) > 1000
        ORDER BY size DESC 
        LIMIT 5
    """)
    
    samples = cursor.fetchall()
    
    print(f"📊 Found {len(samples)} players with large defeated_bosses data:")
    
    for player_id, size, data in samples:
        print(f"\n👤 Player {player_id}: {format_size(size)}")
        
        try:
            bosses_data = json.loads(data)
            
            if isinstance(bosses_data, dict):
                print(f"   📋 Boss entries: {len(bosses_data)}")
                
                # Analyze structure
                if len(bosses_data) > 0:
                    sample_boss = next(iter(bosses_data.values()))
                    print(f"   🔍 Sample boss data structure:")
                    
                    if isinstance(sample_boss, dict):
                        for key, value in sample_boss.items():
                            value_size = len(json.dumps(value))
                            print(f"      {key}: {format_size(value_size)}")
                            
                            # If it's a very large field, show preview
                            if value_size > 10000:  # > 10KB
                                print(f"         🚨 LARGE FIELD: {key}")
                                if isinstance(value, str):
                                    print(f"         Preview: {value[:200]}...")
                                elif isinstance(value, list):
                                    print(f"         List length: {len(value)}")
                                    if len(value) > 0:
                                        print(f"         Sample item: {str(value[0])[:100]}...")
                    else:
                        print(f"   ⚠️  Sample boss is not a dict: {type(sample_boss)}")
            
            elif isinstance(bosses_data, list):
                print(f"   📋 Boss list length: {len(bosses_data)}")
                if len(bosses_data) > 0:
                    sample_boss = bosses_data[0]
                    print(f"   🔍 Sample boss: {str(sample_boss)[:200]}...")
            
            else:
                print(f"   ⚠️  Unexpected data type: {type(bosses_data)}")
        
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"   ❌ Error analyzing data: {e}")
    
    conn.close()
    return samples

def clean_defeated_bosses_data():
    """Clean up the defeated_bosses field to reduce size"""
    print("\n🧹 Cleaning defeated_bosses data...")
    
    db_path = "new_player.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all players with defeated_bosses data
    cursor.execute("SELECT id, defeated_bosses FROM players WHERE defeated_bosses IS NOT NULL")
    players = cursor.fetchall()
    
    print(f"📊 Processing {len(players)} players with defeated_bosses data...")
    
    total_saved = 0
    processed = 0
    
    for player_id, bosses_data in players:
        try:
            original_size = len(bosses_data)
            
            # Parse the JSON
            bosses = json.loads(bosses_data)
            
            # Clean up the data based on structure
            cleaned_bosses = None
            
            if isinstance(bosses, dict):
                # If it's a dict, keep only essential information
                cleaned_bosses = {}
                
                for boss_id, boss_data in bosses.items():
                    if isinstance(boss_data, dict):
                        # Keep only essential fields, remove redundant data
                        essential_data = {}
                        
                        # Keep basic info
                        for key in ['defeated', 'count', 'level', 'last_defeated']:
                            if key in boss_data:
                                essential_data[key] = boss_data[key]
                        
                        # If there's a defeats list, keep only the count
                        if 'defeats' in boss_data and isinstance(boss_data['defeats'], list):
                            essential_data['count'] = len(boss_data['defeats'])
                            # Don't store the full defeats list
                        
                        # Remove any very large fields that might be logs or detailed data
                        for key, value in boss_data.items():
                            if key not in essential_data:
                                value_size = len(json.dumps(value))
                                if value_size < 1000:  # Only keep small additional fields
                                    essential_data[key] = value
                        
                        if essential_data:  # Only add if there's data to keep
                            cleaned_bosses[boss_id] = essential_data
                    
                    else:
                        # If boss_data is not a dict, keep it as is (might be just a count)
                        cleaned_bosses[boss_id] = boss_data
            
            elif isinstance(bosses, list):
                # If it's a list, convert to a more efficient format
                cleaned_bosses = {}
                for i, boss_entry in enumerate(bosses):
                    if isinstance(boss_entry, dict) and 'id' in boss_entry:
                        boss_id = boss_entry['id']
                        cleaned_bosses[boss_id] = {
                            'defeated': True,
                            'count': boss_entry.get('count', 1)
                        }
                    else:
                        # Keep as simplified entry
                        cleaned_bosses[f"boss_{i}"] = boss_entry
            
            else:
                # If it's neither dict nor list, reset to empty
                cleaned_bosses = {}
            
            # Convert back to JSON
            cleaned_json = json.dumps(cleaned_bosses)
            new_size = len(cleaned_json)
            
            # Update database if there's a significant size reduction
            if new_size < original_size * 0.8:  # If new size is less than 80% of original
                cursor.execute("UPDATE players SET defeated_bosses = ? WHERE id = ?", 
                             (cleaned_json, player_id))
                
                saved = original_size - new_size
                total_saved += saved
                
                if saved > 1024 * 1024:  # > 1MB saved
                    print(f"   👤 Player {player_id}: {format_size(original_size)} → {format_size(new_size)} (saved {format_size(saved)})")
            
            processed += 1
            
            if processed % 100 == 0:
                print(f"   📊 Processed {processed}/{len(players)} players...")
        
        except json.JSONDecodeError:
            # If JSON is invalid, reset to empty
            cursor.execute("UPDATE players SET defeated_bosses = ? WHERE id = ?", ('{}', player_id))
            total_saved += len(bosses_data)
            print(f"   🔧 Reset invalid JSON for player {player_id}")
        
        except Exception as e:
            print(f"   ❌ Error processing player {player_id}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"✅ Defeated bosses cleanup complete!")
    print(f"📊 Total space saved: {format_size(total_saved)}")
    print(f"📊 Players processed: {processed}")
    
    return total_saved

def vacuum_database():
    """Vacuum database to reclaim space"""
    print("\n🧹 Vacuuming database to reclaim space...")
    
    db_path = "new_player.db"
    
    size_before = os.path.getsize(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.execute("VACUUM")
    conn.close()
    
    size_after = os.path.getsize(db_path)
    saved = size_before - size_after
    
    print(f"✅ Database vacuum complete!")
    print(f"📊 Size before: {format_size(size_before)}")
    print(f"📊 Size after: {format_size(size_after)}")
    print(f"💾 Space reclaimed: {format_size(saved)}")
    
    return saved

def main():
    print("🔧 DEFEATED BOSSES BLOAT FIX")
    print("🎯 Fixing the 40.12 GB defeated_bosses field issue...")
    print("=" * 80)
    
    # Step 1: Backup
    backup_path = backup_database()
    
    # Step 2: Analyze current data
    samples = analyze_defeated_bosses_data()
    
    # Step 3: Clean up the data
    cleanup_saved = clean_defeated_bosses_data()
    
    # Step 4: Vacuum to reclaim space
    vacuum_saved = vacuum_database()
    
    # Final results
    final_size = os.path.getsize("new_player.db")
    
    print(f"\n🎉 DEFEATED BOSSES FIX COMPLETE!")
    print("=" * 80)
    print(f"📊 Final Results:")
    print(f"   Backup created: {backup_path}")
    print(f"   Data cleanup saved: {format_size(cleanup_saved)}")
    print(f"   Vacuum reclaimed: {format_size(vacuum_saved)}")
    print(f"   Final database size: {format_size(final_size)}")
    print(f"   Total reduction: {format_size(cleanup_saved + vacuum_saved)}")
    
    if final_size < 1024 * 1024 * 1024:  # < 1GB
        print(f"✅ SUCCESS: Database is now under 1GB!")
    elif final_size < 5 * 1024 * 1024 * 1024:  # < 5GB
        print(f"✅ GOOD: Significant size reduction achieved!")
    else:
        print(f"⚠️  Database is still large. May need additional cleanup.")
    
    print(f"\n💡 Next Steps:")
    print(f"   • Restart your bot to use the optimized database")
    print(f"   • Monitor the defeated_bosses field to prevent future bloat")
    print(f"   • Consider implementing more efficient boss tracking")

if __name__ == "__main__":
    main()
