from __future__ import annotations


class OBSClient:
    pass


class OBSClientsManager:
    clients: list[OBSClient]

    def __init__(self: OBSClientsManager):
        self.clients = []
    
    def client_is_connected(self: OBSClientsManager, host: str, port: int) -> bool:
        return False


OBS_MANAGER = OBSClientsManager()
