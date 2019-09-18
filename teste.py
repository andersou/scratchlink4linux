from bleak import discover as bt_discover
from bleak import BleakClient
import asyncio
addr = "C8:40:53:5A:F6:85"


async def print_services(mac_addr: str, loop: asyncio.AbstractEventLoop):
    servico = "{:x}".format(61445)
    client = BleakClient(mac_addr)
    await client.connect()
    svcs = await client.get_services()
    for s in svcs:
        print("Services:", s.uuid, s.description)
        if servico in s.uuid.split("-")[0]:
            print("servico", s)
            for c in s.characteristics:
                print("caracteristica", c.uuid, c.description)

loop = asyncio.get_event_loop()
loop.run_until_complete(print_services(addr, loop))
