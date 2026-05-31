CC      = gcc
CFLAGS  = -fPIC -Wall -Wextra -g
LDFLAGS = -shared

TARGET = libra_engine.so
OBJS   = game.o scoring.o

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $(OBJS)

game.o: game.c game.h scoring.h
	$(CC) $(CFLAGS) -c game.c -o game.o

scoring.o: scoring.c scoring.h game.h
	$(CC) $(CFLAGS) -c scoring.c -o scoring.o

clean:
	rm -f *.o *.so
