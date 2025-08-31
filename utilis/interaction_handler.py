"""
Universal Interaction Handler for Discord Bot
Handles interaction timeouts, webhook token expiration, and other common interaction errors
"""

import discord
import logging
import asyncio
from typing import Optional, Union

class InteractionHandler:
    """Universal handler for Discord interactions with comprehensive error handling"""
    
    @staticmethod
    async def safe_response(
        interaction: discord.Interaction,
        embed: Optional[discord.Embed] = None,
        content: Optional[str] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False,
        delete_after: Optional[float] = None
    ) -> bool:
        """
        Safely respond to an interaction with comprehensive error handling
        Returns True if successful, False if failed
        """
        try:
            # Check if interaction is still valid
            if not interaction or not hasattr(interaction, 'response'):
                return False
            
            # Prepare kwargs
            kwargs = {}
            if embed is not None:
                kwargs['embed'] = embed
            if content is not None:
                kwargs['content'] = content
            if view is not None:
                kwargs['view'] = view
            if ephemeral:
                kwargs['ephemeral'] = ephemeral

            # Try to respond based on interaction state
            if not interaction.response.is_done():
                # Response supports delete_after
                if delete_after is not None:
                    kwargs['delete_after'] = delete_after
                await interaction.response.send_message(**kwargs)
                return True
            else:
                # Followup doesn't support delete_after, handle it manually
                message = await interaction.followup.send(**kwargs)
                if delete_after is not None and message:
                    # Schedule manual deletion
                    import asyncio
                    async def delete_later():
                        await asyncio.sleep(delete_after)
                        try:
                            await message.delete()
                        except:
                            pass  # Ignore deletion errors
                    asyncio.create_task(delete_later())
                return True
                
        except discord.NotFound:
            # Interaction expired (10062 error)
            logging.warning(f"Interaction expired for user {interaction.user.id}")
            return False
        except discord.HTTPException as e:
            if e.code == 10062:  # Unknown interaction
                logging.warning(f"Unknown interaction error for user {interaction.user.id}")
            else:
                logging.error(f"HTTP Exception in interaction response: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in interaction response: {e}")
            return False
    
    @staticmethod
    async def safe_edit(
        interaction: discord.Interaction,
        embed: Optional[discord.Embed] = None,
        content: Optional[str] = None,
        view: Optional[discord.ui.View] = None
    ) -> bool:
        """
        Safely edit an interaction response with comprehensive error handling
        Returns True if successful, False if failed
        """
        try:
            # Check if interaction is still valid
            if not interaction or not hasattr(interaction, 'response'):
                return False
            
            # Prepare kwargs
            kwargs = {}
            if embed is not None:
                kwargs['embed'] = embed
            if content is not None:
                kwargs['content'] = content
            if view is not None:
                kwargs['view'] = view
            
            # Try to edit the original response
            await interaction.edit_original_response(**kwargs)
            return True
            
        except discord.NotFound:
            # Interaction expired or message not found
            logging.warning(f"Cannot edit interaction - expired or not found for user {interaction.user.id}")
            return False
        except discord.HTTPException as e:
            if e.code == 10062:  # Unknown interaction
                logging.warning(f"Unknown interaction error during edit for user {interaction.user.id}")
            else:
                logging.error(f"HTTP Exception in interaction edit: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in interaction edit: {e}")
            return False
    
    @staticmethod
    async def safe_defer(
        interaction: discord.Interaction,
        ephemeral: bool = False,
        thinking: bool = False
    ) -> bool:
        """
        Safely defer an interaction with error handling
        Returns True if successful, False if failed
        """
        try:
            # Check if interaction is still valid and not already responded
            if not interaction or not hasattr(interaction, 'response'):
                return False
            
            if interaction.response.is_done():
                return False  # Already responded
            
            await interaction.response.defer(ephemeral=ephemeral, thinking=thinking)
            return True
            
        except discord.NotFound:
            logging.warning(f"Cannot defer interaction - expired for user {interaction.user.id}")
            return False
        except discord.HTTPException as e:
            if e.code == 10062:  # Unknown interaction
                logging.warning(f"Unknown interaction error during defer for user {interaction.user.id}")
            else:
                logging.error(f"HTTP Exception in interaction defer: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in interaction defer: {e}")
            return False
    
    @staticmethod
    async def safe_followup(
        interaction: discord.Interaction,
        embed: Optional[discord.Embed] = None,
        content: Optional[str] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False
    ) -> bool:
        """
        Safely send a followup message with error handling
        Returns True if successful, False if failed
        """
        try:
            # Check if interaction is still valid
            if not interaction or not hasattr(interaction, 'followup'):
                return False
            
            # Prepare kwargs
            kwargs = {}
            if embed is not None:
                kwargs['embed'] = embed
            if content is not None:
                kwargs['content'] = content
            if view is not None:
                kwargs['view'] = view
            if ephemeral:
                kwargs['ephemeral'] = ephemeral
            
            await interaction.followup.send(**kwargs)
            return True
            
        except discord.NotFound:
            logging.warning(f"Cannot send followup - interaction expired for user {interaction.user.id}")
            return False
        except discord.HTTPException as e:
            if e.code == 10062:  # Unknown interaction
                logging.warning(f"Unknown interaction error during followup for user {interaction.user.id}")
            else:
                logging.error(f"HTTP Exception in interaction followup: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in interaction followup: {e}")
            return False
    
    @staticmethod
    async def handle_view_timeout(view: discord.ui.View, interaction: Optional[discord.Interaction] = None):
        """
        Handle view timeout gracefully
        """
        try:
            if hasattr(view, 'message') and view.message:
                # Try to edit the message to remove the view
                embed = view.message.embeds[0] if view.message.embeds else None
                if embed:
                    embed.set_footer(text="This interaction has timed out.")
                    embed.color = discord.Color.greyple()
                
                await view.message.edit(embed=embed, view=None)
            
        except (discord.NotFound, discord.HTTPException):
            # Message might be deleted or inaccessible
            pass
        except Exception as e:
            logging.error(f"Error handling view timeout: {e}")
    
    @staticmethod
    def create_timeout_embed(original_embed: Optional[discord.Embed] = None) -> discord.Embed:
        """
        Create a timeout embed based on original embed or create new one
        """
        if original_embed:
            embed = original_embed.copy()
            embed.set_footer(text="⏰ This interaction has timed out. Please run the command again.")
            embed.color = discord.Color.greyple()
        else:
            embed = discord.Embed(
                title="⏰ Interaction Timed Out",
                description="This interaction has expired. Please run the command again.",
                color=discord.Color.greyple()
            )
        
        return embed
    
    @staticmethod
    async def safe_message_edit(
        message: discord.Message,
        embed: Optional[discord.Embed] = None,
        content: Optional[str] = None,
        view: Optional[discord.ui.View] = None
    ) -> bool:
        """
        Safely edit a message with error handling
        Returns True if successful, False if failed
        """
        try:
            kwargs = {}
            if embed is not None:
                kwargs['embed'] = embed
            if content is not None:
                kwargs['content'] = content
            if view is not None:
                kwargs['view'] = view
            
            await message.edit(**kwargs)
            return True
            
        except (discord.NotFound, discord.HTTPException) as e:
            logging.warning(f"Cannot edit message: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error editing message: {e}")
            return False

# Decorator for automatic interaction error handling
def handle_interaction_errors(func):
    """
    Decorator to automatically handle interaction errors in command callbacks
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except discord.NotFound as e:
            if e.code == 10062:  # Unknown interaction
                logging.warning(f"Unknown interaction error in {func.__name__}")
            else:
                logging.error(f"NotFound error in {func.__name__}: {e}")
        except discord.HTTPException as e:
            logging.error(f"HTTP Exception in {func.__name__}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
    
    return wrapper
