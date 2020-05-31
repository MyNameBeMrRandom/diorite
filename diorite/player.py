import logging
import time
import typing

import discord
from discord.ext import commands
from discord.gateway import DiscordWebSocket

from . import exceptions, objects
from .node import Node

__log__ = logging.getLogger(__name__)


class Player:

    def __init__(self, node: Node, guild: discord.Guild, **kwargs):

        self.node = node
        self.guild = guild
        self.bot = self.node.bot

        self.voice_channel = None

        self.volume = 100
        self.paused = False
        self.current = None

        self.voice_state = {}
        self.player_state = {}
        self.last_position = 0
        self.last_update = 0
        self.time = 0

    def __repr__(self):
        return f'<DioritePlayer is_connected={self.is_connected} is_playing={self.is_playing}>'

    @property
    def is_connected(self) -> bool:
        return self.voice_channel is not None

    @property
    def is_playing(self) -> bool:
        return self.is_connected is True and self.current is not None

    @property
    def is_paused(self) -> bool:
        return self.is_connected and self.paused is True

    @property
    def position(self) -> float:

        if not self.is_playing:
            return 0

        if not self.current:
            return 0

        if self.paused:
            return min(self.last_position, self.current.length)

        difference = (time.time() * 1000) - self.last_update
        return min(self.last_position + difference, self.current.length)

    async def update_state(self, data: dict) -> None:

        state = data.get('state')

        self.last_update = time.time() * 1000
        self.last_position = state.get('position', 0)
        self.time = state.get('time', 0)

    async def voice_server_update(self, data: dict) -> None:

        __log__.debug(f"Player '{self.guild.id}' has received a voice server update.")
        self.voice_state.update({'event': data})

        __log__.debug(f"Player '{self.guild.id}' has dispatched a voice update.")
        if {'sessionId', 'event'} == self.voice_state.keys():
            await self.node.send(op='voiceUpdate', guildId=str(self.guild.id), **self.voice_state)

    async def voice_state_update(self, data: dict) -> None:

        __log__.debug(f"Player '{self.guild.id}' has received a voice state update.")
        self.voice_state.update({'sessionId': data['session_id']})

        channel_id = data['channel_id']
        if not channel_id:
            self.voice_state.clear()
            return

        self.voice_channel = self.bot.get_channel(int(channel_id))

        __log__.debug(f"Player '{self.guild.id}' has dispatched a voice update.")
        if {'sessionId', 'event'} == self.voice_state.keys():
            await self.node.send(op='voiceUpdate', guildId=str(self.guild.id), **self.voice_state)

    def get_shard_socket(self, shard_id: int) -> typing.Optional[DiscordWebSocket]:

        if isinstance(self.bot, commands.AutoShardedBot):
            return self.bot.shards[shard_id].ws

        if self.bot.shard_id is None or self.bot.shard_id == shard_id:
            return self.bot.ws

    async def connect(self, voice_channel: discord.VoiceChannel) -> None:

        await self.get_shard_socket(self.guild.shard_id).voice_state(self.guild.id, str(voice_channel.id))
        self.voice_channel = voice_channel

        __log__.info(f"Player '{self.guild.id}' has connected to voice channel {self.voice_channel.id!r}.")

    async def disconnect(self) -> None:

        await self.get_shard_socket(self.guild.shard_id).voice_state(self.guild.id, None)
        __log__.info(f"Player '{self.guild.id}' has disconnected from voice channel {self.voice_channel.id!r}.")

        self.voice_channel = None

    async def play(self, track: objects.Track, no_replace: bool = False, start: int = 0, end: int = 0) -> objects.Track:

        payload = {
            'op': 'play',
            'guildId': str(self.guild.id),
            'track': str(track.track_id),
            'noReplace': no_replace,
        }
        if 0 < start < track.length:
            payload['startTime'] = start
        if 0 < end < track.length:
            payload['endTime'] = end

        await self.node.send(**payload)
        self.current = track

        __log__.info(f"Player '{self.guild.id}' has started playing track {self.current!r}.")
        return self.current

    async def stop(self, force: bool = True) -> None:

        if not self.current and force is False:
            __log__.warning(f"Player '{self.guild.id}' attempted to stop with no current track.")
            return

        await self.node.send(op='stop', guildId=str(self.guild.id))
        __log__.info(f"Player '{self.guild.id}' has stopped playing track {self.current!r}.")

        self.current = None

    async def destroy(self) -> None:

        await self.stop()
        await self.disconnect()

        await self.node.send(op='destroy', guildId=str(self.guild.id))
        del self.node.players[self.guild.id]

        __log__.info(f"Player '{self.guild.id}' has been destroyed.")

    async def set_pause(self, pause: bool) -> bool:

        await self.node.send(op='pause', guildId=str(self.guild.id), pause=pause)
        self.paused = pause

        __log__.info(f"Player '{self.guild.id}' pause has been set '{self.paused}'.")

        return self.paused

    async def set_volume(self, volume: int) -> int:

        await self.node.send(op='volume', guildId=str(self.guild.id), volume=volume)
        self.volume = volume

        __log__.info(f"Player '{self.guild.id}' volume has been set '{self.volume}'.")

        return self.volume

    async def seek(self, position: int) -> typing.Optional[float]:

        if not self.current:
            __log__.warning(f"Player '{self.guild.id}' attempted to seek with no current track.")
            return

        if position < 0 or position > self.current.length:
            __log__.warning(f"Player '{self.guild.id}' attempted to seek to invalid position.")
            raise exceptions.TrackInvalidPosition(f'Track seek position must be between 0 and track length.')

        await self.node.send(op='seek', guildId=str(self.guild.id), position=position)
        __log__.info(f"Player '{self.guild.id}' position has been set '{self.position}'.")

        return position

    async def set_filter(self, filter_type: objects.Filter) -> objects.Filter:

        await self.node.send(op="filters", guildId=str(self.guild.id), **filter_type.payload)
        return filter_type

    async def set_timescale(self, *, speed: float = 1, pitch: float = 1, rate: float = 1) -> objects.Filter:

        return await self.set_filter(objects.Timescale(speed=speed, pitch=pitch, rate=rate))

    async def set_karaoke(self, *, level: float = 1, mono_level: float = 1,
                          filter_band: float = 220, filter_width: float = 100) -> objects.Filter:

        return await self.set_filter(objects.Karaoke(level=level, mono_level=mono_level,
                                                     filter_band=filter_band, filter_width=filter_width))

    async def set_tremolo(self, *, frequency: float = 2, depth: float = 0.5) -> objects.Filter:

        return await self.set_filter(objects.Tremolo(frequency=frequency, depth=depth))

    async def set_vibrato(self, frequency: float = 2, depth: float = 0.5) -> objects.Filter:

        return await self.set_filter(objects.Vibrato(frequency=frequency, depth=depth))





