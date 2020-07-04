import logging
from typing import List, Union
from urllib.parse import quote

from . import exceptions, objects, websocket

__log__ = logging.getLogger(__name__)


class Node:

    def __init__(self, client, host: str, port: str, password: str, identifier: str, secure: bool):

        self.client = client
        self.bot = self.client.bot
        self.session = self.client.session

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
        return f'<DioriteNode player_count={len(self.players.keys())} identifier=\'{self.identifier}\' ' \
               f'available={self.available}>'

    @property
    def is_available(self) -> bool:
        return self.websocket.is_connected and self.available

    @property
    def rest_uri(self) -> str:
        secure = 'https' if self.secure else 'http'
        return f'{secure}://{self.host}:{self.port}/'

    async def connect(self) -> None:

        self.websocket = websocket.WebSocket(node=self)
        await self.websocket.connect()
        __log__.info(f'Websocket for node \'{self.identifier}\' is connected.')

    async def disconnect(self) -> None:

        for player in self.players.copy().values():
            __log__.info(f'Node \'{self.identifier}\' destroyed player \'{player.guild.id}\'')
            await player.destroy()

        try:
            self.websocket.task.cancel()
        except Exception:  # TODO Figure out what exception would be suitable here.
            pass

        del self.client.nodes[self.identifier]

    async def get_tracks(self, query: str) -> Union[objects.Playlist, List[objects.Track], None]:

        async with self.client.session.get(url=f'{self.rest_uri}/loadtracks?identifier={quote(query)}',
                                           headers={'Authorization': self.password}) as response:
            data = await response.json()

        load_type = data.get('loadType')

        if load_type == 'LOAD_FAILED':
            exception = data.get('exception')
            msg = f"There was an error of severity level \'{exception.get('severity')}\' while loading a track."
            __log__.error(msg)
            raise exceptions.TrackLoadError(msg, exception)

        elif load_type == 'NO_MATCHES':
            __log__.warning(f'Node \'{self.identifier}\' found no result for query \'{query}\'.')
            return None

        elif load_type == 'PLAYLIST_LOADED':
            __log__.info(f'Node \'{self.identifier}\' found playlist for query \'{query}\'.')
            return objects.Playlist(playlist_info=data.get('playlistInfo'), tracks=data.get('tracks'))

        elif load_type == 'SEARCH_RESULT' or load_type == 'TRACK_LOADED':
            __log__.info(f'Node \'{self.identifier}\' found tracks for query \'{query}\'.')
            return [objects.Track(track_id=track.get('track'), info=track.get('info')) for track in data.get('tracks')]
