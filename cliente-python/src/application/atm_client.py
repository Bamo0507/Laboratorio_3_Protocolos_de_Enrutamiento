from uuid import uuid4

from config.host_configuration import HostConfiguration
from protocol.data_message import DataMessage, HostRoute
from transmission.host_transport import HostTransport


class AtmClient:
    def __init__(self, configuration: HostConfiguration, transport: HostTransport):
        self.configuration = configuration
        self.transport = transport
        self.session_id = str(uuid4())
        self.bit_flip_probability = request_bit_flip_probability()

    def run(self) -> None:
        print("\n=== INICIO DE TRANSACCIÓN ===")
        self.expect_response(self.send_request("START_TRANSACTION"), "TRANSACTION_READY")

        print("\n=== AUTENTICACIÓN ===")
        card_number = input("Número de tarjeta: ").strip()
        card_response = self.send_request("CARD", card_number)

        if card_response.command == "CARD_INVALID":
            print("Tarjeta inválida. La sesión será cerrada.")
            return

        self.expect_response(card_response, "CARD_ACCEPTED")
        pin = input("PIN: ").strip()
        pin_response = self.send_request("PIN", pin)

        if pin_response.command == "PIN_INCORRECT":
            print("PIN incorrecto. La sesión será cerrada.")
            return

        self.expect_response(pin_response, "PIN_ACCEPTED")
        self.run_bank_operation()
        self.expect_response(self.send_request("LOGOUT"), "LOGOUT_ACK")
        print("Sesión finalizada correctamente.")

    def run_bank_operation(self) -> None:
        print("\n=== OPERACIÓN BANCARIA ===")
        selected_option = request_option()
        option_response = self.send_request("OPTION", selected_option)

        if selected_option == "1":
            self.expect_response(option_response, "BALANCE")
            print(f"Saldo disponible: {option_response.payload}")
            return

        self.expect_response(option_response, "REQUEST_AMOUNT")
        self.run_withdrawal()

    def run_withdrawal(self) -> None:
        print("\n=== RETIRO ===")

        while True:
            withdrawal_amount = input("Monto a retirar: ").strip()
            amount_response = self.send_request("AMOUNT", withdrawal_amount)

            if amount_response.command == "INSUFFICIENT_FUNDS":
                print(f"Fondos insuficientes. Saldo disponible: {amount_response.payload}")
                continue

            self.expect_response(amount_response, "WITHDRAWAL_SUCCESSFUL")
            print(f"Retiro realizado correctamente. Nuevo saldo: {amount_response.payload}")
            return

    def send_request(self, command: str, payload: str = "") -> DataMessage:
        request = DataMessage(
            packet_id=str(uuid4()),
            session_id=self.session_id,
            origin=HostRoute(self.configuration.host_id, self.configuration.gateway_id),
            destination=HostRoute(
                self.configuration.remote_host_id,
                self.configuration.remote_gateway_id,
            ),
            bit_flip_probability=self.bit_flip_probability,
            command=command,
            payload=payload,
        )
        self.transport.send_data_message(request)
        response, corrected_block_count = self.transport.receive_data_message()

        if corrected_block_count > 0:
            print(f"Hamming (7,4) corrigió {corrected_block_count} bloque(s) al recibir la respuesta.")

        if response.session_id != self.session_id:
            raise ValueError("La respuesta pertenece a una sesión distinta.")

        return response

    @staticmethod
    def expect_response(response: DataMessage, expected_command: str) -> None:
        if response.command != expected_command:
            raise ValueError(
                f"Se esperaba '{expected_command}', pero se recibió '{response.command}'."
            )


def request_bit_flip_probability() -> float:
    print("\n=== SIMULACIÓN DE RUIDO ===")
    print("Indica la probabilidad de que cada bit se invierta durante un salto.")
    print("0.0 = sin ruido; 0.01 = 1 % de probabilidad por bit; 1.0 = todos los bits.")

    while True:
        user_input = input("Probabilidad de flip por bit [Enter = 0.0]: ").strip()

        if not user_input:
            return 0.0

        try:
            probability = float(user_input)
        except ValueError:
            probability = -1.0

        if 0.0 <= probability <= 1.0:
            return probability

        print("Valor inválido. Ingresa un número entre 0.0 y 1.0.")


def request_option() -> str:
    while True:
        print("Seleccione una operación:")
        print("1. Consultar saldo")
        print("2. Retirar dinero")
        selected_option = input("> ").strip()

        if selected_option in {"1", "2"}:
            return selected_option

        print("Opción inválida. Ingresa 1 o 2.\n")
