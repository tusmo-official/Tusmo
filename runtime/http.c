#include "tusmo_runtime.h"
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#define TUSMO_HTTP_INITIAL_BUFFER 8192
#define TUSMO_HTTP_BACKLOG 16
#define TUSMO_HTTP_MAX_HEADER_SIZE (64 * 1024)
#define TUSMO_HTTP_MAX_BODY_SIZE (8 * 1024 * 1024)

typedef struct TusmoHttpHandleEntry {
    char* handle;
    const char* prefix;
    void* ptr;
    struct TusmoHttpHandleEntry* next;
} TusmoHttpHandleEntry;

static TusmoHttpHandleEntry* tusmo_http_handle_registry = NULL;
static unsigned long tusmo_http_next_handle_id = 1;

typedef struct {
    int server_fd;
    int port;
} TusmoHttpServer;

typedef struct {
    TusmoHttpServer* server;
    int client_fd;
    char* method;
    char* path;
    char* body;
    TusmoQaamuus* headers;
    char* client;
} TusmoHttpRequest;

static char* tusmo_http_empty_string() {
    char* s = (char*)GC_MALLOC(1);
    s[0] = '\0';
    return s;
}

static TusmoHttpHandleEntry* tusmo_http_handle_find(const char* handle) {
    TusmoHttpHandleEntry* entry = tusmo_http_handle_registry;
    while (entry) {
        if (entry->handle && strcmp(entry->handle, handle) == 0) {
            return entry;
        }
        entry = entry->next;
    }
    return NULL;
}

static char* tusmo_http_register_handle(void* ptr, const char* prefix) {
    if (!ptr || !prefix) {
        return tusmo_http_empty_string();
    }

    TusmoHttpHandleEntry* entry = (TusmoHttpHandleEntry*)GC_MALLOC(sizeof(TusmoHttpHandleEntry));
    entry->ptr = ptr;
    entry->prefix = prefix;
    entry->next = tusmo_http_handle_registry;

    char buffer[64];
    unsigned long id = tusmo_http_next_handle_id++;
    snprintf(buffer, sizeof(buffer), "%s:%lu", prefix, id);
    size_t len = strlen(buffer);
    entry->handle = (char*)GC_MALLOC(len + 1);
    strcpy(entry->handle, buffer);

    tusmo_http_handle_registry = entry;
    return entry->handle;
}

static void* tusmo_http_parse_handle(const char* handle, const char* prefix) {
    if (!handle || !prefix) return NULL;
    TusmoHttpHandleEntry* entry = tusmo_http_handle_find(handle);
    if (!entry) return NULL;
    if (strcmp(entry->prefix, prefix) != 0) return NULL;
    if (strncmp(handle, prefix, strlen(prefix)) != 0) return NULL;
    return entry->ptr;
}

static void tusmo_http_unregister_handle(const char* handle) {
    if (!handle) return;
    TusmoHttpHandleEntry** current = &tusmo_http_handle_registry;
    while (*current) {
        TusmoHttpHandleEntry* entry = *current;
        if (entry->handle && strcmp(entry->handle, handle) == 0) {
            *current = entry->next;
            entry->ptr = NULL;
            entry->handle = NULL;
            entry->prefix = NULL;
            return;
        }
        current = &entry->next;
    }
}

static char* tusmo_http_create_handle(void* ptr, const char* prefix) {
    return tusmo_http_register_handle(ptr, prefix);
}

static size_t tusmo_http_parse_content_length(const char* headers, size_t header_len) {
    const char* cursor = headers;
    const char* end = headers + header_len;

    while (cursor < end) {
        const char* line_end = strstr(cursor, "\r\n");
        if (!line_end || line_end == cursor) break;
        size_t line_len = (size_t)(line_end - cursor);
        const char* colon = memchr(cursor, ':', line_len);
        if (colon) {
            size_t name_len = (size_t)(colon - cursor);
            if (name_len == 14 && strncasecmp(cursor, "Content-Length", 14) == 0) {
                const char* value_start = colon + 1;
                while (value_start < line_end && (*value_start == ' ' || *value_start == '\t')) {
                    value_start++;
                }
                char length_buf[32];
                size_t value_len = (size_t)(line_end - value_start);
                if (value_len >= sizeof(length_buf)) value_len = sizeof(length_buf) - 1;
                memcpy(length_buf, value_start, value_len);
                length_buf[value_len] = '\0';
                return (size_t)strtoul(length_buf, NULL, 10);
            }
        }
        cursor = line_end + 2;
    }
    return 0;
}

static char* tusmo_http_trim_copy(const char* begin, size_t len) {
    while (len > 0 && (*begin == ' ' || *begin == '\t')) {
        begin++;
        len--;
    }

    while (len > 0 && (begin[len - 1] == ' ' || begin[len - 1] == '\t')) {
        len--;
    }

    char* result = (char*)GC_MALLOC(len + 1);
    memcpy(result, begin, len);
    result[len] = '\0';
    return result;
}

static char* tusmo_http_copy_segment(const char* begin, size_t len) {
    char* result = (char*)GC_MALLOC(len + 1);
    memcpy(result, begin, len);
    result[len] = '\0';
    return result;
}

static TusmoQaamuus* tusmo_http_make_error(const char* message) {
       TusmoQaamuus* info = tusmo_qaamuus_create();
       TusmoValue val;
       val.type = TUSMO_ERAY;

       char* status = (char*)GC_MALLOC(6);
       strcpy(status, "qalad");
       val.type = TUSMO_ERAY;
       val.value.as_eray = status;
       tusmo_qaamuus_set(info, "__status", val);

       const char* safe_message = message ? message : "";
       char* msg_copy = (char*)GC_MALLOC(strlen(safe_message) + 1);
       strcpy(msg_copy, safe_message);
       val.type = TUSMO_ERAY;
       val.value.as_eray = msg_copy;
       tusmo_qaamuus_set(info, "__farriin", val);

       char* handle = (char*)GC_MALLOC(1);
       handle[0] = '\0';
       val.type = TUSMO_ERAY;
       val.value.as_eray = handle;
       tusmo_qaamuus_set(info, "__handle", val);
} 

static const char* tusmo_http_reason_phrase(int status) {
    switch (status) {
        case 200: return "OK";
        case 201: return "Created";
        case 202: return "Accepted";
        case 204: return "No Content";
        case 301: return "Moved Permanently";
        case 302: return "Found";
        case 304: return "Not Modified";
        case 400: return "Bad Request";
        case 401: return "Unauthorized";
        case 403: return "Forbidden";
        case 404: return "Not Found";
        case 405: return "Method Not Allowed";
        case 409: return "Conflict";
        case 413: return "Payload Too Large";
        case 429: return "Too Many Requests";
        case 500: return "Internal Server Error";
        case 502: return "Bad Gateway";
        case 503: return "Service Unavailable";
        default: return "OK";
    }
}

static char* tusmo_http_read_request(int client_fd, size_t* out_size) {
    size_t capacity = TUSMO_HTTP_INITIAL_BUFFER;
    char* buffer = (char*)GC_MALLOC(capacity + 1);
    size_t total = 0;
    bool headers_complete = false;
    size_t expected_total = 0;
    bool error = false;

    while (1) {
        if (total == capacity) {
            capacity *= 2;
            buffer = (char*)GC_REALLOC(buffer, capacity + 1);
        }

        ssize_t bytes = recv(client_fd, buffer + total, capacity - total, 0);
        if (bytes < 0) {
            if (errno == EINTR) continue;
            error = true;
            break;
        }
        if (bytes == 0) {
            break;
        }

        total += (size_t)bytes;
        buffer[total] = '\0';

        if (!headers_complete && total > TUSMO_HTTP_MAX_HEADER_SIZE) {
            error = true;
            break;
        }

        if (!headers_complete) {
            char* header_end = strstr(buffer, "\r\n\r\n");
            if (header_end) {
                headers_complete = true;
                size_t header_len = (size_t)(header_end - buffer + 4);
                size_t content_length = tusmo_http_parse_content_length(buffer, header_len);
                if (content_length > TUSMO_HTTP_MAX_BODY_SIZE) {
                    error = true;
                    break;
                }
                expected_total = header_len + content_length;
                if (expected_total > capacity) {
                    while (capacity < expected_total) {
                        capacity *= 2;
                    }
                    buffer = (char*)GC_REALLOC(buffer, capacity + 1);
                }
                if (expected_total > TUSMO_HTTP_MAX_HEADER_SIZE + TUSMO_HTTP_MAX_BODY_SIZE) {
                    error = true;
                    break;
                }
                while (total < expected_total) {
                    ssize_t more = recv(client_fd, buffer + total, capacity - total, 0);
                    if (more < 0) {
                        if (errno == EINTR) continue;
                        error = true;
                        break;
                    }
                    if (more == 0) break;
                    total += (size_t)more;
                    buffer[total] = '\0';
                }
                break;
            }
        } else if (expected_total && total >= expected_total) {
            break;
        }
    }

    if (!headers_complete || error || (expected_total && total < expected_total) ||
        total > TUSMO_HTTP_MAX_HEADER_SIZE + TUSMO_HTTP_MAX_BODY_SIZE) {
        *out_size = 0;
        return NULL;
    }

    *out_size = total;
    return buffer;
}

static TusmoQaamuus* tusmo_http_request_to_payload(TusmoHttpRequest* request) {
    TusmoQaamuus* payload = tusmo_qaamuus_create();
    TusmoValue val;

    val.type = TUSMO_ERAY;

    char* status = (char*)GC_MALLOC(3);
    strcpy(status, "ok");
    val.value.as_eray = status;
    tusmo_qaamuus_set(payload, "__status", val);

    val.value.as_eray = request->method ? request->method : "";
    tusmo_qaamuus_set(payload, "hab", val);

    val.value.as_eray = request->path ? request->path : "";
    tusmo_qaamuus_set(payload, "waddo", val);

    val.value.as_eray = request->body ? request->body : "";
    tusmo_qaamuus_set(payload, "xambaare", val);

    val.value.as_eray = request->client ? request->client : "";
    tusmo_qaamuus_set(payload, "macmiil", val);

    val.type = TUSMO_QAAMUUS;
    val.value.as_qaamuus = request->headers;
    tusmo_qaamuus_set(payload, "madax", val);

    val.type = TUSMO_ERAY;
    val.value.as_eray = tusmo_http_create_handle(request, "REQ");
    tusmo_qaamuus_set(payload, "__handle", val);

    return payload;
}

static TusmoHttpRequest* tusmo_http_get_request(const char* request_handle) {
    return (TusmoHttpRequest*)tusmo_http_parse_handle(request_handle, "REQ");
}

static char* tusmo_http_lookup_header(TusmoHttpRequest* request, const char* header_name) {
    if (!request || !request->headers || !header_name) {
        return tusmo_http_empty_string();
    }

    TusmoQaamuus* headers = request->headers;
    for (size_t i = 0; i < headers->capacity; ++i) {
        TusmoQaamuusEntry* entry = headers->entries[i];
        while (entry) {
            if (strcasecmp(entry->key, header_name) == 0) {
                if (entry->value.type == TUSMO_ERAY && entry->value.value.as_eray) {
                    return entry->value.value.as_eray;
                } else if (entry->value.type == TUSMO_QAAMUUS && entry->value.value.as_qaamuus) {
                    // Not expected for headers but guard anyway
                    // Return empty string for unsupported types
                    return tusmo_http_empty_string();
                }
            }
            entry = entry->next;
        }
    }

    return tusmo_http_empty_string();
}

char* tusmo_http_server_listen(const char* port_str) {
    if (!port_str) return tusmo_http_create_handle(NULL, "SRV");

    int port = atoi(port_str);
    if (port <= 0 || port > 65535) {
        port = 8080;
    }

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return tusmo_http_create_handle(NULL, "SRV");
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons((uint16_t)port);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return tusmo_http_create_handle(NULL, "SRV");
    }

    if (listen(server_fd, TUSMO_HTTP_BACKLOG) < 0) {
        perror("listen");
        close(server_fd);
        return tusmo_http_create_handle(NULL, "SRV");
    }

    TusmoHttpServer* server = (TusmoHttpServer*)GC_MALLOC(sizeof(TusmoHttpServer));
    server->server_fd = server_fd;
    server->port = port;

    return tusmo_http_create_handle(server, "SRV");
}

TusmoQaamuus* tusmo_http_server_accept(const char* server_handle) {
    TusmoHttpServer* server = (TusmoHttpServer*)tusmo_http_parse_handle(server_handle, "SRV");
    if (!server) {
        return tusmo_http_make_error("server_handle_ma_saxana");
    }

    struct sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);
    int client_fd = accept(server->server_fd, (struct sockaddr*)&client_addr, &addr_len);
    if (client_fd < 0) {
        perror("accept");
        return tusmo_http_make_error("lama_qaban_karo_macmiil");
    }

    char client_ip[INET_ADDRSTRLEN];
    if (!inet_ntop(AF_INET, &(client_addr.sin_addr), client_ip, sizeof(client_ip))) {
        strcpy(client_ip, "aan_la_aqoon");
    }

    char client_buf[INET_ADDRSTRLEN + 8];
    snprintf(client_buf, sizeof(client_buf), "%s:%d", client_ip, ntohs(client_addr.sin_port));

    size_t raw_size = 0;
    char* raw_request = tusmo_http_read_request(client_fd, &raw_size);
    if (raw_size == 0 || !raw_request) {
        close(client_fd);
        return tusmo_http_make_error("codsi_madhan");
    }

    char* line_end = strstr(raw_request, "\r\n");
    if (!line_end) {
        close(client_fd);
        return tusmo_http_make_error("codsi_garbisan");
    }

    size_t request_line_len = (size_t)(line_end - raw_request);
    const char* request_line = raw_request;

    size_t method_len = strcspn(request_line, " ");
    size_t path_start = method_len + 1;
    if (path_start >= request_line_len) {
        close(client_fd);
        return tusmo_http_make_error("codsi_garbisan");
    }

    size_t path_len = strcspn(request_line + path_start, " ");
    if (path_start + path_len > request_line_len) {
        path_len = request_line_len - path_start;
    }

    char* method = tusmo_http_copy_segment(request_line, method_len);
    char* path = tusmo_http_copy_segment(request_line + path_start, path_len);

    char* headers_start = line_end + 2;
    char* headers_end = strstr(headers_start, "\r\n\r\n");
    if (!headers_end) {
        close(client_fd);
        return tusmo_http_make_error("codsi_garbisan");
    }

    TusmoQaamuus* headers = tusmo_qaamuus_create();
    const char* cursor = headers_start;
    while (cursor < headers_end) {
        const char* this_end = strstr(cursor, "\r\n");
        if (!this_end || this_end == cursor) break;
        const char* colon = memchr(cursor, ':', (size_t)(this_end - cursor));
        if (colon) {
            size_t name_len = (size_t)(colon - cursor);
            char* name = tusmo_http_copy_segment(cursor, name_len);
            char* value = tusmo_http_trim_copy(colon + 1, (size_t)(this_end - colon - 1));
            TusmoValue header_value;
            header_value.type = TUSMO_ERAY;
            header_value.value.as_eray = value;
            tusmo_qaamuus_set(headers, name, header_value);
        }
        cursor = this_end + 2;
    }

    char* body_start = headers_end + 4;
    size_t body_len = raw_size > (size_t)(body_start - raw_request)
                          ? raw_size - (size_t)(body_start - raw_request)
                          : 0;
    char* body = tusmo_http_copy_segment(body_start, body_len);

    TusmoHttpRequest* request = (TusmoHttpRequest*)GC_MALLOC(sizeof(TusmoHttpRequest));
    request->server = server;
    request->client_fd = client_fd;
    request->method = method;
    request->path = path;
    request->body = body;
    request->headers = headers;
    request->client = tusmo_http_copy_segment(client_buf, strlen(client_buf));

    return tusmo_http_request_to_payload(request);
}

char* tusmo_http_request_method(const char* request_handle) {
    TusmoHttpRequest* request = tusmo_http_get_request(request_handle);
    if (!request || !request->method) {
        return tusmo_http_empty_string();
    }
    return request->method;
}

char* tusmo_http_request_path(const char* request_handle) {
    TusmoHttpRequest* request = tusmo_http_get_request(request_handle);
    if (!request || !request->path) {
        return tusmo_http_empty_string();
    }
    return request->path;
}

char* tusmo_http_request_body(const char* request_handle) {
    TusmoHttpRequest* request = tusmo_http_get_request(request_handle);
    if (!request || !request->body) {
        return tusmo_http_empty_string();
    }
    return request->body;
}

char* tusmo_http_request_client(const char* request_handle) {
    TusmoHttpRequest* request = tusmo_http_get_request(request_handle);
    if (!request || !request->client) {
        return tusmo_http_empty_string();
    }
    return request->client;
}

// Get socket file descriptor from HTTP request (for WebSocket upgrade)
int tusmo_http_request_socket_fd(const char* request_handle) {
    TusmoHttpRequest* request = tusmo_http_get_request(request_handle);
    if (!request) {
        return -1;
    }
    return request->client_fd;
}

char* tusmo_http_request_header(const char* request_handle, const char* header_name) {
    TusmoHttpRequest* request = tusmo_http_get_request(request_handle);
    if (!request) {
        return tusmo_http_empty_string();
    }
    return tusmo_http_lookup_header(request, header_name);
}

static char* tusmo_http_payload_get_string(TusmoQaamuus* payload, const char* key) {
    if (!payload || !key) {
        return tusmo_http_empty_string();
    }
    TusmoValue value = tusmo_qaamuus_get(payload, key);
    if (value.type == TUSMO_ERAY && value.value.as_eray) {
        return value.value.as_eray;
    }
    return tusmo_http_empty_string();
}

char* tusmo_http_payload_handle(TusmoQaamuus* payload) {
    return tusmo_http_payload_get_string(payload, "__handle");
}

char* tusmo_http_payload_status(TusmoQaamuus* payload) {
    return tusmo_http_payload_get_string(payload, "__status");
}

char* tusmo_http_payload_error(TusmoQaamuus* payload) {
    return tusmo_http_payload_get_string(payload, "__farriin");
}

static void tusmo_http_json_ensure_capacity(char** buffer, size_t* length, size_t* capacity, size_t additional) {
    size_t required = *length + additional + 1;
    if (required <= *capacity) return;
    while (required > *capacity) {
        *capacity *= 2;
    }
    *buffer = (char*)GC_REALLOC(*buffer, *capacity);
}

static void tusmo_http_json_append_str(char** buffer, size_t* length, size_t* capacity, const char* str) {
    size_t len = strlen(str);
    tusmo_http_json_ensure_capacity(buffer, length, capacity, len);
    memcpy(*buffer + *length, str, len);
    *length += len;
    (*buffer)[*length] = '\0';
}

static void tusmo_http_json_append_char(char** buffer, size_t* length, size_t* capacity, char c) {
    tusmo_http_json_ensure_capacity(buffer, length, capacity, 1);
    (*buffer)[(*length)++] = c;
    (*buffer)[*length] = '\0';
}

static void tusmo_http_json_escape_string(const char* value, char** buffer, size_t* length, size_t* capacity) {
    tusmo_http_json_append_char(buffer, length, capacity, '"');
    for (const char* p = value; *p; ++p) {
        char ch = *p;
        switch (ch) {
            case '\\': tusmo_http_json_append_str(buffer, length, capacity, "\\\\"); break;
            case '"':  tusmo_http_json_append_str(buffer, length, capacity, "\\\""); break;
            case '\n': tusmo_http_json_append_str(buffer, length, capacity, "\\n"); break;
            case '\r': tusmo_http_json_append_str(buffer, length, capacity, "\\r"); break;
            case '\t': tusmo_http_json_append_str(buffer, length, capacity, "\\t"); break;
            case '\b': tusmo_http_json_append_str(buffer, length, capacity, "\\b"); break;
            case '\f': tusmo_http_json_append_str(buffer, length, capacity, "\\f"); break;
            default:
                if ((unsigned char)ch < 0x20) {
                    char tmp[7];
                    snprintf(tmp, sizeof(tmp), "\\u%04x", ch);
                    tusmo_http_json_append_str(buffer, length, capacity, tmp);
                } else {
                    tusmo_http_json_append_char(buffer, length, capacity, ch);
                }
                break;
        }
    }
    tusmo_http_json_append_char(buffer, length, capacity, '"');
}

static void tusmo_http_json_append_value(TusmoValue value, char** buffer, size_t* length, size_t* capacity);
static void tusmo_http_json_append_array(TusmoTixMixed* tix,
                                         char** buffer,
                                         size_t* length,
                                         size_t* capacity) {
    tusmo_http_json_append_char(buffer, length, capacity, '[');

    for (size_t i = 0; i < tix->size; i++) {
        if (i > 0) {
            tusmo_http_json_append_char(buffer, length, capacity, ',');
        }
        tusmo_http_json_append_value(tix->data[i], buffer, length, capacity);
    }

    tusmo_http_json_append_char(buffer, length, capacity, ']');
}


static void tusmo_http_json_append_object(TusmoQaamuus* qaamuus, char** buffer, size_t* length, size_t* capacity) {
    tusmo_http_json_append_char(buffer, length, capacity, '{');
    bool first = true;
    for (size_t i = 0; i < qaamuus->capacity; ++i) {
        TusmoQaamuusEntry* entry = qaamuus->entries[i];
        while (entry) {
            if (!first) {
                tusmo_http_json_append_char(buffer, length, capacity, ',');
            }
            first = false;
            tusmo_http_json_escape_string(entry->key, buffer, length, capacity);
            tusmo_http_json_append_char(buffer, length, capacity, ':');
            tusmo_http_json_append_value(entry->value, buffer, length, capacity);
            entry = entry->next;
        }
    }
    tusmo_http_json_append_char(buffer, length, capacity, '}');
}

static void tusmo_http_json_append_value(TusmoValue value, char** buffer, size_t* length, size_t* capacity) {
    switch (value.type) {
        
        case TUSMO_TIRO: {
            char tmp[32];
            snprintf(tmp, sizeof(tmp), "%d", value.value.as_tiro);
            tusmo_http_json_append_str(buffer, length, capacity, tmp);
            break;
        }
        case TUSMO_JAJAB: {
            char tmp[64];
            snprintf(tmp, sizeof(tmp), "%f", value.value.as_jajab);
            tusmo_http_json_append_str(buffer, length, capacity, tmp);
            break;
        }
        case TUSMO_MIYAA:
            tusmo_http_json_append_str(buffer, length, capacity, value.value.as_miyaa ? "true" : "false");
            break;
        case TUSMO_XARAF: {
            char tmp[8];
            snprintf(tmp, sizeof(tmp), "\"%c\"", value.value.as_xaraf);
            tusmo_http_json_append_str(buffer, length, capacity, tmp);
            break;
        }
        case TUSMO_TIX:
            if (value.value.as_tix) {
                tusmo_http_json_append_array(value.value.as_tix, buffer, length, capacity);
            } else {
                tusmo_http_json_append_str(buffer, length, capacity, "[]");
            }
            break;

        case TUSMO_ERAY:
            tusmo_http_json_escape_string(value.value.as_eray ? value.value.as_eray : "", buffer, length, capacity);
            break;
        case TUSMO_QAAMUUS:
            if (value.value.as_qaamuus) {
                tusmo_http_json_append_object(value.value.as_qaamuus, buffer, length, capacity);
            } else {
                tusmo_http_json_append_str(buffer, length, capacity, "null");
            }
            break;
        default:
            tusmo_http_json_append_str(buffer, length, capacity, "null");
            break;
    }
}

char* tusmo_http_qaamuus_to_json(TusmoQaamuus* qaamuus) {
    if (!qaamuus) {
        char* empty_obj = (char*)GC_MALLOC(3);
        strcpy(empty_obj, "{}");
        return empty_obj;
    }
    size_t capacity = 256;
    size_t length = 0;
    char* buffer = (char*)GC_MALLOC(capacity);
    buffer[0] = '\0';
    tusmo_http_json_append_object(qaamuus, &buffer, &length, &capacity);
    tusmo_http_json_append_char(&buffer, &length, &capacity, '\0');
    return buffer;
}

static bool tusmo_http_send_all(int fd, const char* data, size_t len) {
    size_t sent = 0;
    while (sent < len) {
        ssize_t result = send(fd, data + sent, len - sent, 0);
        if (result < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) continue;
            return false;
        }
        if (result == 0) {
            return false;
        }
        sent += (size_t)result;
    }
    return true;
}

void tusmo_http_send_response(const char* request_handle, int status_code, const char* content_type, const char* body) {
    TusmoHttpRequest* request = (TusmoHttpRequest*)tusmo_http_parse_handle(request_handle, "REQ");
    if (!request || request->client_fd < 0) {
        return;
    }

    const char* reason = tusmo_http_reason_phrase(status_code);
    const char* type = (content_type && strlen(content_type) > 0)
                           ? content_type
                           : "text/plain; charset=utf-8";
    const char* response_body = body ? body : "";
    size_t body_len = strlen(response_body);

    int header_len = snprintf(
        NULL,
        0,
        "HTTP/1.1 %d %s\r\n"
        "Content-Length: %zu\r\n"
        "Content-Type: %s\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Headers: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Connection: close\r\n"
        "\r\n",
        status_code,
        reason,
        body_len,
        type);

    char* header = (char*)GC_MALLOC((size_t)header_len + 1);
    snprintf(
        header,
        (size_t)header_len + 1,
        "HTTP/1.1 %d %s\r\n"
        "Content-Length: %zu\r\n"
        "Content-Type: %s\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Headers: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Connection: close\r\n"
        "\r\n",
        status_code,
        reason,
        body_len,
        type);

    tusmo_http_send_all(request->client_fd, header, (size_t)header_len);
    if (body_len > 0) {
        tusmo_http_send_all(request->client_fd, response_body, body_len);
    }

    close(request->client_fd);
    request->client_fd = -1;
    tusmo_http_unregister_handle(request_handle);
}

void tusmo_http_server_close(const char* server_handle) {
    TusmoHttpServer* server = (TusmoHttpServer*)tusmo_http_parse_handle(server_handle, "SRV");
    if (!server) return;
    if (server->server_fd >= 0) {
        close(server->server_fd);
        server->server_fd = -1;
    }
    tusmo_http_unregister_handle(server_handle);
}
