import asyncio
import socket
import statistics
from time import perf_counter_ns

UDP_PORT = 11112
BROADCAST_IP = '255.255.255.255'
DISCOVERY_INTERVAL = 15  # Interval in seconds between each discovery broadcast
BROADCAST_COUNT = 10  # Number of discovery messages to send in each broadcast
ITERATIONS = 50

async def send_discover(sock):
    sock.sendto("DISCOVER".encode(), (BROADCAST_IP, UDP_PORT))

async def discover_devices(devices):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.5)

    while True:
        tasks = [asyncio.create_task(send_discover(sock)) for _ in range(BROADCAST_COUNT)]
        await asyncio.gather(*tasks)

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < DISCOVERY_INTERVAL:
            try:
                data, addr = await asyncio.get_event_loop().run_in_executor(None, sock.recvfrom, 1024)
                if data.startswith(b'ESP32:'):
                    ip = data.decode().split(':')[1]
                    if (ip, addr[1]) not in devices:
                        devices.append((ip, addr[1]))
                        print("\033[2J\033[H", end="")  # Clear the console
                        print("Available devices:")
                        for i, (dev_ip, dev_port) in enumerate(devices):
                            print(f"{i + 1}. {dev_ip}:{dev_port}")
                        print("\nSelect a device (number) or press Enter to continue: ", end="", flush=True)
            except socket.timeout:
                pass
            except Exception:
                pass
            await asyncio.sleep(0.1)

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
    target_ip, target_port = devices[choice]
    print(f"Connecting to {target_ip}:{target_port}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)  # Set a 10-second timeout

    while True:
        message = input("Enter message to send (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break
        latencies = await measure_latency(sock, message, (target_ip, target_port))
        print_statistics(latencies)

    sock.close()

if __name__ == "__main__":
    asyncio.run(main())