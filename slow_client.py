import itertools
import logging

import trio


format_ = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(format=format_, datefmt='%H:%M:%S')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def slow():
    '''
    This client reads messages very slowly from the Trio Chat server.

    This client demonstrates what happens when the server's message queue is
    full and messages need to be dropped.
    '''
    host, port = '127.0.0.1', 1234
    logger.info('SlowBot 0.0.1a connecting to %s:%d', host, port)
    try:
        stream = await trio.open_tcp_stream(host, port)
        logger.info('Connected')
        # Get name prompt from server and then send name
        await stream.receive_some(256)
        logger.info('Sending name')
        await stream.send_all(b'SlowBot 0.0.1a')
        await stream.receive_some(256)
        # Read messages very slowly
        while True:
            data = await stream.receive_some(2600)
            logger.info('Received %d bytes', len(data))
            await trio.sleep(5)
    except KeyboardInterrupt:
        logger.warn('Interrupt: shutting down')


if __name__ == '__main__':
    trio.run(slow)
