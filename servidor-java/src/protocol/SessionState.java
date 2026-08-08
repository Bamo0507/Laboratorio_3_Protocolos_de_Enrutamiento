package protocol;


public final class SessionState {
    public enum Algorithm {
        HAMMING,
        CRC32
    }

    public enum Phase {
        CONNECTED,
        NAME_RECEIVED,
        ALGORITHM_SELECTED,
        WAITING_CARD,
        WAITING_PIN,
        WAITING_OPTION,
        WAITING_AMOUNT,
        COMPLETED
    }

    private String name;
    private Algorithm algorithm;
    private Phase phase = Phase.CONNECTED;

    public void registerName(String name) {
        if (phase != Phase.CONNECTED) {
            throw new IllegalStateException(
                "El nombre llegó fuera de secuencia."
            );
        }

        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException(
                "El nombre no puede estar vacío."
            );
        }

        this.name = name;
        phase = Phase.NAME_RECEIVED;
    }

    public void selectAlgorithm(Algorithm algorithm) {
        if (phase != Phase.NAME_RECEIVED) {
            throw new IllegalStateException(
                "El algoritmo llegó fuera de secuencia."
            );
        }

        this.algorithm = algorithm;
        phase = Phase.ALGORITHM_SELECTED;
    }

    public void startTransaction() {
        if (phase != Phase.ALGORITHM_SELECTED) {
            throw new IllegalStateException(
                "La transacción inició fuera de secuencia."
            );
        }

        phase = Phase.WAITING_CARD;
    }

    public void acceptCard() {
        if (phase != Phase.WAITING_CARD) {
            throw new IllegalStateException(
                "La tarjeta fue aceptada fuera de secuencia."
            );
        }

        phase = Phase.WAITING_PIN;
    }

    public void acceptPin() {
        if (phase != Phase.WAITING_PIN) {
            throw new IllegalStateException(
                "El PIN fue aceptado fuera de secuencia."
            );
        }

        phase = Phase.WAITING_OPTION;
    }

    public void selectBalanceInquiry() {
        if (phase != Phase.WAITING_OPTION) {
            throw new IllegalStateException(
                "La consulta de saldo ocurrió fuera de secuencia."
            );
        }

        phase = Phase.COMPLETED;
    }

    public void selectWithdrawal() {
        if (phase != Phase.WAITING_OPTION) {
            throw new IllegalStateException(
                "El retiro fue seleccionado fuera de secuencia."
            );
        }

        phase = Phase.WAITING_AMOUNT;
    }

    public void completeWithdrawal() {
        if (phase != Phase.WAITING_AMOUNT) {
            throw new IllegalStateException(
                "El retiro finalizó fuera de secuencia."
            );
        }

        phase = Phase.COMPLETED;
    }

    public String getName() {
        return name;
    }

    public Algorithm getAlgorithm() {
        return algorithm;
    }

    public Phase getPhase() {
        return phase;
    }
}
