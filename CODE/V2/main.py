import asyncio
import time

async def send_and_receive_message(host, port, message):
    reader, writer = await asyncio.open_connection(host, port)

    print(f'Sending: {message}')
    start_time = time.time()
    writer.write((message + '\n').encode())
    await writer.drain()

    data = await reader.read(1024)
    end_time = time.time()
    latency = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f'Received: {data.decode().strip()}')
    print(f'Latency: {latency:.2f} ms')

    writer.close()
    await writer.wait_closed()

async def main():
    host = "192.168.1.1"  # Replace with your ESP32's IP address
    port = 11112

    while True:
        message = input("Enter message to send: ")
        await send_and_receive_message(host, port, message)

if __name__ == "__main__":
    asyncio.run(main())