import socket
import threading
import sys

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 55555
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

class ChatLogic:
    """
    Manages the client-side networking logic, including connection lifecycle,
    protocol handshakes, and message transmission.
    """

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.client = None
        self.nickname = ""
        self.running = False

    def connect(self, nickname):
        """
        Establishes a connection to the server using a synchronous handshake.

        Note: A new socket object is instantiated for every connection attempt
        to prevent 'Bad File Descriptor' errors on retries.

        Returns:
            (bool, str): A tuple containing success status and a status message.
        """
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))

            # Protocol Step 1: Send the requested nickname immediately upon connection
            self.client.send(nickname.encode(ENCODING))

            # Protocol Step 2: Block and wait for server validation (ACK or ERROR)
            response = self.client.recv(BUFFER_SIZE).decode(ENCODING)

            if not response:
                self.client.close()
                return False, "Connection closed by server."

            if response.startswith("ERROR:"):
                error_msg = response.replace("ERROR:", "").strip()
                self.client.close()
                return False, error_msg

            self.nickname = nickname
            self.running = True
            return True, "Connected successfully"

        except Exception as e:
            if self.client:
                try:
                    self.client.close()
                except: pass
            return False, str(e)

    def disconnect(self):
        """Cleanly closes the socket and updates the state flags."""
        self.running = False
        try:
            if self.client:
                self.client.close()
        except:
            pass

    def send_private_message(self, target, message):
        """
        Constructs a payload strictly in 'TARGET:MESSAGE' format for the server router.
        """
        try:
            if not self.running: return
            full_msg = f"{target}:{message}"
            self.client.send(full_msg.encode(ENCODING))
        except socket.error:
            print("Failed to send message. Connection lost.")
            self.disconnect()

    def start_receiving(self, callback):
        """
        Spawns a daemon thread to listen for incoming stream data without blocking the UI.

        Args:
            callback (function): Handle to update the UI/CLI with received strings.
        """
        def receive_loop():
            while self.running:
                try:
                    data = self.client.recv(BUFFER_SIZE).decode(ENCODING)
                    if not data:
                        break
                    callback(data)
                except:
                    break

            self.disconnect()
            callback("System: Disconnected from server.")

        threading.Thread(target=receive_loop, daemon=True).start()

def run_cli_mode():
    """
    Command-line interface entry point. Handles the user input loop and
    instantiates the ChatLogic controller.
    """
    host = input(f"Host IP (default {DEFAULT_HOST}): ").strip() or DEFAULT_HOST
    port_input = input(f"Port (default {DEFAULT_PORT}): ").strip() or str(DEFAULT_PORT)

    try:
        port = int(port_input)
    except ValueError:
        print("Invalid port.")
        return

    logic = None

    while True:
        nickname = input("Choose a Nickname: ").strip()
        if not nickname:
            print("Nickname cannot be empty.")
            continue

        # Logic instance is recreated per attempt to ensure fresh socket state
        logic = ChatLogic(host, port)
        success, msg = logic.connect(nickname)

        if success:
            print(f"Connected as {logic.nickname}! Usage: 'TargetName: Your Message'")
            print(f"Type 'exit' to quit.")
            break
        else:
            print(f"Connection Failed: {msg}")
            print("Please try again.\n")

    def cli_callback(message):
        print(f"\n{message}\n> ", end="")

    logic.start_receiving(cli_callback)

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == 'exit':
                logic.disconnect()
                break

            # Enforce local format validation before sending to network
            if ":" in user_input:
                target, content = user_input.split(":", 1)
                logic.send_private_message(target.strip(), content.strip())
            else:
                print("Invalid format! Use: TargetName: Message")

        except KeyboardInterrupt:
            logic.disconnect()
            break

if __name__ == "__main__":
    run_cli_mode()
