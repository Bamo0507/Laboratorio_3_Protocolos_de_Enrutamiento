from argparse import ArgumentParser

from application.atm_client import AtmClient
from config.host_configuration import load_host_configuration
from transmission.host_transport import HostTransport


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--config", required=True)
    arguments = parser.parse_args()

    configuration = load_host_configuration(arguments.config)

    with HostTransport(configuration) as transport:
        AtmClient(configuration, transport).run()


main()
