import socket
import struct

from config.host_configuration import Address, HostConfiguration
from link.data_frame_codec import decode_data_message, encode_data_message
from noise.bit_noise import apply_bit_flip_noise
from protocol.data_message import DataMessage


FRAME_HEADER_SIZE_IN_BYTES = 4


class HostTransport:
    def __init__(self, configuration: HostConfiguration):
        self.configuration = configuration
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listening_socket.bind((configuration.listening_address.ip, configuration.listening_address.port))
        self.listening_socket.listen()

    def close(self) -> None:
        self.listening_socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self.close()

    def send_data_message(self, data_message: DataMessage) -> None:
        protected_bits = encode_data_message(data_message)
        noisy_bits = apply_bit_flip_noise(protected_bits, data_message.bit_flip_probability)
        self.send_framed_bits(self.configuration.gateway_address, noisy_bits)

    def receive_data_message(self) -> tuple[DataMessage, int]:
        connection, _ = self.listening_socket.accept()
        with connection:
            protected_bits = receive_framed_bits(connection)
        return decode_data_message(protected_bits)

    def send_framed_bits(self, address: Address, protected_bits: str) -> None:
        with socket.create_connection((address.ip, address.port)) as connection:
            send_framed_bits(connection, protected_bits)


def send_framed_bits(connection: socket.socket, protected_bits: str) -> None:
    encoded_bits = protected_bits.encode("ascii")
    frame_header = struct.pack(">I", len(encoded_bits))
    connection.sendall(frame_header + encoded_bits)


def receive_framed_bits(connection: socket.socket) -> str:
    frame_header = receive_exact_bytes(connection, FRAME_HEADER_SIZE_IN_BYTES)
    message_length = struct.unpack(">I", frame_header)[0]
    return receive_exact_bytes(connection, message_length).decode("ascii")


def receive_exact_bytes(connection: socket.socket, expected_byte_count: int) -> bytes:
    received_bytes = bytearray()
    while len(received_bytes) < expected_byte_count:
        next_chunk = connection.recv(expected_byte_count - len(received_bytes))
        if not next_chunk:
            raise ConnectionError("La conexión se cerró antes de completar la trama.")
        received_bytes.extend(next_chunk)
    return bytes(received_bytes)
