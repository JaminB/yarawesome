from abc import abstractmethod


class Daemon:

    @abstractmethod
    def run(self) -> bool:
        return True
