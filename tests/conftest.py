"""Конфигурация pytest для проекта."""

import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH для доступа к src
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
