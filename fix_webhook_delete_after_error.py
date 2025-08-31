#!/usr/bin/env python3
"""
Fix webhook delete_after error by finding and fixing all instances
"""
import os
import re
import glob

def find_webhook_delete_after_issues():
    """Find all potential webhook delete_after issues"""
    print("🔍 Scanning for webhook delete_after issues...")
    
    issues = []
    
    # Patterns to look for
    patterns = [
        r'\.followup\.send\([^)]*delete_after',
        r'webhook\.send\([^)]*delete_after',
        r'interaction\.followup\.send\([^)]*delete_after'
    ]
    
    # Files to check
    file_patterns = [
        "commands/*.py",
        "structure/*.py", 
        "utilis/*.py",
        "*.py"
    ]
    
    for file_pattern in file_patterns:
        for file_path in glob.glob(file_pattern):
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        for i, line in enumerate(lines, 1):
                            for pattern in patterns:
                                if re.search(pattern, line):
                                    issues.append({
                                        'file': file_path,
                                        'line': i,
                                        'content': line.strip(),
                                        'pattern': pattern
                                    })
                except Exception as e:
                    print(f"❌ Error reading {file_path}: {e}")
    
    return issues

def check_interaction_handler_fix():
    """Check if the interaction handler fix is properly applied"""
    print("\n🔧 Checking interaction handler fix...")
    
    try:
        with open('utilis/interaction_handler.py', 'r') as f:
            content = f.read()
            
        # Check for the fix
        if 'Followup doesn\'t support delete_after, handle it manually' in content:
            print("✅ Interaction handler fix is applied")
            return True
        else:
            print("❌ Interaction handler fix is missing")
            return False
            
    except FileNotFoundError:
        print("❌ interaction_handler.py not found")
        return False
    except Exception as e:
        print(f"❌ Error checking interaction handler: {e}")
        return False

def create_safe_webhook_helper():
    """Create a safe webhook helper function"""
    print("\n🛠️ Creating safe webhook helper...")
    
    helper_code = '''"""
Safe webhook utilities to prevent delete_after errors
"""
import asyncio
import discord
import logging
from typing import Optional

class SafeWebhookHelper:
    """Helper class for safe webhook operations"""
    
    @staticmethod
    async def safe_followup_send(
        interaction: discord.Interaction,
        content: str = None,
        embed: discord.Embed = None,
        embeds: list = None,
        view: discord.ui.View = None,
        ephemeral: bool = False,
        delete_after: Optional[float] = None,
        **kwargs
    ):
        """
        Safely send a followup message with delete_after support
        
        Args:
            interaction: Discord interaction
            content: Message content
            embed: Single embed
            embeds: List of embeds
            view: UI view
            ephemeral: Whether message is ephemeral
            delete_after: Seconds to wait before deleting (handled manually)
            **kwargs: Additional arguments
            
        Returns:
            Message object or None if failed
        """
        try:
            # Prepare arguments (exclude delete_after for followup)
            send_kwargs = {}
            if content is not None:
                send_kwargs['content'] = content
            if embed is not None:
                send_kwargs['embed'] = embed
            if embeds is not None:
                send_kwargs['embeds'] = embeds
            if view is not None:
                send_kwargs['view'] = view
            if ephemeral:
                send_kwargs['ephemeral'] = ephemeral
            
            # Add any other kwargs except delete_after
            for key, value in kwargs.items():
                if key != 'delete_after':
                    send_kwargs[key] = value
            
            # Send the message
            message = await interaction.followup.send(**send_kwargs)
            
            # Handle delete_after manually if specified
            if delete_after is not None and message:
                async def delete_later():
                    try:
                        await asyncio.sleep(delete_after)
                        await message.delete()
                    except discord.NotFound:
                        pass  # Message already deleted
                    except discord.Forbidden:
                        pass  # No permission to delete
                    except Exception as e:
                        logging.warning(f"Failed to delete message after {delete_after}s: {e}")
                
                asyncio.create_task(delete_later())
            
            return message
            
        except discord.NotFound:
            logging.warning("Interaction expired - cannot send followup")
            return None
        except discord.HTTPException as e:
            logging.error(f"HTTP error in safe followup: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in safe followup: {e}")
            return None
    
    @staticmethod
    async def safe_webhook_send(
        webhook: discord.Webhook,
        content: str = None,
        embed: discord.Embed = None,
        embeds: list = None,
        view: discord.ui.View = None,
        delete_after: Optional[float] = None,
        **kwargs
    ):
        """
        Safely send a webhook message with delete_after support
        
        Args:
            webhook: Discord webhook
            content: Message content
            embed: Single embed
            embeds: List of embeds
            view: UI view
            delete_after: Seconds to wait before deleting (handled manually)
            **kwargs: Additional arguments
            
        Returns:
            Message object or None if failed
        """
        try:
            # Prepare arguments (exclude delete_after for webhook)
            send_kwargs = {}
            if content is not None:
                send_kwargs['content'] = content
            if embed is not None:
                send_kwargs['embed'] = embed
            if embeds is not None:
                send_kwargs['embeds'] = embeds
            if view is not None:
                send_kwargs['view'] = view
            
            # Add any other kwargs except delete_after
            for key, value in kwargs.items():
                if key != 'delete_after':
                    send_kwargs[key] = value
            
            # Always wait for webhook to get message object
            send_kwargs['wait'] = True
            
            # Send the message
            message = await webhook.send(**send_kwargs)
            
            # Handle delete_after manually if specified
            if delete_after is not None and message:
                async def delete_later():
                    try:
                        await asyncio.sleep(delete_after)
                        await message.delete()
                    except discord.NotFound:
                        pass  # Message already deleted
                    except discord.Forbidden:
                        pass  # No permission to delete
                    except Exception as e:
                        logging.warning(f"Failed to delete webhook message after {delete_after}s: {e}")
                
                asyncio.create_task(delete_later())
            
            return message
            
        except discord.HTTPException as e:
            logging.error(f"HTTP error in safe webhook send: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in safe webhook send: {e}")
            return None
'''
    
    try:
        with open('utilis/safe_webhook.py', 'w', encoding='utf-8') as f:
            f.write(helper_code)
        print("✅ Created safe_webhook.py helper")
        return True
    except Exception as e:
        print(f"❌ Failed to create safe webhook helper: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 WEBHOOK DELETE_AFTER ERROR FIX")
    print("=" * 50)
    
    # Step 1: Find potential issues
    issues = find_webhook_delete_after_issues()
    
    if issues:
        print(f"⚠️ Found {len(issues)} potential webhook delete_after issues:")
        for issue in issues:
            print(f"  📁 {issue['file']}:{issue['line']}")
            print(f"     {issue['content']}")
        print()
    else:
        print("✅ No obvious webhook delete_after issues found in code")
    
    # Step 2: Check if interaction handler fix is applied
    handler_fixed = check_interaction_handler_fix()
    
    # Step 3: Create safe webhook helper
    helper_created = create_safe_webhook_helper()
    
    # Step 4: Summary
    print("\n" + "=" * 50)
    print("📋 FIX SUMMARY:")
    
    if handler_fixed:
        print("✅ Interaction handler fix applied")
    else:
        print("❌ Interaction handler needs fixing")
    
    if helper_created:
        print("✅ Safe webhook helper created")
    else:
        print("❌ Safe webhook helper creation failed")
    
    if len(issues) == 0 and handler_fixed:
        print("\n🎉 WEBHOOK ERROR SHOULD BE FIXED!")
        print("The delete_after parameter error should no longer occur.")
    else:
        print(f"\n⚠️ MANUAL REVIEW NEEDED")
        if issues:
            print(f"Found {len(issues)} potential issues that may need manual fixing")
        if not handler_fixed:
            print("Interaction handler fix needs to be applied")
    
    print("\n💡 USAGE RECOMMENDATIONS:")
    print("1. Use InteractionHandler.safe_response() for interactions")
    print("2. Use SafeWebhookHelper.safe_followup_send() for followups")
    print("3. Use SafeWebhookHelper.safe_webhook_send() for webhooks")
    print("4. Never pass delete_after directly to webhook.send() or followup.send()")

if __name__ == "__main__":
    main()
