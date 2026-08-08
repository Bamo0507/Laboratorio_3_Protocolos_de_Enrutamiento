from argparse import ArgumentParser

from application.atm_client import AtmClient, IntegrityError
from experiment.experiment_runner import ExperimentRunner
from protocol.message import Command, ProtocolMessage
from protocol.session import Algorithm, SessionState
from transmission.tcp_client import TcpClient


def send_message(
    client: TcpClient,
    command: Command,
    payload: str = "",
):
    message = ProtocolMessage(command, payload)
    client.send(message.serialize())


def receive_message(client: TcpClient) -> ProtocolMessage:
    return ProtocolMessage.parse(client.receive())


def expect(
    client: TcpClient,
    expected_command: Command,
    expected_payload: str = "",
):
    received = receive_message(client)

    if (
        received.command != expected_command
        or received.payload != expected_payload
    ):
        raise ValueError(
            f"Se esperaba '{expected_command.value}|{expected_payload}', "
            f"pero se recibió '{received.serialize()}'."
        )


def request_algorithm() -> Algorithm:
    while True:
        print("Seleccione el algoritmo:")
        print("1. Hamming")
        print("2. CRC-32")
        option = input("> ").strip()

        if option == "1":
            return Algorithm.HAMMING

        if option == "2":
            return Algorithm.CRC32

        print("Opción inválida. Ingrese 1 o 2.\n")


def main():
    parser = ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1234)
    parser.add_argument("--name")
    parser.add_argument(
        "--testing",
        action="store_true",
    )
    parser.add_argument(
        "--algorithm",
        choices=("CRC32", "HAMMING"),
    )
    args = parser.parse_args()

    if args.testing and args.algorithm is None:
        parser.error(
            "--algorithm es obligatorio cuando se usa --testing."
        )

    if not args.testing and not args.name:
        parser.error(
            "--name es obligatorio para ejecutar el cajero."
        )

    if args.testing:
        algorithm = Algorithm(args.algorithm)
        client_name = f"Experiment-{algorithm.value}"
    else:
        algorithm = None
        client_name = args.name

    session = SessionState()

    with TcpClient(args.host, args.port) as client:
        send_message(client, Command.YOU_THERE)
        expect(client, Command.SAY_YOUR_NAME)

        send_message(client, Command.REPLY_NAME, client_name)
        expect(client, Command.RECEIVED_NAME)
        session.register_name(client_name)

        if algorithm is None:
            algorithm = request_algorithm()

        send_message(
            client,
            Command.SELECT_ALGORITHM,
            algorithm.value,
        )

        response = receive_message(client)

        if response.command == Command.ALGORITHM_REJECTED:
            raise ValueError("El servidor rechazó el algoritmo.")

        if (
            response.command != Command.ALGORITHM_ACCEPTED
            or response.payload != algorithm.value
        ):
            raise ValueError(
                f"Respuesta inesperada: '{response.serialize()}'."
            )

        session.select_algorithm(algorithm)

        if args.testing:
            experiment_runner = ExperimentRunner(
                client,
                session.algorithm,
            )
            experiment_runner.run()
            print(
                "Experimento finalizado correctamente con "
                f"{session.algorithm.value}."
            )
            return

        atm_client = AtmClient(client, session)

        try:
            atm_client.run()
        except IntegrityError as exception:
            print(exception)
            return

    print(
        "Sesión finalizada correctamente con "
        f"{session.algorithm.value}."
    )


main()
