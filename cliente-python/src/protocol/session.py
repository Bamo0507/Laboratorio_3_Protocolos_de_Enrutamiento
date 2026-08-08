from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Algorithm(Enum):
    HAMMING = "HAMMING"
    CRC32 = "CRC32"


class SessionPhase(Enum):
    CONNECTED = "CONNECTED"
    NAME_RECEIVED = "NAME_RECEIVED"
    ALGORITHM_SELECTED = "ALGORITHM_SELECTED"
    WAITING_CARD = "WAITING_CARD"
    WAITING_PIN = "WAITING_PIN"
    WAITING_OPTION = "WAITING_OPTION"
    WAITING_AMOUNT = "WAITING_AMOUNT"
    COMPLETED = "COMPLETED"


@dataclass
class SessionState:
    name: Optional[str] = None
    algorithm: Optional[Algorithm] = None
    phase: SessionPhase = SessionPhase.CONNECTED

    def register_name(self, name: str):
        if self.phase != SessionPhase.CONNECTED:
            raise ValueError("El nombre llegó fuera de secuencia.")

        if not name:
            raise ValueError("El nombre no puede estar vacío.")

        self.name = name
        self.phase = SessionPhase.NAME_RECEIVED

    def select_algorithm(self, algorithm: Algorithm):
        if self.phase != SessionPhase.NAME_RECEIVED:
            raise ValueError("El algoritmo llegó fuera de secuencia.")

        self.algorithm = algorithm
        self.phase = SessionPhase.ALGORITHM_SELECTED

    def start_transaction(self):
        if self.phase != SessionPhase.ALGORITHM_SELECTED:
            raise ValueError(
                "La transacción inició fuera de secuencia."
            )

        self.phase = SessionPhase.WAITING_CARD

    def accept_card(self):
        if self.phase != SessionPhase.WAITING_CARD:
            raise ValueError(
                "La tarjeta fue aceptada fuera de secuencia."
            )

        self.phase = SessionPhase.WAITING_PIN

    def accept_pin(self):
        if self.phase != SessionPhase.WAITING_PIN:
            raise ValueError(
                "El PIN fue aceptado fuera de secuencia."
            )

        self.phase = SessionPhase.WAITING_OPTION

    def select_balance_inquiry(self):
        if self.phase != SessionPhase.WAITING_OPTION:
            raise ValueError(
                "La consulta de saldo ocurrió fuera de secuencia."
            )

        self.phase = SessionPhase.COMPLETED

    def select_withdrawal(self):
        if self.phase != SessionPhase.WAITING_OPTION:
            raise ValueError(
                "El retiro fue seleccionado fuera de secuencia."
            )

        self.phase = SessionPhase.WAITING_AMOUNT

    def complete_withdrawal(self):
        if self.phase != SessionPhase.WAITING_AMOUNT:
            raise ValueError(
                "El retiro finalizó fuera de secuencia."
            )

        self.phase = SessionPhase.COMPLETED
