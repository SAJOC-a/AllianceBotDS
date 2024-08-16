import itertools
import traceback
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL
import config
import discord
from loader import *
from other.funcs import *
import asyncio

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'executable': config.ffmpeg_path,  # Заменить на свой путь к ffmpeg
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading."""
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop=None, download=False):
        logger.debug("create_source called")
        loop = loop or asyncio.get_event_loop()

        try:
            to_run = partial(ytdl.extract_info, url=search, download=download)
            data = await loop.run_in_executor(None, to_run)

            if 'entries' in data:
                # take first item from a playlist
                data = data['entries'][0]

            logger.debug(f"Song added to queue: {data['title']}")
            await ctx.send(f'```ini\n[Добавлен {data["title"]} в очередь.]\n```')

            if download:
                source = ytdl.prepare_filename(data)
            else:
                return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

            return cls(discord.FFmpegPCMAudio(source, **ffmpegopts), data=data, requester=ctx.author)
        except Exception as e:
            logger.error(f"Error in create_source: {e}")
            await ctx.send(f'Произошла ошибка при добавлении вашей песни в очередь.\n'
                           f'```css\n[{e}]\n```')

    @classmethod
    async def regather_stream(cls, data, *, loop=None):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        logger.debug("regather_stream called")
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        try:
            to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
            data = await loop.run_in_executor(None, to_run)

            return cls(discord.FFmpegPCMAudio(data['url'], **ffmpegopts), data=data, requester=requester)
        except Exception as e:
            logger.error(f"Error in regather_stream: {e}")




class MusicPlayer(commands.Cog):
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Текущий трек
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Ждем следующий трек, если не дождались, но отключаемся
                async with timeout(60*30):  # в секундах
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'Произошла ошибка при обработке вашей песни.\n'
                                             f'css\n[{e}]\n')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f'**Сейчас играет:** {source.title} от '
                                               f'{source.requester}')
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass


    def destroy(self, guild):
        logger.debug(f'Destroying MusicPlayer for guild: {guild.id}')
        return self.bot.loop.create_task(self._cog.cleanup(guild))



class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('Эта команда не может быть использована в личных сообщениях.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Ошибка подключения к голосовому каналу.'
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player



    @commands.command(name='connect', aliases=['join'])
    @is_in_allowed_channel()
    async def connect_(self, ctx):
        # Check if the author is in a voice channel
        try:
            channel = ctx.author.voice.channel
            logger.info(f"Автор в канале: {channel}")
        except AttributeError:
            logger.info('Нет канала для подключения. Автор не в голосовом канале.')
            await ctx.send("Вы не в голосовом канале.")
            return

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                logger.info(f"Уже подключен к каналу: {channel}")
                return
            try:
                await vc.move_to(channel)
                logger.info(f"Перешел в канал: {channel}")
            except asyncio.TimeoutError:
                logger.info(f'Переход в канал не удался: <{channel}> закончился таймаут.')
        else:
            try:
                await channel.connect()
                logger.info(f"Подключаюсь к каналу: {channel}")
            except asyncio.TimeoutError:
                logger.info(f'Подключение в канал не удалосб: <{channel}> закончился таймаут.')

        embed = discord.Embed(title=":musical_note: Успешно подключился!")
        embed.add_field(name=":heavy_minus_sign: Играю в канале:", value=str(channel), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name='play', aliases=['sing', 'p'])
    @is_in_allowed_channel()
    async def play_(self, ctx, *, search: str):
        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)

        await player.queue.put(source)

    @commands.command(name='pause')
    @is_in_allowed_channel()
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send('В данный момент ничего не играет!')
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: остановил трек!')

    @commands.command(name='resume', aliases=['unpause'])
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('В данный момент ничего не играет!')
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: возобновил трек!')

    @commands.command(name='skip')
    @is_in_allowed_channel()
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('В данный момент ничего не играет!')

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: пропустил трек!')

    @commands.command(name='queue', aliases=['q', 'playlist'])
    @is_in_allowed_channel()
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('В данный момент я не подключен к голосовому каналу!')

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('В настоящее время песен, поставленных в очередь, больше нет.')

        # Grab up to 5 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Предстоящий - Следующий {len(upcoming)}', description=fmt)

        await ctx.send(embed=embed)

    @commands.command(name='now_playing', aliases=['np', 'current', 'currentsong', 'playing'])
    @is_in_allowed_channel()
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('В данный момент я не подключен к голосовому каналу!', )

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('В данный момент ничего не играет!')

        try:
            # Remove our previous now_playing message.
            await player.np.delete()
        except discord.HTTPException:
            pass

        player.np = await ctx.send(f'**Сейчас играет:** `{vc.source.title}` '
                                   f'от `{vc.source.requester}`')

    @commands.command(name='volume', aliases=['vol'])
    @is_in_allowed_channel()
    async def change_volume(self, ctx, *, vol: float):
        """Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('В данный момент я не подключен к голосовому каналу!', )

        if not 0 < vol < 101:
            return await ctx.send('Пожалуйста, введите от 1 до 100.')

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(title="Громкость",
        description=f'Громкость изменил: **{ctx.author.name}**')
        embed.add_field(name="Текущая громкость", value=vol, inline=True)
        await ctx.send(embed=embed)
        # await ctx.send(f'**`{ctx.author}`**: Set the volume to **{vol}%**')

    @commands.command(name='stop', aliases=['leave'])
    @is_in_allowed_channel()
    async def stop_(self, ctx):
        """Stop the currently playing song and destroy the player.
        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('В данный момент ничего не играет!')

        await self.cleanup(ctx.guild)