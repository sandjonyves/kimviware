CC = clang
CFLAGS = -Wall -Wextra -g -O0
TARGET = auth_service

all: $(TARGET)

$(TARGET): src/auth.c
	$(CC) $(CFLAGS) -o $(TARGET) src/auth.c

clean:
	rm -f $(TARGET)

test: $(TARGET)
	./$(TARGET)

.PHONY: all clean test
