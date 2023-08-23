import socket

import constants
import init
import configinfo
import reporting
import commsgate
import logicalconductor


g = {"server_socket": None}


"""client_sockets  -- dictionary of real sockets

client_sockets = {id(client_socket): <socket object>,
                  ...}
"""

client_sockets = {}


def bind():
    g["server_socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    g["server_socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind the server socket to the IP address and port
    ip_addr = configinfo.config["ipaddress"]
    port = configinfo.config["port"]
    g["server_socket"].bind((ip_addr, port))
    
    reporting.report_initial_binding(ip_addr, port)
    
    # Set the server socket to non-blocking mode
    g["server_socket"].setblocking(False)

    # Listen for incoming connections
    g["server_socket"].listen()


def accept_new_connections():
    try:
        # Accept new client connections
        client_socket, client_address = g["server_socket"].accept()
        client_socket.setblocking(False)

        # Register it
        client_sockets[id(client_socket)] = client_socket
        
        # Save info for logical interaction
        commsgate.add_conn(id(client_socket),
                           client_address[0],  # IP address
                           client_address[1])  # port
    
    except socket.error as e:
        # Handle socket errors
        if e.errno != socket.errno.EAGAIN and e.errno != socket.errno.EWOULDBLOCK:
            handle_accept_error()

def handle_accept_error():  # TODO!
    breakpoint()  # not sure what to do here, when this situation arises really...


def receive_messages():
    # Message received function call for each connected client
    for client_socket in list(client_sockets.values()):
        try:
            # Receive and process messages from clients
            msg = client_socket.recv(constants.PACKET_SIZE)
            if msg:
                commsgate.add_inbox(id(client_socket), msg)
        
        except socket.error as e:
            # Handle socket errors
            if e.errno != socket.errno.EAGAIN and e.errno != socket.errno.EWOULDBLOCK:
                handle_recv_error(client_socket)

def handle_recv_error(client_socket):
    commsgate.rm_conn(id(client_socket))
    del client_sockets[id(client_socket)]


def send_messages():
    while commsgate.outbox:
        D = commsgate.pop_outbox()
        client_sockets[D["CONN"]].send(D["MSG"])


def loop():
    try:
        while True:
            accept_new_connections()
            receive_messages()
            logicalconductor.loop_once()
            send_messages()
    except KeyboardInterrupt:
        # When operating virtually, raise KeyboardInterrupt programmatically.
        logicalconductor.loop_terminated()
        send_messages()
        g["server_socket"].close()


if __name__ == "__main__":
    # System Initialization as a Server
    init.init_conductor()
    
    # Create the server socket
    bind()
    
    # Main server loop
    loop()

