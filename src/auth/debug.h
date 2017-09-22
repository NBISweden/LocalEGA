#ifndef __LEGA_DEBUG_H_INCLUDED__
#define __LEGA_DEBUG_H_INCLUDED__

#ifdef DEBUG

#include <syslog.h>
#include <stdio.h>

#define D(x...)  fprintf(stderr, ##x);

#define DBGLOG(x...) do { fprintf(stderr, ##x); fprintf(stderr, "\n"); } while(0)
#define SYSLOG(x...) do { fprintf(stderr, ##x); fprintf(stderr, "\n"); } while(0)
#define AUTHLOG(x...) do { fprintf(stderr, ##x); fprintf(stderr, "\n"); } while(0)

/* #define DBGLOG(x...)  if(options->debug) {                          \ */
/*                           openlog("EGA_auth", LOG_PID, LOG_USER);   \ */
/*                           syslog(LOG_DEBUG, ##x);                   \ */
/*                           closelog();                               \ */
/*                       } */
/* #define SYSLOG(x...)  do {                                          \ */
/*                           openlog("EGA_auth", LOG_PID, LOG_USER);   \ */
/*                           syslog(LOG_INFO, ##x);                    \ */
/*                           closelog();                               \ */
/*                       } while(0); */
/* #define AUTHLOG(x...) do {                                          \ */
/*                           openlog("EGA_auth", LOG_PID, LOG_USER);   \ */
/*                           syslog(LOG_AUTHPRIV, ##x);                \ */
/*                           closelog();                               \ */
/*                       } while(0); */

#else

#define D(x...)
#define DBGLOG(x...)
#define SYSLOG(x...)
#define AUTHLOG(x...)

#endif /* !DEBUG */

#endif /* !__LEGA_AUTH_H_INCLUDED__ */
