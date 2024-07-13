import asyncio
import socket
import statistics
from time import perf_counter_ns

UDP_PORT = 11112
BROADCAST_IP = '255.255.255.255'
ITERATIONS = 50

async def discover_devices():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2)

    print("Discovering ESP32 devices...")
    sock.sendto("DISCOVER".encode(), (BROADCAST_IP, UDP_PORT))

    devices = []
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            if data.startswith(b'ESP32:'):
                ip = data.decode().split(':')[1]
                devices.append((ip, addr[1]))
                print(f"Found ESP32 at {ip}")
            else:
                print(f"Received unknown response: {data} from {addr}")
    except socket.timeout:
        print("Discovery timeout.")
    except Exception as e:
        print(f"Error: {e}")

    sock.close()
    return devices

async def send_and_receive(sock, message, addr):
    send_time = perf_counter_ns()
    sock.sendto(message.encode(), addr)
    try:
        data, _ = await asyncio.get_event_loop().run_in_executor(None, sock.recvfrom, 1024)
        receive_time = perf_counter_ns()
        rtt = (receive_time - send_time) / 1e6  # Convert to milliseconds
        return data.decode(), rtt
    except socket.timeout:
        return None, None

async def measure_latency(sock, message, addr):
    latencies = []
    for _ in range(ITERATIONS):
        data, rtt = await send_and_receive(sock, message, addr)
        if data:
            latencies.append(rtt)
            print(f"Received: {data}, RTT: {rtt:.3f} ms")
        else:
            print("Timeout: No response received")
    return latencies

def print_statistics(latencies):
    if latencies:
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
        
        print(f"\nLatency statistics over {ITERATIONS} iterations:")
        print(f"Average: {avg_latency:.3f} ms")
        print(f"Minimum: {min_latency:.3f} ms")
        print(f"Maximum: {max_latency:.3f} ms")
        print(f"Std Dev: {std_dev:.3f} ms")
    else:
        print("No valid latency measurements")

async def main():
    devices = await discover_devices()
    if not devices:
        print("No ESP32 devices found.")
        return

    print("\nAvailable devices:")
    for i, (ip, port) in enumerate(devices):
        print(f"{i + 1}. {ip}:{port}")

    choice = int(input("Select a device to connect to (enter the number): ")) - 1
    if choice < 0 or choice >= len(devices):
        print("Invalid choice.")
        return

    target_ip, target_port = devices[choice]
    print(f"Connecting to {target_ip}:{target_port}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)  # Set a 1-second timeout

    while True:
        message = input("Enter message to send (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break
        latencies = await measure_latency(sock, message, (target_ip, target_port))
        print_statistics(latencies)

    sock.close()

if __name__ == "__main__":
    asyncio.run(main())
