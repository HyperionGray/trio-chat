import itertools
import logging

import trio


format_ = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(format=format_, datefmt='%H:%M:%S')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


connection_counter = itertools.count()
message_queues = dict()


class ClosedByPeer(Exception):
    ''' Indicates the connection was closed by the peer. '''


async def main():
    ''' Main entry point. '''
    host, port = '127.0.0.1', 1234
    logger.info('Trio chat server listening on %s:%d', host, port)
    try:
        await trio.serve_tcp(on_connection, port, host=host)
    except KeyboardInterrupt:
        logger.warn('Interrupt: shutting down')


async def on_connection(stream):
    ''' Handle a new TCP connection. '''
    connection_id = next(connection_counter)
    remote = stream.socket.getpeername()
    logger.info('Connection #%d from %s', connection_id, remote[0])
    try:
        name = await get_name(stream)
        logger.info('Connection #%d: name set to "%s"', connection_id, name)
        message_queue = trio.Queue(3)
        message_queues[connection_id] = message_queue
        async with trio.open_nursery() as nursery:
            nursery.start_soon(chat_reader, stream, connection_id,
                message_queue)
            nursery.start_soon(chat_writer, stream, name)
    except ClosedByPeer:
        logger.info('Connection #%d: closed by peer', connection_id)
    except trio.BrokenStreamError:
        logger.info('Connection #%d: reset by peer', connection_id)
    except Exception:
        logger.exception('Connection #%d: uncaught exception', connection_id)
    finally:
        logger.info('Connection #%d: closed', connection_id)
        message_queues.pop(connection_id, None)


async def get_name(stream):
    ''' Get a chat name from the user. '''
    name = ''
    await stream.send_all(b'Welcome to Trio Chat!\n')
    while name == '':
        await stream.send_all(b'Please enter your name: ')
        data = await stream.receive_some(256)
        if not data:
            raise ClosedByPeer()
        name = data.decode('utf8').strip()
    thanks = f'Hi, {name}! You may now chat.\n'.encode('utf8')
    await stream.send_all(thanks)
    return name


async def chat_reader(stream, connection_id, message_queue):
    ''' Reads messages from a message queue and sends them to a stream. '''
    async for message in message_queue:
        logger.debug('Sending %d bytes to connection #%d', len(message),
            connection_id)
        await stream.send_all(message)


async def chat_writer(stream, name):
    ''' Writes a users messages to the message queue. '''
    while True:
        data = await stream.receive_some(2500)
        if not data:
            raise ClosedByPeer()
        text = data.decode('utf8').strip()
        if text == '':
            continue
        message = f'{name}> {text}\n'.encode('utf8')
        for connection_id, message_queue in message_queues.items():
            logger.debug('Queuing %d bytes for connection #%d', len(message),
                connection_id)
            try:
                message_queue.put_nowait(message)
            except trio.WouldBlock:
                error = 'Connection #%d: queue is full! (dropping message)'
                logger.error(error, connection_id)
        # Apply an artificial rate limit to incoming messages:
        # await trio.sleep(0.2)


if __name__ == '__main__':
    trio.run(main)
