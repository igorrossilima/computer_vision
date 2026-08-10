from vision_core.module import VideoModule

class ModuleManager:
    def __init__(self):
        self._modules: dict[str, VideoModule] = {}
        self._loaded: set[str] = set()
        self._active: set[str] = set()

    def register(self, module: VideoModule) -> None:
        if module.id in self._modules:
            raise ValueError(
                f"O módulo {module.id}, já está registrado"
            )
        self._modules[module.id] = module

    def activate(self, module_id: str) -> None:
        if module_id not in self._modules:
            raise KeyError(f"Módulo desconhecido {module_id}")

        if module_id not in self._loaded:
            module = self._modules[module_id]
            module.start()
            self._loaded.add(module_id)

        self._active.add(module_id)
        

    def deactivate(self, module_id: str) -> None:
        if module_id not in self._modules:
            raise KeyError(f"Módulo desconhecido {module_id}")

        self._active.discard(module_id)
        

    def toggle(self, module_id: str) -> bool:
        if module_id in self._active:
            self.deactivate(module_id)
            return False
        
        self.activate(module_id)
        return True

    def process(self, frame):
        for module_id, module in self._modules.items():
            if module_id in self._active:
                frame = module.process(frame)

        return frame

    def shutdown(self) -> None:
        for module_id, module in reversed(self._modules.items()):
            if module_id in self._loaded:
                module.stop()

        self._active.clear()
        self._loaded.clear()