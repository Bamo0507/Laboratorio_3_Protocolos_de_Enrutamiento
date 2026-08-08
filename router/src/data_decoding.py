from data_messages import DataMessage, parse_data_message
from hamming74 import recover_data_bits


BITS_PER_BYTE = 8


def decode_protected_codeword_bits(codeword_bits: str) -> DataMessage:
    recovered_data_bits = recover_data_bits(codeword_bits).data_bits
    serialized_data_message = convert_bits_to_utf8_text(recovered_data_bits)
    return parse_data_message(serialized_data_message)


def convert_bits_to_utf8_text(bits: str) -> str:
    if len(bits) % BITS_PER_BYTE != 0:
        raise ValueError(
            "Los bits recuperados deben tener una cantidad múltiplo de 8."
        )

    utf8_bytes = bytearray()

    for start_index in range(0, len(bits), BITS_PER_BYTE):
        byte_bits = bits[start_index:start_index + BITS_PER_BYTE]
        utf8_bytes.append(int(byte_bits, 2))

    try:
        return utf8_bytes.decode("utf-8")
    except UnicodeDecodeError as exception:
        raise ValueError(
            "Los bits recuperados no representan texto UTF-8 válido."
        ) from exception
