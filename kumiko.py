  
import asyncio
import discord
import youtube_dl
from discord.ext import commands
import json
import glob
import os


config_file = open('config.json', 'r')
config = json.load(config_file)

youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def avatar(self, ctx):
        """Sends the message's author's avatar"""
        
        async with ctx.typing():
            await ctx.send(ctx.message.author.avatar_url)

    @commands.command()
    async def furkan(self, ctx):
        """sends furkan's mc server"""
        await ctx.send("minecraft.furkanmudanyali.com")


    
    
    @commands.command()
    async def clean_cache(self, ctx):
        """Clear the music cache"""
        
        files = glob.glob("*.webm")
        if (len(files) > 0):
            await ctx.send("Found {} files.".format(len(files)))
            for i in files:
                os.remove(i)
            await ctx.send("Cache cleared.")
        else:
            await ctx.send("There is nothing to delete.")




        


    
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @yt.before_invoke
    
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

bot = commands.Bot(command_prefix=commands.when_mentioned_or(config["prefix"]),
                   description='I mostly am useful for music (for now xd)')

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')
    game = discord.Game("{}help | taking a fat shit".format(config["prefix"]))
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=game)

    

bot.add_cog(Music(bot))
bot.add_cog(Administration(bot))
bot.run(config["token"])

