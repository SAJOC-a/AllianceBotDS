from config import *
from other.sqlite import *
from handlers.default import DefaultCog
from handlers.roles import VerifyCog, Buttons
from handlers.commands import CommandMenuCog
from handlers.music import Music
import asyncio
from loader import *
import logging
import logging.handlers



logger_ = logging.getLogger('discord')
logger_.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='logs/discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,
    backupCount=5,
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger_.addHandler(handler)



@bot.event 
async def on_ready():  # Загрузка частей бота и его запуск
    #bot.loop.create_task(update_server_info())
    if use_music:
        await bot.add_cog(Music(bot))
        logger.success("Music Cog connect!")

    await bot.add_cog(VerifyCog(bot))
    logger.success("Verify Cog connect!")

    await bot.add_cog(DefaultCog(bot))
    logger.success("Default Cog connect!")

    await bot.add_cog(CommandMenuCog(bot))
    logger.success("Command Cog connect!")

    bot.add_view(Buttons())
    #bot.add_view(ButtonsTest())

    synced = await bot.tree.sync()
    logger.info(f"Synced {len(synced)} command(s).")

    logger.success("Bot started!")
    logger.info(f"{bot.user} | {bot.user.id}")
    logger.info(f"Ссылка для приглашения бота на сервер:")
    logger.info(f"> https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&scope=applications.commands%20bot")

async def update_server_info():  # Фоновый поток, пока не используется
    while True:
        pass

if __name__ == '__main__':
    database = db()
    bot.run(bot_token, log_handler=None)
