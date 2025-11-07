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

Если вы не можете установить Java, программа автоматически будет использовать SVG формат вместо PNG. **SVG формат не имеет ограничений по ширине**, поэтому широкие диаграммы будут отображаться полностью.

**Важно:** Для отображения SVG в программе используется автоматическая конвертация:
- Программа пытается использовать `cairosvg` (если установлен)
- Если `cairosvg` недоступен, используется PNG fallback

**Установка cairosvg (опционально):**

Установка `cairosvg` улучшает качество конвертации SVG, но требует дополнительных системных библиотек:

**Windows:**
```bash
pip install cairosvg
```
⚠️ **Примечание для Windows:** После установки `pip install cairosvg` также требуется установить GTK+ runtime с Cairo библиотеками:
- Скачайте установщик: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
- Запустите установщик и следуйте инструкциям
- Перезапустите программу

Если не устанавливать GTK+, программа автоматически будет использовать PNG формат (который может обрезать очень широкие диаграммы).

**Linux:**
```bash
sudo apt install libcairo2-dev pkg-config python3-dev  # Ubuntu/Debian
pip install cairosvg
```

**macOS:**
```bash
brew install cairo pkg-config
pip install cairosvg
```

**Без cairosvg:** Программа автоматически откатится на PNG формат, который работает всегда, но может обрезать очень широкие диаграммы.

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

If you cannot install Java, the program will automatically use SVG format instead of PNG. **SVG format has no width limitations**, so wide diagrams will display fully.

**Important:** To display SVG in the program, automatic conversion is used:
- The program tries to use `cairosvg` (if installed)
- If `cairosvg` is unavailable, it falls back to PNG

**Installing cairosvg (optional):**

Installing `cairosvg` improves SVG conversion quality, but requires additional system libraries:

**Windows:**
```bash
pip install cairosvg
```
⚠️ **Note for Windows:** After installing `pip install cairosvg`, you also need to install GTK+ runtime with Cairo libraries:
- Download installer: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
- Run the installer and follow instructions
- Restart the program

If you don't install GTK+, the program will automatically use PNG format (which may crop very wide diagrams).

**Linux:**
```bash
sudo apt install libcairo2-dev pkg-config python3-dev  # Ubuntu/Debian
pip install cairosvg
```

**macOS:**
```bash
brew install cairo pkg-config
pip install cairosvg
```

**Without cairosvg:** The program will automatically fall back to PNG format, which always works but may crop very wide diagrams.

### Checking Current Mode

When loading a diagram, a message will be printed to console:
- "Using local PlantUML (offline mode)" - offline mode is active
- "Using online PlantUML SVG" - online mode without limitations
- "Using online PlantUML PNG (may be cropped)" - old mode with possible limitations
