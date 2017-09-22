# Makefile for the NSS module used in Local EGA

NSS_LD_SONAME=-Wl,-soname,libnss_ega.so.2
NSS_LIBRARY=libnss_ega.so.2.0
PAM_LIBRARY = pam_ega.la

CC=gcc
LD=ld
CFLAGS=-Wall -Wstrict-prototypes -Werror -fPIC -O2 -I. -I/usr/pgsql-9.6/include
LIBS=-lpq -lpam

LIBDIR=/usr/local/lib/ega

NSS_SOURCES = nss.c config.c backend.c
NSS_HEADERS = debug.h config.h backend.h
NSS_OBJECTS = $(NSS_SOURCES:%.c=%.o)

PAM_SOURCES = pam.c config.c backend.c
PAM_HEADERS = debug.h config.h backend.h
PAM_OBJECTS = $(PAM_SOURCES:%.c=%.o)

.PHONY: clean install
.SUFFIXES: .c .o .so .so.2 .so.2.0

all: $(NSS_LIBRARY) $(PAM_LIBRARY)

debug: CFLAGS += -DDEBUG -g
debug: $(NSS_LIBRARY)

$(NSS_LIBRARY): $(NSS_HEADERS) $(NSS_OBJECTS)
	$(CC) -shared $(NSS_LD_SONAME) -o $@ $(LIBS) $(NSS_OBJECTS)

$(PAM_LIBRARY): $(PAM_HEADERS) $(PAM_OBJECTS)
	$(LD) -x --shared -o $@ $(LIBS) $(PAM_OBJECTS)

#	$(CC) -module -export-dynamic -shared -o $@ 

%.o: %.c
	@echo "Compiling $<"
	@$(CC) $(CFLAGS) -c -o $@ $<


install-nss: $(NSS_LIBRARY)
	@[ -d $(LIBDIR) ] || { echo "Creating lib dir: $(LIBDIR)"; install -d $(LIBDIR); }
	@echo "Installing $< into $(LIBDIR)"
	@install $< $(LIBDIR)

install-pam: $(PAM_LIBRARY)
	@[ -d $(LIBDIR) ] || { echo "Creating lib dir: $(LIBDIR)"; install -d $(LIBDIR); }
	@echo "Installing $< into $(LIBDIR)"
	@install $< $(LIBDIR)

install: install-nss install-pam
	@echo "Do not forget to run ldconfig and create/configure the file /etc/ega/auth.conf"
	@echo "Look at the auth.conf.sample here, for example"

clean:
	-rm -f $(NSS_LIBRARY) $(NSS_OBJECTS)
	-rm -f $(PAM_LIBRARY) $(PAM_OBJECTS)
