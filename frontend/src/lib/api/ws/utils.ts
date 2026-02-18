const API_ENDPOINT: string = process.env.NEXT_PUBLIC_API_ENDPOINT!;

export function getWebSocketUrl(chat_id: string): string {
    console.log("Backend URL for WebSocket:", API_ENDPOINT);
    
    // Switch protocol (http -> ws, https -> wss)
    const protocol = API_ENDPOINT.startsWith("https") ? "wss" : "ws";
    const host = API_ENDPOINT.replace(/^https?:\/\//, "");
    
    // Construct URL
    // Path matches backend router: app.include_router(..., prefix="/api/v1")
    // and ws_router prefix="/ws" -> /api/v1/ws/{chat_id}
    let url = `${protocol}://${host}/api/v1/ws/${chat_id}`;

    return url;
}