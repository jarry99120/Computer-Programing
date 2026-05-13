CC = gcc
CFLAGS = -fPIC -Wall -Wextra
LDFLAGS = -shared

all: libra_engine.so

libra_engine.so: game.o
	$(CC) $(LDFLAGS) -o $@ game.o

game.o: game.c game.h
	$(CC) $(CFLAGS) -c game.c -o game.o

clean:
	rm -f *.o *.so
