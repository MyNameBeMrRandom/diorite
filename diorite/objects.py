import re


class Track:

    __slots__ = ('track_id', 'info', 'identifier', 'is_seekable', 'author', 'length',
                 'is_stream', 'position', 'title', 'uri')

    def __init__(self, track_id: str, info: dict):

        self.track_id = track_id
        self.info = info

        self.identifier = info.get('identifier')
        self.is_seekable = info.get('isSeekable')
        self.author = info.get('author')
        self.length = info.get('length')
        self.is_stream = info.get('isStream')
        self.position = info.get('position')
        self.title = info.get('title')
        self.uri = info.get('uri')

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<DioriteTrack title={self.title!r} uri=<{self.uri}> length={self.length}>'

    @property
    def yt_id(self):
        return self.identifier if re.match(r'^[a-zA-Z0-9_-]{11}$', self.identifier) else None

    @property
    def thumbnail(self):

        return f'https://img.youtube.com/vi/{self.identifier}/maxresdefault.jpg' if self.yt_id else None


class Playlist:

    __slots__ = ('playlist_info', 'raw_tracks', 'tracks', 'name', 'selected_track')

    def __init__(self, playlist_info: dict, tracks: list):

        self.playlist_info = playlist_info
        self.raw_tracks = tracks

        self.tracks = [Track(track_id=track.get('track'), info=track.get('info')) for track in self.raw_tracks]

        self.name = self.playlist_info.get('name')
        self.selected_track = self.playlist_info.get('selectedTrack')

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<DioritePlaylist name={self.name!r} track_count={len(self.tracks)}>'


class Stats:

    __slots__ = ('active_players', 'players', 'uptime', 'memory', 'memory_reservable', 'memory_allocated',
                 'memory_used', 'memory_free', 'cpu', 'cpu_system_load', 'cpu_lavalink_load', 'cpu_cores')

    def __init__(self, stats: dict):

        self.active_players = stats.get('playingPlayers', 0)
        self.players = stats.get('players', 0)
        self.uptime = stats.get('uptime', 0)

        self.memory = stats.get('memory', {})
        self.memory_reservable = self.memory.get('reservable', 0)
        self.memory_allocated = self.memory.get('allocated', 0)
        self.memory_used = self.memory.get('used', 0)
        self.memory_free = self.memory.get('free', 0)

        self.cpu = stats.get('cpu', {})
        self.cpu_system_load = self.cpu.get('systemLoad', 0.0)
        self.cpu_lavalink_load = self.cpu.get('lavalinkLoad', 0.0)
        self.cpu_cores = self.cpu.get('cores', 0)

    def __repr__(self):
        return f'<DioriteStats active_players={self.active_players} players={self.players}>'
