package link;

import protocol.DataMessage;

import java.nio.charset.StandardCharsets;


public final class DataFrameCodec {
    private DataFrameCodec() {
    }

    public static String encode(DataMessage dataMessage) {
        byte[] messageBytes = dataMessage.serialize().getBytes(StandardCharsets.UTF_8);
        StringBuilder dataBits = new StringBuilder();

        for (byte messageByte : messageBytes) {
            for (int bitPosition = 7; bitPosition >= 0; bitPosition--) {
                dataBits.append((messageByte >> bitPosition) & 1);
            }
        }

        return Hamming74.encodeDataBits(dataBits.toString());
    }

    public static DecodedDataMessage decode(String protectedBits) {
        Hamming74.RecoveredDataBits recoveredBits = Hamming74.recoverDataBits(protectedBits);
        String dataBits = recoveredBits.getDataBits();

        if (dataBits.length() % 8 != 0) {
            throw new IllegalArgumentException("Los datos recuperados no completan bytes UTF-8.");
        }

        byte[] messageBytes = new byte[dataBits.length() / 8];

        for (int byteIndex = 0; byteIndex < messageBytes.length; byteIndex++) {
            int startIndex = byteIndex * 8;
            int byteValue = Integer.parseInt(dataBits.substring(startIndex, startIndex + 8), 2);
            messageBytes[byteIndex] = (byte) byteValue;
        }

        DataMessage dataMessage = DataMessage.parse(
            new String(messageBytes, StandardCharsets.UTF_8)
        );
        return new DecodedDataMessage(dataMessage, recoveredBits.getCorrectedBlockCount());
    }

    public static final class DecodedDataMessage {
        private final DataMessage dataMessage;
        private final int correctedBlockCount;

        private DecodedDataMessage(DataMessage dataMessage, int correctedBlockCount) {
            this.dataMessage = dataMessage;
            this.correctedBlockCount = correctedBlockCount;
        }

        public DataMessage getDataMessage() {
            return dataMessage;
        }

        public int getCorrectedBlockCount() {
            return correctedBlockCount;
        }
    }
}
