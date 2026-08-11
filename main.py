from vision_core.app import VisionApp
from vision_core.module_manager import ModuleManager
from vision_core.controls import KeyboardControls
from vision_core.plugin_loader import load_plugins
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / "config" / "modules.yaml"


def main():

    manager = ModuleManager()
    controls = KeyboardControls(manager)
    load_plugins(config_path, manager, controls)
    
    app = VisionApp(
        source=0,
        module_manager=manager,
        controls=controls
    )

    app.run()

if __name__ == "__main__":
    main()