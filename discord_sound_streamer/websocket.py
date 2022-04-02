import logging

import aiohttp
import asyncio
from lavaplayer.websocket import _LOGGER
from lavaplayer.websocket import WS as _WS


class WS(_WS):
    '''
    This is a subclass of the lavaplayer websocket class,
    which has a bug in its callback method that raises an
    unhandled KeyError when the lavalink server sends a 
    payload without a 'message' key. 

    _connect() has been re-implemented with a generic 
    exception handler around the callback invocation.

    TODO Remove this when we are sure the bug is fixed.
    '''
    def __init__(
        self,
        ws: _WS,
    ) -> None:
        self.ws = ws.ws
        self.ws_url = ws.ws_url
        self.client = ws.client
        self._headers = ws._headers
        self._loop = ws._loop
        self.emitter = ws.emitter
        self.is_connect: bool = ws.is_connect
    
    async def _connect(self):
        async with aiohttp.ClientSession(headers=self._headers, loop=self._loop) as session:
            self.session = session
            try:
                self.ws = await self.session.ws_connect(self.ws_url)
                if session is None:
                    await self.check_connection()
            except (aiohttp.ClientConnectorError, aiohttp.WSServerHandshakeError, aiohttp.ServerDisconnectedError) as error:
                
                if isinstance(error, aiohttp.ClientConnectorError):
                    _LOGGER.error(f"Could not connect to websocket: {error}")
                    _LOGGER.warning("Reconnecting to websocket after 10 seconds")  
                    await asyncio.sleep(10)
                    await self._connect()
                    return
                elif isinstance(error, aiohttp.WSServerHandshakeError):
                    if error.status in (403, 401):  # Unauthorized or Forbidden
                        _LOGGER.warning("Password authentication failed - closing websocket")
                        return
                    _LOGGER.warning("Please check your websocket port - closing websocket")
                elif isinstance(error, aiohttp.ServerDisconnectedError):
                    _LOGGER.error(f"Could not connect to websocket: {error}")
                    _LOGGER.warning("Reconnecting to websocket after 10 seconds")
                    await asyncio.sleep(10)
                    await self._connect()
                    return

            _LOGGER.info("Connected to websocket")
            self.is_connect = True
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        await self.callback(msg.json())
                    except Exception as e:
                        _LOGGER.exception(e)
                        continue
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    _LOGGER.error("Websocket closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.error(msg.data)
                    break