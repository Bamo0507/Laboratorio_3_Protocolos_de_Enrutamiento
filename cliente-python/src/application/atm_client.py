from link.crc32 import Crc32
from link.hamming import Hamming
from noise.bit_noise import BitNoise
from presentation.ascii_codec import AsciiCodec
from protocol.message import Command, ProtocolMessage
from protocol.session import Algorithm, SessionState
from transmission.tcp_client import TcpClient


class IntegrityError(Exception):
    pass


class AtmClient:
    def __init__(
        self,
        client: TcpClient,
        session: SessionState,
    ):
        self.client = client
        self.session = session
        self.previous_average_flips = 0
        self.noise_explanation_was_shown = False

    def run(self):
        print("\n=== INICIO DE TRANSACCIÓN ===")
        response = self.send_protected_request(
            Command.START_TRANSACTION
        )
        self.expect_command(
            response,
            Command.TRANSACTION_READY,
        )
        self.session.start_transaction()

        print("\n=== AUTENTICACIÓN ===")
        card_number = self.request_card()
        response = self.send_protected_request(
            Command.CARD,
            card_number,
        )

        if response.command == Command.CARD_INVALID:
            print("Tarjeta inválida. La sesión será cerrada.")
            return

        self.expect_command(response, Command.CARD_ACCEPTED)
        self.session.accept_card()

        pin = self.request_pin()
        response = self.send_protected_request(
            Command.PIN,
            pin,
        )

        if response.command == Command.PIN_INCORRECT:
            print("PIN incorrecto. La sesión será cerrada.")
            return

        self.expect_command(response, Command.PIN_ACCEPTED)
        self.session.accept_pin()

        print("\n=== OPERACIÓN BANCARIA ===")
        selected_option = self.request_option()
        response = self.send_protected_request(
            Command.OPTION,
            selected_option,
        )

        if selected_option == "1":
            self.expect_command(response, Command.BALANCE)
            self.session.select_balance_inquiry()
            print(f"Saldo disponible: {response.payload}")
            return

        self.expect_command(response, Command.REQUEST_AMOUNT)
        self.session.select_withdrawal()
        print("\n=== RETIRO ===")
        self.process_withdrawal()

    def process_withdrawal(self):
        while True:
            withdrawal_amount = self.request_withdrawal_amount()
            response = self.send_protected_request(
                Command.AMOUNT,
                str(withdrawal_amount),
            )

            if response.command == Command.INSUFFICIENT_FUNDS:
                print(
                    "Fondos insuficientes. "
                    f"Saldo disponible: {response.payload}"
                )
                continue

            self.expect_command(
                response,
                Command.WITHDRAWAL_SUCCESSFUL,
            )
            self.session.complete_withdrawal()
            print(
                "Retiro realizado correctamente. "
                f"Nuevo saldo: {response.payload}"
            )
            return

    def send_protected_request(
        self,
        command: Command,
        payload: str = "",
    ) -> ProtocolMessage:
        message = ProtocolMessage(command, payload)
        serialized_message = message.serialize()
        data_bits = AsciiCodec.encode(serialized_message)

        if self.session.algorithm == Algorithm.CRC32:
            codeword_bits = Crc32.encode(data_bits)
        elif self.session.algorithm == Algorithm.HAMMING:
            codeword_bits = Hamming.encode(data_bits)
        else:
            raise ValueError(
                "No se ha seleccionado un algoritmo."
            )

        average_flips = self.request_average_flips(
            command,
            len(codeword_bits)
        )
        noisy_codeword_bits = BitNoise.apply(
            codeword_bits,
            average_flips,
        )

        self.client.send(noisy_codeword_bits)
        response = ProtocolMessage.parse(
            self.client.receive()
        )

        if (
            response.command
            == Command.HAMMING_CORRECTION_APPLIED
        ):
            print(
                "HAMMING: se detectó un síndrome y se aplicó "
                "la corrección. La operación continuará."
            )
            response = ProtocolMessage.parse(
                self.client.receive()
            )

        if response.command == Command.INTEGRITY_ERROR:
            if self.session.algorithm == Algorithm.CRC32:
                raise IntegrityError(
                    "ERROR CRC-32: se detectó que uno o más "
                    "bits fueron alterados. CRC-32 no puede "
                    "corregirlos. Cerrando conexión."
                )

            raise IntegrityError(
                "ERROR HAMMING: no fue posible recuperar el "
                "mensaje. Es posible que más de un bit haya "
                "cambiado dentro de un bloque de 12 bits. "
                "Cerrando conexión."
            )

        if response.command == Command.PROTOCOL_ERROR:
            raise ValueError(
                "El servidor detectó un error de protocolo."
            )

        return response

    def request_average_flips(
        self,
        command: Command,
        total_codeword_bits: int,
    ) -> int:
        if not self.noise_explanation_was_shown:
            self.show_noise_explanation()

        while True:
            algorithm_name = self.session.algorithm.value

            if self.session.algorithm == Algorithm.CRC32:
                algorithm_name = "CRC-32"

            print(
                "\n--- ENVÍO PROTEGIDO: "
                f"{command.value} ---"
            )
            print(
                f"Trama: {total_codeword_bits} bits | "
                f"Algoritmo: {algorithm_name}"
            )

            previous_value_is_valid = (
                self.previous_average_flips
                <= total_codeword_bits
            )

            if previous_value_is_valid:
                print(
                    "Flips promedio entre 0 y "
                    f"{total_codeword_bits} "
                    f"[Enter = {self.previous_average_flips}]:"
                )
            else:
                print(
                    "El valor anterior "
                    f"({self.previous_average_flips}) supera "
                    "el tamaño de esta trama."
                )
                print(
                    "Ingresa un nuevo valor entre 0 y "
                    f"{total_codeword_bits}:"
                )

            user_input = input("> ").strip()

            if not user_input and previous_value_is_valid:
                return self.previous_average_flips

            try:
                average_flips = int(user_input)
            except ValueError:
                average_flips = -1

            if 0 <= average_flips <= total_codeword_bits:
                self.previous_average_flips = average_flips
                return average_flips

            print(
                "Valor inválido. Ingresa un número entero "
                "mayor o igual a 0 y menor o igual a "
                f"{total_codeword_bits}."
            )

    def show_noise_explanation(self):
        # We wanted to give it a comical sense by adding a sarcastic print.
        print("\n¡HAS SIDO HACKEADO!")
        print("=== SIMULACIÓN DE RUIDO ===")
        print(
            "Cada mensaje protegido pasa por esta capa "
            "antes de enviarse."
        )
        print(
            "El valor representa cuántos bits cambiarán "
            "en promedio."
        )
        print(
            "La cantidad exacta puede variar porque cada bit "
            "se evalúa independientemente."
        )

        if self.session.algorithm == Algorithm.CRC32:
            print(
                "CRC-32 detecta errores, pero no puede "
                "corregirlos."
            )
            print(
                "Si el mensaje resulta alterado, la sesión "
                "será cerrada."
            )
        else:
            print(
                "Hamming trabaja con bloques de 12 bits y "
                "puede corregir como máximo un error por bloque."
            )

        self.noise_explanation_was_shown = True

    def request_card(self) -> str:
        return input("Número de tarjeta: ").strip()

    def request_pin(self) -> str:
        return input("PIN: ").strip()

    def request_option(self) -> str:
        while True:
            print("\nSeleccione una operación:")
            print("1. Consultar saldo")
            print("2. Retirar dinero")
            selected_option = input("> ").strip()

            if selected_option in ("1", "2"):
                return selected_option

            print(
                "Opción inválida. Ingrese 1 o 2."
            )

    def request_withdrawal_amount(self) -> int:
        while True:
            user_input = input("Monto a retirar: ").strip()

            try:
                withdrawal_amount = int(user_input)
            except ValueError:
                withdrawal_amount = 0

            if withdrawal_amount > 0:
                return withdrawal_amount

            print(
                "Monto inválido. Ingrese un número entero "
                "mayor que 0."
            )

    def expect_command(
        self,
        response: ProtocolMessage,
        expected_command: Command,
    ):
        if response.command != expected_command:
            raise ValueError(
                f"Se esperaba '{expected_command.value}', "
                f"pero se recibió '{response.serialize()}'."
            )
