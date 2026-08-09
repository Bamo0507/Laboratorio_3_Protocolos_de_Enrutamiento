from random import random


def apply_bit_flip_noise(codeword_bits: str, bit_flip_probability: float) -> str:
    if not 0.0 <= bit_flip_probability <= 1.0:
        raise ValueError("La probabilidad de flip debe estar entre 0.0 y 1.0.")

    noisy_bits = []

    for bit in codeword_bits:
        if random() < bit_flip_probability:
            noisy_bits.append(flip_bit(bit))
        else:
            noisy_bits.append(bit)

    return "".join(noisy_bits)


def flip_bit(bit: str) -> str:
    return "1" if bit == "0" else "0"
