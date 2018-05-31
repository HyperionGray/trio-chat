# Trio Chat

An extremely simple chat server based on the [Trio async
framework](https://trio.readthedocs.io/e) as an excuse to practice writing Trio
code. Requires Python 3.6 or later.

To install dependencies, you should make a virtual environment.

    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv) $ pip install -r requirements.txt

To run the server (Python 3.6 or later):

    (venv) $ python trio_chat.py
    12:07:54 [INFO] Trio chat server listening on 127.0.0.1:1234
    ...

To connect a client, netcat to the server port. The server will prompt you for
a name to use in the chat room. Type a name and press enter. Every subsequent
line will be treated as a chat message and broadcast to all participants.

    $ nc 127.0.0.1 1234
    Welcome to Trio Chat! Enter your name:
    Morty
    Rick> They're just robots, Morty! It's OK to shoot them!
    Guard #1> Aah! My leg is shot off!
    Guard #2> Glenn's bleeding to death!
    They're not Robots, Rick!
    Morty> They're not Robots, Rick!
    Rick> It's a figure of speech, Morty. They're bureaucrats. I don't respect them.

It's a terrible chat experience. For example, if you're in the middle of typing
when somebody sends a message, their message will clobber your typing. Also
two people can choose the same name!

This is clearly not a production-ready chat server, but this project does
demonstrate a concise example of a Trio program that is slightly more
complicated than an echo server, and it handles various edge cases gracefully.
For example, if the user closes the connection, the task associated with that
connection exits cleanly. It also handles backpressure correctly. If clients
send messages faster than the server can handle them (the server has a rate
limit of 5 messages / second), then the client's network stack will start to
slow down the rate of transmission.

The `spam_client.py` script demonstrates back pressure in effect. This script
just sends packets as fast as possible:

    (venv) $ python spam_client.py
    13:03:15 [INFO] Spam client connecting to 127.0.0.1:1234
    13:03:15 [INFO] Connected
    13:03:15 [INFO] Sending name
    13:03:15 [INFO] Sent #0 in 0.000s
    13:03:15 [INFO] Sent #1 in 0.000s
    13:03:15 [INFO] Sent #2 in 0.000s
    13:03:15 [INFO] Sent #3 in 0.000s
    13:03:15 [INFO] Sent #4 in 0.000s
    13:03:15 [INFO] Sent #5 in 0.000s
    ...
    13:03:18 [INFO] Sent #325 in 2.881s
    13:03:18 [INFO] Sent #326 in 0.000s
    13:03:18 [INFO] Sent #327 in 0.000s
    13:03:18 [INFO] Sent #328 in 0.000s

The packets go out quickly at the outset, but as the server's receive buffer
fills up, the back pressure will eventually cause the client's network stack to
block. In the excerpt shown above, message #325 takes 2.881 seconds to send,
the result of backpressure.

The chat server also handles clients that do not _receive_ quickly enough. The
`slow_client.py` script demonstrates a client that is reading messages very
slowly. This slow client creates back pressure, so the server chooses not to
deliver messages when a client's message queue is full.

    $ python slow_client.py
    14:02:17 [INFO] SlowBot 0.0.1a connecting to 127.0.0.1:1234
    14:02:17 [INFO] Connected
    14:02:17 [INFO] Sending name
    14:02:18 [INFO] Received 2514 bytes
    14:02:23 [INFO] Received 2600 bytes
    14:02:28 [INFO] Received 2600 bytes
    ...

The slow client doesn't really do anything interesting, but you can see from the
output that it only reads one message every 5 seconds. If we run the
`spam_client.py` at the same time and watch the server output we will see the
following output.

    $ python trio_chat.py
    13:59:32 [INFO] Trio chat server listening on 127.0.0.1:1234
    13:59:39 [INFO] Connection #0 from 127.0.0.1
    13:59:39 [INFO] Connection #0: name set to "SlowBot 0.0.1a"
    13:59:42 [INFO] Connection #1 from 127.0.0.1
    13:59:42 [INFO] Connection #1: name set to "SpamBot 5000"
    13:59:42 [ERROR] Connection #0: queue is full! (dropping message)
    13:59:42 [ERROR] Connection #0: queue is full! (dropping message)
    13:59:42 [ERROR] Connection #0: queue is full! (dropping message)
    ...

