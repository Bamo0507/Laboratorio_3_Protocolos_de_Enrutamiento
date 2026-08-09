import application.BankService;
import application.BankTransactionService;
import config.HostConfiguration;
import link.BitNoise;
import link.DataFrameCodec;
import protocol.DataMessage;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;


public final class ServerMain {
    private ServerMain() {
    }

    public static void main(String[] arguments) throws IOException {
        String configurationFilePath = readConfigurationFilePath(arguments);
        HostConfiguration configuration = HostConfiguration.load(configurationFilePath);
        BankTransactionService transactionService = new BankTransactionService(new BankService());

        try (ServerSocket listeningSocket = new ServerSocket(
            configuration.getListenAddress().getPort(),
            50,
            java.net.InetAddress.getByName(configuration.getListenAddress().getIp())
        )) {
            System.out.println("Banco escuchando en " + configuration.getListenAddress().getIp() + ":" + configuration.getListenAddress().getPort());

            while (true) {
                try (Socket incomingConnection = listeningSocket.accept()) {
                    processIncomingData(
                        incomingConnection,
                        configuration,
                        transactionService
                    );
                } catch (IOException | IllegalArgumentException exception) {
                    System.out.println("DATA descartado: " + exception.getMessage());
                }
            }
        }
    }

    private static void processIncomingData(
        Socket incomingConnection,
        HostConfiguration configuration,
        BankTransactionService transactionService
    ) throws IOException {
        String protectedBits = receiveFramedBits(incomingConnection);
        DataFrameCodec.DecodedDataMessage decodedMessage = DataFrameCodec.decode(protectedBits);
        DataMessage request = decodedMessage.getDataMessage();

        if (!request.getDestination().getHostId().equals(configuration.getHostId())) {
            throw new IllegalArgumentException("El DATA no está dirigido a este banco.");
        }

        if (decodedMessage.getCorrectedBlockCount() > 0) {
            System.out.println("Hamming (7,4) corrigió " + decodedMessage.getCorrectedBlockCount() + " bloque(s) al recibir una solicitud.");
        }

        DataMessage response = transactionService.process(request);
        String responseBits = DataFrameCodec.encode(response);
        String noisyResponseBits = BitNoise.apply(
            responseBits,
            response.getNoise().getBitFlipProbability()
        );
        sendFramedBitsToGateway(configuration, noisyResponseBits);
    }

    private static void sendFramedBitsToGateway(
        HostConfiguration configuration,
        String protectedBits
    ) throws IOException {
        try (Socket gatewayConnection = new Socket(
            configuration.getGateway().getIp(),
            configuration.getGateway().getPort()
        )) {
            sendFramedBits(gatewayConnection, protectedBits);
        }
    }

    private static void sendFramedBits(Socket connection, String protectedBits) throws IOException {
        byte[] encodedBits = protectedBits.getBytes(StandardCharsets.US_ASCII);
        DataOutputStream output = new DataOutputStream(connection.getOutputStream());
        output.writeInt(encodedBits.length);
        output.write(encodedBits);
        output.flush();
    }

    private static String receiveFramedBits(Socket connection) throws IOException {
        DataInputStream input = new DataInputStream(connection.getInputStream());
        int messageLength = input.readInt();

        if (messageLength < 1) {
            throw new IllegalArgumentException("La trama DATA no puede estar vacía.");
        }

        byte[] encodedBits = input.readNBytes(messageLength);

        if (encodedBits.length != messageLength) {
            throw new IOException("La conexión se cerró antes de completar la trama DATA.");
        }

        return new String(encodedBits, StandardCharsets.US_ASCII);
    }

    private static String readConfigurationFilePath(String[] arguments) {
        if (arguments.length == 2 && arguments[0].equals("--config")) {
            return arguments[1];
        }

        throw new IllegalArgumentException("Uso: java ServerMain --config ruta/al/bank.json");
    }
}
