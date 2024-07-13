import asyncio
import socket
import statistics
from time import perf_counter_ns

HOST = "192.168.1.109"  # Replace with your ESP32's IP address
PORT = 11112
ITERATIONS = 50

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
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)  # Set a 1-second timeout

    while True:
        message = input("Enter message to send (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break

        latencies = await measure_latency(sock, message, (HOST, PORT))
        print_statistics(latencies)

    sock.close()

if __name__ == "__main__":
    asyncio.run(main())