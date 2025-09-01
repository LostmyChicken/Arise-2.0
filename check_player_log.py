#!/usr/bin/env python3
"""
Script to check the command log for player ID 846543765476343828
"""

import os
from datetime import datetime

def check_player_log(player_id=846543765476343828):
    """Check command log for specific player"""
    
    log_file = "player_command_log.txt"
    
    print(f"🔍 Checking command log for player ID: {player_id}")
    print("=" * 60)
    
    if not os.path.exists(log_file):
        print("❌ No log file found. Player hasn't used any commands yet.")
        print(f"📝 Log file will be created at: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Filter lines for the specific player
        player_lines = []
        for line in lines:
            if str(player_id) in line:
                player_lines.append(line.strip())
        
        if not player_lines:
            print(f"❌ No commands found for player {player_id}")
            print(f"📊 Total log entries: {len(lines)}")
            return
        
        print(f"✅ Found {len(player_lines)} commands for player {player_id}")
        print(f"📊 Total log entries: {len(lines)}")
        print("\n📝 Recent Commands (last 20):")
        print("-" * 60)
        
        # Show last 20 commands
        recent_commands = player_lines[-20:] if len(player_lines) > 20 else player_lines
        
        for i, command in enumerate(recent_commands, 1):
            print(f"{i:2d}. {command}")
        
        if len(player_lines) > 20:
            print(f"\n... and {len(player_lines) - 20} more commands")
        
        # Generate summary
        print("\n📊 Command Summary:")
        print("-" * 30)
        
        # Count commands by type
        command_counts = {}
        server_counts = {}
        
        for line in player_lines:
            try:
                # Extract command name (between 'command '' and next ')
                if "command '" in line and "' in server" in line:
                    cmd_start = line.find("command '") + 9
                    cmd_end = line.find("'", cmd_start)
                    command = line[cmd_start:cmd_end]
                    command_counts[command] = command_counts.get(command, 0) + 1
                
                # Extract server name
                if "' in server '" in line:
                    server_start = line.find("' in server '") + 13
                    server_end = line.find("'", server_start)
                    server = line[server_start:server_end]
                    server_counts[server] = server_counts.get(server, 0) + 1
            except:
                continue
        
        # Show top commands
        if command_counts:
            print("🎯 Most Used Commands:")
            sorted_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
            for cmd, count in sorted_commands[:10]:
                print(f"   {cmd}: {count} times")
        
        # Show servers
        if server_counts:
            print("\n🌐 Servers Used:")
            sorted_servers = sorted(server_counts.items(), key=lambda x: x[1], reverse=True)
            for server, count in sorted_servers[:5]:
                print(f"   {server}: {count} commands")
        
        # Show time range
        if len(player_lines) >= 2:
            try:
                first_line = player_lines[0]
                last_line = player_lines[-1]
                
                # Extract timestamps
                first_time = first_line[1:20]  # [YYYY-MM-DD HH:MM:SS]
                last_time = last_line[1:20]
                
                print(f"\n⏰ Time Range:")
                print(f"   First command: {first_time}")
                print(f"   Last command:  {last_time}")
            except:
                pass
        
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def main():
    print("🔍 Player Command Log Checker")
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_player_log()
    
    print("\n" + "=" * 60)
    print("💡 Tips:")
    print("- Log file is updated in real-time as the player uses commands")
    print("- Use 'sl player_log' command in Discord for live updates")
    print("- Admin-only commands are available in the bot")

if __name__ == "__main__":
    main()
