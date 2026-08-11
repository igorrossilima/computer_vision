from importlib import import_module
from pathlib import Path
from vision_core.controls import KeyboardControls
from vision_core.module import VideoModule
from vision_core.module_manager import ModuleManager
import yaml

def load_plugins(
        config_path: str | Path,
        module_manager: ModuleManager,
        controls: KeyboardControls
) -> None:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    module_specs = config.get("modules", [])

    if not isinstance(module_specs, list):
        raise ValueError("'modules' deve ser uma lista.")

    for spec in module_specs:
        import_path = spec["import"]
        plugin = import_module(import_path)

        factory = getattr(plugin, "create_module", None)

        if not callable(factory):
            raise TypeError(
                f"O plugin '{import_path}' não possui create_module()."
            )

        module = factory()

        if not isinstance(module, VideoModule):
            raise TypeError(
                f"A fábrica de '{import_path}' não retornou VideoModule."
            )

        module_manager.register(module)

        shortcut = spec.get("shortcut")

        if shortcut:
            controls.bind_toggle(shortcut, module.id)

        if spec.get("enabled", False):
            module_manager.activate(module.id)
