import socket
import threading

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 55555
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

class ServerLogic:
    """
    Central server controller. Manages socket bindings, client registry,
    and routing messages between distinct client sockets.
    """

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.clients = {}
        self.running = False
        self.on_log = None

    def log(self, message):
        if self.on_log:
            self.on_log(message)
        else:
            print(message)

    def parse_chat_message(self, message, sender_nickname):
        """
        Parses raw text based on the 'TARGET:CONTENT' protocol.
        Does not perform network actions, only string validation.
        """
        result = {"target": None, "content": None, "error": None}
        try:
            parts = message.split(":", 1)
            target = parts[0].strip()
            content = parts[1].strip()

            if target == sender_nickname:
                result["error"] = "You cannot send a message to yourself."
            elif not target or not content:
                result["error"] = "Name or message cannot be empty."
            else:
                result["target"] = target
                result["content"] = content

        except IndexError:
            result["error"] = "Invalid format. Use 'name:message'."
        except Exception:
            result["error"] = "Unknown parsing error."

        return result

    def get_valid_nickname(self, client_socket):
        """
        Performs the initial handshake.
        Note: This is a blocking call that enforces unique nicknames
        before the client is added to the main registry.
        """
        FORBIDDEN_NAMES = {"SYSTEM", "ERROR", "ONLINE_USERS", "", "SERVER"} | {user.upper() for user in list(self.clients)}

        try:
            nickname = client_socket.recv(BUFFER_SIZE).decode(ENCODING).strip()

            if not nickname:
                client_socket.send("ERROR: Nickname cannot be empty.".encode(ENCODING))
                return None

            if nickname.upper() in FORBIDDEN_NAMES:
                client_socket.send("ERROR: Nickname taken or forbidden.".encode(ENCODING))
                return None

            return nickname

        except:
            return None

    def close_connection(self, nickname):
        if nickname not in self.clients:
            return
        client_socket = self.clients.pop(nickname)
        try:
            client_socket.close()
            self.log(f"Connection for {nickname} closed.")
        except Exception as e:
            self.log(f"Error closing socket for {nickname}: {e}")

    def broadcast_online_users(self):
        user_list_msg = "ONLINE_USERS:" + ",".join(self.clients.keys())
        for client_name in list(self.clients.keys()):
            try:
                self.clients[client_name].send(user_list_msg.encode(ENCODING))
            except:
                self.close_connection(client_name)

    def kick_client(self, nickname):
        self.close_connection(nickname)
        self.broadcast_online_users()

    def get_online_users(self):
        users = []
        for nickname, sock in self.clients.items():
            try:
                addr = sock.getpeername()
                users.append({"nickname": nickname, "address": addr})
            except:
                users.append({"nickname": nickname, "address": None})
        return users

    def handle_client(self, client_socket, nickname):
        """
        Main threaded loop for a single client.
        Continually receives data, parses it, and routes it to the target's socket.
        """
        while self.running:
            try:
                message = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
                if not message:
                    self.log(f"Connection closed by {nickname}")
                    break

                res = self.parse_chat_message(message, nickname)

                if res["error"]:
                    client_socket.send(f"System: {res['error']}".encode(ENCODING))
                    continue

                target, msg_content = res["target"], res["content"]

                if target not in self.clients:
                    client_socket.send(f"System: User '{target}' not found.".encode(ENCODING))
                    continue

                recipient_socket = self.clients[target]
                try:
                    # Attempt to forward the message
                    recipient_socket.send(f"[{nickname}]: {msg_content}".encode(ENCODING))
                except (socket.error, BrokenPipeError):
                    # Liveness Check: If sending fails, assume recipient is dead and remove them
                    self.log(f"Liveness Probe Failed: {target} is gone.")
                    self.kick_client(target)
                    client_socket.send(f"System: {target} is no longer online.".encode(ENCODING))

            except (ConnectionResetError, socket.error):
                break

        self.kick_client(nickname)

    def start(self, on_log=None):
        if on_log:
            self.on_log = on_log

        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host, self.port))
            self.server.listen(10)
            self.running = True

            self.log(f"Server started on {self.host}:{self.port}")
            self.log("Waiting for connections...")

            while self.running:
                try:
                    client_socket, address = self.server.accept()

                    # Handshake must succeed before spawning a thread
                    nickname = self.get_valid_nickname(client_socket)

                    if not nickname:
                        client_socket.close()
                        continue

                    self.clients[nickname] = client_socket
                    self.log(f"New User: {nickname} from {address}")
                    client_socket.send("OK: Welcome".encode(ENCODING))

                    self.broadcast_online_users()

                    threading.Thread(target=self.handle_client,
                                     args=(client_socket, nickname),
                                     daemon=True).start()

                except Exception as e:
                    if self.running:
                        self.log(f"Server Error: {e}")
                    break

        except Exception as e:
            self.log(f"CRITICAL ERROR: Failed to bind port. {e}")
            return False, str(e)

        return True, "Server started"

    def start_async(self, on_log=None):
        threading.Thread(target=self.start, args=(on_log,), daemon=True).start()

    def stop(self):
        self.running = False
        for nickname in list(self.clients.keys()):
            self.close_connection(nickname)
        if self.server:
            try:
                self.server.close()
            except:
                pass

def run_cli_mode():
    host = input(f"Host IP (default {DEFAULT_HOST}): ").strip() or DEFAULT_HOST
    port_input = input(f"Port (default {DEFAULT_PORT}): ").strip() or str(DEFAULT_PORT)
    try:
        port = int(port_input)
    except ValueError:
        print("Invalid port.")
        return

    server = ServerLogic(host, port)
    print(f"Starting server on {host}:{port}...")
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    run_cli_mode()
