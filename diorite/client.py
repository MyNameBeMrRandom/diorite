import asyncio
import logging
import random
import typing

import aiohttp
import discord
from discord.ext import commands

from . import exceptions
from .node import Node
from .player import Player

__log__ = logging.getLogger(__name__)


class Client:

    def __init__(self, bot: typing.Union[commands.Bot, commands.AutoShardedBot],
                 loop=None, session: aiohttp.ClientSession = None):

        self.bot = bot
        self.loop = loop or asyncio.get_event_loop()
        self.session = session or aiohttp.ClientSession(loop=self.loop)

        self.nodes = {}

        self.bot.add_listener(self._update_handler, 'on_socket_response')

    def __repr__(self):
        return f'<DioriteClient node_count={len(self.nodes.values())} player_count={len(self.players.values())}>'

    async def _update_handler(self, data: dict) -> None:

        if not data or 't' not in data:
            return

        if data['t'] == 'VOICE_SERVER_UPDATE':

            guild_id = int(data['d']['guild_id'])
            try:
                player = self.players[guild_id]
            except KeyError:
                return
            else:
                await player._voice_server_update(data['d'])

        elif data['t'] == 'VOICE_STATE_UPDATE':

            if int(data['d']['user_id']) != self.bot.user.id:
                return

            guild_id = int(data['d']['guild_id'])
            try:
                player = self.players[guild_id]
            except KeyError:
                return
            else:
                await player._voice_state_update(data['d'])

    @property
    def players(self) -> typing.Mapping[int, Player]:

        players = []
        for node in self.nodes.values():
            players.extend(node.players.values())

        return {player.guild.id: player for player in players}

    async def create_node(self, host: str, port: str, identifier: str, password: str, secure: bool = False) -> Node:

        await self.bot.wait_until_ready()

        if identifier in self.nodes.keys():
            raise exceptions.NodeCreationError(f'Node with identifier {identifier!r} already exists.')

        __log__.debug(f'Node \'{identifier}\' attempting connection.')

        node = Node(client=self, host=host, port=port, identifier=identifier, password=password, secure=secure)
        await node.connect()

        self.nodes[node.identifier] = node

        __log__.info(f'Node \'{identifier}\' connected.')
        return node

    def get_node(self, identifier: str = None) -> typing.Optional[Node]:

        if not self.nodes:
            raise exceptions.NodesNotAvailable('There are no nodes available.')

        if not identifier:  # TODO Find a better way of finding the best node, this is crappy.
            return random.choice([node for node in self.nodes.values() if node.available])

        return self.nodes.get(identifier, None)

    def get_player(self, guild: discord.Guild, cls: typing.Type[Player] = Player, **kwargs) -> Player:

        try:
            player = self.players[guild.id]
        except KeyError:
            pass
        else:
            return player

        if not self.nodes:
            raise exceptions.NodesNotAvailable('There are no nodes available.')

        if not cls:
            cls = Player

        node = self.get_node()
        player = cls(node, guild, **kwargs)
        node.players[guild.id] = player

        __log__.info(f'Player for guild \'{guild.id}\' was created.')
        return self.players[guild.id]
