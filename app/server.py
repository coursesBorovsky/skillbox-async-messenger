"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        #decoded = data
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").strip("\r\n ")
                if login in {client.login for client in self.server.clients}:
                    self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                    self.connection_lost()
                else:
                    if self not in {client for client in self.server.clients}:
                        self.connection_made(self.transport)
                    self.login = login
                    self.send_history()
                    self.transport.write(f"Привет, {self.login}!".encode())
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        self.server.messages.append(encoded)
        if len(self.server.messages) > 10:
            self.server.messages.pop(0)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        for message in self.server.messages:
            self.transport.write(message)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, *exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
