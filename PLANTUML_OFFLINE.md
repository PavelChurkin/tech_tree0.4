# Offline PlantUML Setup / Настройка оффлайн PlantUML

## Русский

### Проблема
При генерации больших диаграмм технологического древа онлайн-сервер PlantUML может обрезать изображение по ширине.

### Решение
Программа теперь поддерживает три режима рендеринга (в порядке приоритета):

1. **Локальный PlantUML (офлайн, без ограничений)**
2. **Онлайн PlantUML SVG (без ограничений по ширине)**
3. **Онлайн PlantUML PNG (может обрезаться на больших диаграммах)**

### Как включить офлайн режим

#### Вариант 1: Установка PlantUML локально (рекомендуется)

1. Установите Java:
   - Windows: скачайте с https://www.java.com/
   - Linux: `sudo apt install default-jre` (Ubuntu/Debian) или `sudo yum install java` (RHEL/CentOS)
   - macOS: `brew install java`

2. Скачайте PlantUML JAR файл:
   ```bash
   wget https://github.com/plantuml/plantuml/releases/download/v1.2024.3/plantuml-1.2024.3.jar -O plantuml.jar
   ```

   Или скачайте вручную с https://plantuml.com/download и сохраните как `plantuml.jar`

3. Поместите файл `plantuml.jar` в ту же папку, где находится `tech_tree.py`

4. Готово! Программа автоматически будет использовать локальный PlantUML

#### Вариант 2: Улучшенный онлайн режим (SVG)

Если вы не можете установить Java, программа автоматически будет использовать SVG формат вместо PNG:

1. Установите библиотеку для конвертации SVG (опционально, но рекомендуется):
   ```bash
   pip install cairosvg
   ```

2. Если cairosvg недоступен, программа попробует другие методы конвертации или откатится на PNG

### Проверка режима работы

При загрузке диаграммы в консоли будет выведено сообщение:
- "Используется локальный PlantUML (офлайн режим)" - офлайн режим активен
- "Используется онлайн PlantUML SVG" - онлайн режим без ограничений
- "Используется онлайн PlantUML PNG (может быть обрезан)" - старый режим с возможными ограничениями

---

## English

### Problem
When generating large technology tree diagrams, the online PlantUML server may crop the image width.

### Solution
The program now supports three rendering modes (in priority order):

1. **Local PlantUML (offline, no limits)**
2. **Online PlantUML SVG (no width limits)**
3. **Online PlantUML PNG (may be cropped on large diagrams)**

### How to Enable Offline Mode

#### Option 1: Install PlantUML Locally (recommended)

1. Install Java:
   - Windows: download from https://www.java.com/
   - Linux: `sudo apt install default-jre` (Ubuntu/Debian) or `sudo yum install java` (RHEL/CentOS)
   - macOS: `brew install java`

2. Download PlantUML JAR file:
   ```bash
   wget https://github.com/plantuml/plantuml/releases/download/v1.2024.3/plantuml-1.2024.3.jar -O plantuml.jar
   ```

   Or download manually from https://plantuml.com/download and save as `plantuml.jar`

3. Place the `plantuml.jar` file in the same folder as `tech_tree.py`

4. Done! The program will automatically use local PlantUML

#### Option 2: Enhanced Online Mode (SVG)

If you cannot install Java, the program will automatically use SVG format instead of PNG:

1. Install SVG conversion library (optional but recommended):
   ```bash
   pip install cairosvg
   ```

2. If cairosvg is unavailable, the program will try other conversion methods or fall back to PNG

### Checking Current Mode

When loading a diagram, a message will be printed to console:
- "Using local PlantUML (offline mode)" - offline mode is active
- "Using online PlantUML SVG" - online mode without limitations
- "Using online PlantUML PNG (may be cropped)" - old mode with possible limitations
