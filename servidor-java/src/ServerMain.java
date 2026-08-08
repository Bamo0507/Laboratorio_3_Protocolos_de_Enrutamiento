import application.BankAccount;
import application.BankService;
import link.Crc32;
import link.Hamming;
import presentation.AsciiCodec;
import protocol.ProtocolMessage;
import protocol.ProtocolMessage.Command;
import protocol.SessionState;
import protocol.SessionState.Algorithm;
import transmission.TcpServer;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;


public class ServerMain {
    public static void main(String[] args) throws IOException {
        int port = 1234;
        BankService bankService = new BankService();

        try (TcpServer server = new TcpServer(port)) {
            while (true) {
                System.out.println(
                    "Esperando cliente en el puerto " + port + "..."
                );
                server.acceptClient();

                try {
                    handleClientSession(server, bankService);
                } catch (
                    IOException | IllegalArgumentException exception
                ) {
                    System.out.println(
                        "La sesión terminó con un error: "
                        + exception.getMessage()
                    );
                } finally {
                    try {
                        server.closeClient();
                    } catch (IOException exception) {
                        System.out.println(
                            "No fue posible cerrar la conexión "
                            + "del cliente: "
                            + exception.getMessage()
                        );
                    }
                }
            }
        }
    }

    private static void handleClientSession(
        TcpServer server,
        BankService bankService
    ) throws IOException {
        SessionState session = new SessionState();

        expect(server, Command.YOU_THERE);
        sendMessage(server, Command.SAY_YOUR_NAME);

        ProtocolMessage nameReply = receiveMessage(server);

        if (nameReply.getCommand() != Command.REPLY_NAME) {
            throw new IllegalArgumentException(
                "Se esperaba REPLY_NAME, pero se recibió: " +
                nameReply.serialize()
            );
        }

        session.registerName(nameReply.getPayload());
        System.out.println(
            "Nombre recibido: " + session.getName()
        );

        sendMessage(server, Command.RECEIVED_NAME);

        ProtocolMessage algorithmRequest = receiveMessage(server);

        if (
            algorithmRequest.getCommand() !=
            Command.SELECT_ALGORITHM
        ) {
            sendMessage(server, Command.ALGORITHM_REJECTED);
            throw new IllegalArgumentException(
                "Se esperaba SELECT_ALGORITHM."
            );
        }

        Algorithm algorithm;

        try {
            algorithm = Algorithm.valueOf(
                algorithmRequest.getPayload()
            );
        } catch (IllegalArgumentException exception) {
            sendMessage(server, Command.ALGORITHM_REJECTED);
            throw new IllegalArgumentException(
                "Algoritmo desconocido: " +
                algorithmRequest.getPayload()
            );
        }

        session.selectAlgorithm(algorithm);
        sendMessage(
            server,
            Command.ALGORITHM_ACCEPTED,
            algorithm.name()
        );

        ProtocolMessage firstProtectedMessage =
            receiveProtectedMessage(
                server,
                session.getAlgorithm()
            );

        if (
            firstProtectedMessage.getCommand()
                == Command.START_EXPERIMENT
            && firstProtectedMessage.getPayload().isEmpty()
        ) {
            handleExperiment(
                server,
                session.getAlgorithm()
            );
        } else {
            handleAtmTransaction(
                server,
                session,
                bankService,
                firstProtectedMessage
            );
        }

        System.out.println(
            "Conversación completada correctamente con " +
            session.getAlgorithm() + "."
        );
    }

    private static void handleAtmTransaction(
        TcpServer server,
        SessionState session,
        BankService bankService,
        ProtocolMessage transactionRequest
    ) throws IOException {
        if (
            transactionRequest.getCommand()
                != Command.START_TRANSACTION
            || !transactionRequest.getPayload().isEmpty()
        ) {
            sendProtocolError(
                server,
                Command.START_TRANSACTION,
                transactionRequest
            );
            return;
        }

        session.startTransaction();
        sendMessage(server, Command.TRANSACTION_READY);

        ProtocolMessage cardMessage = receiveProtectedMessage(
            server,
            session.getAlgorithm()
        );

        if (cardMessage.getCommand() != Command.CARD) {
            sendProtocolError(
                server,
                Command.CARD,
                cardMessage
            );
            return;
        }

        BankAccount selectedAccount = bankService.findAccount(
            cardMessage.getPayload()
        );

        if (selectedAccount == null) {
            sendMessage(server, Command.CARD_INVALID);
            return;
        }

        session.acceptCard();
        sendMessage(server, Command.CARD_ACCEPTED);

        ProtocolMessage pinMessage = receiveProtectedMessage(
            server,
            session.getAlgorithm()
        );

        if (pinMessage.getCommand() != Command.PIN) {
            sendProtocolError(
                server,
                Command.PIN,
                pinMessage
            );
            return;
        }

        boolean pinIsCorrect = bankService.validatePin(
            selectedAccount,
            pinMessage.getPayload()
        );

        if (!pinIsCorrect) {
            sendMessage(server, Command.PIN_INCORRECT);
            return;
        }

        session.acceptPin();
        sendMessage(server, Command.PIN_ACCEPTED);

        ProtocolMessage optionMessage = receiveProtectedMessage(
            server,
            session.getAlgorithm()
        );

        if (optionMessage.getCommand() != Command.OPTION) {
            sendProtocolError(
                server,
                Command.OPTION,
                optionMessage
            );
            return;
        }

        if (optionMessage.getPayload().equals("1")) {
            session.selectBalanceInquiry();
            sendMessage(
                server,
                Command.BALANCE,
                Integer.toString(
                    bankService.getBalance(selectedAccount)
                )
            );
            return;
        }

        if (!optionMessage.getPayload().equals("2")) {
            sendProtocolError(
                server,
                Command.OPTION,
                optionMessage
            );
            return;
        }

        session.selectWithdrawal();
        sendMessage(server, Command.REQUEST_AMOUNT);

        while (session.getPhase() == SessionState.Phase.WAITING_AMOUNT) {
            ProtocolMessage amountMessage = receiveProtectedMessage(
                server,
                session.getAlgorithm()
            );

            if (amountMessage.getCommand() != Command.AMOUNT) {
                sendProtocolError(
                    server,
                    Command.AMOUNT,
                    amountMessage
                );
                return;
            }

            int withdrawalAmount;

            try {
                withdrawalAmount = Integer.parseInt(
                    amountMessage.getPayload()
                );
            } catch (NumberFormatException exception) {
                sendProtocolError(
                    server,
                    Command.AMOUNT,
                    amountMessage
                );
                return;
            }

            if (
                !bankService.hasSufficientFunds(
                    selectedAccount,
                    withdrawalAmount
                )
            ) {
                sendMessage(
                    server,
                    Command.INSUFFICIENT_FUNDS,
                    Integer.toString(
                        bankService.getBalance(selectedAccount)
                    )
                );
                continue;
            }

            bankService.withdraw(
                selectedAccount,
                withdrawalAmount
            );
            session.completeWithdrawal();
            sendMessage(
                server,
                Command.WITHDRAWAL_SUCCESSFUL,
                Integer.toString(
                    bankService.getBalance(selectedAccount)
                )
            );
        }
    }

    private static void handleExperiment(
        TcpServer server,
        Algorithm algorithm
    ) throws IOException {
        sendMessage(server, Command.EXPERIMENT_READY);
        System.out.println(
            "Experimento " + algorithm + " iniciado."
        );

        while (true) {
            String receivedCodewordBits = server.receive();
            String dataBits;

            if (algorithm == Algorithm.CRC32) {
                try {
                    if (!Crc32.verify(receivedCodewordBits)) {
                        sendMessage(
                            server,
                            Command.EXPERIMENT_ERROR_DETECTED
                        );
                        continue;
                    }

                    dataBits = Crc32.recoverData(
                        receivedCodewordBits
                    );
                } catch (IllegalArgumentException exception) {
                    sendMessage(
                        server,
                        Command.EXPERIMENT_ERROR_DETECTED
                    );
                    continue;
                }
            } else {
                try {
                    dataBits = Hamming.recoverData(
                        receivedCodewordBits
                    );
                } catch (IllegalArgumentException exception) {
                    sendMessage(
                        server,
                        Command.EXPERIMENT_RECOVERY_FAILED
                    );
                    continue;
                }
            }

            ProtocolMessage experimentMessage;

            try {
                String serializedMessage = AsciiCodec.decode(
                    dataBits
                );
                experimentMessage = ProtocolMessage.parse(
                    serializedMessage
                );
            } catch (IllegalArgumentException exception) {
                sendMessage(
                    server,
                    Command.EXPERIMENT_RECOVERY_FAILED
                );
                continue;
            }

            if (
                experimentMessage.getCommand()
                    == Command.END_EXPERIMENT
                && experimentMessage.getPayload().isEmpty()
            ) {
                sendMessage(server, Command.EXPERIMENT_FINISHED);
                System.out.println(
                    "Experimento " + algorithm + " finalizado."
                );
                return;
            }

            if (
                experimentMessage.getCommand()
                    != Command.EXPERIMENT_MESSAGE
            ) {
                sendProtocolError(
                    server,
                    Command.EXPERIMENT_MESSAGE,
                    experimentMessage
                );
                return;
            }

            String recoveredTextHash = calculateSha256(
                experimentMessage.getPayload()
            );
            sendMessage(
                server,
                Command.EXPERIMENT_MESSAGE_RECOVERED,
                recoveredTextHash
            );
        }
    }

    private static String calculateSha256(String text) {
        try {
            MessageDigest messageDigest =
                MessageDigest.getInstance("SHA-256");
            byte[] hashBytes = messageDigest.digest(
                text.getBytes(StandardCharsets.UTF_8)
            );
            StringBuilder hexadecimalHash = new StringBuilder();

            for (byte hashByte : hashBytes) {
                int unsignedByte = hashByte & 0xff;

                if (unsignedByte < 16) {
                    hexadecimalHash.append('0');
                }

                hexadecimalHash.append(
                    Integer.toHexString(unsignedByte)
                );
            }

            return hexadecimalHash.toString();
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException(
                "SHA-256 no está disponible.",
                exception
            );
        }
    }

    private static ProtocolMessage receiveProtectedMessage(
        TcpServer server,
        Algorithm algorithm
    ) throws IOException {
        String receivedCodewordBits = server.receive();
        boolean messageWasCorrected = false;
        String dataBits;

        try {
            if (algorithm == Algorithm.CRC32) {
                if (!Crc32.verify(receivedCodewordBits)) {
                    throw new IllegalArgumentException(
                        "ERROR CRC-32: se detectó que uno o "
                        + "más bits fueron alterados. CRC-32 "
                        + "no puede corregirlos."
                    );
                }

                dataBits = Crc32.recoverData(
                    receivedCodewordBits
                );
            } else {
                messageWasCorrected =
                    !Hamming.verify(receivedCodewordBits);
                dataBits = Hamming.recoverData(
                    receivedCodewordBits
                );
            }
        } catch (IllegalArgumentException exception) {
            sendMessage(server, Command.INTEGRITY_ERROR);

            if (algorithm == Algorithm.HAMMING) {
                throw new IllegalArgumentException(
                    "ERROR HAMMING: no fue posible recuperar "
                    + "el mensaje. Es posible que más de un "
                    + "bit haya cambiado dentro de un bloque "
                    + "de 12 bits."
                );
            }

            throw exception;
        }

        ProtocolMessage receivedMessage;

        try {
            String serializedMessage = AsciiCodec.decode(
                dataBits
            );
            receivedMessage = ProtocolMessage.parse(
                serializedMessage
            );
        } catch (IllegalArgumentException exception) {
            sendMessage(server, Command.INTEGRITY_ERROR);

            if (algorithm == Algorithm.HAMMING) {
                throw new IllegalArgumentException(
                    "ERROR HAMMING: no fue posible recuperar "
                    + "el mensaje. Es posible que más de un "
                    + "bit haya cambiado dentro de un bloque "
                    + "de 12 bits."
                );
            }

            throw new IllegalArgumentException(
                "No fue posible recuperar un mensaje válido."
            );
        }

        if (messageWasCorrected) {
            System.out.println(
                "HAMMING: se detectó un síndrome y se aplicó "
                + "la corrección. La operación continuará."
            );
            sendMessage(
                server,
                Command.HAMMING_CORRECTION_APPLIED
            );
        }

        return receivedMessage;
    }

    private static void sendProtocolError(
        TcpServer server,
        Command expectedCommand,
        ProtocolMessage receivedMessage
    ) throws IOException {
        sendMessage(server, Command.PROTOCOL_ERROR);
        System.out.println(
            "Se esperaba '" + expectedCommand
            + "', pero se recibió '"
            + receivedMessage.serialize() + "'."
        );
    }

    private static void sendMessage(
        TcpServer server,
        Command command
    ) throws IOException {
        sendMessage(server, command, "");
    }

    private static void sendMessage(
        TcpServer server,
        Command command,
        String payload
    ) throws IOException {
        ProtocolMessage message =
            new ProtocolMessage(command, payload);
        server.send(message.serialize());
    }

    private static ProtocolMessage receiveMessage(TcpServer server)
            throws IOException {
        return ProtocolMessage.parse(server.receive());
    }

    private static void expect(
        TcpServer server,
        Command expectedCommand
    ) throws IOException {
        ProtocolMessage received = receiveMessage(server);

        if (
            received.getCommand() != expectedCommand
            || !received.getPayload().isEmpty()
        ) {
            throw new IllegalArgumentException(
                "Se esperaba '" + expectedCommand +
                "|', pero se recibió '" +
                received.serialize() + "'."
            );
        }
    }
}
