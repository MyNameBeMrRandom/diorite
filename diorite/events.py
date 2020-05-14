

class DioriteEvent:

    def __init__(self):

        self.name = 'null_event'
        self.type = 'NullEvent'


class TrackStartEvent(DioriteEvent):

    def __init__(self, player, data: dict):
        super().__init__()

        self.player = player
        self.name = 'track_start'

        self.type = data['type']
        self.track = data['track']


class TrackEndEvent(DioriteEvent):

    def __init__(self, player, data: dict):
        super().__init__()

        self.player = player
        self.name = 'track_end'

        self.type = data['type']
        self.track = data['track']

        self.reason = data['reason']


class TrackStuckEvent(DioriteEvent):

    def __init__(self, player, data: dict):
        super().__init__()

        self.player = player
        self.name = 'track_stuck'

        self.type = data['type']
        self.track = data['track']

        self.threshold = data['thresholdMs']


class TrackExceptionEvent(DioriteEvent):

    def __init__(self, player, data: dict):
        super().__init__()

        self.player = player
        self.name = 'track_error'

        self.type = data['type']
        self.track = data['track']

        self.error = data['error']


class WebSocketClosed(DioriteEvent):

    def __init__(self, player, data: dict):
        super().__init__()

        self.player = player
        self.name = 'websocket_closed'

        self.type = data['type']

        self.code = data['code']
        self.reason = data['reason']
        self.by_remote = data['byRemote']
