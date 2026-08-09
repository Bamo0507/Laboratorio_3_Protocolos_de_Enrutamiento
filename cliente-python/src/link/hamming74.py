from dataclasses import dataclass


DATA_BIT_COUNT = 4
CODEWORD_BIT_COUNT = 7


@dataclass(frozen=True)
class RecoveredDataBits:
    data_bits: str
    corrected_block_count: int


def encode_data_bits(data_bits: str) -> str:
    validate_binary_bits(data_bits, "Los bits de datos")
    if len(data_bits) % DATA_BIT_COUNT != 0:
        raise ValueError("Los bits de datos deben ser múltiplo de 4.")
    encoded_blocks = []
    for start_index in range(0, len(data_bits), DATA_BIT_COUNT):
        data_block = data_bits[start_index:start_index + DATA_BIT_COUNT]
        encoded_blocks.append(encode_data_block(data_block))
    return "".join(encoded_blocks)


def recover_data_bits(codeword_bits: str) -> RecoveredDataBits:
    validate_binary_bits(codeword_bits, "Los bits de la trama")
    if len(codeword_bits) % CODEWORD_BIT_COUNT != 0:
        raise ValueError("Los bits de la trama deben ser múltiplo de 7.")
    recovered_blocks = []
    corrected_block_count = 0
    for start_index in range(0, len(codeword_bits), CODEWORD_BIT_COUNT):
        codeword_block = codeword_bits[start_index:start_index + CODEWORD_BIT_COUNT]
        recovered_block, block_was_corrected = recover_data_block(codeword_block)
        recovered_blocks.append(recovered_block)
        if block_was_corrected:
            corrected_block_count += 1
    return RecoveredDataBits("".join(recovered_blocks), corrected_block_count)


def encode_data_block(data_block: str) -> str:
    if len(data_block) != DATA_BIT_COUNT:
        raise ValueError("Un bloque de datos Hamming debe tener 4 bits.")
    codeword_by_position = [None, 0, 0, int(data_block[0]), 0, int(data_block[1]), int(data_block[2]), int(data_block[3])]
    codeword_by_position[1] = calculate_even_parity(codeword_by_position, [3, 5, 7])
    codeword_by_position[2] = calculate_even_parity(codeword_by_position, [3, 6, 7])
    codeword_by_position[4] = calculate_even_parity(codeword_by_position, [5, 6, 7])
    return "".join(str(codeword_by_position[position]) for position in range(1, 8))


def recover_data_block(codeword_block: str) -> tuple[str, bool]:
    codeword_by_position = [None] + [int(bit) for bit in codeword_block]
    error_position = calculate_error_position(codeword_by_position)
    if error_position != 0:
        codeword_by_position[error_position] = 1 - codeword_by_position[error_position]
    recovered_data_bits = "".join(str(codeword_by_position[position]) for position in [3, 5, 6, 7])
    return recovered_data_bits, error_position != 0


def calculate_even_parity(codeword_by_position: list[int | None], data_positions: list[int]) -> int:
    parity = 0
    for position in data_positions:
        parity ^= codeword_by_position[position]
    return parity


def calculate_error_position(codeword_by_position: list[int | None]) -> int:
    parity_check_1 = calculate_parity_check(codeword_by_position, [1, 3, 5, 7])
    parity_check_2 = calculate_parity_check(codeword_by_position, [2, 3, 6, 7])
    parity_check_4 = calculate_parity_check(codeword_by_position, [4, 5, 6, 7])
    return parity_check_1 + (parity_check_2 * 2) + (parity_check_4 * 4)


def calculate_parity_check(codeword_by_position: list[int | None], positions: list[int]) -> int:
    parity_check = 0
    for position in positions:
        parity_check ^= codeword_by_position[position]
    return parity_check


def validate_binary_bits(bits: str, description: str) -> None:
    if not isinstance(bits, str) or any(bit not in {"0", "1"} for bit in bits):
        raise ValueError(f"{description} solo pueden contener 0 y 1.")
