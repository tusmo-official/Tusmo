// runtime/tusmo_runtime.h

#ifndef TUSMO_RUNTIME_H
#define TUSMO_RUNTIME_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdarg.h>
#include <assert.h>
#include <gc.h>
#include "tusmo_types.h"

// ==========================================================================
// --- DATA STRUCTURES
// ==========================================================================
typedef struct TusmoTixTiro { int* data; size_t size; size_t capacity; } TusmoTixTiro;
typedef struct TusmoTixEray { char** data; size_t size; size_t capacity; } TusmoTixEray;
typedef struct TusmoTixJajab { double* data; size_t size; size_t capacity; } TusmoTixJajab;
typedef struct TusmoTixMiyaa { bool* data; size_t size; size_t capacity; } TusmoTixMiyaa;
typedef struct TusmoTixMixed { TusmoValue* data; size_t size; size_t capacity; } TusmoTixMixed;
typedef struct TusmoTixGeneric { void** data; size_t size; size_t capacity; } TusmoTixGeneric;// This holds an array of pointers to other Tusmo array structs.

#include "dictionary.h"
#include "type_conversion.h"
// ==========================================================================
// --- FUNCTION PROTOTYPES
// ==========================================================================

// --- Array Creation (from array.c) ---
TusmoTixTiro* tusmo_hp_tix_tiro_create(size_t cap);
TusmoTixEray* tusmo_hp_tix_eray_create(size_t cap);
TusmoTixJajab* tusmo_hp_tix_jajab_create(size_t cap);
TusmoTixMiyaa* tusmo_hp_tix_miyaa_create(size_t cap);
TusmoTixMixed* tusmo_tix_mixed_create(size_t initial_capacity);
TusmoTixGeneric* tusmo_tix_generic_create(size_t cap);

// --- Array Append (from array.c) ---
void tusmo_hp_tix_tiro_append(TusmoTixTiro* tix, int value);
void tusmo_hp_tix_eray_append(TusmoTixEray* tix, char* value);
void tusmo_hp_tix_jajab_append(TusmoTixJajab* tix, double value);
void tusmo_hp_tix_miyaa_append(TusmoTixMiyaa* tix, bool value);
void tusmo_tix_mixed_append(TusmoTixMixed* tix, TusmoValue value);
size_t tusmo_bounds_check(size_t idx, size_t size);

// --- Array Insert (from array.c) ---
void tusmo_hp_tix_tiro_insert(TusmoTixTiro* tix, size_t index, int value);
void tusmo_hp_tix_eray_insert(TusmoTixEray* tix, size_t index, char* value);
void tusmo_hp_tix_jajab_insert(TusmoTixJajab* tix, size_t index, double value);
void tusmo_hp_tix_miyaa_insert(TusmoTixMiyaa* tix, size_t index, bool value);
void tusmo_tix_mixed_insert(TusmoTixMixed* tix, size_t index, TusmoValue value);

// --- Array Remove (from array.c) ---
int tusmo_hp_tix_tiro_pop(TusmoTixTiro* tix, size_t index);
char* tusmo_hp_tix_eray_pop(TusmoTixEray* tix, size_t index);
double tusmo_hp_tix_jajab_pop(TusmoTixJajab* tix, size_t index);
bool tusmo_hp_tix_miyaa_pop(TusmoTixMiyaa* tix, size_t index);
TusmoValue tusmo_tix_mixed_pop(TusmoTixMixed* tix, size_t index);

bool tusmo_hp_tix_tiro_remove(TusmoTixTiro* tix, int value);
bool tusmo_hp_tix_eray_remove(TusmoTixEray* tix, char* value);
bool tusmo_hp_tix_jajab_remove(TusmoTixJajab* tix, double value);
bool tusmo_hp_tix_miyaa_remove(TusmoTixMiyaa* tix, bool value);
bool tusmo_tix_mixed_remove(TusmoTixMixed* tix, TusmoValue value);

// --- String Formatting (from string.c) ---
char* tusmo_str_format(const char* format, ...);
char* tusmo_concat_cstr(const char* left, const char* right);

// hel
char* hel_str();

// --- I/O Functions (from io.c) ---
void tusmo_qor_dynamic_value(TusmoValue val);

// --- Generic Printing (from io.c) ---
void prints_tix_tiro(TusmoTixTiro* tix);
void prints_tix_eray(TusmoTixEray* tix);
void prints_tix_jajab(TusmoTixJajab* tix);
void prints_tix_miyaa(TusmoTixMiyaa* tix);
void prints_tix_mixed(TusmoTixMixed* tix);

//NEW: Prototypes for the Generic Array (in a new array_generic.c file)
void tusmo_tix_generic_append(TusmoTixGeneric* tix, void* value);
void tusmo_tix_generic_insert(TusmoTixGeneric* tix, size_t index, void* value);
void* tusmo_tix_generic_pop(TusmoTixGeneric* tix, size_t index);
bool tusmo_tix_generic_remove(TusmoTixGeneric* tix, void* value);
// ==========================================================================
// --- GENERIC PRINTING MACRO (This is the fix) ---
// ==========================================================================
#define prints(x) _Generic((x), \
    TusmoTixTiro*:  prints_tix_tiro, \
    TusmoTixEray*:  prints_tix_eray, \
    TusmoTixJajab*: prints_tix_jajab, \
    TusmoTixMiyaa*: prints_tix_miyaa, \
    TusmoTixMixed*: prints_tix_mixed  \
)(x)


// --- Random Functions (from random.c) ---
void tusmo_init_random();
int tusmo_random_int(int min, int max);
double tusmo_random_double(double min, double max);

// --- Time Functions (from time.c) ---
double tusmo_time();
char* tusmo_format_time(const char* format);
int tusmo_get_seconds();
int tusmo_get_minutes();
int tusmo_get_hours();
int tusmo_get_day();
int tusmo_get_month();
int tusmo_get_year();

// --- OS Functions (from os.c) ---
char* tusmo_os_cwd();
void tusmo_os_cd(char* path);
TusmoTixEray* tusmo_os_list_dir(char* path);
void tusmo_os_mkdir(char* path);
void tusmo_os_rmdir(char* path);
void tusmo_os_rmfile(char* path);
bool tusmo_os_path_exists(char* path);
bool tusmo_os_is_file(char* path);
bool tusmo_os_is_dir(char* path);
char* tusmo_os_getenv(char* name);
void tusmo_os_setenv(char* name, char* value);
int tusmo_os_system(char* command);
void tusmo_os_copy(char* source, char* destination);
void tusmo_os_move_rename(char* old_path, char* new_path);
char* tusmo_os_read_file(char* path);
void tusmo_os_write_file(char* path, char* content, bool append);
char* tusmo_os_path_join(char* part1, char* part2);
int tusmo_os_file_size(char* path);

// --- HTTP Functions (from http.c) ---
char* tusmo_http_server_listen(const char* port_str);
TusmoQaamuus* tusmo_http_server_accept(const char* server_handle);
void tusmo_http_send_response(const char* request_handle, int status_code, const char* content_type, const char* body);
void tusmo_http_server_close(const char* server_handle);
char* tusmo_http_request_method(const char* request_handle);
char* tusmo_http_request_path(const char* request_handle);
char* tusmo_http_request_body(const char* request_handle);
char* tusmo_http_request_client(const char* request_handle);
char* tusmo_http_request_header(const char* request_handle, const char* header_name);
int tusmo_http_request_socket_fd(const char* request_handle);  // For WebSocket upgrade
char* tusmo_http_payload_handle(TusmoQaamuus* payload);
char* tusmo_http_payload_status(TusmoQaamuus* payload);
char* tusmo_http_payload_error(TusmoQaamuus* payload);
char* tusmo_http_qaamuus_to_json(TusmoQaamuus* payload);

// --- Socket Functions (from socket.c) ---
char* tusmo_socket_create_server(const char* port);
int tusmo_socket_listen(const char* handle, int backlog);
char* tusmo_socket_accept(const char* server_handle);
char* tusmo_socket_connect(const char* host, const char* port);
int tusmo_socket_send(const char* handle, const char* data);
char* tusmo_socket_receive(const char* handle, int max_size);
void tusmo_socket_close(const char* handle);
int tusmo_socket_get_fd(const char* handle);
bool tusmo_socket_is_valid(const char* handle);
char* tusmo_socket_from_fd(int client_fd);  // For HTTP → WebSocket upgrade

// --- WebSocket Functions (from websocket.c) ---
char* tusmo_ws_generate_accept_key(const char* client_key);
bool tusmo_ws_send_upgrade_response(const char* socket_handle, const char* accept_key);
char* tusmo_ws_encode_frame(uint8_t opcode, const char* payload, size_t payload_len, bool mask);
TusmoQaamuus* tusmo_ws_decode_frame(const char* socket_handle);
int tusmo_ws_send_text(const char* socket_handle, const char* message);
int tusmo_ws_send_binary(const char* socket_handle, const char* data, int data_len);
int tusmo_ws_send_ping(const char* socket_handle);
int tusmo_ws_send_pong(const char* socket_handle);
int tusmo_ws_send_close(const char* socket_handle, int code, const char* reason);




#endif // TUSMO_RUNTIME_H
