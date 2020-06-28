class RedditGrabberException(Exception):
    def __init__(self, mess: str):
        super().__init__(mess)
