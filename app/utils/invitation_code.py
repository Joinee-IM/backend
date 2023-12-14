import random

import app.const as const


def generate():
    return ''.join(
        random.choice(const.AVAILABLE_CODE_CHAR)
        for _ in range(const.INVITE_CODE_LENGTH)
    )
