

class DioriteEvent:
    pass


class TrackStartEvent(DioriteEvent):

    def __init__(self, data: dict):
        super().__init__()

        self.name = 'track_start'

        self.type = data.get('type')
        self.player = data.get('player')

        self.track = data.get('track')

    def __str__(self):
        return self.type

    def __repr__(self):
        return f'<{self.type} player={self.player!r}'


class TrackEndEvent(DioriteEvent):

    def __init__(self, data: dict):
        super().__init__()

        self.name = 'track_end'

        self.type = data.get('type')
        self.player = data.get('player')

        self.track = data.get('track')
        self.reason = data.get('reason')

    def __str__(self):
        return self.type

    def __repr__(self):
        return f'<{self.type} reason={self.reason} player={self.player!r}'


class TrackStuckEvent(DioriteEvent):

    def __init__(self, data: dict):
        super().__init__()

        self.name = 'track_stuck'

        self.type = data.get('type')
        self.player = data.get('player')

        self.track = data.get('track')
        self.threshold = data.get('thresholdMs')

    def __str__(self):
        return self.type

    def __repr__(self):
        return f'<{self.type} threshold={self.threshold} player={self.player!r}'


class TrackExceptionEvent(DioriteEvent):

    def __init__(self, data: dict):
        super().__init__()

        self.name = 'track_error'

        self.type = data.get('type')
        self.player = data.get('player')

        self.track = data.get('track')
        self.error = data.get('error')

    def __str__(self):
        return self.type

    def __repr__(self):
        return f'<{self.type} error={self.error} player={self.player!r}'


class WebSocketClosedEvent(DioriteEvent):

    def __init__(self, data: dict):
        super().__init__()

        self.name = 'websocket_closed'

        self.type = data.get('type')
        self.player = data.get('player')

        self.code = data.get('code')
        self.reason = data.get('reason')
        self.by_remote = data.get('byRemote')

    def __str__(self):
        return self.type

    def __repr__(self):
        return f'<{self.type} code={self.code} reason={self.reason} by_remote={self.by_remote} player={self.player!r}'
