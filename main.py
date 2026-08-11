from vision_core.app import VisionApp
from vision_core.module_manager import ModuleManager
from vision_core.controls import KeyboardControls
from vision_core.plugin_loader import load_plugins
from pathlib import Path
import argparse

BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / "config" / "modules.yaml"





def main():

    args = parse_args()

    source = (
        str(args.video)
        if args.video is not None
        else args.camera
    )

    manager = ModuleManager()
    controls = KeyboardControls(manager)
    load_plugins(config_path, manager, controls)
    
    app = VisionApp(
        source=source,
        module_manager=manager,
        controls=controls
    )

    app.run()


def parse_args():
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--camera", type=int, default=0)
    source_group.add_argument("--video", type=Path)

    return parser.parse_args()


if __name__ == "__main__":
    main()