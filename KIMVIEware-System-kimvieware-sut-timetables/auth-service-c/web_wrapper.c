#include <microhttpd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "src/auth.c" // Include the logic

#define PORT 8082

static enum MHD_Result answer_to_connection(void *cls, struct MHD_Connection *connection,
                          const char *url, const char *method,
                          const char *version, const char *upload_data,
                          size_t *upload_data_size, void **con_cls) {
    
    char *response_text = "{\"status\":\"ok\"}";
    int status_code = MHD_HTTP_OK;

    if (strcmp(url, "/health") == 0) {
        response_text = "{\"status\":\"ok\"}";
    } else if (strcmp(url, "/auth/session") == 0) {
        response_text = "{\"status\":\"SESSION_VALID\", \"info\":\"C Service validated session\"}";
    }

    struct MHD_Response *response = MHD_create_response_from_buffer(strlen(response_text),
                                                                  (void *)response_text,
                                                                  MHD_RESPMEM_PERSISTENT);
    MHD_add_response_header(response, "Content-Type", "application/json");
    enum MHD_Result ret = MHD_queue_response(connection, status_code, response);
    MHD_destroy_response(response);
    return ret;
}

int main(int argc, char *argv[]) {
    int port = PORT;
    if (argc > 1) port = atoi(argv[1]);

    struct MHD_Daemon *daemon;
    daemon = MHD_start_daemon(MHD_USE_INTERNAL_POLLING_THREAD, port, NULL, NULL,
                             &answer_to_connection, NULL, MHD_OPTION_END);
    if (NULL == daemon) return 1;

    printf("🚀 C Auth Web Service started on port %d\n", port);
    getchar(); // Keep running
    MHD_stop_daemon(daemon);
    return 0;
}
