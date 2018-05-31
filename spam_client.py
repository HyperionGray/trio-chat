import itertools
import logging

import trio


format_ = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(format=format_, datefmt='%H:%M:%S')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def spam():
    '''
    This client sends messages very quickly to the Trio Chat server.

    The time in between sending each message is displayed in order to determine
    if backpressure is working correctly.
    '''
    host, port = '127.0.0.1', 1234
    logger.info('SpamBot 5000 connecting to %s:%d', host, port)
    try:
        stream = await trio.open_tcp_stream(host, port)
        logger.info('Connected')
        # Get name prompt from server and then send name
        await stream.receive_some(256)
        logger.info('Sending name')
        await stream.send_all(b'SpamBot 5000')
        await stream.receive_some(256)
        async with trio.open_nursery() as nursery:
            nursery.start_soon(reader, stream)
            nursery.start_soon(writer, stream)
    except KeyboardInterrupt:
        logger.warn('Interrupt: shutting down')


async def reader(stream):
    ''' Read messages and throw them away. '''
    while True:
        await stream.receive_some(2500)


async def writer(stream):
    ''' Send spam messages to chat server. '''
    last_send = trio.current_time()
    spam = ("SPAM " * 500).encode('utf8')
    for message_number in range(1000):
        await stream.send_all(spam)
        now = trio.current_time()
        logger.info('Sent #%d in %0.3fs', message_number, now - last_send)
        last_send = now

if __name__ == '__main__':
    trio.run(spam)
