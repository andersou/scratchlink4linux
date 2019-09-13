#!/usr/bin/env python
import asyncio
import pathlib
import ssl
import websockets
from jsonrpcserver import method, async_dispatch as dispatch
import threading
from jsonrpcclient.clients.websockets_client import WebSocketsClient
from bleak import discover as bt_discover
import json

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = pathlib.Path(__file__).with_name(
    "device-manager.scratch.mit.edu.pem")
ssl_context.load_cert_chain(localhost_pem)


@method
async def discover(filters):
    print(filters)
    return None

devicesList = []


async def enviarPeriferico(ws, device, id):
    await WebSocketsClient(ws).request("didDiscoverPeripheral",
                                       peripheralId=id, name=device.name, rssi=device.rssi)


async def main(websocket, path):
    while True:
        if path == "/scratch/ble":
            mensagem = await websocket.recv()
            mensagemDict = json.loads(mensagem)
            response = await dispatch(mensagem)
            if response.wanted:
                await websocket.send(str(response))
                if mensagemDict["method"] == "discover":
                    devices = await bt_discover(device="hci1", timeout=10.0)
                    for d in devices:
                        print(d)
                        await enviarPeriferico(websocket, d, len(devicesList))
                        devicesList.append(d)


start_server = websockets.serve(
    main, "localhost", 20110, ssl=ssl_context
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
