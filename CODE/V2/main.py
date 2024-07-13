import asyncio
import time

async def send_and_receive_message(host, port, message):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
    except asyncio.TimeoutError:
        print("Connection timed out")
        return
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    try:
        print(f'Sending: {message}')
        start_time = time.time()
        writer.write((message + '\n').encode())
        await writer.drain()

        data = await asyncio.wait_for(reader.readline(), timeout=5)
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f'Received: {data.decode().strip()}')
        print(f'Latency: {latency:.2f} ms')
    except asyncio.TimeoutError:
        print("Response timed out")
    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    host = "192.168.1.1"  # Replace with your ESP32's IP address
    port = 11112

    while True:
        message = input("Enter message to send (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break
        await send_and_receive_message(host, port, message)

if __name__ == "__main__":
    asyncio.run(main())