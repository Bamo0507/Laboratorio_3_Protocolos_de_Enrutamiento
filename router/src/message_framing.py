import socket


LENGTH_HEADER_SIZE_IN_BYTES = 4
MAXIMUM_MESSAGE_SIZE_IN_BYTES = 1_000_000


def send_framed_text(connection_socket: socket.socket, text: str) -> None:
    message_bytes = text.encode("utf-8")
    message_size = len(message_bytes)

    if message_size > MAXIMUM_MESSAGE_SIZE_IN_BYTES:
        raise ValueError(
            "El mensaje excede el tamaño máximo permitido de "
            f"{MAXIMUM_MESSAGE_SIZE_IN_BYTES} bytes."
        )

    length_header = message_size.to_bytes(
        LENGTH_HEADER_SIZE_IN_BYTES,
        byteorder="big",
    )
    connection_socket.sendall(length_header + message_bytes)


def receive_framed_text(connection_socket: socket.socket) -> str:
    length_header = receive_exactly(
        connection_socket,
        LENGTH_HEADER_SIZE_IN_BYTES,
    )
    message_size = int.from_bytes(length_header, byteorder="big")

    if message_size > MAXIMUM_MESSAGE_SIZE_IN_BYTES:
        raise ValueError(
            "El mensaje recibido excede el tamaño máximo permitido de "
            f"{MAXIMUM_MESSAGE_SIZE_IN_BYTES} bytes."
        )

    message_bytes = receive_exactly(connection_socket, message_size)

    try:
        return message_bytes.decode("utf-8")
    except UnicodeDecodeError as exception:
        raise ValueError(
            "El contenido recibido no está codificado como texto UTF-8 válido."
        ) from exception


def receive_exactly(
    connection_socket: socket.socket,
    expected_byte_count: int,
) -> bytes:
    received_bytes = bytearray()

    while len(received_bytes) < expected_byte_count:
        remaining_byte_count = expected_byte_count - len(received_bytes)
        new_bytes = connection_socket.recv(remaining_byte_count)

        if not new_bytes:
            raise ConnectionError(
                "La conexión se cerró antes de recibir el mensaje completo."
            )

        received_bytes.extend(new_bytes)

    return bytes(received_bytes)
