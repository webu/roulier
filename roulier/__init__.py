# -*- coding: utf-8 -*-
import logging

from . import carrier
from . import codec
from . import transport
from . import roulier
from . import exception

# __version__ = open('VERSION').read().strip()
log = logging.getLogger(__name__)  # noqa
log.addHandler(logging.NullHandler())

__all__ = [
    'carrier',
    'codec',
    'transport',
    'roulier',
    'exception',
]
