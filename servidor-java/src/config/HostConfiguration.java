package config;

import com.google.gson.Gson;
import com.google.gson.JsonParseException;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;


public final class HostConfiguration {
    private static final Gson GSON = new Gson();

    private String host_id;
    private Address listen;
    private Gateway gateway;
    private RemoteHost remote_host;

    public static HostConfiguration load(String configurationFilePath) {
        try {
            String configurationText = Files.readString(Path.of(configurationFilePath));
            HostConfiguration configuration = GSON.fromJson(
                configurationText,
                HostConfiguration.class
            );
            configuration.validate();
            return configuration;
        } catch (IOException | JsonParseException exception) {
            throw new IllegalArgumentException(
                "No fue posible leer la configuración del banco.",
                exception
            );
        }
    }

    public String getHostId() {
        return host_id;
    }

    public Address getListenAddress() {
        return listen;
    }

    public Gateway getGateway() {
        return gateway;
    }

    public RemoteHost getRemoteHost() {
        return remote_host;
    }

    private void validate() {
        validateText(host_id, "host_id");
        if (listen == null || gateway == null || remote_host == null) {
            throw new IllegalArgumentException("Faltan listen, gateway o remote_host.");
        }
        listen.validate("listen");
        gateway.validate();
        remote_host.validate();
    }

    private static void validateText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(fieldName + " debe ser texto no vacío.");
        }
    }

    public static final class Address {
        private String ip;
        private int port;

        public String getIp() {
            return ip;
        }

        public int getPort() {
            return port;
        }

        private void validate(String fieldName) {
            validateText(ip, fieldName + ".ip");
            validatePort(port, fieldName + ".port");
        }
    }

    public static final class Gateway {
        private String router_id;
        private String ip;
        private int port;

        public String getRouterId() {
            return router_id;
        }

        public String getIp() {
            return ip;
        }

        public int getPort() {
            return port;
        }

        private void validate() {
            validateText(router_id, "gateway.router_id");
            validateText(ip, "gateway.ip");
            validatePort(port, "gateway.port");
        }
    }

    public static final class RemoteHost {
        private String host_id;
        private String gateway_id;

        public String getHostId() {
            return host_id;
        }

        public String getGatewayId() {
            return gateway_id;
        }

        private void validate() {
            validateText(host_id, "remote_host.host_id");
            validateText(gateway_id, "remote_host.gateway_id");
        }
    }

    private static void validatePort(int port, String fieldName) {
        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException(fieldName + " debe estar entre 1 y 65535.");
        }
    }
}
