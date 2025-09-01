#!/usr/bin/env python3
"""
Quick fix for database connection and indentation issues
"""
import os
import re

def fix_database_connections():
    """Fix all database connection issues in API files"""
    
    backend_dir = "backend/api"
    files_to_fix = [
        "arena.py",
        "gates.py", 
        "skills.py",
        "upgrade.py"
    ]
    
    for filename in files_to_fix:
        filepath = os.path.join(backend_dir, filename)
        if not os.path.exists(filepath):
            continue
            
        print(f"🔧 Fixing {filename}...")
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Fix the main database connection pattern
        content = re.sub(
            r'async with get_db_connection\(\) as db:',
            'db = await get_db_connection()',
            content
        )
        
        # Fix indentation issues - find functions with wrong indentation after db connection
        lines = content.split('\n')
        fixed_lines = []
        in_db_function = False
        
        for i, line in enumerate(lines):
            # Detect start of database function
            if 'db = await get_db_connection()' in line:
                in_db_function = True
                fixed_lines.append(line)
                continue
            
            # Detect end of function
            if in_db_function and line.startswith('@router') or line.startswith('def ') or line.startswith('async def '):
                in_db_function = False
            
            # Fix indentation in database functions
            if in_db_function and line.strip():
                # If line starts with more than 4 spaces of indentation, reduce it
                if line.startswith('        '):  # 8+ spaces
                    line = '    ' + line.lstrip()
                elif line.startswith('    ') and not line.startswith('    #') and not line.startswith('    """'):
                    # Keep 4 spaces for normal function content
                    pass
                
            fixed_lines.append(line)
        
        # Write back the fixed content
        with open(filepath, 'w') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"✅ Fixed {filename}")

def main():
    print("🚀 Quick Fix for Database Connection Issues")
    print("=" * 50)
    
    # Change to the correct directory
    if os.path.exists('backend'):
        fix_database_connections()
        print("\n🎉 All database connection issues fixed!")
        print("Now restart the backend server.")
    else:
        print("❌ Backend directory not found. Make sure you're in the web-game directory.")

if __name__ == "__main__":
    main()
