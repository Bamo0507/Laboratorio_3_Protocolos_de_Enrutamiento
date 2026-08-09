from link.hamming74 import encode_data_bits, recover_data_bits
from protocol.data_message import DataMessage


def encode_data_message(data_message: DataMessage) -> str:
    data_bits = text_to_bits(data_message.serialize())
    return encode_data_bits(data_bits)


def decode_data_message(codeword_bits: str) -> tuple[DataMessage, int]:
    recovered_data_bits = recover_data_bits(codeword_bits)
    serialized_message = bits_to_text(recovered_data_bits.data_bits)
    return DataMessage.parse(serialized_message), recovered_data_bits.corrected_block_count


def text_to_bits(text: str) -> str:
    return "".join(f"{byte:08b}" for byte in text.encode("utf-8"))


def bits_to_text(bits: str) -> str:
    if len(bits) % 8 != 0:
        raise ValueError("Los bits recuperados deben ser múltiplo de 8.")
    bytes_from_bits = bytes(int(bits[index:index + 8], 2) for index in range(0, len(bits), 8))
    return bytes_from_bits.decode("utf-8")
