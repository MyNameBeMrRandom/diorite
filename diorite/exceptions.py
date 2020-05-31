

class DioriteException(Exception):
    pass


class NodeException(DioriteException):
    pass


class NodeConnectionError(NodeException):
    pass


class NodeCreationError(NodeException):
    pass


class NodeNotAvailable(NodeException):
    pass


class NodesNotAvailable(NodeException):
    pass


class TrackException(DioriteException):
    pass


class TrackLoadError(TrackException):

    def __init__(self, message: str, exception: dict):

        self.message = message

        self.severity = exception.get("severity")
        self.error_message = exception.get("message")


class TrackInvalidPosition(TrackException):
    pass


class InvalidFilterParam(DioriteException):
    pass
