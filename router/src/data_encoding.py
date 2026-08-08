from data_messages import DataMessage, serialize_data_message
from hamming74 import encode_data_bits


BITS_PER_BYTE = 8


def encode_data_message(data_message: DataMessage) -> str:
    serialized_data_message = serialize_data_message(data_message)
    data_bits = convert_utf8_text_to_bits(serialized_data_message)
    protected_codeword_bits = encode_data_bits(data_bits)
    return protected_codeword_bits


def convert_utf8_text_to_bits(text: str) -> str:
    utf8_bytes = text.encode("utf-8")
    byte_bits = []

    for utf8_byte in utf8_bytes:
        byte_bits.append(format(utf8_byte, f"0{BITS_PER_BYTE}b"))

    return "".join(byte_bits)
