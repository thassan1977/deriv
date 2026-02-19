import { Client } from '@stomp/stompjs';
import SockJS from 'sockjs-client';

export const createWebSocketClient = (onMessageReceived) => {
    const client = new Client({
        // Point this to your Spring Boot Server's WebSocket endpoint
        // Using SockJS for compatibility with Spring's .withSockJS()
        webSocketFactory: () => new SockJS('http://localhost:8080/ws-fraud'),
        
        // Debugging logs to see traffic in the browser console (useful for the hackathon)
        debug: (str) => {
            console.log('STOMP: ' + str);
        },
        
        onConnect: () => {
            console.log("CONNECTED TO DERVI FRAUD STREAM");
            
            // Subscribe to the global queue (matches your Java @SendTo or messagingTemplate)
            client.subscribe('/topic/queue', (message) => {
                if (message.body) {
                    onMessageReceived(JSON.parse(message.body));
                }
            });

            // Subscribe to the stats update (TPS, Pending counts)
            client.subscribe('/topic/stats', (message) => {
                if (message.body) {
                    onMessageReceived(JSON.parse(message.body));
                }
            });
        },
        
        onStompError: (frame) => {
            console.error('Broker reported error: ' + frame.headers['message']);
            console.error('Additional details: ' + frame.body);
        },
    });

    return client;
};