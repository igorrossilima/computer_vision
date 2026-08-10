from abc import ABC, abstractmethod
import numpy as np

class VideoModule(ABC):
    id: str
    name: str

    def start(self) -> None:
        pass


    @abstractmethod
    def process(self, frame: np.ndarray) -> np.ndarray:
        pass

    def stop(self) -> None:
        pass

    