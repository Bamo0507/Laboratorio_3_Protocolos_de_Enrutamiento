import argparse

from router_config import load_router_configuration
from router_node import RouterNode


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Inicia un router del laboratorio de protocolos de enrutamiento."
    )
    argument_parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo JSON de configuración del router.",
    )
    arguments = argument_parser.parse_args()

    router_configuration = load_router_configuration(arguments.config)
    router_node = RouterNode(router_configuration)

    try:
        router_node.start_listening()
        router_node.accept_connections()
    except KeyboardInterrupt:
        print("\nRouter detenido por el usuario.")
    finally:
        router_node.close()


main()
