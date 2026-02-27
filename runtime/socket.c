// runtime/socket.c
// Socket implementation for Tusmo

#include "tusmo_runtime.h"
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <netdb.h>
#include <fcntl.h>

#define TUSMO_SOCKET_BUFFER_SIZE 4096
#define TUSMO_SOCKET_DEFAULT_BACKLOG 10

// Socket structure to hold socket file descriptor
typedef struct {
    int fd;
    int port;
    bool is_server;
} TusmoSocket;

// Registry for socket handles (similar to HTTP implementation)
typedef struct TusmoSocketHandleEntry {
    char* handle;
    TusmoSocket* socket;
    struct TusmoSocketHandleEntry* next;
} TusmoSocketHandleEntry;

static TusmoSocketHandleEntry* tusmo_socket_handle_registry = NULL;
static unsigned long tusmo_socket_next_handle_id = 1;

// Helper function to create empty string
static char* tusmo_socket_empty_string() {
    char* s = (char*)GC_MALLOC(1);
    s[0] = '\0';
    return s;
}

// Register a socket handle
static char* tusmo_socket_register_handle(TusmoSocket* socket) {
    if (!socket) {
        return tusmo_socket_empty_string();
    }

    TusmoSocketHandleEntry* entry = (TusmoSocketHandleEntry*)GC_MALLOC(sizeof(TusmoSocketHandleEntry));
    entry->socket = socket;
    entry->next = tusmo_socket_handle_registry;

    char buffer[64];
    unsigned long id = tusmo_socket_next_handle_id++;
    snprintf(buffer, sizeof(buffer), "SOCK:%lu", id);
    size_t len = strlen(buffer);
    entry->handle = (char*)GC_MALLOC(len + 1);
    strcpy(entry->handle, buffer);

    tusmo_socket_handle_registry = entry;
    return entry->handle;
}

// Find socket by handle
static TusmoSocketHandleEntry* tusmo_socket_find_handle(const char* handle) {
    TusmoSocketHandleEntry* entry = tusmo_socket_handle_registry;
    while (entry) {
        if (entry->handle && strcmp(entry->handle, handle) == 0) {
            return entry;
        }
        entry = entry->next;
    }
    return NULL;
}

// Get socket from handle
static TusmoSocket* tusmo_socket_get(const char* handle) {
    if (!handle) return NULL;
    TusmoSocketHandleEntry* entry = tusmo_socket_find_handle(handle);
    return entry ? entry->socket : NULL;
}

// Unregister socket handle
static void tusmo_socket_unregister_handle(const char* handle) {
    if (!handle) return;
    TusmoSocketHandleEntry** current = &tusmo_socket_handle_registry;
    while (*current) {
        TusmoSocketHandleEntry* entry = *current;
        if (entry->handle && strcmp(entry->handle, handle) == 0) {
            *current = entry->next;
            entry->socket = NULL;
            entry->handle = NULL;
            return;
        }
        current = &entry->next;
    }
}

// Create a server socket (bind + listen)
// Returns socket handle as string
char* tusmo_socket_create_server(const char* port_str) {
    if (!port_str) {
        fprintf(stderr, "Qalad: Port erayga waa eber\n");
        return tusmo_socket_empty_string();
    }

    int port = atoi(port_str);
    if (port <= 0 || port > 65535) {
        fprintf(stderr, "Qalad: Port waxaa khasab ah in uu u dhaxeeyo 1 ilaa 65535\n");
        return tusmo_socket_empty_string();
    }

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return tusmo_socket_empty_string();
    }

    // Set SO_REUSEADDR to avoid "Address already in use" errors
    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt");
        close(server_fd);
        return tusmo_socket_empty_string();
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons((uint16_t)port);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return tusmo_socket_empty_string();
    }

    TusmoSocket* socket = (TusmoSocket*)GC_MALLOC(sizeof(TusmoSocket));
    socket->fd = server_fd;
    socket->port = port;
    socket->is_server = true;

    return tusmo_socket_register_handle(socket);
}

// Listen for connections on a server socket
// Returns 0 on success, -1 on failure
int tusmo_socket_listen(const char* handle, int backlog) {
    TusmoSocket* socket = tusmo_socket_get(handle);
    if (!socket || !socket->is_server) {
        fprintf(stderr, "Qalad: Invalid server socket handle\n");
        return -1;
    }

    if (backlog <= 0) {
        backlog = TUSMO_SOCKET_DEFAULT_BACKLOG;
    }

    if (listen(socket->fd, backlog) < 0) {
        perror("listen");
        return -1;
    }

    return 0;
}

// Accept a client connection
// Returns handle to client socket
char* tusmo_socket_accept(const char* server_handle) {
    TusmoSocket* server = tusmo_socket_get(server_handle);
    if (!server || !server->is_server) {
        fprintf(stderr, "Qalad: Invalid server socket handle\n");
        return tusmo_socket_empty_string();
    }

    struct sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);
    int client_fd = accept(server->fd, (struct sockaddr*)&client_addr, &addr_len);
    
    if (client_fd < 0) {
        perror("accept");
        return tusmo_socket_empty_string();
    }

    TusmoSocket* client_socket = (TusmoSocket*)GC_MALLOC(sizeof(TusmoSocket));
    client_socket->fd = client_fd;
    client_socket->port = ntohs(client_addr.sin_port);
    client_socket->is_server = false;

    return tusmo_socket_register_handle(client_socket);
}

// Create a client socket and connect to server
// Returns socket handle on success, empty string on failure
char* tusmo_socket_connect(const char* host, const char* port_str) {
    if (!host || !port_str) {
        fprintf(stderr, "Qalad: Invalid host or port\n");
        return tusmo_socket_empty_string();
    }

    int port = atoi(port_str);
    if (port <= 0 || port > 65535) {
        fprintf(stderr, "Qalad: Invalid port number\n");
        return tusmo_socket_empty_string();
    }

    int client_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (client_fd < 0) {
        perror("socket");
        return tusmo_socket_empty_string();
    }

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons((uint16_t)port);

    // Try to convert host as IP address first
    if (inet_pton(AF_INET, host, &server_addr.sin_addr) <= 0) {
        // If not an IP, try resolving as hostname
        struct hostent* he = gethostbyname(host);
        if (!he) {
            fprintf(stderr, "Qalad: Cannot resolve host '%s'\n", host);
            close(client_fd);
            return tusmo_socket_empty_string();
        }
        memcpy(&server_addr.sin_addr, he->h_addr_list[0], (size_t)he->h_length);
    }

    if (connect(client_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("connect");
        close(client_fd);
        return tusmo_socket_empty_string();
    }

    TusmoSocket* socket = (TusmoSocket*)GC_MALLOC(sizeof(TusmoSocket));
    socket->fd = client_fd;
    socket->port = port;
    socket->is_server = false;

    return tusmo_socket_register_handle(socket);
}

// Send data through socket
// Returns number of bytes sent, -1 on error
int tusmo_socket_send(const char* handle, const char* data) {
    TusmoSocket* socket = tusmo_socket_get(handle);
    if (!socket) {
        fprintf(stderr, "Qalad: Invalid socket handle\n");
        return -1;
    }

    if (!data) {
        return 0;
    }

    size_t len = strlen(data);
    ssize_t sent = send(socket->fd, data, len, 0);
    
    if (sent < 0) {
        perror("send");
        return -1;
    }

    return (int)sent;
}

// Receive data from socket
// Returns received data as string
char* tusmo_socket_receive(const char* handle, int max_size) {
    TusmoSocket* socket = tusmo_socket_get(handle);
    if (!socket) {
        fprintf(stderr, "Qalad: Invalid socket handle\n");
        return tusmo_socket_empty_string();
    }

    if (max_size <= 0) {
        max_size = TUSMO_SOCKET_BUFFER_SIZE;
    }

    char* buffer = (char*)GC_MALLOC((size_t)max_size + 1);
    ssize_t received = recv(socket->fd, buffer, (size_t)max_size, 0);
    
    if (received < 0) {
        perror("recv");
        return tusmo_socket_empty_string();
    }

    buffer[received] = '\0';
    return buffer;
}

// Close socket and free resources
void tusmo_socket_close(const char* handle) {
    TusmoSocket* socket = tusmo_socket_get(handle);
    if (!socket) {
        return;
    }

    if (socket->fd >= 0) {
        close(socket->fd);
        socket->fd = -1;
    }

    tusmo_socket_unregister_handle(handle);
}

// Get socket file descriptor (for advanced users)
int tusmo_socket_get_fd(const char* handle) {
    TusmoSocket* socket = tusmo_socket_get(handle);
    return socket ? socket->fd : -1;
}

// Check if socket is valid
bool tusmo_socket_is_valid(const char* handle) {
    TusmoSocket* socket = tusmo_socket_get(handle);
    return socket && socket->fd >= 0;
}

// Create socket handle from existing file descriptor (for HTTP → WebSocket upgrade)
char* tusmo_socket_from_fd(int client_fd) {
    if (client_fd < 0) {
        return tusmo_socket_empty_string();
    }

    TusmoSocket* socket = (TusmoSocket*)GC_MALLOC(sizeof(TusmoSocket));
    socket->fd = client_fd;
    socket->port = 0;  // Unknown port for adopted socket
    socket->is_server = false;

    return tusmo_socket_register_handle(socket);
}
