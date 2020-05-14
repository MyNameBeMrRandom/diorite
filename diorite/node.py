import json
import logging
from typing import Union, List

import websockets

from . import events, exceptions, objects

__log__ = logging.getLogger(__name__)


class Node:

    def __init__(self, client, host: str, port: int, password: str, identifier: str, secure: bool):

        self.client = client
        self.bot = client.bot
        self.host = host
        self.port = port
        self.password = password
        self.identifier = identifier
        self.secure = secure

        self.available = False
        self.stats = None

        self.websocket = None
        self.task = None

        self.players = {}

    def __repr__(self):
        return f'<DioriteNode player_count={len(self.players.keys())} identifier={self.identifier!r} ' \
               f'available={self.available}>'

    @property
    def headers(self) -> dict:
        return {
            'Authorization': self.password,
            'Num-Shards': self.bot.shard_count if self.bot.shard_count else 1,
            'User-Id': str(self.bot.user.id)
        }

    @property
    def is_connected(self) -> bool:
        return self.websocket is not None and self.websocket.open

    @property
    def websocket_uri(self) -> str:
        secure = 'wss' if self.secure else 'ws'
        return f'{secure}://{self.host}:{self.port}/'

    @property
    def rest_uri(self) -> str:
        secure = 'https' if self.secure else 'http'
        return f'{secure}://{self.host}:{self.port}/'

    async def connect(self) -> None:

        await self.bot.wait_until_ready()

        if self.is_connected:
            raise exceptions.NodeConnectionError(f'Node {self.identifier!r} is already connected.')

        try:
            self.websocket = await websockets.connect(uri=self.websocket_uri, extra_headers=self.headers)

        except websockets.InvalidURI:
            msg = f'Node {self.identifier!r} has an invalid uri, check your host and port.'
            __log__.error(msg)
            raise exceptions.NodeConnectionError(msg)

        except websockets.InvalidHandshake:
            msg = f'Node {self.identifier!r} failed to connect to the websocket.'
            __log__.error(msg)
            raise exceptions.NodeConnectionError(msg)

        except Exception as e:
            msg = f'Node {self.identifier!r} failed to connect to the websocket. Reason: {e}'
            __log__.error(msg)  # TODO Get and format error properly
            raise exceptions.NodeConnectionError(msg)

        else:
            __log__.info(f'Node {self.identifier!r} connected.')

            self.task = self.bot.loop.create_task(self._listen())
            self.available = True

    async def disconnect(self) -> None:

        for player in self.players.copy().values():
            __log__.info(f'Node {self.identifier!r} destroyed player {player!r}')
            await player.destroy()

        try:
            self.task.cancel()
            self.websocket.close()
            self.available = False
            __log__.info(f'Node {self.identifier!r} has been disconnected.')

        except Exception:  # TODO figure out an error to put here.
            pass

        del self.client.nodes[self.identifier]

    async def get_tracks(self, query: str) -> Union[objects.Playlist, List[objects.Track], None]:

        async with self.client.session.get(url=f'{self.rest_uri}/loadtracks?identifier={query}',
                                           headers={'Authorization': self.password}) as response:
            data = await response.json()

        load_type = data.get('loadType')

        if load_type == 'LOAD_FAILED':
            exception = data.get('exception')
            msg = f"There was an error of severity level {exception.get('severity')!r} while loading a track."
            __log__.error(msg)
            raise exceptions.TrackLoadError(msg, exception)

        elif load_type == 'NO_MATCHES':
            __log__.warning(f'Node {self.identifier!r} found no result for query {query!r}.')
            return None

        elif load_type == 'PLAYLIST_LOADED':
            __log__.info(f'Node {self.identifier!r} found playlist for query {query!r}.')
            return objects.Playlist(playlist_info=data.get('playlistInfo'), tracks=data.get('tracks'))

        elif load_type == 'SEARCH_RESULT' or load_type == 'TRACK_LOADED':
            __log__.info(f'Node {self.identifier!r} found tracks for query {query!r}.')
            return [objects.Track(track_id=track.get('track'), info=track.get('info')) for track in data.get('tracks')]

    async def send(self, **data) -> None:

        if not self.available:
            raise exceptions.NodeNotAvailable(f'Node {self.identifier!r} is not currently available.')

        __log__.debug(f'Node {self.identifier!r} has sent payload | {data}')
        await self.websocket.send(json.dumps(data))

    async def _listen(self) -> None:

        while True:

            try:
                data = await self.websocket.recv()

            except websockets.ConnectionClosed as e:

                if e.code == 4001:
                    msg = f'Node {self.identifier!r} failed to authenticate.'
                    __log__.error(msg)
                    raise exceptions.NodeConnectionError(msg)

            else:
                data = json.loads(data)
                op = data.get('op')

                if op == 'stats':
                    __log__.debug(f'Node {self.identifier!r} received stats payload | {data}')
                    self.stats = objects.Stats(data)

                elif op == 'event':
                    __log__.debug(f'Node {self.identifier!r} received event payload | {data}')
                    await self._dispatch_event(data)

                elif op == 'playerUpdate':
                    __log__.debug(f'Node {self.identifier!r} received playerUpdate payload | {data}')
                    try:
                        player = self.players[int(data['guildId'])]
                        await player.update_state(data)
                    except KeyError:
                        continue

    async def _dispatch_event(self, data: dict) -> None:

        try:
            player = self.players[int(data['guildId'])]
        except KeyError:
            return

        event = getattr(events, data['type'], None)
        if not event:
            return

        event = event(player, data)
        self.bot.dispatch(f'diorite_{event.name}', event)

        __log__.info(f"Node {self.identifier!r} dispatched {event.type!r} event for player '{player.guild.id}'.")

