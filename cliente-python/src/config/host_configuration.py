import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Address:
    ip: str
    port: int


@dataclass(frozen=True)
class HostConfiguration:
    host_id: str
    listening_address: Address
    gateway_id: str
    gateway_address: Address
    remote_host_id: str
    remote_gateway_id: str


def load_host_configuration(configuration_file_path: str) -> HostConfiguration:
    try:
        configuration = json.loads(
            Path(configuration_file_path).read_text(encoding="utf-8")
        )
        return HostConfiguration(
            host_id=read_text(configuration, "host_id"),
            listening_address=read_address(configuration["listen"]),
            gateway_id=read_text(configuration["gateway"], "router_id"),
            gateway_address=read_address(configuration["gateway"]),
            remote_host_id=read_text(configuration["remote_host"], "host_id"),
            remote_gateway_id=read_text(configuration["remote_host"], "gateway_id"),
        )
    except FileNotFoundError as exception:
        raise ValueError("No existe el archivo de configuración del host.") from exception
    except (KeyError, TypeError, json.JSONDecodeError) as exception:
        raise ValueError("La configuración del host no tiene el formato esperado.") from exception


def read_address(address_data: dict) -> Address:
    port = address_data.get("port")

    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("El puerto debe estar entre 1 y 65535.")

    return Address(ip=read_text(address_data, "ip"), port=port)


def read_text(json_object: dict, field_name: str) -> str:
    value = json_object.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"El campo '{field_name}' debe ser texto no vacío.")

    return value
