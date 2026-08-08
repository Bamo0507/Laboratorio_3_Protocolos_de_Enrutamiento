package transmission;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;


public class TcpServer implements AutoCloseable {
    private final ServerSocket serverSocket;
    private Socket clientSocket;
    private DataInputStream input;
    private DataOutputStream output;

    public TcpServer(int port) throws IOException {
        serverSocket = new ServerSocket(port);
    }

    public void acceptClient() throws IOException {
        clientSocket = serverSocket.accept();
        input = new DataInputStream(clientSocket.getInputStream());
        output = new DataOutputStream(clientSocket.getOutputStream());
    }

    public void closeClient() throws IOException {
        Socket socketToClose = clientSocket;

        clientSocket = null;
        input = null;
        output = null;

        if (socketToClose != null) {
            socketToClose.close();
        }
    }

    public void send(String message) throws IOException {
        byte[] data = message.getBytes(StandardCharsets.UTF_8);
        output.writeInt(data.length);
        output.write(data);
        output.flush();
    }

    public String receive() throws IOException {
        int length = input.readInt();
        byte[] data = new byte[length];
        input.readFully(data);
        return new String(data, StandardCharsets.UTF_8);
    }

    @Override
    public void close() throws IOException {
        try {
            closeClient();
        } finally {
            serverSocket.close();
        }
    }
}
