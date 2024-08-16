from loader import *
from other.funcs import *
import config
import discord



class DefaultCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):  # Событие при заходе участника
        welcome_channel_id = config.welcome_channel_id
        welcome_channel = self.bot.get_channel(welcome_channel_id)
        if welcome_channel:
            await welcome_channel.send(f"{member.mention}, привет! Чтобы присоединиться к чатам альянса, тебе нужно выбрать роль, её ты можешь получить тут: <#{config.roles_channel_id}>")

    @commands.command()  # Команда /ping, возвращает миллисекунды для ответа
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send(f"> Pong! {round(self.bot.latency * 1000)}ms")


    @commands.Cog.listener()
    async def on_message(self, message):  # Событие при отправке любого сообщения
        try:
            # Логирование сообщений
            logger.info(
                f'{message.author.nick if not message.author.bot else "Бот"} '
                f'(Канал - {message.channel.name if hasattr(message.channel, "name") else "DM"}): '
                f'{message.content}'
            )
        except Exception as e:
            logger.error(f"Ошибка логирования сообщения: {e}")

        # Проверка, что сообщение не от самого бота
        if message.author.bot or not config.use_logs:
            return

        # Отправка в логи сервера
        try:
            guild = message.guild
            log_channel = self.bot.get_channel(config.logs_channel_id)
            if log_channel is None:
                logger.error(f"Канал логов с ID {config.logs_channel_id} не найден.")
                return

            embed = discord.Embed(
                color=0x47E7E2,
                timestamp=datetime.utcnow(),
                description=f"in {message.channel.mention}:\n{message.content}"
            )
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.set_footer(text=str(message.author.id))

            if len(message.attachments) > 0:
                embed.set_image(url=message.attachments[0].url)

            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в канал логов: {e}")



    @commands.Cog.listener()
    async def on_message_edit(self, before, after):  # Событие при изменении сообщения
        if before.content != after.content:
            try:
                # Логирование изменения сообщений
                logger.info(
                    f'{before.author.nick if not before.author.bot else "Бот"} (Канал - {before.channel.name}): {before.content} -> {after.content}')
            except Exception as e:
                logger.error(f"Ошибка логирования изменения сообщения: {e}")

            # Проверка, что сообщение не от самого бота
            if before.author.bot:
                return

            # Отправка в логи сервера
            try:
                guild = before.guild
                log_channel = self.bot.get_channel(config.logs_channel_id)
                if log_channel is None:
                    logger.error(f"Канал логов с ID {config.logs_channel_id} не найден.")
                    return

                embed = discord.Embed(
                    color=0x8447E7,
                    timestamp=datetime.utcnow(),
                    description=f"Сообщение в {before.channel.mention} было изменено"
                )
                embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
                embed.add_field(name="Старое сообщение", value=before.content, inline=False)
                embed.add_field(name="Новое сообщение", value=after.content, inline=False)
                embed.set_footer(text=str(before.author.id))

                await log_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Ошибка отправки изменения сообщения в канал логов: {e}")

