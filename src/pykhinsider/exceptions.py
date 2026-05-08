class KHError(Exception):
    pass


class InvalidURLError(KHError):
    pass


class ParseError(KHError):
    pass


class DownloadError(KHError):
    pass
