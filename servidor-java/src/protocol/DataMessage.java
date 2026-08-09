package protocol;

import com.google.gson.Gson;
import com.google.gson.JsonParseException;
import com.google.gson.annotations.SerializedName;

import java.util.Set;


public final class DataMessage {
    private static final String DATA_MESSAGE_TYPE = "DATA";
    private static final Gson GSON = new Gson();
    private static final Set<String> SUPPORTED_BANK_COMMANDS = Set.of(
        "START_TRANSACTION",
        "TRANSACTION_READY",
        "CARD",
        "CARD_ACCEPTED",
        "CARD_INVALID",
        "PIN",
        "PIN_ACCEPTED",
        "PIN_INCORRECT",
        "OPTION",
        "BALANCE",
        "REQUEST_AMOUNT",
        "AMOUNT",
        "WITHDRAWAL_SUCCESSFUL",
        "INSUFFICIENT_FUNDS",
        "PROTOCOL_ERROR",
        "LOGOUT",
        "LOGOUT_ACK"
    );

    @SerializedName("type")
    private String messageType;

    @SerializedName("packet_id")
    private String packetId;

    @SerializedName("session_id")
    private String sessionId;

    private HostRoute origin;
    private HostRoute destination;
    private NoiseConfiguration noise;
    private BankPayload payload;

    public DataMessage(
        String packetId,
        String sessionId,
        HostRoute origin,
        HostRoute destination,
        NoiseConfiguration noise,
        BankPayload payload
    ) {
        this.messageType = DATA_MESSAGE_TYPE;
        this.packetId = packetId;
        this.sessionId = sessionId;
        this.origin = origin;
        this.destination = destination;
        this.noise = noise;
        this.payload = payload;
        validate();
    }

    public String serialize() {
        validate();
        return GSON.toJson(this);
    }

    public static DataMessage parse(String serializedMessage) {
        try {
            DataMessage dataMessage = GSON.fromJson(
                serializedMessage,
                DataMessage.class
            );

            if (dataMessage == null) {
                throw new IllegalArgumentException(
                    "El mensaje DATA no puede ser nulo."
                );
            }

            dataMessage.validate();
            return dataMessage;
        } catch (JsonParseException exception) {
            throw new IllegalArgumentException(
                "El mensaje DATA no contiene JSON válido.",
                exception
            );
        }
    }

    public void validate() {
        if (!DATA_MESSAGE_TYPE.equals(messageType)) {
            throw new IllegalArgumentException(
                "El campo 'type' debe ser 'DATA'."
            );
        }

        validateRequiredText(packetId, "packet_id");
        validateRequiredText(sessionId, "session_id");

        if (origin == null || destination == null || noise == null || payload == null) {
            throw new IllegalArgumentException(
                "Los campos origin, destination, noise y payload son obligatorios."
            );
        }

        origin.validate("origin");
        destination.validate("destination");
        noise.validate();
        payload.validate();
    }

    public String getPacketId() {
        return packetId;
    }

    public String getSessionId() {
        return sessionId;
    }

    public HostRoute getOrigin() {
        return origin;
    }

    public HostRoute getDestination() {
        return destination;
    }

    public NoiseConfiguration getNoise() {
        return noise;
    }

    public BankPayload getPayload() {
        return payload;
    }

    public static final class HostRoute {
        @SerializedName("host_id")
        private String hostId;

        @SerializedName("gateway_id")
        private String gatewayId;

        public HostRoute(String hostId, String gatewayId) {
            this.hostId = hostId;
            this.gatewayId = gatewayId;
        }

        private void validate(String fieldPrefix) {
            validateRequiredText(hostId, fieldPrefix + ".host_id");
            validateRequiredText(gatewayId, fieldPrefix + ".gateway_id");
        }

        public String getHostId() {
            return hostId;
        }

        public String getGatewayId() {
            return gatewayId;
        }
    }

    public static final class NoiseConfiguration {
        @SerializedName("bit_flip_probability")
        private double bitFlipProbability;

        public NoiseConfiguration(double bitFlipProbability) {
            this.bitFlipProbability = bitFlipProbability;
        }

        private void validate() {
            if (bitFlipProbability < 0 || bitFlipProbability > 1) {
                throw new IllegalArgumentException(
                    "La probabilidad de flip debe estar entre 0.0 y 1.0."
                );
            }
        }

        public double getBitFlipProbability() {
            return bitFlipProbability;
        }
    }

    public static final class BankPayload {
        private String command;
        private String payload;

        public BankPayload(String command, String payload) {
            this.command = command;
            this.payload = payload;
        }

        private void validate() {
            validateRequiredText(command, "payload.command");

            if (!SUPPORTED_BANK_COMMANDS.contains(command)) {
                throw new IllegalArgumentException(
                    "El comando bancario no es reconocido: " + command + "."
                );
            }

            if (payload == null) {
                throw new IllegalArgumentException(
                    "El campo 'payload.payload' debe ser texto."
                );
            }
        }

        public String getCommand() {
            return command;
        }

        public String getPayload() {
            return payload;
        }
    }

    private static void validateRequiredText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                "El campo '" + fieldName + "' debe ser texto no vacío."
            );
        }
    }
}
