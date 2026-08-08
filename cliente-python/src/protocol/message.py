from dataclasses import dataclass
from enum import Enum


class Command(Enum):
    YOU_THERE = "YOU_THERE"
    SAY_YOUR_NAME = "SAY_YOUR_NAME"
    REPLY_NAME = "REPLY_NAME"
    RECEIVED_NAME = "RECEIVED_NAME"
    SELECT_ALGORITHM = "SELECT_ALGORITHM"
    ALGORITHM_ACCEPTED = "ALGORITHM_ACCEPTED"
    ALGORITHM_REJECTED = "ALGORITHM_REJECTED"
    INTEGRITY_ERROR = "INTEGRITY_ERROR"
    HAMMING_CORRECTION_APPLIED = "HAMMING_CORRECTION_APPLIED"
    START_TRANSACTION = "START_TRANSACTION"
    TRANSACTION_READY = "TRANSACTION_READY"
    CARD = "CARD"
    CARD_ACCEPTED = "CARD_ACCEPTED"
    CARD_INVALID = "CARD_INVALID"
    PIN = "PIN"
    PIN_ACCEPTED = "PIN_ACCEPTED"
    PIN_INCORRECT = "PIN_INCORRECT"
    OPTION = "OPTION"
    BALANCE = "BALANCE"
    REQUEST_AMOUNT = "REQUEST_AMOUNT"
    AMOUNT = "AMOUNT"
    WITHDRAWAL_SUCCESSFUL = "WITHDRAWAL_SUCCESSFUL"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    START_EXPERIMENT = "START_EXPERIMENT"
    EXPERIMENT_READY = "EXPERIMENT_READY"
    EXPERIMENT_MESSAGE = "EXPERIMENT_MESSAGE"
    EXPERIMENT_MESSAGE_RECOVERED = "EXPERIMENT_MESSAGE_RECOVERED"
    EXPERIMENT_ERROR_DETECTED = "EXPERIMENT_ERROR_DETECTED"
    EXPERIMENT_RECOVERY_FAILED = "EXPERIMENT_RECOVERY_FAILED"
    END_EXPERIMENT = "END_EXPERIMENT"
    EXPERIMENT_FINISHED = "EXPERIMENT_FINISHED"


@dataclass(frozen=True)
class ProtocolMessage:
    command: Command
    payload: str = ""

    def serialize(self) -> str:
        return f"{self.command.value}|{self.payload}"

    @classmethod
    def parse(cls, raw_message: str):
        command_text, separator, payload = raw_message.partition("|")

        if not separator or not command_text:
            raise ValueError(f"Mensaje inválido: '{raw_message}'.")

        try:
            command = Command(command_text)
        except ValueError:
            raise ValueError(f"Comando desconocido: '{command_text}'.")

        return cls(command, payload)
