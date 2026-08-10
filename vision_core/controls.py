from vision_core.module_manager import ModuleManager

class KeyboardControls:
    def __init__(self, module_manager: ModuleManager):
        self._module_manager = module_manager
        self._bindings: dict[str, str] = {}

    def bind_toggle(self, key: str, module_id: str) -> None:
        if len(key) !=1:
            raise ValueError("O atalho deve possuir uma única tecla.")

        normalized_key = key.lower()

        if normalized_key in self._bindings:
            raise ValueError(
                f"A tecla '{normalized_key}' já está associada."
            )
        self._bindings[normalized_key] = module_id

    def handle(self, key_code: int):
        if key_code == -1:
            return None

        key = chr(key_code & 0xFF).lower()
        module_id = self._bindings.get(key)

        if module_id is None:
            return None

        active = self._module_manager.toggle(module_id)
        return module_id, active