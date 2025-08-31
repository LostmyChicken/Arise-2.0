#!/usr/bin/env python3
# Auto-generated data monitoring script
import os
import json
from datetime import datetime

def check_data_sizes():
    sizes = {}
    
    # Check database
    if os.path.exists('new_player.db'):
        sizes['database'] = os.path.getsize('new_player.db')
    
    # Check JSON files
    json_files = ['hunters.json', 'items.json', 'shadows.json', 'leaderboard.json']
    for filename in json_files:
        if os.path.exists(filename):
            sizes[filename] = os.path.getsize(filename)
    
    # Log sizes
    with open('data_size_log.json', 'a') as f:
        entry = {
            'timestamp': datetime.now().isoformat(),
            'sizes': sizes,
            'total': sum(sizes.values())
        }
        f.write(json.dumps(entry) + '\n')
    
    # Alert if total > 1GB
    total_size = sum(sizes.values())
    if total_size > 1024 * 1024 * 1024:
        print(f"⚠️  WARNING: Total data size is {total_size / 1024 / 1024 / 1024:.2f} GB")

if __name__ == "__main__":
    check_data_sizes()
