import socket

from router_config import RouterConfiguration


class RouterNode:
    def __init__(self, configuration: RouterConfiguration):
        self.configuration = configuration
        self.listener_socket: socket.socket | None = None

    def start_listening(self) -> None:
        listening_address = self.configuration.listening_address
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_socket.bind((listening_address.ip, listening_address.port))
        self.listener_socket.listen()

        print(
            f"[ROUTER {self.configuration.router_id}] Escuchando en "
            f"{listening_address.ip}:{listening_address.port}."
        )

    def accept_connections(self) -> None:
        if self.listener_socket is None:
            raise RuntimeError(
                "El router debe iniciar su socket antes de aceptar conexiones."
            )

        while True:
            client_socket, client_address = self.listener_socket.accept()

            with client_socket:
                client_ip, client_port = client_address
                print(
                    f"[ROUTER {self.configuration.router_id}] "
                    f"Conexión recibida desde {client_ip}:{client_port}."
                )

    def close(self) -> None:
        if self.listener_socket is not None:
            self.listener_socket.close()
            self.listener_socket = None
