// Технологическое древо - клиентская часть

class TechTreeApp {
    constructor() {
        this.technologies = [];
        this.progress = {}; // {tech_name: true/false}
        this.selectedTech = null;
        this.currentView = 0; // 0: brief, 1: detailed, 2: all
        this.currentFilter = 'all';
        this.currentSort = 'default';
        this.canvas = null;
        this.ctx = null;
        this.graphData = null;
        this.viewTransform = { x: 0, y: 0, scale: 1 };
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.nodePositions = {};

        this.init();
    }

    async init() {
        // Загрузка прогресса из localStorage
        this.loadProgress();

        // Загрузка данных
        await this.loadTechnologies();

        // Инициализация UI
        this.setupEventListeners();
        this.renderTechList();

        // Выбор первой технологии
        if (this.technologies.length > 0) {
            this.selectTechnology(this.technologies[0].название);
        }
    }

    async loadTechnologies() {
        try {
            const response = await fetch('/api/technologies');
            const data = await response.json();
            this.technologies = data.технологии || [];
        } catch (error) {
            console.error('Error loading technologies:', error);
        }
    }

    setupEventListeners() {
        // Загрузка древа из файла
        document.getElementById('fileUpload').addEventListener('change', (e) => this.loadTreeFromFile(e));

        // Кнопки прогресса
        document.getElementById('saveProgress').addEventListener('click', () => this.saveProgress());
        document.getElementById('loadProgress').addEventListener('click', () => this.loadProgress(true));
        document.getElementById('resetProgress').addEventListener('click', () => this.resetProgress());

        // Поиск
        document.getElementById('searchButton').addEventListener('click', () => this.searchTechnology());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchTechnology();
            }
        });

        // Кнопки вида
        document.getElementById('viewFocus').addEventListener('click', () => this.setView(0));

        // Фильтры и сортировка
        document.getElementById('filterSelect').addEventListener('change', (e) => {
            this.currentFilter = e.target.value;
            this.renderTechList();
        });

        document.getElementById('sortSelect').addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.renderTechList();
        });

        // Справка
        document.getElementById('helpButton').addEventListener('click', () => {
            document.getElementById('helpPanel').classList.add('active');
        });

        document.getElementById('closeHelp').addEventListener('click', () => {
            document.getElementById('helpPanel').classList.remove('active');
        });

        // Canvas для визуализации
        this.canvas = document.getElementById('techCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.setupCanvas();
    }

    setupCanvas() {
        // Устанавливаем размер canvas
        const resizeCanvas = () => {
            const container = this.canvas.parentElement;
            this.canvas.width = container.clientWidth;
            this.canvas.height = container.clientHeight;
            if (this.selectedTech) {
                this.renderGraph();
            }
        };

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        // События мыши для масштабирования и перемещения
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // Масштабирование относительно позиции мыши
            const worldX = (mouseX - this.viewTransform.x) / this.viewTransform.scale;
            const worldY = (mouseY - this.viewTransform.y) / this.viewTransform.scale;

            this.viewTransform.scale *= delta;
            this.viewTransform.scale = Math.max(0.1, Math.min(5, this.viewTransform.scale));

            this.viewTransform.x = mouseX - worldX * this.viewTransform.scale;
            this.viewTransform.y = mouseY - worldY * this.viewTransform.scale;

            this.renderGraph();
        });

        // Перемещение
        this.canvas.addEventListener('mousedown', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // Проверка клика по узлу
            const clickedNode = this.getNodeAtPosition(mouseX, mouseY);
            if (clickedNode) {
                if (e.button === 2 || e.ctrlKey) { // Правая кнопка или Ctrl+Click
                    e.preventDefault();
                    this.toggleTechProgress(clickedNode);
                } else {
                    this.selectTechnology(clickedNode);
                }
            } else {
                this.isDragging = true;
                this.dragStart = { x: mouseX, y: mouseY };
            }
        });

        this.canvas.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                const rect = this.canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                this.viewTransform.x += mouseX - this.dragStart.x;
                this.viewTransform.y += mouseY - this.dragStart.y;

                this.dragStart = { x: mouseX, y: mouseY };
                this.renderGraph();
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            this.isDragging = false;
        });

        this.canvas.addEventListener('mouseleave', () => {
            this.isDragging = false;
        });

        // Контекстное меню
        this.canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });

        // Touch events для мобильных устройств
        let touchStartDistance = 0;
        let lastTouchPos = null;
        let touchStartTime = 0;
        let touchStartPos = null;

        this.canvas.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
            if (e.touches.length === 1) {
                const touch = e.touches[0];
                const rect = this.canvas.getBoundingClientRect();
                const touchX = touch.clientX - rect.left;
                const touchY = touch.clientY - rect.top;
                touchStartPos = { x: touchX, y: touchY };
                lastTouchPos = { x: touchX, y: touchY };
            } else if (e.touches.length === 2) {
                const touch1 = e.touches[0];
                const touch2 = e.touches[1];
                touchStartDistance = Math.hypot(
                    touch2.clientX - touch1.clientX,
                    touch2.clientY - touch1.clientY
                );
            }
        });

        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();

            if (e.touches.length === 1 && lastTouchPos) {
                const touch = e.touches[0];
                const rect = this.canvas.getBoundingClientRect();
                const touchX = touch.clientX - rect.left;
                const touchY = touch.clientY - rect.top;

                this.viewTransform.x += touchX - lastTouchPos.x;
                this.viewTransform.y += touchY - lastTouchPos.y;

                lastTouchPos = { x: touchX, y: touchY };
                this.renderGraph();
            } else if (e.touches.length === 2) {
                const touch1 = e.touches[0];
                const touch2 = e.touches[1];
                const currentDistance = Math.hypot(
                    touch2.clientX - touch1.clientX,
                    touch2.clientY - touch1.clientY
                );

                const delta = currentDistance / touchStartDistance;
                const centerX = (touch1.clientX + touch2.clientX) / 2 - this.canvas.getBoundingClientRect().left;
                const centerY = (touch1.clientY + touch2.clientY) / 2 - this.canvas.getBoundingClientRect().top;

                const worldX = (centerX - this.viewTransform.x) / this.viewTransform.scale;
                const worldY = (centerY - this.viewTransform.y) / this.viewTransform.scale;

                this.viewTransform.scale *= delta;
                this.viewTransform.scale = Math.max(0.1, Math.min(5, this.viewTransform.scale));

                this.viewTransform.x = centerX - worldX * this.viewTransform.scale;
                this.viewTransform.y = centerY - worldY * this.viewTransform.scale;

                touchStartDistance = currentDistance;
                this.renderGraph();
            }
        });

        this.canvas.addEventListener('touchend', (e) => {
            if (e.touches.length === 0) {
                const touchDuration = Date.now() - touchStartTime;
                if (touchDuration > 500 && touchStartPos) {
                    // Долгое нажатие - переключить прогресс
                    const clickedNode = this.getNodeAtPosition(touchStartPos.x, touchStartPos.y);
                    if (clickedNode) {
                        this.toggleTechProgress(clickedNode);
                    }
                } else if (touchDuration < 300 && touchStartPos && lastTouchPos) {
                    // Короткое нажатие - выбрать технологию
                    const distance = Math.hypot(
                        lastTouchPos.x - touchStartPos.x,
                        lastTouchPos.y - touchStartPos.y
                    );
                    if (distance < 10) {
                        const clickedNode = this.getNodeAtPosition(touchStartPos.x, touchStartPos.y);
                        if (clickedNode) {
                            this.selectTechnology(clickedNode);
                        }
                    }
                }
                lastTouchPos = null;
                touchStartPos = null;
            }
        });
    }

    getNodeAtPosition(x, y) {
        const worldX = (x - this.viewTransform.x) / this.viewTransform.scale;
        const worldY = (y - this.viewTransform.y) / this.viewTransform.scale;

        for (const [nodeName, pos] of Object.entries(this.nodePositions)) {
            const nodeRadius = 40;
            const distance = Math.hypot(worldX - pos.x, worldY - pos.y);
            if (distance < nodeRadius) {
                return nodeName;
            }
        }
        return null;
    }

    renderTechList() {
        const listContainer = document.getElementById('techList');
        listContainer.innerHTML = '';

        // Получаем отфильтрованный и отсортированный список
        let techs = [...this.technologies];

        // Фильтрация
        if (this.currentFilter !== 'all') {
            techs = techs.filter(tech => {
                const status = this.getTechStatus(tech.название);
                return status === this.currentFilter;
            });
        }

        // Сортировка
        if (this.currentSort === 'alphabet') {
            techs.sort((a, b) => a.название.localeCompare(b.название, 'ru'));
        } else if (this.currentSort === 'status') {
            techs.sort((a, b) => {
                const statusOrder = { 'completed': 0, 'available': 1, 'unavailable': 2 };
                const statusA = statusOrder[this.getTechStatus(a.название)] || 3;
                const statusB = statusOrder[this.getTechStatus(b.название)] || 3;
                return statusA - statusB;
            });
        }

        // Отображение
        techs.forEach(tech => {
            const itemWrapper = document.createElement('div');
            itemWrapper.className = 'tech-item-wrapper';

            const item = document.createElement('div');
            item.className = 'tech-item';
            item.textContent = tech.название;

            const status = this.getTechStatus(tech.название);
            item.classList.add(status);

            if (this.selectedTech === tech.название) {
                item.classList.add('selected');
            }

            item.addEventListener('click', () => {
                this.selectTechnology(tech.название);
            });

            // Кнопка "?" для открытия справки по технологии
            const helpButton = document.createElement('button');
            helpButton.className = 'tech-help-button';
            helpButton.textContent = '?';
            helpButton.title = 'Открыть справку';
            helpButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openTechHelp(tech.название);
            });

            itemWrapper.appendChild(item);
            itemWrapper.appendChild(helpButton);
            listContainer.appendChild(itemWrapper);
        });

        // Обновляем счетчик и прогресс
        this.updateProgressLabel();
    }

    searchTechnology() {
        const searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
        if (!searchQuery) {
            return;
        }

        // Ищем технологию в списке
        for (const tech of this.technologies) {
            if (tech.название.toLowerCase().includes(searchQuery)) {
                this.selectTechnology(tech.название);

                // Прокручиваем к найденной технологии в списке
                const listContainer = document.getElementById('techList');
                const techItems = listContainer.querySelectorAll('.tech-item');
                for (const item of techItems) {
                    if (item.textContent === tech.название) {
                        item.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        break;
                    }
                }
                return;
            }
        }

        alert(`Технология '${searchQuery}' не найдена`);
    }

    updateProgressLabel() {
        const totalTechs = this.technologies.length;
        const completedTechs = Object.values(this.progress).filter(v => v).length;
        const progressPercent = totalTechs > 0 ? (completedTechs / totalTechs * 100).toFixed(2) : 0;

        document.getElementById('progressLabel').textContent =
            `Технологий: ${totalTechs} | Прогресс: ${progressPercent}%`;
    }

    async openTechHelp(techName) {
        try {
            // Проверяем наличие mhtml файла для технологии
            const response = await fetch(`/api/tech_help/${encodeURIComponent(techName)}`);
            const data = await response.json();

            if (data.exists) {
                // Если файл существует, открываем его
                window.open(`/web/${data.filename}`, '_blank');
            } else {
                // Если файла нет, открываем Yandex поиск
                const searchUrl = `https://yandex.ru/search?text=${encodeURIComponent(techName)}`;
                window.open(searchUrl, '_blank');
            }
        } catch (error) {
            console.error('Error checking tech help:', error);
            // В случае ошибки открываем Yandex поиск
            const searchUrl = `https://yandex.ru/search?text=${encodeURIComponent(techName)}`;
            window.open(searchUrl, '_blank');
        }
    }

    async loadTreeFromFile(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (!data.технологии || !Array.isArray(data.технологии)) {
                throw new Error('Неверный формат файла');
            }

            this.technologies = data.технологии;
            this.progress = {};
            this.selectedTech = null;

            this.renderTechList();

            if (this.technologies.length > 0) {
                this.selectTechnology(this.technologies[0].название);
            }

            alert('Древо технологий успешно загружено!');
        } catch (error) {
            console.error('Error loading tree from file:', error);
            alert('Ошибка загрузки файла: ' + error.message);
        }
    }

    getTechStatus(techName) {
        if (this.progress[techName]) {
            return 'completed';
        }
        return this.isTechAvailable(techName) ? 'available' : 'unavailable';
    }

    isTechAvailable(techName) {
        const tech = this.technologies.find(t => t.название === techName);
        if (!tech) return true;

        const conditions = tech.условия;
        if (!conditions || conditions.length === 0) return true;

        if (typeof conditions[0] === 'string') {
            // Старый формат: все условия должны быть выполнены
            return conditions.every(parent => this.progress[parent]);
        } else if (Array.isArray(conditions[0])) {
            // Новый формат: хотя бы один путь должен быть полностью выполнен
            return conditions.some(path => path.every(parent => this.progress[parent]));
        }

        return true;
    }

    async selectTechnology(techName) {
        this.selectedTech = techName;

        // Обновление описания
        const tech = this.technologies.find(t => t.название === techName);
        if (tech) {
            document.getElementById('techDescription').textContent = tech.описание || 'Описание отсутствует';
        }

        // Обновление списка (для выделения)
        this.renderTechList();

        // Загрузка и отображение древа
        await this.loadTechTree(techName);
    }

    async loadTechTree(techName) {
        try {
            const response = await fetch(`/api/tree/${encodeURIComponent(techName)}`);
            this.graphData = await response.json();
            this.calculateNodePositions();
            this.centerView();
            this.renderGraph();
        } catch (error) {
            console.error('Error loading tech tree:', error);
        }
    }

    calculateNodePositions() {
        if (!this.graphData) return;

        const { nodes, parents, children, center } = this.graphData;
        this.nodePositions = {};

        // Центральный узел
        this.nodePositions[center] = { x: 0, y: 0 };

        // Распределение родителей по уровням
        const parentLevels = {};
        for (const [node, level] of Object.entries(parents)) {
            if (node === center) continue;
            if (!parentLevels[level]) parentLevels[level] = [];
            parentLevels[level].push(node);
        }

        for (const [level, techs] of Object.entries(parentLevels)) {
            const numTechs = techs.length;
            const startX = -(numTechs - 1) * 150;
            techs.forEach((tech, i) => {
                this.nodePositions[tech] = {
                    x: startX + i * 300,
                    y: parseInt(level) * 200
                };
            });
        }

        // Распределение детей по уровням
        const childLevels = {};
        for (const [node, level] of Object.entries(children)) {
            if (node === center) continue;
            if (!childLevels[level]) childLevels[level] = [];
            childLevels[level].push(node);
        }

        for (const [level, techs] of Object.entries(childLevels)) {
            const numTechs = techs.length;
            const startX = -(numTechs - 1) * 150;
            techs.forEach((tech, i) => {
                this.nodePositions[tech] = {
                    x: startX + i * 300,
                    y: -parseInt(level) * 200
                };
            });
        }
    }

    centerView() {
        this.viewTransform.x = this.canvas.width / 2;
        this.viewTransform.y = this.canvas.height / 2;
        this.viewTransform.scale = 1;
    }

    renderGraph() {
        if (!this.graphData || !this.ctx) return;

        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        ctx.save();
        ctx.translate(this.viewTransform.x, this.viewTransform.y);
        ctx.scale(this.viewTransform.scale, this.viewTransform.scale);

        // Рисуем связи
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2 / this.viewTransform.scale;
        this.graphData.edges.forEach(edge => {
            const from = this.nodePositions[edge.from];
            const to = this.nodePositions[edge.to];
            if (from && to) {
                this.drawArrow(ctx, from.x, from.y, to.x, to.y);
            }
        });

        // Рисуем узлы
        for (const [nodeName, pos] of Object.entries(this.nodePositions)) {
            const status = this.getTechStatus(nodeName);
            const colors = {
                'completed': '#4CAF50',
                'available': '#FFC107',
                'unavailable': '#f44336'
            };

            ctx.fillStyle = colors[status];
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 40, 0, Math.PI * 2);
            ctx.fill();

            // Обводка для выбранной технологии
            if (nodeName === this.selectedTech) {
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 4 / this.viewTransform.scale;
                ctx.stroke();
            }

            // Текст
            ctx.fillStyle = status === 'available' ? '#000' : '#fff';
            ctx.font = `${14 / this.viewTransform.scale}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            // Разбиваем длинные названия на несколько строк
            const words = nodeName.split(' ');
            const lines = [];
            let currentLine = '';

            words.forEach(word => {
                const testLine = currentLine ? `${currentLine} ${word}` : word;
                const metrics = ctx.measureText(testLine);
                if (metrics.width > 70 && currentLine) {
                    lines.push(currentLine);
                    currentLine = word;
                } else {
                    currentLine = testLine;
                }
            });
            if (currentLine) lines.push(currentLine);

            const lineHeight = 16 / this.viewTransform.scale;
            const startY = pos.y - (lines.length - 1) * lineHeight / 2;

            lines.forEach((line, i) => {
                ctx.fillText(line, pos.x, startY + i * lineHeight);
            });
        }

        ctx.restore();
    }

    drawArrow(ctx, fromX, fromY, toX, toY) {
        const headlen = 15 / this.viewTransform.scale;
        const angle = Math.atan2(toY - fromY, toX - fromX);
        const nodeRadius = 40;

        // Вычисляем начальную и конечную точки стрелки (на границе кругов)
        const fromXAdj = fromX + Math.cos(angle) * nodeRadius;
        const fromYAdj = fromY + Math.sin(angle) * nodeRadius;
        const toXAdj = toX - Math.cos(angle) * nodeRadius;
        const toYAdj = toY - Math.sin(angle) * nodeRadius;

        // Вычисляем контрольную точку для кривой Безье
        // Размещаем её перпендикулярно к середине линии для создания изгиба
        const midX = (fromXAdj + toXAdj) / 2;
        const midY = (fromYAdj + toYAdj) / 2;

        // Вектор, перпендикулярный к линии
        const perpAngle = angle + Math.PI / 2;

        // Величина изгиба зависит от расстояния между узлами
        const distance = Math.hypot(toX - fromX, toY - fromY);
        const curvature = Math.min(distance * 0.15, 50); // Ограничиваем максимальный изгиб

        const controlX = midX + Math.cos(perpAngle) * curvature;
        const controlY = midY + Math.sin(perpAngle) * curvature;

        // Рисуем кривую
        ctx.beginPath();
        ctx.moveTo(fromXAdj, fromYAdj);
        ctx.quadraticCurveTo(controlX, controlY, toXAdj, toYAdj);
        ctx.stroke();

        // Вычисляем угол стрелки в конечной точке (касательная к кривой)
        const t = 1; // В конечной точке
        const tangentX = 2 * (1 - t) * (controlX - fromXAdj) + 2 * t * (toXAdj - controlX);
        const tangentY = 2 * (1 - t) * (controlY - fromYAdj) + 2 * t * (toYAdj - controlY);
        const endAngle = Math.atan2(tangentY, tangentX);

        // Рисуем стрелку
        ctx.beginPath();
        ctx.moveTo(toXAdj, toYAdj);
        ctx.lineTo(
            toXAdj - headlen * Math.cos(endAngle - Math.PI / 6),
            toYAdj - headlen * Math.sin(endAngle - Math.PI / 6)
        );
        ctx.moveTo(toXAdj, toYAdj);
        ctx.lineTo(
            toXAdj - headlen * Math.cos(endAngle + Math.PI / 6),
            toYAdj - headlen * Math.sin(endAngle + Math.PI / 6)
        );
        ctx.stroke();
    }

    toggleTechProgress(techName) {
        this.progress[techName] = !this.progress[techName];
        this.renderTechList();
        this.renderGraph();
        this.saveProgress();
    }

    setView(viewIndex) {
        this.currentView = viewIndex;

        // Обновление кнопок
        document.querySelectorAll('.btn-view').forEach((btn, i) => {
            btn.classList.toggle('active', i === viewIndex);
        });

        // Фокусировка - показываем выбранную технологию
        if (this.selectedTech) {
            this.loadTechTree(this.selectedTech);
        }
    }

    saveProgress() {
        localStorage.setItem('techTreeProgress', JSON.stringify(this.progress));
        alert('Прогресс сохранен!');
    }

    loadProgress(showAlert = false) {
        const saved = localStorage.getItem('techTreeProgress');
        if (saved) {
            this.progress = JSON.parse(saved);
            this.renderTechList();
            this.renderGraph();
            if (showAlert) {
                alert('Прогресс загружен!');
            }
        } else if (showAlert) {
            alert('Сохраненный прогресс не найден');
        }
    }

    resetProgress() {
        if (confirm('Вы уверены, что хотите сбросить весь прогресс?')) {
            this.progress = {};
            localStorage.removeItem('techTreeProgress');
            this.renderTechList();
            this.renderGraph();
            alert('Прогресс сброшен!');
        }
    }
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', () => {
    new TechTreeApp();
});
