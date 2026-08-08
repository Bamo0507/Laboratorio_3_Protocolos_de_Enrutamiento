import random


def apply_bit_flip_noise(
    protected_codeword_bits: str,
    bit_flip_probability: float,
) -> str:
    validate_binary_bits(protected_codeword_bits)
    validate_bit_flip_probability(bit_flip_probability)

    noisy_bits = []

    for protected_bit in protected_codeword_bits:
        if random.random() < bit_flip_probability:
            noisy_bits.append(flip_bit(protected_bit))
        else:
            noisy_bits.append(protected_bit)

    return "".join(noisy_bits)


def flip_bit(bit: str) -> str:
    if bit == "0":
        return "1"

    return "0"


def validate_binary_bits(bits: str) -> None:
    if not isinstance(bits, str):
        raise ValueError("Los bits protegidos deben ser texto.")

    for bit in bits:
        if bit not in {"0", "1"}:
            raise ValueError("Los bits protegidos solo pueden contener 0 y 1.")


def validate_bit_flip_probability(bit_flip_probability: float) -> None:
    if (
        isinstance(bit_flip_probability, bool)
        or not isinstance(bit_flip_probability, (int, float))
    ):
        raise ValueError("La probabilidad de flip debe ser un número.")

    if bit_flip_probability < 0 or bit_flip_probability > 1:
        raise ValueError(
            "La probabilidad de flip debe estar entre 0.0 y 1.0."
        )
