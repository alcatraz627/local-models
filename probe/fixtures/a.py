"""Page model. (multi-file probe: should import + use slugify from b.py.)"""

from b import truncate


class Page:
    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.slug = ""          # multi-file probe: set this from title via slugify
        self.preview = truncate(body)
