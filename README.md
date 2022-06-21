# IDOM Auth Example for Sanic

This project demonstrates how to authenticate users in an [IDOM](https://github.com/idom-team/idom) 
project using server-side sessions.

## Quickstart

To start the webserver run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Visit http://127.0.0.1:8000/ to see the login form.
You can use `user1/user1` or `user2/user2` for logging in.
Watch the server log while doing that to get an impression how the session handling works.

## How does it work?

The problem we need to solve is how to securely authenticate users inside an IDOM single page application.
Usually authentication is done via `Cookie` or `Authorization` header on each HTTP request.
But after the websocket connection has been established no further HTTP requests and therefore no further headers will be sent.
There are multiple ways how to handle this:

1. You could push some Javascript via `html.script` that sends a separate auth request to your auth API and then
reloads the page to reestablish the websocket connection with new auth headers, but this is kinda ugly.
It defeats the purpose of IDOM not having to write any Javascript and having a visible reload has a negative impact on 
the user-experience.

2. You could also render the login page traditionally and then redirect to a new page with 
[embedded IDOM](https://idom-docs.herokuapp.com/docs/guides/getting-started/running-idom.html?highlight=embed#embed-in-an-existing-webpage).
But then you already split your application into two parts: "pre-auth" with traditional server-side template rendering and "post-auth" with IDOM.
Keeping both parts consistent is probably not fun.

3. You can also do authentication inside the single page app and save the auth state via `use_state`.
But it will be gone as soon as a websocket disconnect happens. You can mitigate this by pushing some Javascript
that sets a session cookie. But now there is a new problem: Session cookies should be set with the `HttpOnly` flag to
prevent XSS attacks from recovering the session cookie. This can not be done (or at least is difficult to do) with Javascript.
So you might end up with a security flaw in your app.

The approaches above are all unsatisfying. To my knowledge the approach below is the most secure and least cumbersome:

When visiting an IDOM app in your browser at least two things will happen:

1. An HTML document is loaded.
2. A websocket connection is established.

So we have at least one full HTTP request-response cycle. Therefore, we can always set a session cookie with a session 
ID on that response if the request does not already contain a cookie with a valid session ID.
That ensures that the following request for the websocket connection always contains a session ID cookie.
With `use_request` we can now extract the session ID and retrieve the session data. In that data we can look up the 
authentication state and let IDOM display a login form or the actual content. 
We can later manipulate the session data to perform a login or logout. 
All without the need to set a further cookie or push Javascript - provided we implement a server-side session.

This example repo implements such a flow for IDOM + Sanic. But the approach can be easily translated to other frameworks.
The most important part is the middleware that implements setting/retrieving the session cookie.
Note that in this example the session data is non-persistent and will be gone when restarting the webserver.
In the real world you need to put session data into a fast storage like a database or even better a key-value store like 
Redis. Also do not forget to save that data on each change.
