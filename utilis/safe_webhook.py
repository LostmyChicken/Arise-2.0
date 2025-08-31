"""
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
