package link;


public final class Hamming74 {
    private static final int DATA_BIT_COUNT = 4;
    private static final int CODEWORD_BIT_COUNT = 7;

    private Hamming74() {
    }

    public static String encodeDataBits(String dataBits) {
        validateBinaryBits(dataBits, "Los bits de datos");

        if (dataBits.length() % DATA_BIT_COUNT != 0) {
            throw new IllegalArgumentException(
                "Los bits de datos deben tener una cantidad múltiplo de 4."
            );
        }

        StringBuilder encodedBits = new StringBuilder();

        for (
            int startIndex = 0;
            startIndex < dataBits.length();
            startIndex += DATA_BIT_COUNT
        ) {
            String dataBlock = dataBits.substring(
                startIndex,
                startIndex + DATA_BIT_COUNT
            );
            encodedBits.append(encodeDataBlock(dataBlock));
        }

        return encodedBits.toString();
    }

    public static RecoveredDataBits recoverDataBits(String codewordBits) {
        validateBinaryBits(codewordBits, "Los bits de la trama");

        if (codewordBits.length() % CODEWORD_BIT_COUNT != 0) {
            throw new IllegalArgumentException(
                "Los bits de la trama deben tener una cantidad múltiplo de 7."
            );
        }

        StringBuilder recoveredDataBits = new StringBuilder();
        int correctedBlockCount = 0;

        for (
            int startIndex = 0;
            startIndex < codewordBits.length();
            startIndex += CODEWORD_BIT_COUNT
        ) {
            String codewordBlock = codewordBits.substring(
                startIndex,
                startIndex + CODEWORD_BIT_COUNT
            );
            RecoveredDataBlock recoveredDataBlock = recoverDataBlock(
                codewordBlock
            );
            recoveredDataBits.append(recoveredDataBlock.dataBits);

            if (recoveredDataBlock.wasCorrected) {
                correctedBlockCount++;
            }
        }

        return new RecoveredDataBits(
            recoveredDataBits.toString(),
            correctedBlockCount
        );
    }

    private static String encodeDataBlock(String dataBlock) {
        int[] codewordByPosition = new int[CODEWORD_BIT_COUNT + 1];
        codewordByPosition[3] = dataBlock.charAt(0) - '0';
        codewordByPosition[5] = dataBlock.charAt(1) - '0';
        codewordByPosition[6] = dataBlock.charAt(2) - '0';
        codewordByPosition[7] = dataBlock.charAt(3) - '0';

        codewordByPosition[1] = calculateEvenParity(
            codewordByPosition,
            new int[] {3, 5, 7}
        );
        codewordByPosition[2] = calculateEvenParity(
            codewordByPosition,
            new int[] {3, 6, 7}
        );
        codewordByPosition[4] = calculateEvenParity(
            codewordByPosition,
            new int[] {5, 6, 7}
        );

        StringBuilder codewordBits = new StringBuilder();

        for (int position = 1; position <= CODEWORD_BIT_COUNT; position++) {
            codewordBits.append(codewordByPosition[position]);
        }

        return codewordBits.toString();
    }

    private static RecoveredDataBlock recoverDataBlock(String codewordBlock) {
        int[] codewordByPosition = new int[CODEWORD_BIT_COUNT + 1];

        for (int position = 1; position <= CODEWORD_BIT_COUNT; position++) {
            codewordByPosition[position] = codewordBlock.charAt(position - 1) - '0';
        }

        int errorPosition = calculateErrorPosition(codewordByPosition);
        boolean wasCorrected = errorPosition != 0;

        if (wasCorrected) {
            codewordByPosition[errorPosition] = 1 - codewordByPosition[errorPosition];
        }

        String dataBits = ""
            + codewordByPosition[3]
            + codewordByPosition[5]
            + codewordByPosition[6]
            + codewordByPosition[7];
        return new RecoveredDataBlock(dataBits, wasCorrected);
    }

    private static int calculateEvenParity(
        int[] codewordByPosition,
        int[] dataPositions
    ) {
        int parity = 0;

        for (int position : dataPositions) {
            parity ^= codewordByPosition[position];
        }

        return parity;
    }

    private static int calculateErrorPosition(int[] codewordByPosition) {
        int parityCheckForPosition1 = calculateParityCheck(
            codewordByPosition,
            new int[] {1, 3, 5, 7}
        );
        int parityCheckForPosition2 = calculateParityCheck(
            codewordByPosition,
            new int[] {2, 3, 6, 7}
        );
        int parityCheckForPosition4 = calculateParityCheck(
            codewordByPosition,
            new int[] {4, 5, 6, 7}
        );

        return parityCheckForPosition1
            + (parityCheckForPosition2 * 2)
            + (parityCheckForPosition4 * 4);
    }

    private static int calculateParityCheck(
        int[] codewordByPosition,
        int[] checkedPositions
    ) {
        int parityCheck = 0;

        for (int position : checkedPositions) {
            parityCheck ^= codewordByPosition[position];
        }

        return parityCheck;
    }

    private static void validateBinaryBits(String bits, String description) {
        if (bits == null) {
            throw new IllegalArgumentException(description + " deben ser texto.");
        }

        for (int index = 0; index < bits.length(); index++) {
            char bit = bits.charAt(index);

            if (bit != '0' && bit != '1') {
                throw new IllegalArgumentException(
                    description + " solo pueden contener 0 y 1."
                );
            }
        }
    }

    public static final class RecoveredDataBits {
        private final String dataBits;
        private final int correctedBlockCount;

        private RecoveredDataBits(String dataBits, int correctedBlockCount) {
            this.dataBits = dataBits;
            this.correctedBlockCount = correctedBlockCount;
        }

        public String getDataBits() {
            return dataBits;
        }

        public int getCorrectedBlockCount() {
            return correctedBlockCount;
        }
    }

    private static final class RecoveredDataBlock {
        private final String dataBits;
        private final boolean wasCorrected;

        private RecoveredDataBlock(String dataBits, boolean wasCorrected) {
            this.dataBits = dataBits;
            this.wasCorrected = wasCorrected;
        }
    }
}
