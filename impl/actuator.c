//
// C program emulating the driver of an actuator (infusion pump)
//
// Build with simply gcc/clang actuador.c
//

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/wait.h>

// The actuator is controlled (like many hardware devices) by writing the
// desired amount of dose to a file. In a real setting, the file will handled
// by the controller or driver of the infusion pump that will act accordingly.
// Here, the file is named pipe that triggers some actions specified in this file.

// Default name for the named file or entry point of the syringe controller
const char* const DEFAULT_PATH = "actuator.pipe";
// Actual path of the pipe (need to be global to be removed by Ctrl-C)
const char* pipe_path = DEFAULT_PATH;

// Flag to be activated by Ctrl-C
int exitFlag = 0;

void sigint_handler(int signo)
{
	// Ctrl-C handler
	if (signo == SIGINT) {
		puts("Interrupted by the user");
		unlink(pipe_path);
		exit(0);
	}
}

void handle_shot(const char* units)
{
#ifdef __APPLE__
	printf("Injected %s mg\n", units);

	pid_t pid = fork();

	if (pid == 0) {
		// Build the message to be spoken
		char message[256];
		sprintf(message, "%s milligrames injected", units);

		// Use the builtin say command in macOS to spoke the message
		if (execlp("say", "say", message, NULL) < 0) {
			perror("Cannot execute say");
			exit(0);
		}
	}

	wait(NULL);
#else
	printf("Injected %s mg\a\n", units);
#endif
}

int main(int argc, char* argv[])
{
	// Check input arguments
	if (argc > 2)
		printf("Wrong number of arguments.\nSyntax: %s [pipe path]\n", argv[0]);

	// Take the optional first argument as pipe path
	else if (argc == 2)
		pipe_path = argv[1];

	// Create the FIFO
	if (mkfifo(pipe_path, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP) < 0) {
		perror("Unable to create the pipe");
		return 1;
	}

	if (signal(SIGINT, sigint_handler) == SIG_ERR)
		puts("Cannot set Ctrl-C handler\n");

	// Open the FIFO for reading
	int fd = open(pipe_path, O_RDONLY, 0);

	if (fd < 0) {
		perror("Unable to open the pipe for reading");
		unlink(pipe_path);
		return 2;
	}

	// Keep reading from the pipe until the Ctrl-C or closed connection
	char buffer[201];

	ssize_t count = read(fd, buffer, 200);

	while (!exitFlag && count > 0) {
		// Add the terminating null byte to the buffer
		buffer[count] = '\0';
		handle_shot(buffer);

		count = read(fd, buffer, 200);
	}

	if (!exitFlag && count < 0) {
		perror("Unable to read from the pipe");
		close(fd);
		unlink(pipe_path);
		return 3;
	}

	close(fd);
	unlink(pipe_path);

	return 0;
}
