class Crc32:
    GENERATOR_BITS = "100000100110000010001110110110111"
    CRC_SIZE = 32

    @staticmethod
    def _validate_bits(bits: str, field_name: str):
        if not bits:
            raise ValueError(
                f"{field_name} no puede estar vacío."
            )

        for bit in bits:
            if bit != "0" and bit != "1":
                raise ValueError(
                    f"{field_name} solo puede contener 0 y 1."
                )

    @staticmethod
    def _divide(dividend_bits: str) -> str:
        working_dividend_bits = list(dividend_bits)
        generator_size = len(Crc32.GENERATOR_BITS)
        last_possible_division_position = (
            len(dividend_bits) - generator_size
        )

        for current_division_position in range(
            last_possible_division_position + 1
        ):
            current_dividend_bit = working_dividend_bits[
                current_division_position
            ]

            if current_dividend_bit == "0":
                continue

            for current_generator_position in range(
                generator_size
            ):
                current_dividend_position = (
                    current_division_position
                    + current_generator_position
                )

                dividend_bit = working_dividend_bits[
                    current_dividend_position
                ]
                generator_bit = Crc32.GENERATOR_BITS[
                    current_generator_position
                ]

                if dividend_bit == generator_bit:
                    working_dividend_bits[
                        current_dividend_position
                    ] = "0"
                else:
                    working_dividend_bits[
                        current_dividend_position
                    ] = "1"

        remainder_bits = working_dividend_bits[
            -Crc32.CRC_SIZE:
        ]
        return "".join(remainder_bits)

    @staticmethod
    def _calculate_remainder(data_bits: str) -> str:
        Crc32._validate_bits(data_bits, "Los datos")

        appended_zeros = "0" * Crc32.CRC_SIZE
        dividend_bits = data_bits + appended_zeros

        remainder_bits = Crc32._divide(dividend_bits)
        return remainder_bits

    @staticmethod
    def encode(data_bits: str) -> str:
        remainder_bits = Crc32._calculate_remainder(data_bits)
        codeword_bits = data_bits + remainder_bits

        return codeword_bits

    @staticmethod
    def verify(codeword_bits: str) -> bool:
        Crc32._validate_bits(
            codeword_bits,
            "La palabra código",
        )

        if len(codeword_bits) <= Crc32.CRC_SIZE:
            raise ValueError(
                "La palabra código debe contener datos "
                "y 32 bits de CRC."
            )

        calculated_remainder_bits = Crc32._divide(
            codeword_bits
        )
        expected_remainder_bits = "0" * Crc32.CRC_SIZE

        return (
            calculated_remainder_bits
            == expected_remainder_bits
        )

    @staticmethod
    def recover_data(codeword_bits: str) -> str:
        codeword_is_valid = Crc32.verify(codeword_bits)

        if not codeword_is_valid:
            raise ValueError(
                "CRC-32 detectó un error en la palabra código."
            )

        data_end_position = (
            len(codeword_bits) - Crc32.CRC_SIZE
        )
        original_data_bits = codeword_bits[
            :data_end_position
        ]

        return original_data_bits
