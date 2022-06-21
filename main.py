from idom import component, html, event, use_state
from idom.backend.sanic import configure, use_request
from sanic import Sanic
from sanic.log import logger

from auth import SessionAuthenticator
from session import configure_sessions


@component
def Page():
    request = use_request()
    session = request.ctx.session

    if session.fresh:
        # handle edge case when we have a new session, but the cookie has not been set
        # this might happen when the first connection is a websockets connection and not the index page
        logger.info(
            f"Session {session.sid} is new and the cookie has not been set yet. Reloading window to set cookie..."
        )
        return DoReload()

    authenticator = SessionAuthenticator(app, session)
    authenticated, set_authenticated = use_state(authenticator.is_authenticated())

    async def on_auth_change(auth_state: bool):
        set_authenticated(auth_state)

    authenticator.register_handler(on_auth_change)

    if authenticated:
        return Greet(authenticator)
    else:
        return Auth(authenticator)


@component
def Greet(authenticator):
    return html.div(
        html.h1(f"Hello {authenticator.get_user()}!"),
        html.button({"onClick": lambda _: authenticator.logout()}, "Logout"),
    )


@component
def Auth(authenticator):
    username, set_username = use_state("")
    password, set_password = use_state("")
    message, set_message = use_state("")

    @event(prevent_default=True)
    async def handle_submit(_):
        authenticated = authenticator.authenticate(username=username, password=password)
        if not authenticated:
            set_message("Login failed. Try again.")

    return html.div(
        html.h1("Login"),
        html.form(
            {"onSubmit": handle_submit, "style": {"display": "inline-grid"}},
            html.p(message),
            html.input(
                {
                    "type": "text",
                    "placeholder": "Username",
                    "value": username,
                    "onChange": lambda event: set_username(event["target"]["value"]),
                }
            ),
            html.input(
                {
                    "type": "password",
                    "placeholder": "Password",
                    "value": password,
                    "onChange": lambda event: set_password(event["target"]["value"]),
                }
            ),
            html.input({"type": "submit", "value": "Submit"}),
        ),
    )


@component
def DoReload():
    return html.script("() => { location.reload(); return () => {} }")


app = Sanic("MyApp")
configure(app, Page)
configure_sessions(app)

if __name__ == "__main__":
    app.run()
