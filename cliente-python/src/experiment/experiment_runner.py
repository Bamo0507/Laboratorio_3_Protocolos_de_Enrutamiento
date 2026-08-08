import csv
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from link.crc32 import Crc32
from link.hamming import Hamming
from noise.bit_noise import BitNoise
from presentation.ascii_codec import AsciiCodec
from protocol.message import Command, ProtocolMessage
from protocol.session import Algorithm
from transmission.tcp_client import TcpClient


@dataclass(frozen=True)
class ExperimentPayload:
    page_range: str
    page_count: int
    text: str


class ExperimentRunner:
    ERROR_PROBABILITIES_PERCENT = (0.0, 0.01, 0.1, 1.0)
    WARMUP_REPETITIONS = 5
    MEASURED_REPETITIONS = 100

    CSV_FIELD_NAMES = (
        "algorithm",
        "pages",
        "page_count",
        "repetition",
        "payload_characters",
        "payload_bits",
        "serialized_data_bits",
        "codeword_bits",
        "redundancy_bits",
        "overhead_percentage",
        "configured_error_probability_percent",
        "effective_error_probability_percent",
        "configured_average_flips",
        "actual_flips",
        "round_trip_nanoseconds",
        "round_trip_milliseconds",
        "recovered_message_matches",
        "status",
    )

    def __init__(
        self,
        client: TcpClient,
        algorithm: Algorithm,
    ):
        self.client = client
        self.algorithm = algorithm

        client_directory = Path(__file__).resolve().parents[2]
        self.data_file_path = (
            client_directory
            / "experiments"
            / "data"
            / "chapter_783_pages_13_18.json"
        )
        self.results_directory = (
            client_directory
            / "experiments"
            / "results"
        )

    def run(self):
        experiment_payloads = self.load_experiment_payloads()
        measured_results = []

        self.start_experiment()

        for experiment_payload in experiment_payloads:
            for error_probability_percent in (
                self.ERROR_PROBABILITIES_PERCENT
            ):
                for _ in range(self.WARMUP_REPETITIONS):
                    self.execute_trial(
                        experiment_payload,
                        error_probability_percent,
                        repetition=0,
                    )

                for repetition in range(
                    1,
                    self.MEASURED_REPETITIONS + 1,
                ):
                    trial_result = self.execute_trial(
                        experiment_payload,
                        error_probability_percent,
                        repetition,
                    )
                    measured_results.append(trial_result)

                self.save_results(measured_results)
                print(
                    f"{self.algorithm.value} | páginas "
                    f"{experiment_payload.page_range} | error "
                    f"{error_probability_percent:g} % | "
                    f"{self.MEASURED_REPETITIONS} pruebas "
                    "completadas"
                )

        self.finish_experiment()
        print(
            "Resultados guardados en: "
            f"{self.get_results_file_path()}"
        )

    def load_experiment_payloads(self) -> list[ExperimentPayload]:
        with self.data_file_path.open(
            "r",
            encoding="utf-8",
        ) as data_file:
            pages = json.load(data_file)

        sorted_page_numbers = sorted(
            pages.keys(),
            key=int,
        )
        first_page_number = sorted_page_numbers[0]
        accumulated_page_texts = []
        experiment_payloads = []

        for page_number in sorted_page_numbers:
            page_text = pages[page_number]
            page_text.encode("ascii")
            accumulated_page_texts.append(page_text)

            if page_number == first_page_number:
                page_range = first_page_number
            else:
                page_range = (
                    f"{first_page_number}-{page_number}"
                )

            experiment_payloads.append(
                ExperimentPayload(
                    page_range=page_range,
                    page_count=len(accumulated_page_texts),
                    text="\n\n".join(accumulated_page_texts),
                )
            )

        return experiment_payloads

    def start_experiment(self):
        response = self.send_control_message(
            Command.START_EXPERIMENT
        )
        self.expect_command(response, Command.EXPERIMENT_READY)

    def finish_experiment(self):
        response = self.send_control_message(
            Command.END_EXPERIMENT
        )
        self.expect_command(
            response,
            Command.EXPERIMENT_FINISHED,
        )

    def send_control_message(
        self,
        command: Command,
    ) -> ProtocolMessage:
        message = ProtocolMessage(command)
        data_bits = AsciiCodec.encode(message.serialize())
        codeword_bits = self.calculate_integrity(data_bits)

        self.client.send(codeword_bits)
        return ProtocolMessage.parse(self.client.receive())

    def execute_trial(
        self,
        experiment_payload: ExperimentPayload,
        error_probability_percent: float,
        repetition: int,
    ) -> dict:
        expected_text_hash = hashlib.sha256(
            experiment_payload.text.encode("ascii")
        ).hexdigest()

        start_time = time.perf_counter_ns()

        message = ProtocolMessage(
            Command.EXPERIMENT_MESSAGE,
            experiment_payload.text,
        )
        serialized_message = message.serialize()
        data_bits = AsciiCodec.encode(serialized_message)
        codeword_bits = self.calculate_integrity(data_bits)

        error_probability = error_probability_percent / 100
        average_flips = round(
            error_probability * len(codeword_bits)
        )
        noisy_codeword_bits = BitNoise.apply(
            codeword_bits,
            average_flips,
        )
        actual_flips = self.count_bit_differences(
            codeword_bits,
            noisy_codeword_bits,
        )

        self.client.send(noisy_codeword_bits)
        response = ProtocolMessage.parse(self.client.receive())

        end_time = time.perf_counter_ns()

        recovered_message_matches = self.compare_recovered_hash(
            response,
            expected_text_hash,
        )
        status = self.classify_result(
            response,
            actual_flips,
            recovered_message_matches,
        )

        redundancy_bits = len(codeword_bits) - len(data_bits)
        round_trip_nanoseconds = end_time - start_time

        return {
            "algorithm": self.algorithm.value,
            "pages": experiment_payload.page_range,
            "page_count": experiment_payload.page_count,
            "repetition": repetition,
            "payload_characters": len(experiment_payload.text),
            "payload_bits": len(experiment_payload.text) * 8,
            "serialized_data_bits": len(data_bits),
            "codeword_bits": len(codeword_bits),
            "redundancy_bits": redundancy_bits,
            "overhead_percentage": (
                redundancy_bits / len(data_bits) * 100
            ),
            "configured_error_probability_percent": (
                error_probability_percent
            ),
            "effective_error_probability_percent": (
                average_flips / len(codeword_bits) * 100
            ),
            "configured_average_flips": average_flips,
            "actual_flips": actual_flips,
            "round_trip_nanoseconds": round_trip_nanoseconds,
            "round_trip_milliseconds": (
                round_trip_nanoseconds / 1_000_000
            ),
            "recovered_message_matches": (
                recovered_message_matches
            ),
            "status": status,
        }

    def calculate_integrity(self, data_bits: str) -> str:
        if self.algorithm == Algorithm.CRC32:
            return Crc32.encode(data_bits)

        return Hamming.encode(data_bits)

    def compare_recovered_hash(
        self,
        response: ProtocolMessage,
        expected_text_hash: str,
    ) -> bool | None:
        if (
            response.command
            != Command.EXPERIMENT_MESSAGE_RECOVERED
        ):
            return None

        return response.payload == expected_text_hash

    def classify_result(
        self,
        response: ProtocolMessage,
        actual_flips: int,
        recovered_message_matches: bool | None,
    ) -> str:
        if actual_flips == 0:
            if recovered_message_matches:
                return "CLEAN"

            raise ValueError(
                "Una trama sin ruido no fue recuperada "
                "correctamente."
            )

        if self.algorithm == Algorithm.CRC32:
            if (
                response.command
                == Command.EXPERIMENT_ERROR_DETECTED
            ):
                return "CRC_DETECTED"

            return "CRC_UNDETECTED_CORRUPTION"

        if recovered_message_matches:
            return "HAMMING_CORRECTED"

        return "HAMMING_RECOVERY_FAILED"

    def count_bit_differences(
        self,
        original_bits: str,
        noisy_bits: str,
    ) -> int:
        different_bits = 0

        for original_bit, noisy_bit in zip(
            original_bits,
            noisy_bits,
        ):
            if original_bit != noisy_bit:
                different_bits += 1

        return different_bits

    def save_results(self, measured_results: list[dict]):
        self.results_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.get_results_file_path().open(
            "w",
            encoding="utf-8",
            newline="",
        ) as results_file:
            writer = csv.DictWriter(
                results_file,
                fieldnames=self.CSV_FIELD_NAMES,
            )
            writer.writeheader()
            writer.writerows(measured_results)

    def get_results_file_path(self) -> Path:
        algorithm_file_name = self.algorithm.value.lower()
        return (
            self.results_directory
            / f"gear_fourth_{algorithm_file_name}_results.csv"
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
