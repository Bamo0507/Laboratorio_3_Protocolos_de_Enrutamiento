package link;

import java.util.concurrent.ThreadLocalRandom;


public final class BitNoise {
    private BitNoise() {
    }

    public static String apply(String protectedBits, double bitFlipProbability) {
        if (bitFlipProbability < 0 || bitFlipProbability > 1) {
            throw new IllegalArgumentException("La probabilidad debe estar entre 0.0 y 1.0.");
        }

        StringBuilder noisyBits = new StringBuilder();

        for (int index = 0; index < protectedBits.length(); index++) {
            char originalBit = protectedBits.charAt(index);
            boolean shouldFlip = ThreadLocalRandom.current().nextDouble() < bitFlipProbability;
            noisyBits.append(shouldFlip ? flipBit(originalBit) : originalBit);
        }

        return noisyBits.toString();
    }

    private static char flipBit(char bit) {
        return bit == '0' ? '1' : '0';
    }
}
