//
// C program emulating a sensor with sensor traces
//
// Build with simply gcc/clang sensor.c
//


#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

#include <unistd.h>
#include <strings.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

// Termination flag
int active = 1;

void sigint_handler(int signo)
{
	// Ctrl-C handler
	if (signo == SIGINT) {
		puts("Interrupted by the user");
		exit(0);
	}
}

void handleClient(int fd, FILE* input) {
	char command;
	// Read from the socket (a single character command)
	ssize_t count = read(fd, &command, 1);
	// Reserve a buffer for getline
	size_t bufferSize = 512;
	char* buffer = (char*) malloc(bufferSize);

	while (active && count > 0) {
		if (command == 'm') {
			// Read a line from the input file
			ssize_t icount = getline(&buffer, &bufferSize, input);

			if (icount < 0) {
				perror("Error while reading from the file");
				break;
			}
			else if (icount == 0) {
				// Rewind in case the file is exhausted
				fseek(input, 0, SEEK_SET);
				icount = getline(&buffer, &bufferSize, input);

				if (icount <= 0) {
					perror("Error while trying to rewind");
					break;
				}
			}

			// Write the read line to the client
			if (write(fd, buffer, icount - 1) < 0) {
				perror("Error while sending data to the client");
				break;
			}
		}

		// Block until the next message
		count = read(fd, &command, 1);
	}

	if (count < 0) {
		perror("Error while reading from the client");
	}

	free(buffer);
	close(fd);
}

int main(int argc, char* argv[]) {
	// Check input arguments
	if (argc != 3) {
		printf("Wrong number of arguments.\nSyntax: %s <input> <port>\n", argv[0]);
		return 1;
	}

	FILE* input = fopen(argv[1], "r");

	if (input == NULL) {
		perror("Unable to open input file.");
		return 2;
	}

	// Create server socket
	int sockfd = socket(AF_INET, SOCK_STREAM, 0);

	if (sockfd < 0) {
		perror("Unable to create socket");
		fclose(input);
		return 3;
	}

	// Reuse address (when restarting the server, to avoid the TIME_WAIT delay)
	if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &(int){1}, sizeof(int)) < 0)
		perror("Unable to set the REUSEADDR option");

	// Associate it with an address
	struct sockaddr_in serveraddr, clientaddr;
	socklen_t length;

	bzero(&serveraddr, sizeof(serveraddr));

	serveraddr.sin_family = AF_INET;
	serveraddr.sin_addr.s_addr = htonl(INADDR_ANY);
	serveraddr.sin_port = htons(atoi(argv[2]));

	if (bind(sockfd, (struct sockaddr*) &serveraddr, sizeof(serveraddr)) < 0) {
		perror("Unable to bind socket to address");
		close(sockfd);
		fclose(input);
		return 4;
	}

	// Listen for incoming connections
	if (listen(sockfd, 1) < 0) {
		perror("Unable to listen on socket");
		close(sockfd);
		fclose(input);
		return 5;
	}

	// Set Ctrl-C to finish gracefully
	if (signal(SIGINT, sigint_handler) == SIG_ERR)
		puts("Cannot set Ctrl-C handler\n");

	while (active) {
		int connfd = accept(sockfd, (struct sockaddr*) &clientaddr, &length);

		if (connfd < 0) {
			perror("Unable to accept incoming connection");
			close(sockfd);
			fclose(input);
			return 4;
		}

		// Print client info
		printf("Established connection with port %i", clientaddr.sin_port);

		// Handle the request from the client
		handleClient(connfd, input);
	}

	close(sockfd);
	fclose(input);

	return 0;
}
