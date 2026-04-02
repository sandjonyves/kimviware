package com.kimvieware.auth;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.io.*;
import java.net.InetSocketAddress;
import java.util.stream.Collectors;

public class WebAuthService {
    private static AuthService authService = new AuthService();

    public static void main(String[] args) throws Exception {
        int port = 8081;
        if (args.length > 0) port = Integer.parseInt(args[0]);
        
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        
        server.createContext("/auth/register", new HttpHandler() {
            public void handle(HttpExchange exchange) throws IOException {
                if ("POST".equals(exchange.getRequestMethod())) {
                    String body = new BufferedReader(new InputStreamReader(exchange.getRequestBody()))
                            .lines().collect(Collectors.joining("\n"));
                    // Simple parsing (in a real app we'd use JSON library)
                    String username = body.contains("username") ? body.split("\"username\":\"")[1].split("\"")[0] : "";
                    String password = body.contains("password") ? body.split("\"password\":\"")[1].split("\"")[0] : "";
                    
                    String result = authService.registerUser(username, password);
                    String response = "{\"status\":\"" + result + "\"}";
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    exchange.sendResponseHeaders(result.contains("CREATED") ? 201 : 400, response.length());
                    OutputStream os = exchange.getResponseBody();
                    os.write(response.getBytes());
                    os.close();
                }
            }
        });

        server.createContext("/auth/login", new HttpHandler() {
            public void handle(HttpExchange exchange) throws IOException {
                if ("POST".equals(exchange.getRequestMethod())) {
                    String body = new BufferedReader(new InputStreamReader(exchange.getRequestBody()))
                            .lines().collect(Collectors.joining("\n"));
                    String username = body.contains("username") ? body.split("\"username\":\"")[1].split("\"")[0] : "";
                    String password = body.contains("password") ? body.split("\"password\":\"")[1].split("\"")[0] : "";
                    
                    String result = authService.authenticate(username, password);
                    String response = "{\"status\":\"" + result + "\"}";
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    exchange.sendResponseHeaders(result.contains("AUTHENTICATED") ? 200 : 401, response.length());
                    OutputStream os = exchange.getResponseBody();
                    os.write(response.getBytes());
                    os.close();
                }
            }
        });

        server.createContext("/health", new HttpHandler() {
            public void handle(HttpExchange exchange) throws IOException {
                String response = "{\"status\":\"ok\"}";
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.length());
                OutputStream os = exchange.getResponseBody();
                os.write(response.getBytes());
                os.close();
            }
        });

        System.out.println("🚀 Java Auth Web Service started on port " + port);
        server.setExecutor(null);
        server.start();
    }
}
