import os
from typing import TypedDict

from dotenv import load_dotenv

load_dotenv()


class TypedSettings(TypedDict):
    token: str
    hcaptcha_token: str
    apiToken: str
    bot_domain: str


settings: TypedSettings = {
    "token": os.environ["BOT_TOKEN"],
    "hcaptcha_token": os.environ["HCAPTCHA_TOKEN"],
    "apiToken": os.environ["API_TOKEN"],
    "bot_domain": os.environ["BOT_DOMAIN"]
}
