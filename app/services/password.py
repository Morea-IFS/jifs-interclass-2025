"""Geração de senhas aleatórias."""

import random

from app.helpers import ALPHANUMERIC_CHARS


def generate_random_password(length=8):
    """Gera senha aleatória alfanumérica."""
    return ''.join(random.sample(ALPHANUMERIC_CHARS, length))
