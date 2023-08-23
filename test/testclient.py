import socket
import argparse
import json
import time

import constants


def send_message(sock, message):
    sock.send(message.encode())

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", help="Client identifier")
    parser.add_argument("--delay", type=int, default=0, help="Delay in seconds before sending the identification message")
    args = parser.parse_args()

    # Pad the identifier to 12 bytes
    identifier = args.identifier.ljust(12)[:12]

    # Load client configuration from config.json
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
        server_address = (config["ipaddress"], config["port"])

    # Create the client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect(server_address)

    # Sleep
    time.sleep(args.delay)

    # Send the identification message
    message = 'A1' + identifier
    send_message(client_socket, message)

    try:
        # Keep the client running until Ctrl-C is pressed
        while True:
            pass
    except KeyboardInterrupt:
        # Graceful termination on Ctrl-C
        client_socket.close()
        print("Client stopped.")

if __name__ == "__main__":
    main()
