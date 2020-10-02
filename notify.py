from requests import post as _post


_DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/761679919172157460/spO4yf9bAf9IkLd128j_E7GFa14p6tkXGrjY7XDPSFyDLmQdycIebnURfUELu5paqNyi"


def notify(message):
    """Notify people via Discord about the given message."""
    _post(_DISCORD_WEBHOOK_URL, json={"content": message})
