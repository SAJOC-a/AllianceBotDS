import discord
from discord.ext import commands

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

