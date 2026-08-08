import socket
import threading
import time
from typing import Any

from control_messages import (
    HELLO_MESSAGE_TYPE,
    HELLO_REPLY_MESSAGE_TYPE,
    LSA_MESSAGE_TYPE,
    build_forwarded_lsa_message,
    build_hello_message,
    build_hello_reply_message,
    build_lsa_message,
    parse_control_message,
)
from message_framing import receive_framed_text, send_framed_text
from router_config import NeighborConfiguration, RouterConfiguration


NEIGHBOR_DISCOVERY_INTERVAL_IN_SECONDS = 5
CONNECTION_TIMEOUT_IN_SECONDS = 2


class RouterNode:
    def __init__(self, configuration: RouterConfiguration):
        self.configuration = configuration
        self.listener_socket: socket.socket | None = None
        self.keep_running = threading.Event()
        self.listener_thread: threading.Thread | None = None
        self.neighbor_discovery_thread: threading.Thread | None = None
        self.neighbor_availability: dict[str, bool | None] = {
            neighbor.router_id: None
            for neighbor in self.configuration.neighbors
        }
        self.local_lsa_sequence = 1
        self.local_lsa_message = ""
        self.latest_lsa_sequence_by_origin: dict[str, int] = {}
        self.latest_lsa_by_origin: dict[str, dict[str, Any]] = {}

    def start(self) -> None:
        self.start_listening()
        self.prepare_local_lsa()
        self.keep_running.set()
        self.start_listener_thread()
        self.start_neighbor_discovery_thread()

    def start_listening(self) -> None:
        listening_address = self.configuration.listening_address
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_socket.bind((listening_address.ip, listening_address.port))
        self.listener_socket.listen()
        self.listener_socket.settimeout(1)

        print(
            f"[ROUTER {self.configuration.router_id}] Escuchando en "
            f"{listening_address.ip}:{listening_address.port}."
        )

    def start_listener_thread(self) -> None:
        self.listener_thread = threading.Thread(
            target=self.accept_connections,
            name=f"router-{self.configuration.router_id}-listener",
        )
        self.listener_thread.start()

    def start_neighbor_discovery_thread(self) -> None:
        self.neighbor_discovery_thread = threading.Thread(
            target=self.discover_neighbors_periodically,
            name=f"router-{self.configuration.router_id}-neighbor-discovery",
        )
        self.neighbor_discovery_thread.start()

    def accept_connections(self) -> None:
        if self.listener_socket is None:
            raise RuntimeError(
                "El router debe iniciar su socket antes de aceptar conexiones."
            )

        while self.keep_running.is_set():
            try:
                client_socket, client_address = self.listener_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                return

            with client_socket:
                client_ip, client_port = client_address
                print(
                    f"[ROUTER {self.configuration.router_id}] "
                    f"Conexión recibida desde {client_ip}:{client_port}."
                )
                self.handle_received_connection(client_socket)

    def handle_received_connection(self, client_socket: socket.socket) -> None:
        try:
            received_text = receive_framed_text(client_socket)
        except (ConnectionError, OSError, ValueError) as exception:
            print(
                f"[ROUTER {self.configuration.router_id}] "
                f"No fue posible leer la conexión: {exception}"
            )
            return

        if not received_text.startswith("{"):
            print(
                f"[ROUTER {self.configuration.router_id}] "
                "Se recibió DATA, pero el forwarding aún no está implementado."
            )
            return

        try:
            control_message = parse_control_message(received_text)
        except ValueError as exception:
            print(
                f"[ROUTER {self.configuration.router_id}] "
                f"Mensaje de control inválido: {exception}"
            )
            return

        if control_message["type"] == HELLO_MESSAGE_TYPE:
            self.respond_to_hello(client_socket, control_message)
            return

        if control_message["type"] == HELLO_REPLY_MESSAGE_TYPE:
            print(
                f"[ROUTER {self.configuration.router_id}] "
                "Se recibió HELLO_REPLY sin una solicitud HELLO pendiente."
            )

        if control_message["type"] == LSA_MESSAGE_TYPE:
            self.process_received_lsa(control_message)

    def prepare_local_lsa(self) -> None:
        self.local_lsa_message = build_lsa_message(
            self.configuration,
            sequence=self.local_lsa_sequence,
            from_router_id=self.configuration.router_id,
        )
        local_lsa_data = parse_control_message(self.local_lsa_message)
        self.store_lsa(local_lsa_data)
        print(
            f"[ROUTER {self.configuration.router_id}] "
            f"LSA local preparada con secuencia {self.local_lsa_sequence}."
        )

    def process_received_lsa(
        self,
        lsa_message_data: dict[str, Any],
    ) -> None:
        origin_router_id = lsa_message_data["origin_router_id"]
        sequence = lsa_message_data["sequence"]
        from_router_id = lsa_message_data["from_router_id"]

        if not isinstance(origin_router_id, str):
            return

        if not isinstance(sequence, int):
            return

        if not isinstance(from_router_id, str):
            return

        if self.find_neighbor_configuration(from_router_id) is None:
            print(
                f"[ROUTER {self.configuration.router_id}] "
                f"LSA descartada: {from_router_id} no es vecino directo."
            )
            return

        latest_known_sequence = self.latest_lsa_sequence_by_origin.get(
            origin_router_id
        )

        if (
            latest_known_sequence is not None
            and sequence <= latest_known_sequence
        ):
            print(
                f"[ROUTER {self.configuration.router_id}] "
                f"LSA de {origin_router_id} secuencia {sequence} descartada: "
                "es repetida o antigua."
            )
            return

        self.store_lsa(lsa_message_data)
        print(
            f"[ROUTER {self.configuration.router_id}] "
            f"LSA nueva de {origin_router_id} secuencia {sequence} almacenada."
        )
        self.flood_lsa_to_neighbors(
            lsa_message_data,
            excluded_neighbor_router_id=from_router_id,
        )

    def store_lsa(self, lsa_message_data: dict[str, Any]) -> None:
        origin_router_id = lsa_message_data["origin_router_id"]
        sequence = lsa_message_data["sequence"]

        if not isinstance(origin_router_id, str) or not isinstance(sequence, int):
            raise ValueError("La LSA no contiene origen y secuencia válidos.")

        self.latest_lsa_sequence_by_origin[origin_router_id] = sequence
        self.latest_lsa_by_origin[origin_router_id] = dict(lsa_message_data)

    def flood_lsa_to_neighbors(
        self,
        lsa_message_data: dict[str, Any],
        excluded_neighbor_router_id: str,
    ) -> None:
        forwarded_lsa_message = build_forwarded_lsa_message(
            lsa_message_data,
            forwarding_router_id=self.configuration.router_id,
        )

        for neighbor_configuration in self.configuration.neighbors:
            if neighbor_configuration.router_id == excluded_neighbor_router_id:
                continue

            self.send_lsa_to_neighbor(
                neighbor_configuration,
                forwarded_lsa_message,
            )

    def send_known_lsas_to_neighbor(
        self,
        neighbor_configuration: NeighborConfiguration,
    ) -> None:
        known_lsa_messages = list(self.latest_lsa_by_origin.values())

        for lsa_message_data in known_lsa_messages:
            forwarded_lsa_message = build_forwarded_lsa_message(
                lsa_message_data,
                forwarding_router_id=self.configuration.router_id,
            )
            self.send_lsa_to_neighbor(
                neighbor_configuration,
                forwarded_lsa_message,
            )

    def send_lsa_to_neighbor(
        self,
        neighbor_configuration: NeighborConfiguration,
        serialized_lsa_message: str,
    ) -> None:
        try:
            with socket.create_connection(
                (neighbor_configuration.ip, neighbor_configuration.port),
                timeout=CONNECTION_TIMEOUT_IN_SECONDS,
            ) as neighbor_socket:
                send_framed_text(neighbor_socket, serialized_lsa_message)

            print(
                f"[ROUTER {self.configuration.router_id}] "
                f"LSA enviada a {neighbor_configuration.router_id}."
            )
        except (ConnectionError, OSError, ValueError) as exception:
            self.register_neighbor_availability(
                neighbor_configuration.router_id,
                is_available=False,
                error_message=str(exception),
            )

    def respond_to_hello(
        self,
        client_socket: socket.socket,
        hello_message: dict[str, object],
    ) -> None:
        origin_router_id = hello_message["origin_router_id"]

        if not isinstance(origin_router_id, str):
            return

        neighbor_configuration = self.find_neighbor_configuration(
            origin_router_id
        )

        if neighbor_configuration is None:
            print(
                f"[ROUTER {self.configuration.router_id}] "
                f"HELLO rechazado: {origin_router_id} no es vecino configurado."
            )
            return

        hello_reply_message = build_hello_reply_message(
            self.configuration,
            neighbor_configuration.cost,
        )
        send_framed_text(client_socket, hello_reply_message)
        print(
            f"[ROUTER {self.configuration.router_id}] "
            f"HELLO recibido correctamente desde {origin_router_id}."
        )

    def discover_neighbors_periodically(self) -> None:
        while self.keep_running.is_set():
            for neighbor_configuration in self.configuration.neighbors:
                self.send_hello_to_neighbor(neighbor_configuration)

            self.keep_running.wait(NEIGHBOR_DISCOVERY_INTERVAL_IN_SECONDS)

    def send_hello_to_neighbor(
        self,
        neighbor_configuration: NeighborConfiguration,
    ) -> None:
        try:
            with socket.create_connection(
                (neighbor_configuration.ip, neighbor_configuration.port),
                timeout=CONNECTION_TIMEOUT_IN_SECONDS,
            ) as neighbor_socket:
                hello_message = build_hello_message(self.configuration)
                send_framed_text(neighbor_socket, hello_message)
                received_text = receive_framed_text(neighbor_socket)
                hello_reply_message = parse_control_message(received_text)

            self.validate_hello_reply(neighbor_configuration, hello_reply_message)
            neighbor_became_available = self.register_neighbor_availability(
                neighbor_configuration.router_id,
                is_available=True,
            )

            if neighbor_became_available:
                self.send_known_lsas_to_neighbor(neighbor_configuration)
        except (ConnectionError, OSError, ValueError) as exception:
            self.register_neighbor_availability(
                neighbor_configuration.router_id,
                is_available=False,
                error_message=str(exception),
            )

    def validate_hello_reply(
        self,
        neighbor_configuration: NeighborConfiguration,
        hello_reply_message: dict[str, object],
    ) -> None:
        if hello_reply_message["type"] != HELLO_REPLY_MESSAGE_TYPE:
            raise ValueError("Se esperaba un mensaje HELLO_REPLY.")

        received_router_id = hello_reply_message["origin_router_id"]

        if received_router_id != neighbor_configuration.router_id:
            raise ValueError(
                "HELLO_REPLY recibido desde un router distinto al esperado: "
                f"{received_router_id}."
            )

        received_cost = hello_reply_message["cost"]

        if received_cost != neighbor_configuration.cost:
            raise ValueError(
                "El costo recibido en HELLO_REPLY no coincide con la "
                f"configuración del enlace hacia {neighbor_configuration.router_id}."
            )

    def find_neighbor_configuration(
        self,
        router_id: str,
    ) -> NeighborConfiguration | None:
        for neighbor_configuration in self.configuration.neighbors:
            if neighbor_configuration.router_id == router_id:
                return neighbor_configuration

        return None

    def register_neighbor_availability(
        self,
        neighbor_router_id: str,
        is_available: bool,
        error_message: str = "",
    ) -> bool:
        previous_availability = self.neighbor_availability[neighbor_router_id]
        self.neighbor_availability[neighbor_router_id] = is_available
        neighbor_became_available = (
            is_available and previous_availability is not True
        )

        if previous_availability == is_available:
            return False

        if is_available:
            print(
                f"[ROUTER {self.configuration.router_id}] "
                f"Vecino {neighbor_router_id} confirmado mediante HELLO."
            )
            return neighbor_became_available

        print(
            f"[ROUTER {self.configuration.router_id}] "
            f"No fue posible contactar al vecino {neighbor_router_id}: "
            f"{error_message}"
        )
        return False

    def close(self) -> None:
        self.keep_running.clear()

        if self.listener_socket is not None:
            self.listener_socket.close()
            self.listener_socket = None

        self.wait_for_thread(self.listener_thread)
        self.wait_for_thread(self.neighbor_discovery_thread)

    def wait_for_thread(self, thread: threading.Thread | None) -> None:
        if thread is not None and thread is not threading.current_thread():
            thread.join()
