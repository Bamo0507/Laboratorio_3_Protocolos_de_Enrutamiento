package presentation;


public final class AsciiCodec {
    private AsciiCodec() {
    }

    public static String encode(String message) {
        StringBuilder bits = new StringBuilder();

        for (int position = 0; position < message.length(); position++) {
            char character = message.charAt(position);

            if (character > 127) {
                throw new IllegalArgumentException(
                    "El mensaje contiene caracteres fuera de ASCII."
                );
            }

            String binary = Integer.toBinaryString(character);
            bits.append("0".repeat(8 - binary.length()));
            bits.append(binary);
        }

        return bits.toString();
    }

    public static String decode(String bits) {
        for (int position = 0; position < bits.length(); position++) {
            char bit = bits.charAt(position);

            if (bit != '0' && bit != '1') {
                throw new IllegalArgumentException(
                    "El mensaje binario solo puede contener 0 y 1."
                );
            }
        }

        if (bits.length() % 8 != 0) {
            throw new IllegalArgumentException(
                "La longitud del mensaje binario debe ser múltiplo de 8."
            );
        }

        StringBuilder message = new StringBuilder();

        for (int position = 0; position < bits.length(); position += 8) {
            String binaryCharacter =
                bits.substring(position, position + 8);
            int asciiValue = Integer.parseInt(binaryCharacter, 2);

            if (asciiValue > 127) {
                throw new IllegalArgumentException(
                    "El mensaje binario contiene valores fuera de ASCII."
                );
            }

            message.append((char) asciiValue);
        }

        return message.toString();
    }
}
