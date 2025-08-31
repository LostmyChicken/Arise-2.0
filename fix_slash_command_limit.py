#!/usr/bin/env python3
"""
Fix slash command limit issues by converting hybrid commands to text commands
"""
import os
import re
import glob

def find_hybrid_commands():
    """Find all hybrid commands in the codebase"""
    print("🔍 Scanning for hybrid commands...")
    
    # Find all Python files in commands directory
    command_files = glob.glob("commands/*.py")
    
    hybrid_commands = []
    
    for file_path in command_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if '@commands.hybrid_command' in line:
                        # Get the command name
                        name_match = re.search(r'name=["\']([^"\']+)["\']', line)
                        command_name = name_match.group(1) if name_match else "unknown"
                        
                        hybrid_commands.append({
                            'file': file_path,
                            'line': i,
                            'command': command_name,
                            'full_line': line.strip()
                        })
        
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    return hybrid_commands

def fix_hybrid_command(file_path, line_num, original_line):
    """Fix a single hybrid command by converting to text command"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the hybrid command line
        for i, line in enumerate(lines):
            if i + 1 == line_num and '@commands.hybrid_command' in line:
                # Replace hybrid_command with command
                new_line = line.replace('@commands.hybrid_command', '@commands.command')
                lines[i] = new_line
                
                # Check if the next line has @app_commands.describe and remove it
                if i + 1 < len(lines) and '@app_commands.describe' in lines[i + 1]:
                    # Remove the app_commands.describe line
                    lines.pop(i + 1)
                
                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def check_app_commands_imports():
    """Check for unnecessary app_commands imports"""
    print("\n🔍 Checking for app_commands imports...")
    
    command_files = glob.glob("commands/*.py")
    files_with_app_commands = []
    
    for file_path in command_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check if file imports app_commands but doesn't use hybrid commands
                if 'from discord import app_commands' in content or 'import app_commands' in content:
                    if '@commands.hybrid_command' not in content and '@app_commands' not in content:
                        files_with_app_commands.append(file_path)
        
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
    
    return files_with_app_commands

def remove_unused_app_commands_imports(file_path):
    """Remove unused app_commands imports"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            # Skip app_commands import lines if they're not used
            if ('from discord import app_commands' in line or 
                'import app_commands' in line or
                ', app_commands' in line):
                # Check if it's part of a multi-import line
                if 'from discord import' in line and ', app_commands' in line:
                    # Remove just the app_commands part
                    new_line = line.replace(', app_commands', '').replace('app_commands, ', '')
                    new_lines.append(new_line)
                else:
                    # Skip the entire line
                    continue
            else:
                new_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing imports from {file_path}: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 Slash Command Limit Fix")
    print("=" * 40)
    
    # Step 1: Find all hybrid commands
    hybrid_commands = find_hybrid_commands()
    
    if not hybrid_commands:
        print("✅ No hybrid commands found!")
        return
    
    print(f"Found {len(hybrid_commands)} hybrid commands:")
    for cmd in hybrid_commands:
        print(f"  📁 {cmd['file']}:{cmd['line']} - {cmd['command']}")
    
    # Step 2: Ask for confirmation
    print(f"\n⚠️ This will convert {len(hybrid_commands)} hybrid commands to text-only commands.")
    print("This will remove slash command functionality but keep text commands working.")
    
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    # Step 3: Fix each hybrid command
    print(f"\n🔧 Converting hybrid commands to text commands...")
    fixed_count = 0
    
    for cmd in hybrid_commands:
        print(f"Fixing {cmd['file']}:{cmd['line']} - {cmd['command']}")
        if fix_hybrid_command(cmd['file'], cmd['line'], cmd['full_line']):
            fixed_count += 1
            print(f"  ✅ Fixed")
        else:
            print(f"  ❌ Failed")
    
    # Step 4: Check for unused app_commands imports
    unused_imports = check_app_commands_imports()
    if unused_imports:
        print(f"\n🧹 Cleaning up unused app_commands imports...")
        for file_path in unused_imports:
            print(f"Cleaning {file_path}")
            if remove_unused_app_commands_imports(file_path):
                print(f"  ✅ Cleaned")
            else:
                print(f"  ❌ Failed")
    
    # Step 5: Summary
    print(f"\n" + "=" * 40)
    print(f"🎉 Fix Complete!")
    print(f"✅ Fixed {fixed_count}/{len(hybrid_commands)} hybrid commands")
    print(f"✅ Cleaned {len(unused_imports)} files with unused imports")
    print(f"\n📋 What was changed:")
    print(f"  • @commands.hybrid_command → @commands.command")
    print(f"  • Removed @app_commands.describe decorators")
    print(f"  • Cleaned up unused imports")
    print(f"\n🎮 Commands now work as text-only (sl prefix)")
    print(f"🚀 Bot should start without CommandLimitReached errors")

if __name__ == "__main__":
    main()
