# diorite
diorite is a python wrapper for the audio provider called [Lavalink](https://github.com/Frederikam/Lavalink) intended 
for use with [discord.py](https://github.com/Rapptz/discord.py).

## Links
* [Discord support server](https://discord.gg/xP8xsHr)
* Soom:tm:

# Installation
From PyPi
```shell script
python -m pip install -U diorite
```
From Github
```shell script
python -m pip install -U git+https://github.com/iDevision/diorite
```

# Example
```python
from discord.ext import commands
import diorite

class MyBot(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('!'), reconnect=True)    
        
        self.bot = self
        self.bot.add_cog(Music(self))
    
    async def on_ready(self):
        print(f'Bot is now online and running as {self.bot.user.name}')


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.diorite = diorite.Client(self.bot)

        self.bot.loop.create_task(self.start_node())

    async def start_node(self):
        
        # Connect diorite to your lavalink node, you should probably use a try/except here to catch any errors.
        await self.bot.diorite.create_node(host='lavalink-server-ip', port='lavalink-server-port',
                                           password='lavalink-server-password', identifier='custom-identifier')  
    
    @commands.command(name='connect')
    async def connect(self, ctx):
    
        # Try to get the author's voice channel and join it.
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('Please join a voice to use this command.')
        
        # Gets a player for the guild, if one doesn't exist this will create it.
        player = self.bot.diorite.get_player(ctx.guild)

        # Joins the author's voice channel.
        await player.connect(channel=channel)
        return await ctx.send('Joined your voice channel.')
    
    @commands.command(name='play')
    async def play(self, ctx, *, search: str):

        player = self.bot.diorite.get_player(ctx.guild)
    
        # If the player isn't connected, invoke the connect command.
        if not player.is_connected:
            await ctx.invoke(self.connect)
        
        # Search youtube for tracks, this can return a playlist, list of tracks or none. 'Notice the `ytsearch:'
        search_result = await player.node.get_tracks(search=f'ytsearch:{search}')
        if not search_result:
            return await ctx.send(f'No track found for search: `{search}`')
        
        # Play the first entry in the list of results, note that this will error 
        # if the author searched for a playlist link.
        await player.play(search_result[0])
        return await ctx.send(f'Now playing {search_result[0].title} by {search_result[0].author}')


MyBot().run('Your bots token')
```
test
