#include "tusmo_runtime.h"
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>
#include <sys/wait.h>

// Get current working directory
char* tusmo_os_cwd() {
    char* buf = (char*)GC_MALLOC(1024 * sizeof(char));
    if (getcwd(buf, 1024) != NULL) {
        return buf;
    } else {
        perror("getcwd");
        return ""; // Return empty string on error
    }
}

// Change current working directory
void tusmo_os_cd(char* path) {
    if (chdir(path) != 0) {
        perror("chdir");
    }
}

// List directory contents
TusmoTixEray* tusmo_os_list_dir(char* path) {
    TusmoTixEray* list = tusmo_hp_tix_eray_create(8);
    DIR *d;
    struct dirent *dir;
    d = opendir(path);
    if (d) {
        while ((dir = readdir(d)) != NULL) {
            tusmo_hp_tix_eray_append(list, strdup(dir->d_name));
        }
        closedir(d);
    }
    return list;
}

// Create a directory
void tusmo_os_mkdir(char* path) {
    if (mkdir(path, 0777) != 0) {
        perror("mkdir");
    }
}

// Remove a directory
void tusmo_os_rmdir(char* path) {
    if (rmdir(path) != 0) {
        perror("rmdir");
    }
}

// Remove a file
void tusmo_os_rmfile(char* path) {
    if (remove(path) != 0) {
        perror("remove");
    }
}

// Check if path exists
bool tusmo_os_path_exists(char* path) {
    struct stat buffer;
    return (stat(path, &buffer) == 0);
}

// Check if path is a file
bool tusmo_os_is_file(char* path) {
    struct stat buffer;
    if (stat(path, &buffer) != 0) return false;
    return S_ISREG(buffer.st_mode);
}

// Check if path is a directory
bool tusmo_os_is_dir(char* path) {
    struct stat buffer;
    if (stat(path, &buffer) != 0) return false;
    return S_ISDIR(buffer.st_mode);
}

// Get environment variable
char* tusmo_os_getenv(char* name) {
    char* val = getenv(name);
    return val ? strdup(val) : ""; // Return empty string if not found
}

// Set environment variable
void tusmo_os_setenv(char* name, char* value) {
    if (setenv(name, value, 1) != 0) {
        perror("setenv");
    }
}

// Execute a shell command
int tusmo_os_system(char* command) {
    return system(command);
}

// Copy file or directory
void tusmo_os_copy(char* source, char* destination) {
    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return;
    } else if (pid == 0) {
        // Child process
        execlp("cp", "cp", "-r", source, destination, (char *)NULL);
        perror("execlp"); // Should not reach here
        _exit(1);
    } else {
        // Parent process
        int status;
        waitpid(pid, &status, 0);
    }
}

// Move or rename file or directory
void tusmo_os_move_rename(char* old_path, char* new_path) {
    if (rename(old_path, new_path) != 0) {
        perror("rename");
    }
}

// Read file
char* tusmo_os_read_file(char* path) {
    FILE* fp = fopen(path, "r");
    if (!fp) {
        perror("fopen");
        return "";
    }

    fseek(fp, 0, SEEK_END);
    long fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char* content = (char*)GC_MALLOC(fsize + 1);
    fread(content, 1, fsize, fp);
    fclose(fp);
    content[fsize] = 0;
    return content;
}

// Write file
void tusmo_os_write_file(char* path, char* content, bool append) {
    FILE* fp = fopen(path, append ? "a" : "w");
    if (!fp) {
        perror("fopen");
        return;
    }
    fputs(content, fp);
    fclose(fp);
}

// Path join
char* tusmo_os_path_join(char* part1, char* part2) {
    // Simple join, assumes part1 doesn't end with / and part2 doesn't start with /
    // More robust implementation would handle these cases
    size_t len1 = strlen(part1);
    size_t len2 = strlen(part2);
    char* result = (char*)GC_MALLOC(len1 + len2 + 2); // +1 for /, +1 for null terminator
    strcpy(result, part1);
    if (result[len1 - 1] != '/' && part2[0] != '/') {
        strcat(result, "/");
    }
    strcat(result, part2);
    return result;
}

// Get file size
int tusmo_os_file_size(char* path) {
    struct stat st;
    if (stat(path, &st) == 0) {
        return st.st_size;
    }
    perror("stat");
    return -1; // Return -1 on error
}
