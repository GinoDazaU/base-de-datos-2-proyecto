
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

class Utils:
    @staticmethod
    def build_path(*parts: str) -> str:
        """Concatena partes de ruta usando el separador del sistema."""
        return os.path.join(base_dir,*parts)