"""This is a poor man's version of https://github.com/xen/sanic_session."""
import datetime
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict

from sanic.log import logger

SESSION_EXPIRY = 604800  # a week


@dataclass
class Session:
    sid: str = field(default_factory=lambda: uuid.uuid4().hex)
    values: Dict = field(default_factory=dict)
    expiry_date: datetime.datetime = datetime.datetime.fromtimestamp(
        time.time() + SESSION_EXPIRY
    )
    fresh: bool = True

    def is_expired(self):
        return datetime.datetime.now() > self.expiry_date


# store this in a DB or KV store in real life
poor_mans_session_store: Dict[str, Session] = {}


async def set_session_on_request(request):
    sid = request.cookies.get("session")
    if (
        not sid
        or sid not in poor_mans_session_store
        or poor_mans_session_store[sid].is_expired()
    ):
        session = Session()
        sid = session.sid
        poor_mans_session_store[sid] = session
        logger.info(
            f"Created new session with ID {sid} with values {poor_mans_session_store[sid].values}"
        )
    else:
        logger.info(
            f"Reusing existing session ID {sid} with values {poor_mans_session_store[sid].values}"
        )
    request.ctx.session = poor_mans_session_store[sid]


async def set_session_cookie_header(request, response):
    session = request.ctx.session
    if session.fresh:  # only set cookie if it has not been set before
        response.cookies["session"] = session.sid
        response.cookies["session"]["secure"] = True
        response.cookies["session"]["httponly"] = True
        response.cookies["session"]["samesite"] = "strict"
        response.cookies["session"]["expires"] = session.expiry_date
        # more on cookies: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie
        session.fresh = False
        logger.info(f"Setting cookie {response.cookies['session']}")


def configure_sessions(app):
    app.on_request(set_session_on_request)
    app.on_response(set_session_cookie_header)
