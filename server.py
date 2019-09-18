#!/usr/bin/env python
import asyncio
import pathlib
import ssl
import websockets
from jsonrpcserver import method, async_dispatch as dispatch
import threading
from jsonrpcclient.clients.websockets_client import WebSocketsClient
from bleak import discover as bt_discover
from bleak import BleakClient
import json
import base64
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = pathlib.Path(__file__).with_name(
    "device-manager.scratch.mit.edu.pem")
ssl_context.load_cert_chain(localhost_pem)
rpcClient = None
devicesList = []
selectedDevice = None
deviceClient = None
lastWsClient = None
chxsvc = {}


@method
async def discover(filters):
    print(filters)
    return None


@method
async def connect(peripheral_id):
    print(peripheral_id)
    global selectedDevice, deviceClient
    selectedDevice = devicesList[int(peripheral_id)]
    deviceClient = BleakClient(selectedDevice.address)
    await deviceClient.connect()
    return None


def is_servico_by_id(servico_id, servico):
    servico_id in servico.uuid.split("-")[0]


def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""

    async def send_message(sender, data):
        msg = base64.b64encode(data).decode("utf-8")
        print(sender, msg)
        await rpcClient.request("characteristicDidChange",
                                serviceId=chxsvc[sender], characteristicId=sender, message=msg, encoding="base64")
    asyncio.get_event_loop().create_task(send_message(sender, data))


@method
async def getServices():
    return {"services": [s.uuid for s in deviceClient.services]}

# {"jsonrpc":"2.0","method":"read","params":{"serviceId":61445,"characteristicId":"5261da01-fa7e-42ab-850b-7c80220097cc","":true},"id":2}
@method
async def read(service_id, characteristic_id, start_notifications):
    global chxsvc
    chxsvc[characteristic_id] = service_id
    """ servico_id = "{:x}".format(service_id)
    for servico in deviceClient.services:
        print("Services:", servico.uuid, servico.description)
        if is_servico_by_id(servico_id, servico):
            print("encontrou serviço")
            for c in servico.characteristics:
                if c.uuid == characteristic_id:
                    print("encontrou caracteristica")

            break; """
    if(start_notifications):
        await deviceClient.start_notify(characteristic_id, notification_handler)
        return None
    else:
        return await deviceClient.read_gatt_char(characteristic_id)


async def enviarPeriferico(ws, device, id):
    await rpcClient.request("didDiscoverPeripheral",
                            peripheralId=id, name=device.name, rssi=device.rssi)


async def main(websocket, path):
    global lastWsClient, rpcClient
    rpcClient = WebSocketsClient(websocket)
    lastWsClient = websocket

    while True:
        mensagem = await websocket.recv()
        if path == "/scratch/ble":
            mensagemDict = json.loads(mensagem)
            if "result" in mensagemDict:
                continue
            response = await dispatch(mensagem)
            if response.wanted:
                await websocket.send(str(response))
                if mensagemDict["method"] == "discover":
                    global devicesList
                    devicesList = []
                    devices = await bt_discover(timeout=5.0)
                    for d in devices:
                        print(d, d.rssi)
                        if d.name.find("micro:bit") != -1:
                            await enviarPeriferico(websocket, d, len(devicesList))
                            devicesList.append(d)


start_server = websockets.serve(
    main, "localhost", 20110, ssl=ssl_context
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
