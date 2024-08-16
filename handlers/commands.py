import discord
from discord.ext import commands
from discord import app_commands
import config
from other.funcs import *


class CommandMenuCog(commands.Cog):  # Стандартные команды бота
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear_roles", description="Очистить роли альянса")
    async def clear(self, interaction: discord.Interaction):
        for delete_role_id in config.roles:
            role = interaction.guild.get_role(delete_role_id)
            if role:
                await interaction.user.remove_roles(role)

        await interaction.response.send_message(':star: Успешно сняты роли альянса', ephemeral=True)
        logger.success(f'{interaction.user.id} очистил все роли')

    @app_commands.command(name="stats", description="Статистика количества ролей в чате")
    async def stats(self, interaction: discord.Interaction):
        roles = {}
        for i in config.roles:
            role = discord.utils.get(interaction.guild.roles, id=i)
            if role:
                count = len([member for member in interaction.guild.members if role in member.roles])
            roles[role.name] = count
        
        text = ':ringed_planet: Количество участников с ролью:\n'
        text += '\n'.join([f'       └  {role}: {roles[role]}' for role in roles.keys()])

        await interaction.response.send_message(text)


    @commands.command(name='arizona')
    async def arizona(self, ctx):
        guild = ctx.guild
        arizona_players = []

        for member in guild.members:
            if member.activities:
                for activity in member.activities:
                    if activity.name == "Arizona Role Play":
                        player_info = {
                            'id': getattr(activity, 'state', 'Пусто'),
                            'status': getattr(activity, 'details', 'Играет'),
                            'state': activity.large_image_text
                        }
                        arizona_players.append(player_info)

        if arizona_players:
            response = "Список игроков в Arizona Role Play:\n"
            for player in arizona_players:
                response += f"      └ ``{player['id']}`` (_{player['status']}_) | {player['state']}\n"
        else:
            response = "Никто не играет в Arizona Role Play."

        await ctx.send(f'{response}')