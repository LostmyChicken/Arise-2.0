#!/usr/bin/env python3
"""
Deep Database Analysis Script
Analyzes the actual content of large database fields to identify the real issue
"""

import sqlite3
import json
import sys
from collections import defaultdict

def format_size(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def analyze_large_fields():
    """Analyze which fields are actually taking up space"""
    print("🔍 DEEP DATABASE FIELD ANALYSIS")
    print("=" * 80)
    
    db_path = "new_player.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all columns in players table
    cursor.execute("PRAGMA table_info(players)")
    columns = cursor.fetchall()
    
    print(f"📋 Analyzing {len(columns)} columns in players table...")
    
    # Analyze each column
    field_sizes = {}
    
    for col_info in columns:
        col_name = col_info[1]  # Column name
        
        print(f"   🔍 Analyzing column: {col_name}")
        
        # Get total size of this column across all players
        cursor.execute(f"SELECT LENGTH({col_name}) FROM players WHERE {col_name} IS NOT NULL")
        sizes = cursor.fetchall()
        
        total_size = sum(size[0] for size in sizes if size[0])
        avg_size = total_size / len(sizes) if sizes else 0
        max_size = max((size[0] for size in sizes if size[0]), default=0)
        
        field_sizes[col_name] = {
            'total': total_size,
            'average': avg_size,
            'max': max_size,
            'count': len([s for s in sizes if s[0] and s[0] > 0])
        }
        
        if total_size > 1024 * 1024:  # > 1MB total
            print(f"      🚨 LARGE FIELD: {col_name}")
            print(f"         Total: {format_size(total_size)}")
            print(f"         Average: {format_size(avg_size)}")
            print(f"         Max: {format_size(max_size)}")
            print(f"         Non-null count: {field_sizes[col_name]['count']}")
    
    # Sort by total size
    sorted_fields = sorted(field_sizes.items(), key=lambda x: x[1]['total'], reverse=True)
    
    print(f"\n📊 TOP 10 LARGEST FIELDS BY TOTAL SIZE:")
    print("-" * 80)
    
    for i, (field_name, data) in enumerate(sorted_fields[:10], 1):
        print(f"{i:2}. {field_name:<20} Total: {format_size(data['total']):>12} "
              f"Avg: {format_size(data['average']):>10} Max: {format_size(data['max']):>10}")
    
    # Analyze specific large records
    print(f"\n🔍 ANALYZING LARGEST INDIVIDUAL RECORDS:")
    print("-" * 80)
    
    # Find players with largest total data
    cursor.execute("""
        SELECT id, 
               LENGTH(hunters) as hunters_size,
               LENGTH(inventory) as inventory_size,
               LENGTH(equipped) as equipped_size,
               LENGTH(hunters) + LENGTH(inventory) + LENGTH(equipped) as total_size
        FROM players 
        ORDER BY total_size DESC 
        LIMIT 10
    """)
    
    large_players = cursor.fetchall()
    
    for player_id, hunters_size, inventory_size, equipped_size, total_size in large_players:
        print(f"👤 Player {player_id}:")
        print(f"   Hunters: {format_size(hunters_size or 0)}")
        print(f"   Inventory: {format_size(inventory_size or 0)}")
        print(f"   Equipped: {format_size(equipped_size or 0)}")
        print(f"   Total: {format_size(total_size)}")
        
        # Analyze the content of the largest field
        if hunters_size and hunters_size > inventory_size and hunters_size > equipped_size:
            cursor.execute("SELECT hunters FROM players WHERE id = ?", (player_id,))
            hunters_data = cursor.fetchone()[0]
            if hunters_data:
                try:
                    hunters = json.loads(hunters_data)
                    print(f"   └─ Hunters count: {len(hunters) if isinstance(hunters, dict) else 'Invalid format'}")
                    if isinstance(hunters, dict) and len(hunters) > 0:
                        # Sample a hunter to see data structure
                        sample_hunter = next(iter(hunters.values()))
                        sample_size = len(json.dumps(sample_hunter))
                        print(f"   └─ Sample hunter size: {format_size(sample_size)}")
                except:
                    print(f"   └─ Invalid JSON in hunters field")
        
        elif inventory_size and inventory_size > hunters_size and inventory_size > equipped_size:
            cursor.execute("SELECT inventory FROM players WHERE id = ?", (player_id,))
            inventory_data = cursor.fetchone()[0]
            if inventory_data:
                try:
                    inventory = json.loads(inventory_data)
                    print(f"   └─ Inventory count: {len(inventory) if isinstance(inventory, dict) else 'Invalid format'}")
                    if isinstance(inventory, dict) and len(inventory) > 0:
                        # Sample an item to see data structure
                        sample_item = next(iter(inventory.values()))
                        sample_size = len(json.dumps(sample_item))
                        print(f"   └─ Sample item size: {format_size(sample_size)}")
                except:
                    print(f"   └─ Invalid JSON in inventory field")
        
        print()
    
    conn.close()
    
    return sorted_fields

def analyze_json_structure():
    """Analyze the structure of JSON fields to find inefficiencies"""
    print(f"\n🔬 JSON STRUCTURE ANALYSIS:")
    print("-" * 80)
    
    db_path = "new_player.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get a sample of large hunters data
    cursor.execute("""
        SELECT hunters FROM players 
        WHERE LENGTH(hunters) > 100000 
        ORDER BY LENGTH(hunters) DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result and result[0]:
        try:
            hunters = json.loads(result[0])
            print(f"📊 Sample large hunters data analysis:")
            print(f"   Total hunters: {len(hunters)}")
            
            if isinstance(hunters, dict) and len(hunters) > 0:
                # Analyze structure
                sample_hunter = next(iter(hunters.values()))
                print(f"   Sample hunter keys: {list(sample_hunter.keys()) if isinstance(sample_hunter, dict) else 'Not a dict'}")
                
                # Check for redundant data
                all_keys = set()
                for hunter in hunters.values():
                    if isinstance(hunter, dict):
                        all_keys.update(hunter.keys())
                
                print(f"   All hunter keys: {sorted(all_keys)}")
                
                # Check for very large individual values
                for hunter_id, hunter_data in list(hunters.items())[:5]:  # Check first 5
                    if isinstance(hunter_data, dict):
                        for key, value in hunter_data.items():
                            value_size = len(json.dumps(value))
                            if value_size > 1000:  # > 1KB
                                print(f"   🚨 Large value in hunter {hunter_id}, key '{key}': {format_size(value_size)}")
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"      Preview: {value[:100]}...")
        
        except Exception as e:
            print(f"   ❌ Error analyzing hunters JSON: {e}")
    
    # Same for inventory
    cursor.execute("""
        SELECT inventory FROM players 
        WHERE LENGTH(inventory) > 100000 
        ORDER BY LENGTH(inventory) DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result and result[0]:
        try:
            inventory = json.loads(result[0])
            print(f"\n📦 Sample large inventory data analysis:")
            print(f"   Total items: {len(inventory)}")
            
            if isinstance(inventory, dict) and len(inventory) > 0:
                # Check for redundant data
                sample_item = next(iter(inventory.values()))
                print(f"   Sample item keys: {list(sample_item.keys()) if isinstance(sample_item, dict) else 'Not a dict'}")
                
                # Check for very large individual values
                for item_id, item_data in list(inventory.items())[:5]:  # Check first 5
                    if isinstance(item_data, dict):
                        for key, value in item_data.items():
                            value_size = len(json.dumps(value))
                            if value_size > 1000:  # > 1KB
                                print(f"   🚨 Large value in item {item_id}, key '{key}': {format_size(value_size)}")
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"      Preview: {value[:100]}...")
        
        except Exception as e:
            print(f"   ❌ Error analyzing inventory JSON: {e}")
    
    conn.close()

def main():
    print("🔬 DEEP DATABASE ANALYSIS")
    print("🎯 Finding the real cause of 40GB database...")
    print("=" * 80)
    
    # Analyze field sizes
    sorted_fields = analyze_large_fields()
    
    # Analyze JSON structure
    analyze_json_structure()
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 80)
    
    # Generate specific recommendations based on findings
    total_db_size = 40.17 * 1024 * 1024 * 1024  # 40.17 GB in bytes
    
    if sorted_fields:
        largest_field = sorted_fields[0]
        field_name, field_data = largest_field
        
        if field_data['total'] > total_db_size * 0.5:  # If one field is >50% of database
            print(f"🚨 CRITICAL: '{field_name}' field is taking up {format_size(field_data['total'])}")
            print(f"   This is {(field_data['total'] / total_db_size * 100):.1f}% of the total database!")
            print(f"   Average size per record: {format_size(field_data['average'])}")
            print(f"   Recommendations:")
            print(f"   • Investigate data structure in '{field_name}' field")
            print(f"   • Look for redundant or inefficient data storage")
            print(f"   • Consider data normalization or compression")
            print(f"   • Check for corrupted or malformed JSON data")
    
    print(f"\n🔧 NEXT STEPS:")
    print(f"   1. Focus on the largest fields identified above")
    print(f"   2. Check for data corruption or malformed JSON")
    print(f"   3. Consider implementing data compression")
    print(f"   4. Look into database schema optimization")

if __name__ == "__main__":
    main()
