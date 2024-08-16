import aiohttp
import random
from loguru import logger
import re
import hashlib
from datetime import datetime, timedelta
import config
from discord.ext import commands

def split_text(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    current_part = ''
    
    for sentence in sentences:
        if len(current_part) + len(sentence) <= 200:
            current_part += sentence
        else:
            result.append(current_part)
            current_part = sentence
        
        if len(current_part) > 200:
            parts = re.findall(r'.{1,200}(?:\b|\Z)', current_part)
            result.extend(parts[:-1])
            current_part = parts[-1]
    
    result.append(current_part)
    return result

def is_in_allowed_channel():  # Проверка на разрешенные каналы для муз. каналов
    async def predicate(ctx):
        return ctx.channel.id in config.music_channels
    return commands.check(predicate)
