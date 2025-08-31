#!/usr/bin/env python3
"""
Script to generate a list of all servers the bot is in with invite links.
This is a standalone script that can be run to get server information.
"""

import asyncio
import discord
import os
from datetime import datetime

# Bot token from environment
TOKEN = os.getenv("DISCORD_TOKEN")

class ServerListBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        
        await self.generate_server_list()
        await self.close()

    async def generate_server_list(self):
        """Generate a comprehensive server list with invite links"""
        server_info = []
        total_members = 0
        
        print(f"Scanning {len(self.guilds)} servers...")
        
        for guild in self.guilds:
            try:
                # Try to create an invite
                invite_url = "No invite available"
                
                # Find a suitable channel to create invite from
                invite_channel = None
                
                # Prefer general channels
                for channel in guild.text_channels:
                    if any(name in channel.name.lower() for name in ['general', 'main', 'chat', 'welcome']):
                        if channel.permissions_for(guild.me).create_instant_invite:
                            invite_channel = channel
                            break
                
                # Fallback to first available channel
                if not invite_channel:
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).create_instant_invite:
                            invite_channel = channel
                            break
                
                # Create the invite
                if invite_channel:
                    try:
                        invite = await invite_channel.create_invite(
                            max_age=0,  # Never expires
                            max_uses=0,  # Unlimited uses
                            unique=False,  # Don't create unique invite
                            reason="Admin server list generation"
                        )
                        invite_url = invite.url
                    except Exception as e:
                        invite_url = f"Failed to create invite: {str(e)[:50]}"
                
                server_info.append({
                    'name': guild.name,
                    'id': guild.id,
                    'members': guild.member_count or 0,
                    'invite': invite_url,
                    'owner': str(guild.owner) if guild.owner else "Unknown",
                    'created': guild.created_at.strftime("%Y-%m-%d"),
                    'channels': len(guild.channels),
                    'roles': len(guild.roles)
                })
                total_members += guild.member_count or 0
                
                print(f"✅ {guild.name} ({guild.member_count:,} members)")
                
            except Exception as e:
                server_info.append({
                    'name': guild.name,
                    'id': guild.id,
                    'members': guild.member_count or 0,
                    'invite': f"Error: {str(e)[:30]}",
                    'owner': "Unknown",
                    'created': "Unknown",
                    'channels': 0,
                    'roles': 0
                })
                print(f"❌ {guild.name} - Error: {e}")
        
        # Sort by member count (largest first)
        server_info.sort(key=lambda x: x['members'], reverse=True)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# 🌐 Bot Server List Report
**Generated**: {timestamp}
**Total Servers**: {len(server_info)}
**Total Members**: {total_members:,}

## 📊 Server Statistics
- **Largest Server**: {server_info[0]['name']} ({server_info[0]['members']:,} members)
- **Average Members**: {total_members // len(server_info):,} per server
- **Servers with 1000+ members**: {len([s for s in server_info if s['members'] >= 1000])}
- **Servers with 100+ members**: {len([s for s in server_info if s['members'] >= 100])}

## 🔗 Server List with Invite Links

"""
        
        for i, server in enumerate(server_info, 1):
            report += f"""
### {i}. {server['name']}
- **Server ID**: `{server['id']}`
- **Members**: {server['members']:,}
- **Owner**: {server['owner']}
- **Created**: {server['created']}
- **Channels**: {server['channels']} | **Roles**: {server['roles']}
- **Invite Link**: {server['invite']}

---
"""
        
        # Save to file
        filename = f"server_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {filename}")
        print(f"📊 Summary: {len(server_info)} servers, {total_members:,} total members")

async def main():
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN environment variable not set.")
        return
    
    client = ServerListBot()
    try:
        await client.start(TOKEN)
    except KeyboardInterrupt:
        print("\n⏹️ Script interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
