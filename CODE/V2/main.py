import socket

def main():
    host = "ESP32_IP_ADDRESS"  # Replace with your ESP32's IP address
    port = 11112

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        while True:
            message = input("Enter message to send: ")
            client_socket.sendall(message.encode() + b'\n')
            
            data = client_socket.recv(1024)
            print(f"Received from ESP32: {data.decode()}")
    except KeyboardInterrupt:
        print("Closing connection")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
