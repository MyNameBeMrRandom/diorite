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
        self.filter = None
        self.equalizer = objects.Equalizer.flat()

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
        return self.paused is True

    @property
    def position(self) -> float:

        if not self.is_playing:
            return 0

        if not self.current:
            return 0

        if self.paused:
            return min(self.last_position, self.current.length)

        difference = (time.time() * 1000) - self.last_update
        position = self.last_position + difference

        if position > self.current.length:
            return 0

        return min(position, self.current.length)

    async def _update_state(self, data: dict) -> None:

        state = data.get('state')

        self.last_update = time.time() * 1000
        self.last_position = state.get('position', 0)
        self.time = state.get('time', 0)

    async def _voice_server_update(self, data: dict) -> None:

        __log__.debug(f'Player \'{self.guild.id}\' received a voice server update | {data}')
        self.voice_state.update({'event': data})

        await self._dispatch_voice_update()

    async def _voice_state_update(self, data: dict) -> None:

        __log__.debug(f'Player \'{self.guild.id}\' received a voice state update | {data}')
        self.voice_state.update({'sessionId': data['session_id']})

        channel_id = data['channel_id']
        if not channel_id:
            self.voice_state.clear()
            return

        self.voice_channel = self.bot.get_channel(int(channel_id))
        await self._dispatch_voice_update()

    async def _dispatch_voice_update(self) -> None:

        __log__.debug(f'Player \'{self.guild.id}\' has dispatched a voice update.')

        if {'sessionId', 'event'} == self.voice_state.keys():
            await self.node.websocket.send(op='voiceUpdate', guildId=str(self.guild.id), **self.voice_state)

    def _get_shard_socket(self, shard_id: int) -> typing.Optional[DiscordWebSocket]:

        if isinstance(self.bot, commands.AutoShardedBot):
            return self.bot.shards[shard_id].ws

        if self.bot.shard_id is None or self.bot.shard_id == shard_id:
            return self.bot.ws

    async def connect(self, voice_channel: discord.VoiceChannel) -> None:

        self.voice_channel = voice_channel
        await self._get_shard_socket(self.guild.shard_id).voice_state(self.guild.id, str(voice_channel.id))

        __log__.info(f'Player \'{self.guild.id}\' has connected to voice channel \'{self.voice_channel.id}\'.')

    async def disconnect(self) -> None:

        __log__.info(f'Player \'{self.guild.id}\' has disconnected from voice channel \'{self.voice_channel.id}\'.')

        self.voice_channel = None
        await self._get_shard_socket(self.guild.shard_id).voice_state(self.guild.id, None)

    async def play(self, track: objects.Track, no_replace: bool = False, start: int = 0, end: int = 0):

        if no_replace is False or not self.is_playing:
            self.last_update = 0
            self.last_position = 0
            self.time = 0
            self.paused = False

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

        await self.node.websocket.send(**payload)
        self.current = track

        __log__.info(f'Player \'{self.guild.id}\' has started playing track {self.current!r}.')

    async def stop(self) -> None:

        await self.node.websocket.send(op='stop', guildId=str(self.guild.id))
        __log__.info(f'Player \'{self.guild.id}\' has stopped playing track {self.current!r}.')

        self.current = None

    async def destroy(self) -> None:

        await self.stop()
        await self.disconnect()

        await self.node.websocket.send(op='destroy', guildId=str(self.guild.id))
        del self.node.players[self.guild.id]

        __log__.info(f'Player \'{self.guild.id}\' has been destroyed.')

    async def set_pause(self, pause: bool) -> None:

        await self.node.websocket.send(op='pause', guildId=str(self.guild.id), pause=pause)
        self.paused = pause

        __log__.info(f'Player \'{self.guild.id}\' pause has been set to \'{self.paused}\'.')

    async def set_volume(self, volume: int) -> None:

        await self.node.websocket.send(op='volume', guildId=str(self.guild.id), volume=volume)
        self.volume = volume

        __log__.info(f'Player \'{self.guild.id}\' volume has been set to \'{self.volume}\'.')

    async def seek(self, position: int) -> None:

        if not self.current:
            __log__.warning(f'Player \'{self.guild.id}\' attempted to seek with no current track.')
            return

        if position < 0 or position > self.current.length:
            __log__.warning(f'Player \'{self.guild.id}\' attempted to seek to invalid position.')
            raise exceptions.TrackInvalidPosition(f'Track seek position must be between 0 and track length.')

        await self.node.websocket.send(op='seek', guildId=str(self.guild.id), position=position)
        __log__.info(f'Player \'{self.guild.id}\' position has been set to \'{self.position}\'.')

    async def set_equalizer(self, equalizer: objects.Equalizer):

        await self.node.websocket.send(op='equalizer', guildId=str(self.guild.id), bands=equalizer.eq)
        self.equalizer = equalizer

        __log__.info(f'Player \'{self.guild.id}\' equalizer has been set to {equalizer!r}.')

    async def set_filter(self, filter_type: objects.Filter):

        await self.node.websocket.send(op="filters", guildId=str(self.guild.id), **filter_type.payload)
        self.filter = filter_type

        __log__.info(f'Player \'{self.guild.id}\'  has had {filter_type!r} filter applied.')

    async def set_timescale(self, *, speed: float = 1, pitch: float = 1, rate: float = 1):

        return await self.set_filter(objects.Timescale(speed=speed, pitch=pitch, rate=rate))

    async def set_tremolo(self, *, frequency: float = 2, depth: float = 0.5):

        return await self.set_filter(objects.Tremolo(frequency=frequency, depth=depth))

    async def set_karaoke(self, *, level: float = 1, mono_level: float = 1,
                          filter_band: float = 220, filter_width: float = 100):

        return await self.set_filter(objects.Karaoke(level=level, mono_level=mono_level,
                                                     filter_band=filter_band, filter_width=filter_width))
