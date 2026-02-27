// runtime/websocket.c
// WebSocket protocol implementation for Tusmo
// RFC 6455 compliant

#include "tusmo_runtime.h"
#include <arpa/inet.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

// WebSocket opcodes
#define WS_OPCODE_CONTINUATION 0x0
#define WS_OPCODE_TEXT         0x1
#define WS_OPCODE_BINARY       0x2
#define WS_OPCODE_CLOSE        0x8
#define WS_OPCODE_PING         0x9
#define WS_OPCODE_PONG         0xA

// WebSocket constants
#define WS_MAGIC_STRING "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
#define WS_MAX_FRAME_SIZE (1024 * 1024)  // 1MB max frame

// ============================================================================
// SHA-1 Implementation (for WebSocket handshake)
// ============================================================================

typedef struct {
    uint32_t state[5];
    uint32_t count[2];
    uint8_t buffer[64];
} SHA1_CTX;

#define SHA1_ROTLEFT(a, b) (((a) << (b)) | ((a) >> (32 - (b))))

static void sha1_transform(SHA1_CTX* ctx, const uint8_t data[64]) {
    uint32_t a, b, c, d, e, i, j, t, m[80];

    for (i = 0, j = 0; i < 16; ++i, j += 4)
        m[i] = (data[j] << 24) + (data[j + 1] << 16) + (data[j + 2] << 8) + (data[j + 3]);
    for (; i < 80; ++i) {
        m[i] = (m[i - 3] ^ m[i - 8] ^ m[i - 14] ^ m[i - 16]);
        m[i] = (m[i] << 1) | (m[i] >> 31);
    }

    a = ctx->state[0];
    b = ctx->state[1];
    c = ctx->state[2];
    d = ctx->state[3];
    e = ctx->state[4];

    for (i = 0; i < 20; ++i) {
        t = SHA1_ROTLEFT(a, 5) + ((b & c) ^ (~b & d)) + e + 0x5A827999 + m[i];
        e = d;
        d = c;
        c = SHA1_ROTLEFT(b, 30);
        b = a;
        a = t;
    }
    for (; i < 40; ++i) {
        t = SHA1_ROTLEFT(a, 5) + (b ^ c ^ d) + e + 0x6ED9EBA1 + m[i];
        e = d;
        d = c;
        c = SHA1_ROTLEFT(b, 30);
        b = a;
        a = t;
    }
    for (; i < 60; ++i) {
        t = SHA1_ROTLEFT(a, 5) + ((b & c) ^ (b & d) ^ (c & d)) + e + 0x8F1BBCDC + m[i];
        e = d;
        d = c;
        c = SHA1_ROTLEFT(b, 30);
        b = a;
        a = t;
    }
    for (; i < 80; ++i) {
        t = SHA1_ROTLEFT(a, 5) + (b ^ c ^ d) + e + 0xCA62C1D6 + m[i];
        e = d;
        d = c;
        c = SHA1_ROTLEFT(b, 30);
        b = a;
        a = t;
    }

    ctx->state[0] += a;
    ctx->state[1] += b;
    ctx->state[2] += c;
    ctx->state[3] += d;
    ctx->state[4] += e;
}

static void sha1_init(SHA1_CTX* ctx) {
    ctx->state[0] = 0x67452301;
    ctx->state[1] = 0xEFCDAB89;
    ctx->state[2] = 0x98BADCFE;
    ctx->state[3] = 0x10325476;
    ctx->state[4] = 0xC3D2E1F0;
    ctx->count[0] = ctx->count[1] = 0;
}

static void sha1_update(SHA1_CTX* ctx, const uint8_t* data, size_t len) {
    size_t i;
    for (i = 0; i < len; ++i) {
        ctx->buffer[ctx->count[0]++ % 64] = data[i];
        if (ctx->count[0] % 64 == 0)
            sha1_transform(ctx, ctx->buffer);
        if (ctx->count[0] == 0)
            ctx->count[1]++;
    }
}

static void sha1_final(SHA1_CTX* ctx, uint8_t hash[20]) {
    uint32_t i = ctx->count[0] % 64;
    ctx->buffer[i++] = 0x80;
    if (i > 56) {
        while (i < 64) ctx->buffer[i++] = 0x00;
        sha1_transform(ctx, ctx->buffer);
        i = 0;
    }
    while (i < 56) ctx->buffer[i++] = 0x00;
    
    uint64_t bit_len = (((uint64_t)ctx->count[1]) << 32) | ctx->count[0];
    bit_len *= 8;
    ctx->buffer[63] = bit_len;
    ctx->buffer[62] = bit_len >> 8;
    ctx->buffer[61] = bit_len >> 16;
    ctx->buffer[60] = bit_len >> 24;
    ctx->buffer[59] = bit_len >> 32;
    ctx->buffer[58] = bit_len >> 40;
    ctx->buffer[57] = bit_len >> 48;
    ctx->buffer[56] = bit_len >> 56;
    sha1_transform(ctx, ctx->buffer);

    for (i = 0; i < 4; ++i) {
        hash[i] = (ctx->state[0] >> (24 - i * 8)) & 0x000000ff;
        hash[i + 4] = (ctx->state[1] >> (24 - i * 8)) & 0x000000ff;
        hash[i + 8] = (ctx->state[2] >> (24 - i * 8)) & 0x000000ff;
        hash[i + 12] = (ctx->state[3] >> (24 - i * 8)) & 0x000000ff;
        hash[i + 16] = (ctx->state[4] >> (24 - i * 8)) & 0x000000ff;
    }
}

// ============================================================================
// Base64 Encoding (for WebSocket handshake)
// ============================================================================

static const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static char* base64_encode(const uint8_t* data, size_t input_length) {
    size_t output_length = 4 * ((input_length + 2) / 3);
    char* encoded = (char*)GC_MALLOC(output_length + 1);
    
    if (!encoded) return NULL;

    for (size_t i = 0, j = 0; i < input_length;) {
        uint32_t octet_a = i < input_length ? data[i++] : 0;
        uint32_t octet_b = i < input_length ? data[i++] : 0;
        uint32_t octet_c = i < input_length ? data[i++] : 0;
        uint32_t triple = (octet_a << 16) + (octet_b << 8) + octet_c;

        encoded[j++] = base64_chars[(triple >> 18) & 0x3F];
        encoded[j++] = base64_chars[(triple >> 12) & 0x3F];
        encoded[j++] = base64_chars[(triple >> 6) & 0x3F];
        encoded[j++] = base64_chars[triple & 0x3F];
    }

    size_t mod = input_length % 3;
    if (mod == 1) {
        encoded[output_length - 2] = '=';
        encoded[output_length - 1] = '=';
    } else if (mod == 2) {
        encoded[output_length - 1] = '=';
    }

    encoded[output_length] = '\0';
    return encoded;
}

// ============================================================================
// WebSocket Handshake
// ============================================================================

char* tusmo_ws_generate_accept_key(const char* client_key) {
    if (!client_key) return NULL;

    // Concatenate client key with magic string
    size_t key_len = strlen(client_key);
    size_t magic_len = strlen(WS_MAGIC_STRING);
    char* combined = (char*)GC_MALLOC(key_len + magic_len + 1);
    strcpy(combined, client_key);
    strcat(combined, WS_MAGIC_STRING);

    // Calculate SHA-1 hash
    SHA1_CTX sha;
    uint8_t hash[20];
    sha1_init(&sha);
    sha1_update(&sha, (uint8_t*)combined, strlen(combined));
    sha1_final(&sha, hash);

    // Base64 encode the hash
    return base64_encode(hash, 20);
}

bool tusmo_ws_send_upgrade_response(const char* socket_handle, const char* accept_key) {
    if (!socket_handle || !accept_key) return false;

    char response[512];
    snprintf(response, sizeof(response),
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: %s\r\n"
        "\r\n",
        accept_key);

    int sent = tusmo_socket_send(socket_handle, response);
    return sent > 0;
}

// ============================================================================
// WebSocket Frame Encoding/Decoding
// ============================================================================

static void apply_mask(uint8_t* data, size_t len, const uint8_t mask[4]) {
    for (size_t i = 0; i < len; i++) {
        data[i] ^= mask[i % 4];
    }
}

char* tusmo_ws_encode_frame(uint8_t opcode, const char* payload, size_t payload_len, bool mask) {
    size_t frame_size = 2 + payload_len;  // Minimum: 2 bytes header + payload
    
    // Calculate extended payload length bytes
    if (payload_len > 125) {
        if (payload_len <= 0xFFFF) {
            frame_size += 2;  // 16-bit length
        } else {
            frame_size += 8;  // 64-bit length
        }
    }
    
    // Add masking key if needed
    if (mask) frame_size += 4;

    uint8_t* frame = (uint8_t*)GC_MALLOC(frame_size);
    size_t pos = 0;

    // Byte 0: FIN + opcode
    frame[pos++] = 0x80 | (opcode & 0x0F);  // FIN=1

    // Byte 1: MASK + payload length
    if (payload_len <= 125) {
        frame[pos++] = (mask ? 0x80 : 0x00) | payload_len;
    } else if (payload_len <= 0xFFFF) {
        frame[pos++] = (mask ? 0x80 : 0x00) | 126;
        frame[pos++] = (payload_len >> 8) & 0xFF;
        frame[pos++] = payload_len & 0xFF;
    } else {
        frame[pos++] = (mask ? 0x80 : 0x00) | 127;
        for (int i = 7; i >= 0; i--) {
            frame[pos++] = (payload_len >> (i * 8)) & 0xFF;
        }
    }

    // Masking key (if needed)
    uint8_t mask_key[4] = {0};
    if (mask) {
        // Generate random mask
        for (int i = 0; i < 4; i++) {
            mask_key[i] = rand() & 0xFF;
            frame[pos++] = mask_key[i];
        }
    }

    // Copy and mask payload
    if (payload && payload_len > 0) {
        memcpy(frame + pos, payload, payload_len);
        if (mask) {
            apply_mask(frame + pos, payload_len, mask_key);
        }
    }

    return (char*)frame;
}

TusmoQaamuus* tusmo_ws_decode_frame(const char* socket_handle) {
    TusmoQaamuus* result = tusmo_qaamuus_create();
    TusmoValue val;

    // Read first 2 bytes
    char* header = tusmo_socket_receive(socket_handle, 2);
    if (!header || strlen(header) < 2) {
        val.type = TUSMO_ERAY;
        val.value.as_eray = "qalad";
        tusmo_qaamuus_set(result, "xaalad", val);
        return result;
    }

    uint8_t byte1 = (uint8_t)header[0];
    uint8_t byte2 = (uint8_t)header[1];

    bool fin = (byte1 & 0x80) != 0;
    uint8_t opcode = byte1 & 0x0F;
    bool masked = (byte2 & 0x80) != 0;
    uint64_t payload_len = byte2 & 0x7F;

    // Extended payload length
    if (payload_len == 126) {
        char* len_bytes = tusmo_socket_receive(socket_handle, 2);
        payload_len = ((uint8_t)len_bytes[0] << 8) | (uint8_t)len_bytes[1];
    } else if (payload_len == 127) {
        char* len_bytes = tusmo_socket_receive(socket_handle, 8);
        payload_len = 0;
        for (int i = 0; i < 8; i++) {
            payload_len = (payload_len << 8) | (uint8_t)len_bytes[i];
        }
    }

    // Check frame size
    if (payload_len > WS_MAX_FRAME_SIZE) {
        val.type = TUSMO_ERAY;
        val.value.as_eray = "frame_wa_weyn";
        tusmo_qaamuus_set(result, "xaalad", val);
        return result;
    }

    // Read masking key
    uint8_t mask[4] = {0};
    if (masked) {
        char* mask_bytes = tusmo_socket_receive(socket_handle, 4);
        for (int i = 0; i < 4; i++) {
            mask[i] = (uint8_t)mask_bytes[i];
        }
    }

    // Read payload
    char* payload = NULL;
    if (payload_len > 0) {
        payload = tusmo_socket_receive(socket_handle, (int)payload_len);
        if (masked && payload) {
            apply_mask((uint8_t*)payload, payload_len, mask);
        }
    } else {
        payload = (char*)GC_MALLOC(1);
        payload[0] = '\0';
    }

    // Build result dictionary
    val.type = TUSMO_ERAY;
    val.value.as_eray = "guul";
    tusmo_qaamuus_set(result, "xaalad", val);

    val.type = TUSMO_TIRO;
    val.value.as_tiro = opcode;
    tusmo_qaamuus_set(result, "opcode", val);

    val.type = TUSMO_ERAY;
    // Set type based on opcode
    if (opcode == WS_OPCODE_TEXT) val.value.as_eray = "qoraal";
    else if (opcode == WS_OPCODE_BINARY) val.value.as_eray = "binary";
    else if (opcode == WS_OPCODE_PING) val.value.as_eray = "ping";
    else if (opcode == WS_OPCODE_PONG) val.value.as_eray = "pong";
    else if (opcode == WS_OPCODE_CLOSE) val.value.as_eray = "xir";
    else val.value.as_eray = "kale";
    tusmo_qaamuus_set(result, "nooc", val);

    val.type = TUSMO_ERAY;
    val.value.as_eray = payload ? payload : "";
    tusmo_qaamuus_set(result, "xog", val);

    return result;
}

// ============================================================================
// High-level WebSocket Functions
// ============================================================================

int tusmo_ws_send_text(const char* socket_handle, const char* message) {
    if (!socket_handle || !message) return -1;
    
    size_t len = strlen(message);
    char* frame = tusmo_ws_encode_frame(WS_OPCODE_TEXT, message, len, false);
    
    // Calculate actual frame size
    size_t frame_size = 2 + len;
    if (len > 125) frame_size += (len <= 0xFFFF) ? 2 : 8;
    
    int sent = tusmo_socket_send(socket_handle, frame);
    return sent > 0 ? (int)len : -1;
}

int tusmo_ws_send_binary(const char* socket_handle, const char* data, int data_len) {
    if (!socket_handle || !data) return -1;
    
    char* frame = tusmo_ws_encode_frame(WS_OPCODE_BINARY, data, data_len, false);
    
    size_t frame_size = 2 + data_len;
    if (data_len > 125) frame_size += (data_len <= 0xFFFF) ? 2 : 8;
    
    int sent = tusmo_socket_send(socket_handle, frame);
    return sent > 0 ? data_len : -1;
}

int tusmo_ws_send_ping(const char* socket_handle) {
    char* frame = tusmo_ws_encode_frame(WS_OPCODE_PING, "", 0, false);
    return tusmo_socket_send(socket_handle, frame);
}

int tusmo_ws_send_pong(const char* socket_handle) {
    char* frame = tusmo_ws_encode_frame(WS_OPCODE_PONG, "", 0, false);
    return tusmo_socket_send(socket_handle, frame);
}

int tusmo_ws_send_close(const char* socket_handle, int code, const char* reason) {
    char payload[128];
    payload[0] = (code >> 8) & 0xFF;
    payload[1] = code & 0xFF;
    
    size_t reason_len = reason ? strlen(reason) : 0;
    if (reason_len > 123) reason_len = 123;  // Leave room for status code
    
    if (reason && reason_len > 0) {
        memcpy(payload + 2, reason, reason_len);
    }
    
    char* frame = tusmo_ws_encode_frame(WS_OPCODE_CLOSE, payload, 2 + reason_len, false);
    return tusmo_socket_send(socket_handle, frame);
}
