import logging

import aiohttp

from . import events, exceptions, objects

__log__ = logging.getLogger(__name__)


class WebSocket:

    def __init__(self, node):

        self.node = node
        self.client = self.node.client
        self.bot = self.client.bot

        self.host = self.node.host
        self.port = self.node.port
        self.password = self.node.password
        self.secure = self.node.secure

        self.ws = None
        self.task = None

    @property
    def is_connected(self) -> bool:
        return self.ws is not None and not self.ws.closed

    @property
    def ws_uri(self) -> str:
        secure = 'wss' if self.secure else 'ws'
        return f'{secure}://{self.host}:{self.port}/'

    @property
    def headers(self) -> dict:
        return {
            'Authorization': self.password,
            'Num-Shards': str(self.bot.shard_count or 1),
            'User-Id': str(self.bot.user.id)
        }

    async def connect(self) -> None:

        await self.bot.wait_until_ready()

        try:
            self.ws = await self.node.session.ws_connect(self.ws_uri, headers=self.headers)

        except aiohttp.WSServerHandshakeError as error:

            if error.status == 401:
                msg = f'Websocket for node \'{self.node.identifier}\' had invalid authorization.'
                __log__.error(msg)
                raise exceptions.NodeConnectionError(msg)

            else:
                msg = f'Websocket for node \'{self.node.identifier}\' was unable to connect.\n\n{error}'
                __log__.error(msg)
                raise exceptions.NodeConnectionError(msg)

            # TODO See if any other errors raise here and handle them.

        self.task = self.bot.loop.create_task(self.listen())
        self.node.available = True

    async def listen(self) -> None:

        while True:

            message = await self.ws.receive()

            if message.type is aiohttp.WSMsgType.CLOSED:
                msg = f'Websocket for node \'{self.node.identifier}\' has closed\n\n{message.extra}'
                __log__.error(msg)
                raise exceptions.NodeConnectionError(msg)

            else:
                message = message.json()
                op = message.get('op')

                if op == 'stats':

                    __log__.debug(f'Node \'{self.node.identifier}\' received stats payload | {message}')
                    self.node.stats = objects.Stats(message)

                elif op == 'event':

                    __log__.debug(f'Node \'{self.node.identifier}\' received event payload | {message}')

                    try:
                        player = self.node.players[int(message['guildId'])]
                    except KeyError:
                        continue

                    message['player'] = player

                    event = getattr(events, message['type'], None)
                    if not event:
                        continue

                    event = event(message)
                    self.bot.dispatch(f'diorite_{event.name}', event)

                    __log__.info(f'Node \'{self.node.identifier}\' dispatched \'{event.type}\' '
                                 f'event for player \'{player.guild.id}\'.')

                elif op == 'playerUpdate':

                    __log__.debug(f'Node \'{self.node.identifier}\' received playerUpdate payload | {message}')
                    try:
                        player = self.node.players[int(message['guildId'])]
                        await player._update_state(message)
                    except KeyError:
                        continue

                else:
                    __log__.warning(f'Node \'{self.node.identifier}\' received unknown payload | {message}')

    async def send(self, **data) -> None:

        if not self.is_connected:
            raise exceptions.NodeNotAvailable(f'Node \'{self.node.identifier}\' is not currently available.')

        await self.ws.send_json(data)
        __log__.debug(f'Node \'{self.node.identifier}\' has sent payload | {data}')

    def __repr__(self):
        return f'<DioriteWebsocket is_connected={self.is_connected}>'
