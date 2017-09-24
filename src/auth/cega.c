#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <stdbool.h>
#include <libpq-fe.h>

/* #include <curl/curl.h> */

#include "debug.h"
#include "config.h"

#define PORT 9100
#define REQUEST(username) GET /user/#username\r\n

/* static bool _connect(){ */
/*   CURL *curl; */
/*   CURLcode res; */

/*   curl_global_init(CURL_GLOBAL_DEFAULT); */

/*   curl = curl_easy_init(); */
/*   if(curl) { */
/*     curl_easy_setopt(curl, CURLOPT_URL, "https://example.com/"); */
/* #ifdef SKIP_PEER_VERIFICATION */
/*     /\* */
/*      * If you want to connect to a site who isn't using a certificate that is */
/*      * signed by one of the certs in the CA bundle you have, you can skip the */
/*      * verification of the server's certificate. This makes the connection */
/*      * A LOT LESS SECURE. */
/*      * */
/*      * If you have a CA cert for the server stored someplace else than in the */
/*      * default bundle, then the CURLOPT_CAPATH option might come handy for */
/*      * you. */
/*      *\/ */
/*     curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L); */
/* #endif */

/* #ifdef SKIP_HOSTNAME_VERIFICATION */
/*     /\* */
/*      * If the site you're connecting to uses a different host name that what */
/*      * they have mentioned in their server certificate's commonName (or */
/*      * subjectAltName) fields, libcurl will refuse to connect. You can skip */
/*      * this check, but this will make the connection less secure. */
/*      *\/ */
/*     curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L); */
/* #endif */

/*     /\* Perform the request, res will get the return code *\/ */
/*     res = curl_easy_perform(curl); */
/*     /\* Check for errors *\/ */
/*     if(res != CURLE_OK) */
/*       DBGLOG("EGA: curl_easy_perform() failed: %s", curl_easy_strerror(res)); */

/*     /\* always cleanup *\/ */
/*     curl_easy_cleanup(curl); */
/*   } */

/*   curl_global_cleanup(); */
/*   return true; */
/* } */

bool
fetch_from_cega(const char *username, char **buffer, size_t *buflen, int *errnop)
{
  /* int rc; */
  /* const char *s; */
  /* size_t slen; */
  /* char* *ega_params; */
  /* int ega_params_nb; */

  D("contacting cega for user: %s\n", username);

  D("user %s not found\n", username);
  return false;
    
  /* /\* Get an answer from Central EGA via sockets *\/ */
  /* fd = _cega_connect(options->rest_endpoint);  */
  /* 	write(fd, "GET /\r\n", strlen("GET /\r\n")); // write(fd, char[]*, len);   */
  /* 	bzero(buffer, BUFFER_SIZE); */
  /* /\* Convert JSON answer to cega_t *\/ */

  /* /\* Add the result to the database *\/ */
  /* rc = PQexecParams(conn, options->nss_add_user, ega_params_nb, NULL, ega_params, NULL, NULL, 0); */

  /* /\* clean up *\/ */
  /* return true; */
}
