package link;

import java.util.Arrays;


public final class Hamming {
    private static final int DATA_BLOCK_SIZE = 8;
    private static final int CODEWORD_BLOCK_SIZE = 12;

    private static final int[] PARITY_POSITIONS = {
        1, 2, 4, 8
    };

    private static final int[] DATA_POSITIONS = {
        3, 5, 6, 7, 9, 10, 11, 12
    };

    private Hamming() {
    }

    private static int[] getCheckedPositions(
        int parityPosition
    ) {
        if (parityPosition == 1) {
            return new int[] {1, 3, 5, 7, 9, 11};
        }

        if (parityPosition == 2) {
            return new int[] {2, 3, 6, 7, 10, 11};
        }

        if (parityPosition == 4) {
            return new int[] {4, 5, 6, 7, 12};
        }

        if (parityPosition == 8) {
            return new int[] {8, 9, 10, 11, 12};
        }

        throw new IllegalArgumentException(
            "Posición de paridad desconocida: "
            + parityPosition
        );
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

    private static String encodeBlock(
        String dataBlockBits
    ) {
        char[] codewordPositions =
            new char[CODEWORD_BLOCK_SIZE + 1];
        Arrays.fill(codewordPositions, '0');

        for (
            int dataIndex = 0;
            dataIndex < DATA_BLOCK_SIZE;
            dataIndex++
        ) {
            int codewordPosition = DATA_POSITIONS[dataIndex];
            codewordPositions[codewordPosition] =
                dataBlockBits.charAt(dataIndex);
        }

        for (int parityPosition : PARITY_POSITIONS) {
            int[] checkedPositions =
                getCheckedPositions(parityPosition);
            int onesCount = 0;

            for (int checkedPosition : checkedPositions) {
                if (codewordPositions[checkedPosition] == '1') {
                    onesCount++;
                }
            }

            if (onesCount % 2 == 0) {
                codewordPositions[parityPosition] = '0';
            } else {
                codewordPositions[parityPosition] = '1';
            }
        }

        return new String(
            codewordPositions,
            1,
            CODEWORD_BLOCK_SIZE
        );
    }

    public static String encode(String dataBits) {
        validateBits(dataBits, "Los datos");

        if (dataBits.length() % DATA_BLOCK_SIZE != 0) {
            throw new IllegalArgumentException(
                "La longitud de los datos debe ser "
                + "múltiplo de 8."
            );
        }

        StringBuilder encodedBlocks = new StringBuilder();

        for (
            int blockStartPosition = 0;
            blockStartPosition < dataBits.length();
            blockStartPosition += DATA_BLOCK_SIZE
        ) {
            int blockEndPosition =
                blockStartPosition + DATA_BLOCK_SIZE;
            String dataBlockBits = dataBits.substring(
                blockStartPosition,
                blockEndPosition
            );
            encodedBlocks.append(encodeBlock(dataBlockBits));
        }

        return encodedBlocks.toString();
    }

    private static int calculateErrorPosition(
        String codewordBlockBits
    ) {
        char[] codewordPositions =
            new char[CODEWORD_BLOCK_SIZE + 1];

        for (
            int codewordIndex = 0;
            codewordIndex < CODEWORD_BLOCK_SIZE;
            codewordIndex++
        ) {
            int codewordPosition = codewordIndex + 1;
            codewordPositions[codewordPosition] =
                codewordBlockBits.charAt(codewordIndex);
        }

        int errorPosition = 0;

        for (int parityPosition : PARITY_POSITIONS) {
            int[] checkedPositions =
                getCheckedPositions(parityPosition);
            int onesCount = 0;

            for (int checkedPosition : checkedPositions) {
                if (codewordPositions[checkedPosition] == '1') {
                    onesCount++;
                }
            }

            boolean parityFailed = onesCount % 2 != 0;

            if (parityFailed) {
                errorPosition += parityPosition;
            }
        }

        return errorPosition;
    }

    private static void validateCodeword(
        String codewordBits
    ) {
        validateBits(codewordBits, "La palabra código");

        if (
            codewordBits.length() % CODEWORD_BLOCK_SIZE != 0
        ) {
            throw new IllegalArgumentException(
                "La longitud de la palabra código debe ser "
                + "múltiplo de 12."
            );
        }
    }

    public static boolean verify(String codewordBits) {
        validateCodeword(codewordBits);

        for (
            int blockStartPosition = 0;
            blockStartPosition < codewordBits.length();
            blockStartPosition += CODEWORD_BLOCK_SIZE
        ) {
            int blockEndPosition =
                blockStartPosition + CODEWORD_BLOCK_SIZE;
            String codewordBlockBits = codewordBits.substring(
                blockStartPosition,
                blockEndPosition
            );

            if (calculateErrorPosition(codewordBlockBits) != 0) {
                return false;
            }
        }

        return true;
    }

    public static String correct(String codewordBits) {
        validateCodeword(codewordBits);
        StringBuilder correctedBlocks = new StringBuilder();

        for (
            int blockStartPosition = 0;
            blockStartPosition < codewordBits.length();
            blockStartPosition += CODEWORD_BLOCK_SIZE
        ) {
            int blockEndPosition =
                blockStartPosition + CODEWORD_BLOCK_SIZE;
            String codewordBlockBits = codewordBits.substring(
                blockStartPosition,
                blockEndPosition
            );
            int errorPosition =
                calculateErrorPosition(codewordBlockBits);
            char[] correctedBlockBits =
                codewordBlockBits.toCharArray();

            if (errorPosition > CODEWORD_BLOCK_SIZE) {
                throw new IllegalArgumentException(
                    "Hamming detectó un síndrome fuera "
                    + "del bloque de 12 bits."
                );
            }

            if (errorPosition != 0) {
                int errorIndex = errorPosition - 1;

                if (correctedBlockBits[errorIndex] == '0') {
                    correctedBlockBits[errorIndex] = '1';
                } else {
                    correctedBlockBits[errorIndex] = '0';
                }
            }

            correctedBlocks.append(correctedBlockBits);
        }

        return correctedBlocks.toString();
    }

    public static String recoverData(String codewordBits) {
        String correctedCodewordBits = correct(codewordBits);
        StringBuilder recoveredDataBits = new StringBuilder();

        for (
            int blockStartPosition = 0;
            blockStartPosition < correctedCodewordBits.length();
            blockStartPosition += CODEWORD_BLOCK_SIZE
        ) {
            int blockEndPosition =
                blockStartPosition + CODEWORD_BLOCK_SIZE;
            String correctedBlockBits =
                correctedCodewordBits.substring(
                    blockStartPosition,
                    blockEndPosition
                );

            for (int dataPosition : DATA_POSITIONS) {
                int dataIndex = dataPosition - 1;
                recoveredDataBits.append(
                    correctedBlockBits.charAt(dataIndex)
                );
            }
        }

        return recoveredDataBits.toString();
    }
}
