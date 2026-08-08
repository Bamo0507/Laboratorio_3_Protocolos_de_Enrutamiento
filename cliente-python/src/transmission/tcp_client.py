import socket


class TcpClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None

    def __enter__(self):
        self.socket = socket.create_connection((self.host, self.port))
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.socket:
            self.socket.close()
            self.socket = None

    def send(self, message: str):
        data = message.encode("utf-8")
        header = len(data).to_bytes(4, "big")
        self.socket.sendall(header + data)

    def receive(self) -> str:
        header = self._receive_exactly(4)
        length = int.from_bytes(header, "big")
        data = self._receive_exactly(length)
        return data.decode("utf-8")

    def _receive_exactly(self, size: int) -> bytes:
        data = b""

        while len(data) < size:
            chunk = self.socket.recv(size - len(data))

            if not chunk:
                raise ConnectionError("El servidor cerró la conexión.")

            data += chunk

        return data
