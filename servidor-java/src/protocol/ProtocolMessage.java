package protocol;


public final class ProtocolMessage {
    public enum Command {
        YOU_THERE,
        SAY_YOUR_NAME,
        REPLY_NAME,
        RECEIVED_NAME,
        SELECT_ALGORITHM,
        ALGORITHM_ACCEPTED,
        ALGORITHM_REJECTED,
        INTEGRITY_ERROR,
        HAMMING_CORRECTION_APPLIED,
        START_TRANSACTION,
        TRANSACTION_READY,
        CARD,
        CARD_ACCEPTED,
        CARD_INVALID,
        PIN,
        PIN_ACCEPTED,
        PIN_INCORRECT,
        OPTION,
        BALANCE,
        REQUEST_AMOUNT,
        AMOUNT,
        WITHDRAWAL_SUCCESSFUL,
        INSUFFICIENT_FUNDS,
        PROTOCOL_ERROR,
        START_EXPERIMENT,
        EXPERIMENT_READY,
        EXPERIMENT_MESSAGE,
        EXPERIMENT_MESSAGE_RECOVERED,
        EXPERIMENT_ERROR_DETECTED,
        EXPERIMENT_RECOVERY_FAILED,
        END_EXPERIMENT,
        EXPERIMENT_FINISHED
    }

    private final Command command;
    private final String payload;

    public ProtocolMessage(Command command) {
        this(command, "");
    }

    public ProtocolMessage(Command command, String payload) {
        this.command = command;
        this.payload = payload;
    }

    public String serialize() {
        return command.name() + "|" + payload;
    }

    public static ProtocolMessage parse(String rawMessage) {
        int separatorPosition = rawMessage.indexOf('|');

        if (separatorPosition <= 0) {
            throw new IllegalArgumentException(
                "Mensaje inválido: " + rawMessage
            );
        }

        String commandText = rawMessage.substring(0, separatorPosition);
        String payload = rawMessage.substring(separatorPosition + 1);

        try {
            Command command = Command.valueOf(commandText);
            return new ProtocolMessage(command, payload);
        } catch (IllegalArgumentException exception) {
            throw new IllegalArgumentException(
                "Comando desconocido: " + commandText
            );
        }
    }

    public Command getCommand() {
        return command;
    }

    public String getPayload() {
        return payload;
    }
}
