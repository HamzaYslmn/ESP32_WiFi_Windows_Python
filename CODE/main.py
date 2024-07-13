import asyncio
import socket
import keyboard
from rich.console import Console
from datetime import datetime

console = Console()

UDP_PORT = 11113
TCP_PORT = 11112
BROADCAST_ADDRESS = '255.255.255.255'

async def discover_devices():
    devices = []
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DeviceDiscoveryProtocol(devices),
        local_addr=('0.0.0.0', 0),
        allow_broadcast=True
    )
    
    try:
        transport.sendto(b'DISCOVER', (BROADCAST_ADDRESS, UDP_PORT))
        await asyncio.sleep(2)  # Wait for responses
    finally:
        transport.close()
    
    return devices

class DeviceDiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, devices):
        self.devices = devices

    def datagram_received(self, data, addr):
        self.devices.append((data.decode(), addr[0]))

class UDPClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_receive):
        self.on_receive = on_receive
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode().strip()
        self.on_receive(message, addr)

    def send_message(self, message, addr):
        self.transport.sendto(message.encode(), addr)

async def handle_connection(ip):
    # TCP connection
    reader, writer = await asyncio.open_connection(ip, TCP_PORT)
    
    # UDP connection
    loop = asyncio.get_running_loop()
    udp_transport, udp_protocol = await loop.create_datagram_endpoint(
        lambda: UDPClientProtocol(on_receive=lambda msg, addr: console.print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]}] UDP Received: {msg}", style="bold blue")),
        remote_addr=(ip, UDP_PORT)
    )

    async def listen_tcp():
        while True:
            try:
                data = await reader.readline()
                if data:
                    message = data.decode().strip()
                    console.print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]}] TCP Received: {message}", style="bold green")
            except asyncio.CancelledError:
                break

    tcp_listener = asyncio.create_task(listen_tcp())

    while True:
        console.print("\nMain Menu:", style="bold cyan")
        console.print("1 - TCP")
        console.print("2 - UDP")
        console.print("Press 'esc' to go back to device selection")

        choice = await asyncio.to_thread(input, "Enter your choice: ")

        if keyboard.is_pressed('esc'):
            break

        if choice == '1':
            await send_tcp_messages(writer)
        elif choice == '2':
            await send_udp_messages(udp_protocol, ip)
        else:
            console.print("Invalid choice. Please try again.", style="bold red")

    tcp_listener.cancel()
    writer.close()
    await writer.wait_closed()
    udp_transport.close()

async def send_tcp_messages(writer):
    console.print("Entering TCP mode. Press 'esc' to return to the main menu.", style="bold yellow")
    while True:
        if keyboard.is_pressed('esc'):
            break
        message = await asyncio.to_thread(input, "Enter TCP message: ")
        writer.write((message + '\n').encode())
        await writer.drain()
        console.print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]}] TCP Sent: {message}", style="bold purple")

async def send_udp_messages(udp_protocol, ip):
    console.print("Entering UDP mode. Press 'esc' to return to the main menu.", style="bold yellow")
    while True:
        if keyboard.is_pressed('esc'):
            break
        message = await asyncio.to_thread(input, "Enter UDP message: ")
        udp_protocol.send_message(message, (ip, UDP_PORT))
        console.print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]}] UDP Sent: {message}", style="bold yellow")

async def main():
    while True:
        console.print("Discovering devices...", style="bold yellow")
        devices = await discover_devices()
        
        if not devices:
            console.print("No devices found. Retrying...", style="bold red")
            continue
        
        console.print("Available devices:", style="bold cyan")
        for i, (device_id, ip) in enumerate(devices):
            console.print(f"{i+1}. {device_id} ({ip})", style="cyan")
        
        selection = await asyncio.to_thread(input, "Select a device (number): ")
        try:
            selected_device = devices[int(selection) - 1]
        except (ValueError, IndexError):
            console.print("Invalid selection. Please try again.", style="bold red")
            continue
        
        ip = selected_device[1]
        
        await handle_connection(ip)

asyncio.run(main())