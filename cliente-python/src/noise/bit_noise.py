from random import Random


class BitNoise:
    @staticmethod
    def apply(
        codeword_bits: str,
        average_flips: int,
        random_number_generator: Random | None = None,
    ) -> str:
        BitNoise._validate_codeword_bits(codeword_bits)
        BitNoise._validate_average_flips(
            average_flips,
            len(codeword_bits),
        )

        if random_number_generator is None:
            random_number_generator = Random()

        total_codeword_bits = len(codeword_bits)
        noisy_codeword_bits = []

        for original_bit in codeword_bits:
            random_number = random_number_generator.randint(
                1,
                total_codeword_bits,
            )
            bit_should_flip = random_number <= average_flips

            if bit_should_flip:
                if original_bit == "0":
                    noisy_bit = "1"
                else:
                    noisy_bit = "0"
            else:
                noisy_bit = original_bit

            noisy_codeword_bits.append(noisy_bit)

        return "".join(noisy_codeword_bits)

    @staticmethod
    def _validate_codeword_bits(codeword_bits: str):
        if not codeword_bits:
            raise ValueError(
                "La palabra código no puede estar vacía."
            )

        for bit in codeword_bits:
            if bit != "0" and bit != "1":
                raise ValueError(
                    "La palabra código solo puede contener 0 y 1."
                )

    @staticmethod
    def _validate_average_flips(
        average_flips: int,
        total_codeword_bits: int,
    ):
        if not isinstance(average_flips, int):
            raise TypeError(
                "La cantidad promedio de flips debe ser un entero."
            )

        if (
            average_flips < 0
            or average_flips > total_codeword_bits
        ):
            raise ValueError(
                "La cantidad promedio de flips debe ser "
                "mayor o igual a 0 y menor o igual a "
                f"{total_codeword_bits}."
            )
