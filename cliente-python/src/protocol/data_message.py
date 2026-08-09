import json
from dataclasses import dataclass


SUPPORTED_COMMANDS = {
    "START_TRANSACTION", "TRANSACTION_READY", "CARD", "CARD_ACCEPTED",
    "CARD_INVALID", "PIN", "PIN_ACCEPTED", "PIN_INCORRECT", "OPTION",
    "BALANCE", "REQUEST_AMOUNT", "AMOUNT", "WITHDRAWAL_SUCCESSFUL",
    "INSUFFICIENT_FUNDS", "PROTOCOL_ERROR", "LOGOUT", "LOGOUT_ACK",
}


@dataclass(frozen=True)
class HostRoute:
    host_id: str
    gateway_id: str


@dataclass(frozen=True)
class DataMessage:
    packet_id: str
    session_id: str
    origin: HostRoute
    destination: HostRoute
    bit_flip_probability: float
    command: str
    payload: str

    def serialize(self) -> str:
        self.validate()
        return json.dumps({
            "type": "DATA", "packet_id": self.packet_id, "session_id": self.session_id,
            "origin": {"host_id": self.origin.host_id, "gateway_id": self.origin.gateway_id},
            "destination": {"host_id": self.destination.host_id, "gateway_id": self.destination.gateway_id},
            "noise": {"bit_flip_probability": self.bit_flip_probability},
            "payload": {"command": self.command, "payload": self.payload},
        }, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def parse(cls, serialized_message: str):
        try:
            data = json.loads(serialized_message)
            message = cls(
                data["packet_id"], data["session_id"], HostRoute(**data["origin"]),
                HostRoute(**data["destination"]), data["noise"]["bit_flip_probability"],
                data["payload"]["command"], data["payload"]["payload"],
            )
        except (KeyError, TypeError, json.JSONDecodeError) as exception:
            raise ValueError("El mensaje DATA no tiene el formato acordado.") from exception
        if data.get("type") != "DATA":
            raise ValueError("El campo 'type' debe ser 'DATA'.")
        message.validate()
        return message

    def validate(self) -> None:
        required_values = [
            self.packet_id, self.session_id, self.origin.host_id,
            self.origin.gateway_id, self.destination.host_id,
            self.destination.gateway_id, self.command,
        ]
        if any(not isinstance(value, str) or not value.strip() for value in required_values):
            raise ValueError("Los identificadores DATA deben ser texto no vacío.")
        if not isinstance(self.payload, str):
            raise ValueError("El payload debe ser texto.")
        if self.command not in SUPPORTED_COMMANDS:
            raise ValueError(f"El comando no es reconocido: {self.command}.")
        if isinstance(self.bit_flip_probability, bool) or not isinstance(self.bit_flip_probability, (int, float)):
            raise ValueError("La probabilidad de flip debe ser numérica.")
        if not 0 <= self.bit_flip_probability <= 1:
            raise ValueError("La probabilidad de flip debe estar entre 0.0 y 1.0.")
