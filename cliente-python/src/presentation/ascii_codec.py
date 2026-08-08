class AsciiCodec:
    @staticmethod
    def encode(message: str) -> str:
        try:
            ascii_bytes = message.encode("ascii")
        except UnicodeEncodeError as exception:
            raise ValueError(
                "El mensaje contiene caracteres fuera de ASCII."
            ) from exception

        return "".join(
            f"{byte:08b}"
            for byte in ascii_bytes
        )

    @staticmethod
    def decode(bits: str) -> str:
        if any(bit not in "01" for bit in bits):
            raise ValueError(
                "El mensaje binario solo puede contener 0 y 1."
            )

        if len(bits) % 8 != 0:
            raise ValueError(
                "La longitud del mensaje binario debe ser múltiplo de 8."
            )

        ascii_bytes = bytes(
            int(bits[position:position + 8], 2)
            for position in range(0, len(bits), 8)
        )

        try:
            return ascii_bytes.decode("ascii")
        except UnicodeDecodeError as exception:
            raise ValueError(
                "El mensaje binario contiene valores fuera de ASCII."
            ) from exception
