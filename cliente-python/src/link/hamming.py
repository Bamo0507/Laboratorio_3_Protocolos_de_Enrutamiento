class Hamming:
    DATA_BLOCK_SIZE = 8
    CODEWORD_BLOCK_SIZE = 12

    PARITY_POSITIONS = (1, 2, 4, 8)
    DATA_POSITIONS = (3, 5, 6, 7, 9, 10, 11, 12)

    PARITY_GROUPS = {
        1: (1, 3, 5, 7, 9, 11),
        2: (2, 3, 6, 7, 10, 11),
        4: (4, 5, 6, 7, 12),
        8: (8, 9, 10, 11, 12),
    }

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
    def _encode_block(data_block_bits: str) -> str:
        codeword_positions = ["0"] * (
            Hamming.CODEWORD_BLOCK_SIZE + 1
        )

        for data_index in range(Hamming.DATA_BLOCK_SIZE):
            codeword_position = Hamming.DATA_POSITIONS[
                data_index
            ]
            codeword_positions[codeword_position] = (
                data_block_bits[data_index]
            )

        for parity_position in Hamming.PARITY_POSITIONS:
            checked_positions = Hamming.PARITY_GROUPS[
                parity_position
            ]
            ones_count = 0

            for checked_position in checked_positions:
                if codeword_positions[checked_position] == "1":
                    ones_count += 1

            if ones_count % 2 == 0:
                parity_bit = "0"
            else:
                parity_bit = "1"

            codeword_positions[parity_position] = parity_bit

        return "".join(codeword_positions[1:])

    @staticmethod
    def encode(data_bits: str) -> str:
        Hamming._validate_bits(data_bits, "Los datos")

        if len(data_bits) % Hamming.DATA_BLOCK_SIZE != 0:
            raise ValueError(
                "La longitud de los datos debe ser "
                "múltiplo de 8."
            )

        encoded_blocks = []

        for block_start_position in range(
            0,
            len(data_bits),
            Hamming.DATA_BLOCK_SIZE,
        ):
            block_end_position = (
                block_start_position
                + Hamming.DATA_BLOCK_SIZE
            )
            data_block_bits = data_bits[
                block_start_position:block_end_position
            ]
            encoded_block_bits = Hamming._encode_block(
                data_block_bits
            )
            encoded_blocks.append(encoded_block_bits)

        return "".join(encoded_blocks)

    @staticmethod
    def _calculate_error_position(
        codeword_block_bits: str,
    ) -> int:
        codeword_positions = [""] + list(
            codeword_block_bits
        )
        error_position = 0

        for parity_position in Hamming.PARITY_POSITIONS:
            checked_positions = Hamming.PARITY_GROUPS[
                parity_position
            ]
            ones_count = 0

            for checked_position in checked_positions:
                if codeword_positions[checked_position] == "1":
                    ones_count += 1

            parity_failed = ones_count % 2 != 0

            if parity_failed:
                error_position += parity_position

        return error_position

    @staticmethod
    def _validate_codeword(codeword_bits: str):
        Hamming._validate_bits(
            codeword_bits,
            "La palabra código",
        )

        if (
            len(codeword_bits)
            % Hamming.CODEWORD_BLOCK_SIZE
            != 0
        ):
            raise ValueError(
                "La longitud de la palabra código debe ser "
                "múltiplo de 12."
            )

    @staticmethod
    def verify(codeword_bits: str) -> bool:
        Hamming._validate_codeword(codeword_bits)

        for block_start_position in range(
            0,
            len(codeword_bits),
            Hamming.CODEWORD_BLOCK_SIZE,
        ):
            block_end_position = (
                block_start_position
                + Hamming.CODEWORD_BLOCK_SIZE
            )
            codeword_block_bits = codeword_bits[
                block_start_position:block_end_position
            ]
            error_position = (
                Hamming._calculate_error_position(
                    codeword_block_bits
                )
            )

            if error_position != 0:
                return False

        return True

    @staticmethod
    def correct(codeword_bits: str) -> str:
        Hamming._validate_codeword(codeword_bits)
        corrected_blocks = []

        for block_start_position in range(
            0,
            len(codeword_bits),
            Hamming.CODEWORD_BLOCK_SIZE,
        ):
            block_end_position = (
                block_start_position
                + Hamming.CODEWORD_BLOCK_SIZE
            )
            codeword_block_bits = codeword_bits[
                block_start_position:block_end_position
            ]
            error_position = (
                Hamming._calculate_error_position(
                    codeword_block_bits
                )
            )
            corrected_block_bits = list(
                codeword_block_bits
            )

            if error_position > Hamming.CODEWORD_BLOCK_SIZE:
                raise ValueError(
                    "Hamming detectó un síndrome fuera "
                    "del bloque de 12 bits."
                )

            if error_position != 0:
                error_index = error_position - 1
                current_bit = corrected_block_bits[error_index]

                if current_bit == "0":
                    corrected_block_bits[error_index] = "1"
                else:
                    corrected_block_bits[error_index] = "0"

            corrected_blocks.append(
                "".join(corrected_block_bits)
            )

        return "".join(corrected_blocks)

    @staticmethod
    def recover_data(codeword_bits: str) -> str:
        corrected_codeword_bits = Hamming.correct(
            codeword_bits
        )
        recovered_data_bits = []

        for block_start_position in range(
            0,
            len(corrected_codeword_bits),
            Hamming.CODEWORD_BLOCK_SIZE,
        ):
            block_end_position = (
                block_start_position
                + Hamming.CODEWORD_BLOCK_SIZE
            )
            corrected_block_bits = corrected_codeword_bits[
                block_start_position:block_end_position
            ]

            for data_position in Hamming.DATA_POSITIONS:
                data_index = data_position - 1
                recovered_data_bits.append(
                    corrected_block_bits[data_index]
                )

        return "".join(recovered_data_bits)
