import logging

import aiohttp
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
            self.client.session = session
            self.session = session
            try:
                self.ws = await self.session.ws_connect(self.ws_url)
            except (aiohttp.ClientConnectorError, aiohttp.WSServerHandshakeError, aiohttp.ServerDisconnectedError, aiohttp.ClientConnectorError) as error:
                _LOGGER.error(f"Could not connect to websocket: {error}")
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
                    logging.error("close")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logging.error(msg.data)
                    break
