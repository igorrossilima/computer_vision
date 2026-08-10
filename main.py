from modules.face_blur.plugin import FaceBlurModule
from vision_core.app import VisionApp
from vision_core.module_manager import ModuleManager
from vision_core.controls import KeyboardControls

def main():

    manager = ModuleManager()
    manager.register(FaceBlurModule())

    controls = KeyboardControls(manager)
    controls.bind_toggle("b", "face_blur")
    
    app = VisionApp(
        source=0,
        module_manager=manager,
        controls=controls
    )

    app.run()

if __name__ == "__main__":
    main()