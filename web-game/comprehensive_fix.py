#!/usr/bin/env python3
"""
Comprehensive fix for all remaining database connection issues
"""
import os
import re
import glob

def fix_all_database_connections():
    """Fix all database connection issues in all API files"""
    
    backend_dir = "backend/api"
    
    # Find all Python files in the API directory
    python_files = glob.glob(os.path.join(backend_dir, "*.py"))
    
    for filepath in python_files:
        if not os.path.exists(filepath):
            continue
            
        filename = os.path.basename(filepath)
        print(f"🔧 Fixing {filename}...")
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Skip if file doesn't have database connection issues
        if 'async with get_db_connection()' not in content:
            print(f"   ✅ {filename} - No issues found")
            continue
        
        # Fix the main database connection pattern
        original_content = content
        content = re.sub(
            r'async with get_db_connection\(\) as db:',
            'db = await get_db_connection()',
            content
        )
        
        # Fix indentation issues that result from the change
        lines = content.split('\n')
        fixed_lines = []
        in_db_function = False
        indent_level = 0
        
        for i, line in enumerate(lines):
            # Detect start of database function
            if 'db = await get_db_connection()' in line:
                in_db_function = True
                indent_level = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                continue
            
            # Detect end of function (new function definition or class)
            if in_db_function and (line.startswith('@') or line.startswith('def ') or line.startswith('async def ') or line.startswith('class ')):
                in_db_function = False
            
            # Fix indentation in database functions
            if in_db_function and line.strip():
                current_indent = len(line) - len(line.lstrip())
                # If line has more indentation than the db connection line, reduce it by 4 spaces
                if current_indent > indent_level:
                    new_indent = max(0, current_indent - 4)
                    line = ' ' * new_indent + line.lstrip()
                
            fixed_lines.append(line)
        
        # Write back the fixed content
        fixed_content = '\n'.join(fixed_lines)
        
        if fixed_content != original_content:
            with open(filepath, 'w') as f:
                f.write(fixed_content)
            print(f"   ✅ Fixed {filename}")
        else:
            print(f"   ✅ {filename} - No changes needed")

def main():
    print("🚀 Comprehensive Fix for All Database Connection Issues")
    print("=" * 60)
    
    # Change to the correct directory
    if os.path.exists('backend'):
        fix_all_database_connections()
        print("\n🎉 All database connection issues fixed!")
        print("Now restart the backend server.")
    else:
        print("❌ Backend directory not found. Make sure you're in the web-game directory.")

if __name__ == "__main__":
    main()
