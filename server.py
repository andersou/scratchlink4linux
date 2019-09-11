#!/usr/bin/env python
import asyncio
import pathlib
import ssl
import websockets
from jsonrpcserver import method, async_dispatch as dispatch
from jsonrpcclient.clients.websockets_client import WebSocketsClient

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = pathlib.Path(__file__).with_name(
    "device-manager.scratch.mit.edu.pem")
ssl_context.load_cert_chain(localhost_pem)


@method
async def discover(filters):
    print(filters)
    return None


async def main(websocket, path):
    if path == "/scratch/ble":
        response = await dispatch(await websocket.recv())
        if response.wanted:
            await websocket.send(str(response))
            response = await WebSocketsClient(websocket).request("didDiscoverPeripheral", peripheralId=0x0000, name="MICROBIT DA ELIMU", rssi=-70)


start_server = websockets.serve(
    main, "localhost", 20110, ssl=ssl_context
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
