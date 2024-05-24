all: actuator-bin sensor-bin

%-bin: %.c
	$(CC) -O2 $< -o $@

clean:
	$(RM) actuator-bin sensor-bin
