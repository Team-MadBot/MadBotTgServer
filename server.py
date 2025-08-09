from typing import Optional

import uvicorn
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.web_app import safe_parse_webapp_init_data
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from hcaptcha.hcaptcha import HCaptchaVerificationError, HCaptchaVerifier
from pydantic import BaseModel

from db import UserRepository
from config import settings

app = FastAPI()
bot = Bot(token=settings["token"])
hverifier = HCaptchaVerifier(settings["hcaptcha_token"])

load_dotenv()


class CaptchaResponse(BaseModel):
    hCaptchaResponse: str
    initData: str
    groupId: int
    irlAccepted: Optional[bool] = False


class GroupInfo(BaseModel):
    groupId: int
    initData: str


@app.get("/", status_code=404)
async def nado():
    return "Nothing here. Absolutely. Go away."


@app.get("/api/downloadgroupavatar/{file_id}")
async def download(file_id: str):
    file = await bot.get_file(file_id)

    assert file.file_path is not None
    assert file.file_size is not None

    file_path = file.file_path
    url = bot.session.api.file_url(bot.token, file_path)
    stream = bot.session.stream_content(
        url=url,
        timeout=max(60, file.file_size // 524288),
        chunk_size=65536,
        raise_for_status=True,
    )

    async def file_streamer():
        async for chunk in stream:
            yield chunk

    headers = {
        "Content-Disposition": "inline",
        "Content-Length": str(file.file_size),
    }
    return StreamingResponse(
        file_streamer(), media_type="application/octet-stream", headers=headers
    )


@app.post("/api/getgroupinfo", status_code=200)
async def get_group_info(group_info: GroupInfo, response: Response):
    try:
        safe_parse_webapp_init_data(settings["token"], group_info.initData)
    except ValueError:
        response.status_code = 400
        return "Pidoras, wth is it?"

    group = await bot.get_chat(group_info.groupId)
    group_avatar_url = (
        f"{settings['bot_domain']}/api/downloadgroupavatar/{group.photo.big_file_id}"
        if group.photo
        else None
    )
    return {"groupTitle": group.title, "groupAvatarUrl": group_avatar_url}


@app.post("/api/submitcaptcha", status_code=200)
async def handle_captcha_aboba(captcha: CaptchaResponse, response: Response):
    try:
        init_data = safe_parse_webapp_init_data(settings["token"], captcha.initData)
    except ValueError:
        response.status_code = 400
        return {"status": "Pidoras, wth is it?"}

    assert init_data.user is not None

    user_id = init_data.user.id
    group_id = captcha.groupId

    if captcha.hCaptchaResponse == "":
        response.status_code = 400
        return {"status": "Where is the Captcha????"}
    try:
        if await hverifier.verify(captcha.hCaptchaResponse):
            db_user = await UserRepository.get_user_by_id(user_id=user_id)
            if db_user is not None and db_user.is_irl and not captcha.irlAccepted:
                return {"status": "IRL"}
            try:
                await bot.approve_chat_join_request(group_id, user_id)
            except TelegramBadRequest as e:
                response.status_code = 500
                return e.__class__.__name__
            return {"status": "OK"}
        else:
            response.status_code = 400
            return {"status": "Not OK"}
    except HCaptchaVerificationError as e:
        print(e)
        response.status_code = 500
        return {"status": "Internal Server Error"}


@app.get("/api/irlinfo/{user_id}", status_code=200)
async def get_user_info(user_id: int, response: Response, request: Request):
    if request.headers.get("Authorization", "") != settings["apiToken"]:
        response.status_code = 401
        return {"status": "Unauthorized"}

    db_user = await UserRepository.get_user_by_id(user_id=user_id)

    return {"status": "OK", "isIrl": db_user is not None and db_user.is_irl}


@app.put("/api/irlinfo/{user_id}", status_code=200)
async def post_user_info(user_id: int, response: Response, request: Request):
    if request.headers.get("Authorization", "") != settings["apiToken"]:
        response.status_code = 401
        return {"status": "Unauthorized"}

    db_user = await UserRepository.get_user_by_id(user_id=user_id)

    if db_user is not None and db_user.is_irl:
        response.status_code = 400
        return {"status": "Bad request", "message": "User is already in the list!"}

    if db_user is not None:
        await UserRepository.create_user(user_id=user_id, is_irl=True)
    else:
        await UserRepository.update_user_settings(current_user_id=user_id, is_irl=True)

    return {"status": "OK"}


@app.delete("/api/irlinfo/{user_id}", status_code=200)
async def delete_user_info(user_id: int, response: Response, request: Request):
    if request.headers.get("Authorization", "") != settings["apiToken"]:
        response.status_code = 401
        return {"status": "Unauthorized"}

    db_user = await UserRepository.get_user_by_id(user_id=user_id)

    if db_user is None or not db_user.is_irl:
        response.status_code = 400
        return {"status": "Bad request", "message": "User wasn't found in the list!"}

    await UserRepository.update_user_settings(current_user_id=user_id, is_irl=False)

    return {"status": "OK"}


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=9002)


start_server()
