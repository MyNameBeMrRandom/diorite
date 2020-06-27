import re

from . import exceptions


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
        return f'https://img.youtube.com/vi/{self.identifier}/mqdefault.jpg' if self.yt_id else None


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


class Filter:

    __slots__ = 'payload'

    def __init__(self):
        self.payload = {"filters": None}

    def __repr__(self):
        return f'<DioriteBaseFilter payload={self.payload}'


class Timescale(Filter):

    __slots__ = ('speed', 'pitch', 'rate')

    def __init__(self, *, speed: float, pitch: float, rate: float):
        super().__init__()

        self.speed = speed
        self.pitch = pitch
        self.rate = rate

        self.payload = {
            "timescale": {
                "speed": self.speed,
                "pitch": self.pitch,
                "rate": self.rate
            }
        }

    def __repr__(self):
        return f"<DioriteTimescaleFilter speed={self.speed} pitch={self.pitch} rate={self.rate}>"


class Karaoke(Filter):

    __slots__ = ('level', 'mono_level', 'filter_band', 'filter_width')

    def __init__(self, *, level: float, mono_level: float, filter_band: float, filter_width: float):
        super().__init__()

        self.level = level
        self.mono_level = mono_level
        self.filter_band = filter_band
        self.filter_width = filter_width

        self.payload = {
            "karaoke": {
                "level": self.level,
                "monoLevel": self.mono_level,
                "filterBand": self.filter_band,
                "filterWidth": self.filter_width
            }
        }

    def __repr__(self):
        return f"<DioriteKaraokeFilter level={self.level} mono_level={self.mono_level} " \
               f"filter_band={self.filter_band} filter_width={self.filter_width}>"


class Tremolo(Filter):

    __slots__ = ('frequency', 'depth')

    def __init__(self, *, frequency: float, depth: float):
        super().__init__()

        if frequency < 0:
            raise exceptions.InvalidFilterParam("Tremolo frequency must be more than 0.0")
        if depth < 0 or depth >= 1:
            raise exceptions.InvalidFilterParam("Tremolo depth must be between 0.0 and 1.0")

        self.frequency = frequency
        self.depth = depth

        self.payload = {
            "tremolo": {
                "frequency": self.frequency,
                "depth": self.depth
            }
        }

    def __repr__(self):
        return f"<DioriteTremoloFilter frequency={self.frequency} depth={self.depth}>"


class Vibrato(Filter):

    __slots__ = ('frequency', 'depth')

    def __init__(self, *, frequency: float, depth: float):
        super().__init__()

        if frequency < 0 or frequency >= 14:
            raise exceptions.InvalidFilterParam("Vibrato frequency must be between 0.0 and 14.0.")
        if depth < 0 or depth >= 1:
            raise exceptions.InvalidFilterParam("Vibrato depth must be between 0.0 and 1.0.")

        self.frequency = frequency
        self.depth = depth

        self.payload = {
            "vibrato": {
                "frequency": self.frequency,
                "depth": self.depth
            }
        }

    def __repr__(self):
        return f"<DioriteVibratoFilter frequency={self.frequency} depth={self.depth}>"

