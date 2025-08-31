import discord
from discord.ext import commands
from discord import app_commands, ui
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.emoji import getEmoji
from structure.player import Player
from utilis.utilis import create_embed, INFO_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR

class SacrificeQuantityModal(ui.Modal):
    def __init__(self, item_type: str, item_id: str, item_name: str, max_quantity: int, sacrifice_cog):
        super().__init__(title=f"Sacrifice {item_name}")
        self.item_type = item_type
        self.item_id = item_id
        self.item_name = item_name
        self.max_quantity = max_quantity
        self.sacrifice_cog = sacrifice_cog

        self.quantity_input = ui.TextInput(
            label="Quantity to Sacrifice",
            placeholder=f"Enter a number (max: {max_quantity})",
            required=True,
            min_length=1,
            max_length=len(str(max_quantity))
        )
        self.add_item(self.quantity_input)

    async def on_submit(self, interaction: discord.Interaction):
        quantity_str = self.quantity_input.value
        try:
            quantity = int(quantity_str)
            if not (1 <= quantity <= self.max_quantity):
                raise ValueError
        except ValueError:
            embed = create_embed("Invalid Quantity", f"Please enter a valid number between 1 and {self.max_quantity}.", ERROR_COLOR, interaction.user)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.sacrifice_cog.perform_sacrifice(interaction, self.item_type, self.item_id, self.item_name, quantity)

class SacrificeItemSelect(ui.Select):
    def __init__(self, author: discord.User, item_type: str, sacrifice_cog):
        self.author = author
        self.item_type = item_type
        self.sacrifice_cog = sacrifice_cog
        super().__init__(placeholder=f'Select a {item_type} to sacrifice...', min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        item_id = self.values[0]
        player = await Player.get(self.author.id)

        is_hunter = self.item_type == 'hunter'
        item_obj = await (HeroManager.get(item_id) if is_hunter else ItemManager.get(item_id))

        if is_hunter:
            # For hunters, get from hunters inventory
            inventory = player.get_hunters()
            item_data = inventory.get(item_id)

            # Safely get quantity regardless of data format
            quantity = 0
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', 1)
            elif isinstance(item_data, int):
                quantity = item_data

            # The number of sacrificable shards is the total quantity minus the base item
            max_quantity = quantity - 1
        else:
            # For items, get shard quantity from inventory
            inventory = player.get_inventory()
            shard_id = f"s_{item_id}"
            item_data = inventory.get(shard_id)

            # Safely get quantity regardless of data format
            quantity = 0
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', 0)
            elif isinstance(item_data, int):
                quantity = item_data

            # For shards, we can sacrifice all of them
            max_quantity = quantity

        modal = SacrificeQuantityModal(self.item_type, item_id, item_obj.name, max_quantity, self.sacrifice_cog)
        await interaction.response.send_modal(modal)

class SacrificeItemSelectView(ui.View):
    def __init__(self, author: discord.User, item_type: str, sacrifice_cog):
        super().__init__(timeout=180)
        self.author = author
        self.item_type = item_type
        self.sacrifice_cog = sacrifice_cog
        self.select_menu = SacrificeItemSelect(author, item_type, sacrifice_cog)
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return False
        return True

    async def populate_items(self):
        player = await Player.get(self.author.id)
        is_hunter = self.item_type == 'hunter'

        options = []

        if is_hunter:
            # For hunters, check hunters inventory for duplicates (quantity > 1)
            inventory = player.get_hunters()
            for item_id, data in inventory.items():
                # Safely check quantity for both old (int) and new (dict) formats
                quantity = 0
                if isinstance(data, dict):
                    quantity = data.get('quantity', 1)
                elif isinstance(data, int):
                    quantity = data

                if quantity > 1:
                    item_obj = await HeroManager.get(item_id)
                    if item_obj:
                        emoji_str = getEmoji(item_obj.id)
                        shard_count = quantity - 1
                        options.append(discord.SelectOption(
                            label=f"{item_obj.name} (Shards: {shard_count})",
                            value=item_obj.id,
                            emoji=emoji_str
                        ))
        else:
            # For items, check inventory for shards (items starting with 's_')
            inventory = player.get_inventory()
            for item_id, data in inventory.items():
                if item_id.startswith('s_'):  # This is a shard
                    # Get the actual item ID (remove 's_' prefix)
                    actual_item_id = item_id[2:]

                    # Safely check quantity for both old (int) and new (dict) formats
                    quantity = 0
                    if isinstance(data, dict):
                        quantity = data.get('quantity', 0)
                    elif isinstance(data, int):
                        quantity = data

                    if quantity > 0:
                        item_obj = await ItemManager.get(actual_item_id)
                        if item_obj:
                            emoji_str = getEmoji(actual_item_id)
                            options.append(discord.SelectOption(
                                label=f"{item_obj.name} (Shards: {quantity})",
                                value=actual_item_id,
                                emoji=emoji_str
                            ))

        self.select_menu.options = options[:25] # Limit to 25 options per select menu

class SacrificeTypeSelectView(ui.View):
    def __init__(self, author: discord.User, sacrifice_cog):
        super().__init__(timeout=180)
        self.author = author
        self.sacrifice_cog = sacrifice_cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return False
        return True

    async def show_item_select(self, interaction: discord.Interaction, item_type: str):
        view = SacrificeItemSelectView(self.author, item_type, self.sacrifice_cog)
        await view.populate_items()

        if not view.select_menu.options:
            embed = create_embed(f"No {item_type} Shards", f"You don't have any surplus {item_type} shards to sacrifice.", ERROR_COLOR, self.author)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        embed = create_embed(f"Sacrifice {item_type.capitalize()} Shards", f"Select the {item_type} whose shards you want to sacrifice.", INFO_COLOR, self.author)
        await interaction.response.edit_message(embed=embed, view=view)

    @ui.button(label="Hunter Shards", style=discord.ButtonStyle.primary, emoji="👤")
    async def hunter_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_item_select(interaction, 'hunter')

    @ui.button(label="Weapon Shards", style=discord.ButtonStyle.secondary, emoji="🗡️")
    async def weapon_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_item_select(interaction, 'weapon')

class SacrificeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="sacrifice", aliases=["sac"], help="Interactively sacrifice hunter or weapon shards for elemental cubes.")
    async def sacrifice(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed("Not Registered", "You don't have a profile yet. Use `/start` to get started!", ERROR_COLOR, ctx.author)
            await ctx.send(embed=embed)
            return

        if player.trade:
            embed = create_embed("Trade in Progress", f"You are in the middle of a trade. Please complete or cancel it before sacrificing items.", WARNING_COLOR, ctx.author)
            await ctx.send(embed=embed)
            return

        embed = create_embed(
            title="Sacrifice System",
            description="What type of shards would you like to sacrifice?",
            color=INFO_COLOR,
            author=ctx.author
        )
        view = SacrificeTypeSelectView(ctx.author, self)
        await ctx.send(embed=embed, view=view)

    async def perform_sacrifice(self, interaction: discord.Interaction, item_type: str, item_id: str, item_name: str, quantity: int):
        player = await Player.get(interaction.user.id)
        is_hunter = item_type == 'hunter'

        if is_hunter:
            # For hunters, check hunters inventory
            inventory = player.get_hunters()
            item_data = inventory.get(item_id)
            item_obj = await HeroManager.get(item_id)

            # Safely get current quantity
            current_quantity = 0
            if isinstance(item_data, dict):
                current_quantity = item_data.get('quantity', 1)
            elif isinstance(item_data, int):
                current_quantity = item_data

            # Double-check server-side (need at least quantity + 1 to keep one)
            if current_quantity < quantity + 1:
                embed = create_embed("Not Enough Shards", f"You don't have enough shards of {item_name}. You tried to sacrifice {quantity} but only have {current_quantity - 1}.", ERROR_COLOR, interaction.user)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        else:
            # For items, check inventory for shards (with 's_' prefix)
            inventory = player.get_inventory()
            shard_id = f"s_{item_id}"
            item_data = inventory.get(shard_id)
            item_obj = await ItemManager.get(item_id)

            # Safely get current quantity
            current_quantity = 0
            if isinstance(item_data, dict):
                current_quantity = item_data.get('quantity', 0)
            elif isinstance(item_data, int):
                current_quantity = item_data

            # Double-check server-side (for shards, we can sacrifice all)
            if current_quantity < quantity:
                embed = create_embed("Not Enough Shards", f"You don't have enough shards of {item_name}. You tried to sacrifice {quantity} but only have {current_quantity}.", ERROR_COLOR, interaction.user)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        cube_attr_map = {
            "Water": "icube", "Wind": "wcube", "Fire": "fcube", "Dark": "dcube", "Light": "lcube"
        }
        cube_type = cube_attr_map.get(item_obj.classType)
        if not cube_type:
            embed = create_embed("Error", f"Invalid class type for {item_name}.", ERROR_COLOR, interaction.user)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Update quantity
        if is_hunter:
            # For hunters, reduce quantity in hunters inventory
            if isinstance(item_data, dict):
                item_data['quantity'] -= quantity
            elif isinstance(item_data, int):
                inventory[item_id] -= quantity
        else:
            # For items, reduce shard quantity in inventory
            shard_id = f"s_{item_id}"
            if isinstance(item_data, dict):
                item_data['quantity'] -= quantity
                if item_data['quantity'] <= 0:
                    del inventory[shard_id]
            elif isinstance(item_data, int):
                inventory[shard_id] -= quantity
                if inventory[shard_id] <= 0:
                    del inventory[shard_id]
            
        current_cubes = getattr(player, cube_type, 0)
        setattr(player, cube_type, current_cubes + quantity)

        await player.save()

        embed = create_embed(
            title="Sacrifice Successful!",
            description=f"You sacrificed `{quantity}` shard(s) of {getEmoji(item_id)} **{item_name}** and obtained {getEmoji(cube_type)} `{quantity} {item_obj.classType} Cube`!",
            color=SUCCESS_COLOR,
            author=interaction.user
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

# This is the required setup function that was missing
async def setup(bot):
    await bot.add_cog(SacrificeCog(bot))