import asyncio
import socket
from datetime import datetime

UDP_PORT = 11112
BROADCAST_IP = '255.255.255.255'
DISCOVERY_INTERVAL = 15
BROADCAST_COUNT = 10

async def send_discover(sock):
    sock.sendto("DISCOVER".encode(), (BROADCAST_IP, UDP_PORT))

async def discover_devices(devices):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1)

    while True:
        tasks = [asyncio.create_task(send_discover(sock)) for _ in range(BROADCAST_COUNT)]
        await asyncio.gather(*tasks)

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < DISCOVERY_INTERVAL:
            try:
                data, addr = await asyncio.get_event_loop().run_in_executor(None, sock.recvfrom, 1024)
                if data.startswith(b'ESP32:'):
                    parts = data.decode().split(':')
                    device_name = parts[1]
                    ip = parts[2]
                    if (device_name, ip, addr[1]) not in devices:
                        devices.append((device_name, ip, addr[1]))
                        print("\033[2J\033[H", end="")  # Clear the console
                        print("Available devices:")
                        for i, (dev_name, dev_ip, dev_port) in enumerate(devices):
                            print(f"{i + 1}. {dev_name} ({dev_ip}:{dev_port})")
                        print("\nSelect a device (number) or press Enter to continue: ", end="", flush=True)
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error: {e}")
            await asyncio.sleep(0.1)
            
async def terminal_mode(sock, target):
    while True:
        message = await asyncio.get_event_loop().run_in_executor(None, input, "Enter message to send (or 'q' to exit): ")
        
        if message.lower() == "q":
            break
        
        start_time = datetime.now()
        sock.sendto(message.encode(), target)
        print(f"{start_time.strftime('%H:%M:%S.%f')[:-3]}: Sent: {message}")
        
        data, addr = await asyncio.get_event_loop().run_in_executor(None, sock.recvfrom, 1024)
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        print(f"{end_time.strftime('%H:%M:%S.%f')[:-3]}: Received: {data.decode()} ({elapsed_time:.3f} ms)")
             
async def keyboard_mode(sock, target):
    return

async def latency_test(sock, message, target, iterations=100):
    return

async def main():
    devices = []
    discovery_task = asyncio.create_task(discover_devices(devices))

    while True:
        choice = await asyncio.get_event_loop().run_in_executor(None, input, "")
        if choice == "":
            continue
        try:
            choice = int(choice) - 1
            if 0 <= choice < len(devices):
                break
            print("Invalid choice. Try again.")
        except ValueError:
            print("Invalid input. Enter a number.")

    discovery_task.cancel()
    target_name, target_ip, target_port = devices[choice]
    print(f"Connecting to {target_name} ({target_ip}:{target_port})")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)  # Set a 10-second timeout
    
    print("\033[2J\033[H", end="")  # Clear the console
    while True:
        print("[1] Terminal Mode")   # send and receive messages asynchronously
        print("[2] Keyboard Mode")   # listen asynchronously for key presses on the keyboard and send them to esp32, listen asynchronously for responses.
        print("[3] Latency Test")    # send 100 messages and wait for a response to calculate the latency of the connection
        
        mode_choice = await asyncio.get_event_loop().run_in_executor(None, input, "Select mode (or 'q' to exit): ")
        if mode_choice.lower() == 'q':
            break
        elif mode_choice == "cls":
            print("\033[2J\033[H", end="")
            continue
        elif mode_choice == "1":
            await terminal_mode(sock, (target_ip, target_port))
        elif mode_choice == "2":
            await keyboard_mode(sock, (target_ip, target_port))
        elif mode_choice == "3":
            await latency_test(sock, "PING", (target_ip, target_port))

    sock.close()

if __name__ == "__main__":
    asyncio.run(main())
