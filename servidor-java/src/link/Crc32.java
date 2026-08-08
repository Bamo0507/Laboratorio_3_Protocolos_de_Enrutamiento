package link;


public final class Crc32 {
    private static final String GENERATOR_BITS =
        "100000100110000010001110110110111";
    private static final int CRC_SIZE = 32;

    private Crc32() {
    }

    private static void validateBits(
        String bits,
        String fieldName
    ) {
        if (bits == null || bits.isEmpty()) {
            throw new IllegalArgumentException(
                fieldName + " no puede estar vacío."
            );
        }

        for (
            int currentBitPosition = 0;
            currentBitPosition < bits.length();
            currentBitPosition++
        ) {
            char currentBit = bits.charAt(currentBitPosition);

            if (currentBit != '0' && currentBit != '1') {
                throw new IllegalArgumentException(
                    fieldName + " solo puede contener 0 y 1."
                );
            }
        }
    }

    private static String divide(String dividendBits) {
        char[] workingDividendBits =
            dividendBits.toCharArray();
        int generatorSize = GENERATOR_BITS.length();
        int lastPossibleDivisionPosition =
            dividendBits.length() - generatorSize;

        for (
            int currentDivisionPosition = 0;
            currentDivisionPosition
                <= lastPossibleDivisionPosition;
            currentDivisionPosition++
        ) {
            char currentDividendBit =
                workingDividendBits[currentDivisionPosition];

            if (currentDividendBit == '0') {
                continue;
            }

            for (
                int currentGeneratorPosition = 0;
                currentGeneratorPosition < generatorSize;
                currentGeneratorPosition++
            ) {
                int currentDividendPosition =
                    currentDivisionPosition
                    + currentGeneratorPosition;

                char dividendBit = workingDividendBits[
                    currentDividendPosition
                ];
                char generatorBit = GENERATOR_BITS.charAt(
                    currentGeneratorPosition
                );

                if (dividendBit == generatorBit) {
                    workingDividendBits[
                        currentDividendPosition
                    ] = '0';
                } else {
                    workingDividendBits[
                        currentDividendPosition
                    ] = '1';
                }
            }
        }

        int remainderStartPosition =
            workingDividendBits.length - CRC_SIZE;

        return new String(
            workingDividendBits,
            remainderStartPosition,
            CRC_SIZE
        );
    }

    private static String calculateRemainder(
        String dataBits
    ) {
        validateBits(dataBits, "Los datos");

        String appendedZeros = "0".repeat(CRC_SIZE);
        String dividendBits = dataBits + appendedZeros;

        String remainderBits = divide(dividendBits);
        return remainderBits;
    }

    public static String encode(String dataBits) {
        String remainderBits =
            calculateRemainder(dataBits);
        String codewordBits = dataBits + remainderBits;

        return codewordBits;
    }

    public static boolean verify(String codewordBits) {
        validateBits(
            codewordBits,
            "La palabra código"
        );

        if (codewordBits.length() <= CRC_SIZE) {
            throw new IllegalArgumentException(
                "La palabra código debe contener datos "
                + "y 32 bits de CRC."
            );
        }

        String calculatedRemainderBits =
            divide(codewordBits);
        String expectedRemainderBits =
            "0".repeat(CRC_SIZE);

        return calculatedRemainderBits.equals(
            expectedRemainderBits
        );
    }

    public static String recoverData(
        String codewordBits
    ) {
        boolean codewordIsValid = verify(codewordBits);

        if (!codewordIsValid) {
            throw new IllegalArgumentException(
                "CRC-32 detectó un error "
                + "en la palabra código."
            );
        }

        int dataEndPosition =
            codewordBits.length() - CRC_SIZE;
        String originalDataBits = codewordBits.substring(
            0,
            dataEndPosition
        );

        return originalDataBits;
    }
}
