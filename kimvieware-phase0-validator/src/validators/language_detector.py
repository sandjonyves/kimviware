from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Set
import logging


# =========================================================
# 🧠 STRATEGY INTERFACE
# =========================================================
class LanguageStrategy(ABC):

    @abstractmethod
    def get_extensions(self) -> Set[str]:
        pass

    @abstractmethod
    def detect_files(self, files: List[Path]) -> List[Path]:
        pass

    @abstractmethod
    def find_entry_point(self, source_dir: Path, files: List[Path]) -> Optional[Path]:
        pass

    @abstractmethod
    def detect_framework(self, source_dir: Path) -> Optional[str]:
        pass


# =========================================================
# 🐍 PYTHON
# =========================================================
class PythonStrategy(LanguageStrategy):

    def get_extensions(self):
        return {'.py'}

    def detect_files(self, files):
        return [f for f in files if f.suffix.lower() == '.py']

    def find_entry_point(self, source_dir, files):
        candidates = ['main.py', 'app.py', '__main__.py', 'run.py']

        for c in candidates:
            f = source_dir / c
            if f.exists():
                return f

        return files[0] if files else None

    def detect_framework(self, source_dir):
        if (source_dir / "manage.py").exists():
            return "django"
        if (source_dir / "requirements.txt").exists():
            return "flask"
        return None


# =========================================================
# ☕ JAVA
# =========================================================
class JavaStrategy(LanguageStrategy):

    def get_extensions(self):
        return {'.java'}

    def detect_files(self, files):
        return [f for f in files if f.suffix.lower() == '.java']

    def find_entry_point(self, source_dir, files):
        for f in files:
            try:
                content = f.read_text(errors="ignore")
                if "public static void main" in content:
                    return f
            except Exception:
                continue
        return files[0] if files else None

    def detect_framework(self, source_dir):
        if (source_dir / "pom.xml").exists():
            return "spring_boot"
        return None


# =========================================================
# ⚙️ C / C++
# =========================================================
class CppStrategy(LanguageStrategy):

    def get_extensions(self):
        return {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'}

    def detect_files(self, files):
        return [f for f in files if f.suffix.lower() in self.get_extensions()]

    def find_entry_point(self, source_dir, files):
        for f in files:
            try:
                content = f.read_text(errors="ignore")
                if "main(" in content:
                    return f
            except Exception:
                continue
        return files[0] if files else None

    def detect_framework(self, source_dir):
        return None


# =========================================================
# 🌐 JS / TS
# =========================================================
class JavaScriptStrategy(LanguageStrategy):

    def get_extensions(self):
        return {'.js', '.ts', '.jsx', '.tsx'}

    def detect_files(self, files):
        return [f for f in files if f.suffix.lower() in self.get_extensions()]

    def find_entry_point(self, source_dir, files):
        candidates = ["index.js", "app.js", "server.js", "index.ts"]

        for c in candidates:
            f = source_dir / c
            if f.exists():
                return f

        return files[0] if files else None

    def detect_framework(self, source_dir):
        if (source_dir / "package.json").exists():
            return "express"
        return None


# =========================================================
# 🗂️ REGISTRY
# =========================================================
class StrategyRegistry:

    def __init__(self):
        self._strategies: Dict[str, LanguageStrategy] = {}

    def register(self, name: str, strategy: LanguageStrategy):
        self._strategies[name] = strategy

    def get_all(self):
        return self._strategies.items()

    def get(self, name: str):
        return self._strategies.get(name)


# =========================================================
# 🚀 DETECTOR (OCP CLEAN + ROBUST)
# =========================================================
class LanguageDetector:

    def __init__(self, registry: StrategyRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)

    def detect(self, source_dir: Path, logger: Optional[logging.Logger] = None):

        logger = logger or self.logger

        ignore_dirs = {
            'venv', '.venv', 'env', 'node_modules',
            '__pycache__', '.git', '.idea', '.vscode',
            'dist', 'build'
        }

        all_files = []

        for path in source_dir.rglob('*'):
            if any(d in path.parts for d in ignore_dirs):
                continue
            if path.is_file():
                all_files.append(path)

        if not all_files:
            logger.warning("No files found")
            return {
                'language': 'unknown',
                'confidence': 0.0,
                'files': []
            }

        # =====================================================
        # 🔥 SCORING OCP
        # =====================================================
        scores = {}

        for name, strategy in self.registry.get_all():
            scores[name] = sum(
                1 for f in all_files if f.suffix.lower() in strategy.get_extensions()
            )

        primary_language = max(scores, key=scores.get)

        strategy = self.registry.get(primary_language)

        if strategy is None:
            return {
                'language': 'unknown',
                'confidence': 0.0,
                'files': all_files
            }

        language_files = strategy.detect_files(all_files)

        total = sum(scores.values()) or 1  # 🔥 avoid division by zero
        confidence = scores[primary_language] / total

        entry = strategy.find_entry_point(source_dir, language_files)
        framework = strategy.detect_framework(source_dir)

        logger.info(f"Detected {primary_language} ({confidence:.0%})")

        return {
            'language': primary_language,
            'framework': framework,
            'files': language_files,
            'entry_point': entry,
            'confidence': confidence,
            'file_count': len(language_files),
        }


# =========================================================
# 🔌 INIT
# =========================================================
registry = StrategyRegistry()
registry.register("python", PythonStrategy())
registry.register("java", JavaStrategy())
registry.register("cpp", CppStrategy())
registry.register("javascript", JavaScriptStrategy())

detector = LanguageDetector(registry)