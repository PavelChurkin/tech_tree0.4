import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, simpledialog
import json
import os
import webbrowser
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import tempfile
import subprocess
import urllib.request
import urllib.parse
from PIL import Image, ImageTk
import io
import zlib
import base64
import xml.etree.ElementTree as ET
from io import BytesIO

# Путь к текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Загрузка данных из JSON файла
json_path = os.path.join(BASE_DIR, 'techno2.json')
try:
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    data = {"технологии": []}

dct_tech = {}
for _, _i in enumerate(data['технологии']):
    dct_tech[data['технологии'][_]['название']] = data['технологии'][_]

# Основное окно приложения
root = tk.Tk()
root.title("Технологическое древо")
root.configure(bg='#2e2e2e')
root.geometry("1300x800")

# Создание фреймов для областей
left_frame = tk.Frame(root, width=600, height=600, bg='lightgray')
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

left_top_frame = tk.Frame(left_frame, width=600, height=300, bg='lightgray')
left_top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

left_bottom_frame = tk.Frame(left_frame, width=600, height=300, bg='lightgray')
left_bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

right_frame = tk.Frame(root, width=600, height=600, bg='gray')
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Переменные
selected_tech = tk.StringVar()
tech_flags = {tech['название']: False for tech in data['технологии']}
zoom_factor = 1.0
pan_start = None
drag_start = None
current_xlim = None
current_ylim = None
view_flags = ["Кратко", "Подробно", "Всё"]
current_state = 0
is_selecting = False

desc_text1 = scrolledtext.ScrolledText(
    left_top_frame,
    wrap=tk.WORD,
    font=('Arial', 20),
    bg='white',
    width=60,
    height=10
)
desc_text1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
desc_text1.insert(tk.END, "Выберите технологию из списка")


# Функции для масштабирования и панорамирования
def on_scroll(event):
    global zoom_factor, current_xlim, current_ylim
    if event.inaxes:
        x, y = event.xdata, event.ydata
        scale_factor = 1.1 if event.button == 'up' else 0.9
        zoom_factor *= scale_factor
        ax = event.inaxes
        ax.set_xlim((x - (x - ax.get_xlim()[0]) * scale_factor,
                     x + (ax.get_xlim()[1] - x) * scale_factor))
        ax.set_ylim((y - (y - ax.get_ylim()[0]) * scale_factor,
                     y + (ax.get_ylim()[1] - y) * scale_factor))
        canvas.draw_idle()
        current_xlim = ax.get_xlim()
        current_ylim = ax.get_ylim()


def on_press(event):
    global pan_start, drag_start
    if event.button == 1 and event.inaxes:
        drag_start = (event.xdata, event.ydata)


def on_motion(event):
    global pan_start, drag_start, current_xlim, current_ylim
    if drag_start and event.inaxes:
        ax = event.inaxes
        if pan_start is None:
            dx = event.xdata - drag_start[0]
            dy = event.ydata - drag_start[1]
            if (dx ** 2 + dy ** 2) > 1:
                pan_start = drag_start
        if pan_start:
            dx = event.xdata - pan_start[0]
            dy = event.ydata - pan_start[1]

            ax.set_xlim(ax.get_xlim()[0] - dx, ax.get_xlim()[1] - dx)
            ax.set_ylim(ax.get_ylim()[0] - dy, ax.get_ylim()[1] - dy)
            canvas.draw_idle()
        current_xlim = ax.get_xlim()
        current_ylim = ax.get_ylim()


def on_release(event):
    global pan_start, drag_start
    if event.button == 1:
        if pan_start is None and drag_start:
            x, y = event.xdata, event.ydata
            for node, (nx, ny) in pos.items():
                if (nx - 0.9 <= x <= nx + 0.9) and (ny - 0.9 <= y <= ny + 0.9):
                    update_description(node)
                    break
        pan_start = None
        drag_start = None


# Функция для обновления описания технологии
def update_description(tech_name):
    # Очистка предыдущего описания
    for widget in left_top_frame.winfo_children():
        widget.destroy()

    # Поиск технологии
    for tech in data['технологии']:
        if tech['название'] == tech_name:
            # Описание
            desc_text = scrolledtext.ScrolledText(
                left_top_frame,
                wrap=tk.WORD,
                font=('Arial', 12),
                bg='white',
                width=60,
                height=10
            )
            desc_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            desc_text.insert(tk.END, tech['описание'])
            desc_text.configure(state='disabled')

            selected_tech.set(tech_name)
            update_visualization(tech_name)
            update_listbox_colors()
            break


def open_mhtml():
    tech_name = selected_tech.get()
    if tech_name:
        if os.path.exists(fr"web\{tech_name}.mhtml"):
            webbrowser.open(fr"web\{tech_name}.mhtml")
        else:
            webbrowser.open(fr"https://yandex.ru/search?text={tech_name}")


# Функция для проверки доступности технологии
def is_tech_available(tech_name):
    # Проверяем, все ли родители изучены
    for tech in data['технологии']:
        if tech['название'] == tech_name:
            for parent in tech['условия']:
                if not tech_flags.get(parent, False):
                    return False
    return True


# Функция для обновления цветов списка
def update_listbox_colors():
    global is_selecting
    is_selecting = True

    # Сохраняем текущую позицию прокрутки
    scroll_pos = tech_listbox.yview()

    tech_listbox.delete(0, tk.END)
    for tech in data['технологии']:
        name = tech['название']
        tech_listbox.insert(tk.END, name)
        # Определение цвета
        if tech_flags[name]:
            color = 'green'
        elif is_tech_available(name):
            color = 'yellow'
        else:
            color = 'red'
        tech_listbox.itemconfig(tk.END, bg=color)

    # Восстанавливаем позицию прокрутки
    tech_listbox.yview_moveto(scroll_pos[0])
    is_selecting = False


# Функция для поиска всех родителей
def find_all_parents(tech_name):
    parents = {}
    queue = deque([(tech_name, 0)])
    while queue:
        current_tech, level = queue.popleft()
        if current_tech in parents:
            continue
        parents[current_tech] = level
        for tech in data['технологии']:
            if tech['название'] == current_tech:
                for parent in tech['условия']:
                    queue.append((parent, level + 1))
                break
    return parents


# Функция для поиска всех детей
def find_all_children(tech_name):
    children = {}
    queue = deque([(tech_name, 0)])
    while queue:
        current_tech, level = queue.popleft()
        if current_tech in children:
            continue
        children[current_tech] = level
        for tech in data['технологии']:
            if current_tech in tech['условия']:
                queue.append((tech['название'], level + 1))
    return children


# Функция для обновления визуализации древа
def update_visualization(tech_name, preserve_view=False):
    global G, pos, fig, ax, canvas, current_xlim, current_ylim

    if not tech_name:
        return

    if not preserve_view:
        # Очистка правой области
        for widget in right_frame.winfo_children():
            widget.destroy()

    if current_state == 0:
        if not preserve_view:
            # Создание графа
            G = nx.DiGraph()
            pos = {}

            # Центральный узел
            pos[tech_name] = (0, 0)
            G.add_node(tech_name)

            # Поиск всех родителей и детей
            parents = find_all_parents(tech_name)
            children = find_all_children(tech_name)

            # Распределение родителей с увеличенным расстоянием
            parent_levels = {}
            for parent, level in parents.items():
                if parent == tech_name:
                    continue
                if level not in parent_levels:
                    parent_levels[level] = []
                parent_levels[level].append(parent)

            for level, techs in parent_levels.items():
                num_techs = len(techs)
                start_x = -(num_techs - 1) * 4
                for i, tech in enumerate(techs):
                    pos[tech] = (start_x + i * 8, level * 8)
                    if level == 1:
                        G.add_edge(tech, tech_name)

            # Распределение детей
            child_levels = {}
            for child, level in children.items():
                if child == tech_name:
                    continue
                if level not in child_levels:
                    child_levels[level] = []
                child_levels[level].append(child)

            for level, techs in child_levels.items():
                num_techs = len(techs)
                start_x = -(num_techs - 1) * 4
                for i, tech in enumerate(techs):
                    pos[tech] = (start_x + i * 8, -level * 8)
                    if level == 1:
                        G.add_edge(tech_name, tech)

            # Визуализация
            fig, ax = plt.subplots(figsize=(15, 15))
            node_colors = ['green' if tech_flags[node] else 'yellow' if is_tech_available(node) else 'red' for node in
                           G.nodes]

            nx.draw(
                G,
                pos,
                with_labels=True,
                node_size=2500,
                node_color=node_colors,
                font_size=10,
                arrows=True,
                arrowstyle='->,head_width=0.6,head_length=0.8',
                ax=ax
            )

            # Встраивание и настройка событий
            canvas = FigureCanvasTkAgg(fig, master=right_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            # Подключение обработчиков
            fig.canvas.mpl_connect('scroll_event', on_scroll)
            fig.canvas.mpl_connect('button_press_event', on_press)
            fig.canvas.mpl_connect('motion_notify_event', on_motion)
            fig.canvas.mpl_connect('button_release_event', on_release)
            fig.canvas.mpl_connect('button_press_event', lambda e: on_right_click(e) if e.button == 3 else None)

            # Сохраняем текущие границы
            current_xlim = ax.get_xlim()
            current_ylim = ax.get_ylim()
        else:
            # Обновляем только цвета узлов
            if G is not None and ax is not None:
                node_colors = ['green' if tech_flags[node] else 'yellow' if is_tech_available(node) else 'red' for node
                               in G.nodes]
                ax.clear()
                nx.draw(
                    G,
                    pos,
                    with_labels=True,
                    node_size=2500,
                    node_color=node_colors,
                    font_size=10,
                    arrows=True,
                    arrowstyle='->,head_width=0.6,head_length=0.8',
                    ax=ax
                )
                ax.set_xlim(current_xlim)
                ax.set_ylim(current_ylim)
                canvas.draw_idle()

    elif current_state == 1:
        if not preserve_view:
            # Очистка правой области
            for widget in right_frame.winfo_children():
                widget.destroy()

            # Создание графа
            G = nx.DiGraph()
            pos = {}

            # Центральный узел
            pos[tech_name] = (0, 0)
            G.add_node(tech_name)

            # Поиск всех родителей и детей
            parents = find_all_parents(tech_name)
            children = find_all_children(tech_name)

            # Распределение родителей с увеличенным расстоянием
            parent_levels = {}
            for parent, level in parents.items():
                if parent == tech_name:
                    continue
                if level not in parent_levels:
                    parent_levels[level] = []
                parent_levels[level].append(parent)

            _previous_techs = [tech_name]
            for level, techs in parent_levels.items():
                num_techs = len(techs)
                start_x = -(num_techs - 1) * 4
                for i, tech in enumerate(techs):
                    pos[tech] = (start_x + i * 8, level * 8)
                    for _tech in _previous_techs:
                        if tech in dct_tech[_tech]['условия']:
                            G.add_edge(tech, _tech)
                _previous_techs = techs

            # Распределение детей
            child_levels = {}
            for child, level in children.items():
                if child == tech_name:
                    continue
                if level not in child_levels:
                    child_levels[level] = []
                child_levels[level].append(child)

            _previous_techs = [tech_name]
            for level, techs in child_levels.items():
                num_techs = len(techs)
                start_x = -(num_techs - 1) * 4
                for i, tech in enumerate(techs):
                    pos[tech] = (start_x + i * 8, -level * 8)
                    for _tech in _previous_techs:
                        if _tech in dct_tech[tech]['условия']:
                            G.add_edge(_tech, tech)
                _previous_techs = techs

            # Визуализация
            fig, ax = plt.subplots(figsize=(15, 15))
            node_colors = ['green' if tech_flags[node] else 'yellow' if is_tech_available(node) else 'red' for node in
                           G.nodes]

            nx.draw(
                G,
                pos,
                with_labels=True,
                node_size=2500,
                node_color=node_colors,
                font_size=10,
                arrows=True,
                arrowstyle='->,head_width=0.6,head_length=0.8',
                ax=ax
            )

            # Встраивание и настройка событий
            canvas = FigureCanvasTkAgg(fig, master=right_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            # Подключение обработчиков
            fig.canvas.mpl_connect('scroll_event', on_scroll)
            fig.canvas.mpl_connect('button_press_event', on_press)
            fig.canvas.mpl_connect('motion_notify_event', on_motion)
            fig.canvas.mpl_connect('button_release_event', on_release)
            fig.canvas.mpl_connect('button_press_event', lambda e: on_right_click(e) if e.button == 3 else None)

            # Сохраняем текущие границы
            current_xlim = ax.get_xlim()
            current_ylim = ax.get_ylim()
        else:
            # Обновляем только цвета узлов
            if G is not None and ax is not None:
                node_colors = ['green' if tech_flags[node] else 'yellow' if is_tech_available(node) else 'red' for node
                               in G.nodes]
                ax.clear()
                nx.draw(
                    G,
                    pos,
                    with_labels=True,
                    node_size=2500,
                    node_color=node_colors,
                    font_size=10,
                    arrows=True,
                    arrowstyle='->,head_width=0.6,head_length=0.8',
                    ax=ax
                )
                ax.set_xlim(current_xlim)
                ax.set_ylim(current_ylim)
                canvas.draw_idle()

    elif current_state == 2:
        if not preserve_view:
            # Очистка правой области
            for widget in right_frame.winfo_children():
                widget.destroy()

            # Создание графа
            G = nx.DiGraph()
            # Добавляем все технологии и их связи
            for tech in data['технологии']:
                G.add_node(tech['название'])
                for parent in tech['условия']:
                    G.add_edge(parent, tech['название'])

            pos = nx.spring_layout(G, seed=42)

            # Визуализация
            fig, ax = plt.subplots(figsize=(15, 15))
            node_colors = ['green' if tech_flags[node] else 'yellow' if is_tech_available(node) else 'red' for node in
                           G.nodes]

            nx.draw(
                G,
                pos,
                with_labels=True,
                node_size=2500,
                node_color=node_colors,
                font_size=10,
                arrows=True,
                arrowstyle='->,head_width=0.6,head_length=0.8',
                ax=ax
            )

            # Встраивание и настройка событий
            canvas = FigureCanvasTkAgg(fig, master=right_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            # Подключение обработчиков
            fig.canvas.mpl_connect('scroll_event', on_scroll)
            fig.canvas.mpl_connect('button_press_event', on_press)
            fig.canvas.mpl_connect('motion_notify_event', on_motion)
            fig.canvas.mpl_connect('button_release_event', on_release)
            fig.canvas.mpl_connect('button_press_event', lambda e: on_right_click(e) if e.button == 3 else None)

            # Сохраняем текущие границы
            current_xlim = ax.get_xlim()
            current_ylim = ax.get_ylim()
        else:
            # Обновляем только цвета узлов
            if G is not None and ax is not None:
                node_colors = ['green' if tech_flags[node] else 'yellow' if is_tech_available(node) else 'red' for node
                               in G.nodes]
                ax.clear()
                nx.draw(
                    G,
                    pos,
                    with_labels=True,
                    node_size=2500,
                    node_color=node_colors,
                    font_size=10,
                    arrows=True,
                    arrowstyle='->,head_width=0.6,head_length=0.8',
                    ax=ax
                )
                ax.set_xlim(current_xlim)
                ax.set_ylim(current_ylim)
                canvas.draw_idle()


# Обработка правой кнопки мыши
def on_right_click(event):
    global zoom_factor, pos
    if event.inaxes:
        x, y = event.xdata, event.ydata
        for node, (nx, ny) in pos.items():
            if (nx - 0.2 <= x <= nx + 0.2) and (ny - 0.2 <= y <= ny + 0.2):
                tech_flags[node] = not tech_flags[node]
                update_visualization(selected_tech.get(), preserve_view=True)
                update_listbox_colors()
                break


tech_listbox = tk.Listbox(left_bottom_frame, font=('Arial', 12))
tech_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Вертикальный ползунок
v_scrollbar = ttk.Scrollbar(tech_listbox, orient=tk.VERTICAL, command=tech_listbox.yview)
v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tech_listbox.configure(yscrollcommand=v_scrollbar.set)

# Горизонтальный ползунок
h_scrollbar = ttk.Scrollbar(tech_listbox, orient=tk.HORIZONTAL, command=tech_listbox.xview)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
tech_listbox.configure(xscrollcommand=h_scrollbar.set)

update_listbox_colors()


# Обработка выбора в списке
def on_select(event):
    global is_selecting
    if not is_selecting:
        selected_index = tech_listbox.curselection()
        if selected_index:
            tech_name = tech_listbox.get(selected_index)
            update_description(tech_name)


tech_listbox.bind('<<ListboxSelect>>', on_select)


# Функция для загрузки нового древа
def load_tech_tree():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                global data, dct_tech, tech_flags
                data = json.load(file)
                dct_tech = {}
                for tech in data['технологии']:
                    dct_tech[tech['название']] = tech

                # Сброс прогресса для нового древа
                tech_flags = {tech['название']: False for tech in data['технологии']}

                update_listbox_colors()
                if data['технологии']:
                    update_description(data['технологии'][0]['название'])
                else:
                    # Очистка описания если древо пустое
                    for widget in left_top_frame.winfo_children():
                        widget.destroy()
                    desc_text1 = scrolledtext.ScrolledText(
                        left_top_frame,
                        wrap=tk.WORD,
                        font=('Arial', 20),
                        bg='white',
                        width=60,
                        height=10
                    )
                    desc_text1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                    desc_text1.insert(tk.END, "Древо технологий пусто")

                messagebox.showinfo("Успех", "Древо технологий успешно загружено!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить древо: {str(e)}")


# Функция для сохранения прогресса
def save_progress():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        initialfile=f"{data.get('название_древа', 'древо')}.progress.json"
    )
    if file_path:
        progress_data = {
            "dree_name": data.get('название_древа', 'древо'),
            "progress": tech_flags
        }
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(progress_data, file, ensure_ascii=False, indent=4)


# Функция для загрузки прогресса
def load_progress():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                progress_data = json.load(file)

            # Проверка соответствия древа
            if progress_data.get("dree_name") != data.get('название_древа', 'древо'):
                messagebox.showerror("Ошибка", "Файл прогресса не соответствует текущему древу технологий!")
                return

            global tech_flags
            tech_flags.update(progress_data.get("progress", {}))
            update_visualization(selected_tech.get())
            update_listbox_colors()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить прогресс: {str(e)}")


def set_view(state):
    global current_state
    current_state = state
    update_visualization(selected_tech.get())


# Функция для открытия редактора древа
def open_editor():
    root.withdraw()  # Скрыть основное окно
    editor = EditorWindow(root)
    editor.window.protocol("WM_DELETE_WINDOW", lambda: on_editor_close(editor))


def on_editor_close(editor):
    editor.window.destroy()
    root.deiconify()  # Показать основное окно
    # Обновить данные после редактирования
    global data, dct_tech
    data = editor.data
    dct_tech = editor.dct_tech
    tech_flags.update({tech['название']: False for tech in data['технологии'] if tech['название'] not in tech_flags})
    update_listbox_colors()
    if selected_tech.get():
        update_visualization(selected_tech.get())


# Кнопки "Сохранить" и "Загрузить прогресс"
button_frame = tk.Frame(left_bottom_frame, bg='lightgray')
button_frame.pack(side=tk.BOTTOM, fill=tk.X)

load_tree_button = tk.Button(button_frame, text="Загрузить древо", command=load_tech_tree)
load_tree_button.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

save_button = tk.Button(button_frame, text="Сохр. прогресс", command=save_progress)
save_button.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

load_button = tk.Button(button_frame, text="Загр. прогресс", command=load_progress)
load_button.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

details_button = tk.Button(button_frame, text="Подробности", command=open_mhtml)
details_button.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

view_button1 = tk.Button(button_frame, text='Вид1', command=lambda: set_view(0))
view_button1.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

view_button2 = tk.Button(button_frame, text='Вид2', command=lambda: set_view(1))
view_button2.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

view_button3 = tk.Button(button_frame, text='Вид3', command=lambda: set_view(2))
view_button3.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

edit_button = tk.Button(button_frame, text="Открыть редактор", command=open_editor)
edit_button.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)


# Класс для окна редактора
class EditorWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Редактор технологического древа")
        self.window.geometry("1200x800")

        # Основные фреймы
        self.top_frame = tk.Frame(self.window)
        self.top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.bottom_frame = tk.Frame(self.window)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(self.window)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Верхний фрейм - визуализация с ползунками
        self.viz_label = tk.Label(self.top_frame, text="Визуализация древа (PlantUML)")
        self.viz_label.pack(side=tk.TOP, fill=tk.X)

        # Фрейм для canvas и ползунков
        self.viz_container = tk.Frame(self.top_frame)
        self.viz_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Горизонтальный ползунок
        self.h_scrollbar = ttk.Scrollbar(self.viz_container, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Вертикальный ползунок
        self.v_scrollbar = ttk.Scrollbar(self.viz_container, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas для изображения
        self.viz_canvas = tk.Canvas(
            self.viz_container,
            bg='white',
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set
        )
        self.viz_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Настройка ползунков
        self.h_scrollbar.config(command=self.viz_canvas.xview)
        self.v_scrollbar.config(command=self.viz_canvas.yview)

        # Привязка событий мыши для прокрутки
        self.viz_canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows/Mac
        self.viz_canvas.bind("<Button-4>", self._on_mousewheel)  # Linux
        self.viz_canvas.bind("<Button-5>", self._on_mousewheel)  # Linux

        # Нижний фрейм - список технологий
        self.tech_list_frame = tk.Frame(self.bottom_frame)
        self.tech_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tech_list_label = tk.Label(self.tech_list_frame, text="Список технологий")
        self.tech_list_label.pack(side=tk.TOP, fill=tk.X)

        self.tech_listbox = tk.Listbox(self.tech_list_frame, font=('Arial', 10))
        self.tech_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tech_scrollbar = ttk.Scrollbar(self.tech_list_frame, orient=tk.VERTICAL, command=self.tech_listbox.yview)
        self.tech_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tech_listbox.configure(yscrollcommand=self.tech_scrollbar.set)

        # Фрейм редактирования
        self.edit_frame = tk.Frame(self.bottom_frame)
        self.edit_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Поля редактирования
        self.name_label = tk.Label(self.edit_frame, text="Название:")
        self.name_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        self.name_entry = tk.Entry(self.edit_frame)
        self.name_entry.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        self.name_entry.bind('<KeyRelease>', self.on_data_change)

        self.desc_label = tk.Label(self.edit_frame, text="Описание:")
        self.desc_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        self.desc_text = scrolledtext.ScrolledText(self.edit_frame, height=5)
        self.desc_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=2)
        # self.desc_text.bind('<KeyRelease>', self.on_data_change)

        self.conditions_label = tk.Label(self.edit_frame, text="Условия (родители):")
        self.conditions_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        self.conditions_listbox = tk.Listbox(self.edit_frame, height=5)
        self.conditions_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Кнопки управления условиями
        self.conditions_button_frame = tk.Frame(self.edit_frame)
        self.conditions_button_frame.pack(side=tk.TOP, fill=tk.X)

        self.add_condition_button = tk.Button(self.conditions_button_frame, text="Добавить условие",
                                              command=self.add_condition)
        self.add_condition_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)

        self.remove_condition_button = tk.Button(self.conditions_button_frame, text="Удалить условие",
                                                 command=self.remove_condition)
        self.remove_condition_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)

        # Кнопки управления
        self.new_tech_button = tk.Button(self.button_frame, text="Новый узел", command=self.new_technology)
        self.new_tech_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.delete_tech_button = tk.Button(self.button_frame, text="Удалить узел", command=self.delete_technology)
        self.delete_tech_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.save_json_button = tk.Button(self.button_frame, text="Сохранить JSON", command=self.save_json)
        self.save_json_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.load_json_button = tk.Button(self.button_frame, text="Загрузить JSON", command=self.load_json)
        self.load_json_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.sort_alpha_button = tk.Button(self.button_frame, text="Сортировка по алфавиту",
                                           command=self.sort_alphabetical)
        self.sort_alpha_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.sort_graph_button = tk.Button(self.button_frame, text="Сортировка по графу", command=self.sort_graph)
        self.sort_graph_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.save_image_button = tk.Button(self.button_frame, text="Сохранить картинку", command=self.save_image)
        self.save_image_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        # Загрузка данных
        self.load_data()
        self.update_tech_list()
        self.current_tech = None
        self.original_image = None

        # Привязка событий
        self.tech_listbox.bind('<<ListboxSelect>>', self.on_tech_select)

    def _on_mousewheel(self, event):
        """Обработка прокрутки колесиком мыши"""
        if event.delta:
            self.viz_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.viz_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.viz_canvas.yview_scroll(1, "units")

    def load_data(self):
        global data, dct_tech
        self.data = data
        self.dct_tech = dct_tech.copy()

    def update_tech_list(self):
        self.tech_listbox.delete(0, tk.END)
        for tech in self.data['технологии']:
            self.tech_listbox.insert(tk.END, tech['название'])

    def generate_plantuml(self, center_tech):
        # Находим всех родителей и детей
        parents = find_all_parents(center_tech)
        children = find_all_children(center_tech)

        # Собираем все узлы
        all_nodes = set([center_tech])
        all_nodes.update(parents.keys())
        all_nodes.update(children.keys())

        # Генерируем код PlantUML
        plantuml_code = "@startuml\n"
        plantuml_code += "scale 0.8\n"
        plantuml_code += "skinparam ranksep 50\n" # ranksep 50-150 - расстояние между уровнями
        plantuml_code += "skinparam nodesep 20\n" # nodesep 20-60 - расстояние между узлами в одном уровне
        # plantuml_code += "skinparam monochrome true\n"
        plantuml_code += "skinparam shadowing false\n"
        plantuml_code += "left to right direction\n"

        # Добавляем узлы с цветом для выбранной технологии
        for node in all_nodes:
            if node == center_tech:
                # Выделяем центральную технологию желтым цветом
                plantuml_code += f'rectangle "<b>{node}</b>" as {node.replace(" ", "_").replace("-", "_")} #yellow\n'
            else:
                plantuml_code += f'rectangle "{node}" as {node.replace(" ", "_").replace("-", "_")}\n'

        # Добавляем связи
        for node in all_nodes:
            if node in self.dct_tech:
                for parent in self.dct_tech[node]['условия']:
                    if parent in all_nodes:
                        plantuml_code += f'{parent.replace(" ", "_").replace("-", "_")} --> {node.replace(" ", "_").replace("-", "_")}\n'

        plantuml_code += "@enduml"

        print(f'PlantUML code:\n{plantuml_code}')

        return plantuml_code

    def encode_plantuml(self, text):
        """Правильное кодирование PlantUML текста для URL"""
        # Сжимаем текст
        compressed = zlib.compress(text.encode('utf-8'))
        # Кодируем в base64
        encoded = base64.b64encode(compressed).decode('ascii')
        # Заменяем символы для URL
        encoded = encoded.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',
                                                  '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'))
        # Добавляем префикс для DEFLATE сжатия
        encoded = '~1' + encoded
        # print(encoded)
        return encoded

    def svg_to_png(self, svg_data):
        """Конвертирует SVG данные в PNG используя PIL и встроенные возможности"""
        # Пытаемся использовать cairosvg если доступен
        try:
            import cairosvg
            png_data = cairosvg.svg2png(bytestring=svg_data)
            return png_data
        except (ImportError, OSError) as e:
            # Cairosvg недоступен или Cairo библиотека не установлена
            # Это нормальная ситуация, особенно на Windows
            pass
        except Exception:
            # Другие ошибки cairosvg - пробуем fallback
            pass

        # Пытаемся использовать PIL (работает только для простых SVG)
        try:
            from PIL import Image
            img = Image.open(BytesIO(svg_data))
            png_buffer = BytesIO()
            img.save(png_buffer, format='PNG')
            return png_buffer.getvalue()
        except Exception:
            # PIL не может обработать SVG - используем PNG fallback
            raise Exception("SVG конвертация недоступна")

    def render_plantuml(self, plantuml_code):
        try:
            # Пробуем сначала локальный PlantUML, затем онлайн SVG, затем онлайн PNG
            image_data = None

            # Попытка использовать локальный PlantUML JAR файл
            plantuml_jar = os.path.join(BASE_DIR, 'plantuml.jar')
            if os.path.exists(plantuml_jar):
                try:
                    # Создаем временный файл для PlantUML кода
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False, encoding='utf-8') as f:
                        f.write(plantuml_code)
                        temp_puml = f.name

                    # Генерируем SVG с помощью локального PlantUML (SVG не имеет ограничений по ширине)
                    temp_svg = temp_puml.replace('.puml', '.svg')
                    result = subprocess.run(
                        ['java', '-jar', plantuml_jar, '-tsvg', temp_puml],
                        capture_output=True,
                        timeout=30
                    )

                    if result.returncode == 0 and os.path.exists(temp_svg):
                        with open(temp_svg, 'rb') as f:
                            svg_data = f.read()
                        os.unlink(temp_svg)

                        # Конвертируем SVG в PNG для отображения в Tkinter
                        try:
                            image_data = self.svg_to_png(svg_data)
                            print("Используется локальный PlantUML SVG (офлайн режим, без ограничений по ширине)")
                        except Exception as e:
                            print(f"SVG конвертация не удалась: {e}")
                            # Если конвертация не удалась, пробуем сгенерировать PNG напрямую как fallback
                            temp_png = temp_puml.replace('.puml', '.png')
                            result = subprocess.run(
                                ['java', '-jar', plantuml_jar, '-tpng', temp_puml],
                                capture_output=True,
                                timeout=30
                            )
                            if result.returncode == 0 and os.path.exists(temp_png):
                                with open(temp_png, 'rb') as f:
                                    image_data = f.read()
                                os.unlink(temp_png)
                                print("Используется локальный PlantUML PNG (офлайн режим, может быть обрезан для широких диаграмм)")

                    os.unlink(temp_puml)
                except Exception as e:
                    print(f"Локальный PlantUML не удался: {e}")

            # Если локальный PlantUML не сработал, используем онлайн SVG
            if image_data is None:
                encoded = self.encode_plantuml(plantuml_code)

                # Используем SVG формат вместо PNG для избежания ограничений по ширине
                url = f"https://www.plantuml.com/plantuml/svg/{encoded}"
                print(f"PlantUML SVG URL: {url}")

                try:
                    with urllib.request.urlopen(url, timeout=30) as response:
                        svg_data = response.read()

                    # Конвертируем SVG в PNG используя PIL
                    # SVG не имеет ограничений по ширине
                    try:
                        image_data = self.svg_to_png(svg_data)
                        print("Используется онлайн PlantUML SVG (без ограничений по ширине)")
                    except Exception as svg_error:
                        # SVG конвертация не удалась - используем PNG fallback
                        # Не печатаем подробности ошибки, чтобы не пугать пользователя
                        print("Примечание: SVG конвертация недоступна, используется PNG формат")
                        url = f"https://www.plantuml.com/plantuml/png/{encoded}"
                        with urllib.request.urlopen(url, timeout=30) as response:
                            image_data = response.read()
                        print("Используется онлайн PlantUML PNG (может быть обрезан для очень широких диаграмм)")
                except Exception as e:
                    print(f"Онлайн PlantUML не удался: {e}")
                    # Последний fallback - пробуем прямой PNG
                    url = f"https://www.plantuml.com/plantuml/png/{encoded}"
                    print(f"PlantUML PNG URL: {url}")
                    with urllib.request.urlopen(url, timeout=30) as response:
                        image_data = response.read()
                    print("Используется онлайн PlantUML PNG (может быть обрезан для широких диаграмм)")

            # Сохраняем оригинальное изображение
            self.original_image = Image.open(BytesIO(image_data))

            # Отображаем изображение в полном размере
            self.photo = ImageTk.PhotoImage(self.original_image)
            self.viz_canvas.delete("all")

            # Устанавливаем размеры canvas под изображение
            self.viz_canvas.config(
                scrollregion=(0, 0, self.original_image.width, self.original_image.height),
                width=min(800, self.original_image.width),
                height=min(600, self.original_image.height)
            )

            # Создаем изображение на canvas
            self.image_id = self.viz_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            print(f"Изображение отрендерено: {self.original_image.width}x{self.original_image.height} пикселей")

        except Exception as e:
            # Если онлайн-рендеринг не удался, показываем код
            self.viz_canvas.delete("all")
            self.viz_canvas.config(scrollregion=(0, 0, 800, 600))
            self.viz_canvas.create_text(400, 300,
                                        text=f"PlantUML rendering failed:\n{str(e)}\n\nPlantUML Code:\n{plantuml_code}",
                                        font=('Arial', 10), justify=tk.LEFT)

    def update_viz(self, center_tech=None):
        if not center_tech and self.tech_listbox.curselection():
            center_tech = self.tech_listbox.get(self.tech_listbox.curselection()[0])

        if not center_tech:
            return

        plantuml_code = self.generate_plantuml(center_tech)
        self.render_plantuml(plantuml_code)

    def on_tech_select(self, event):
        if self.tech_listbox.curselection():
            tech_name = self.tech_listbox.get(self.tech_listbox.curselection()[0])
            self.load_tech_data(tech_name)
            self.update_viz(tech_name)

    def load_tech_data(self, tech_name):
        self.current_tech = tech_name
        tech_data = self.dct_tech.get(tech_name, {})

        # Отключаем события чтобы не вызывать on_data_change
        self.name_entry.unbind('<KeyRelease>')
        self.desc_text.unbind('<KeyRelease>')

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, tech_name)

        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(1.0, tech_data.get('описание', ''))

        self.conditions_listbox.delete(0, tk.END)
        for condition in tech_data.get('условия', []):
            self.conditions_listbox.insert(tk.END, condition)

        # Включаем события обратно
        self.name_entry.bind('<KeyRelease>', self.on_data_change)
        self.desc_text.bind('<KeyRelease>', self.on_data_change)

    def on_data_change(self, event=None):
        if self.current_tech:
            self.save_current_tech()
            self.update_viz(self.current_tech)

    def save_current_tech(self):
        if not self.current_tech:
            return

        new_name = self.name_entry.get().strip()
        description = self.desc_text.get(1.0, tk.END).strip()
        conditions = list(self.conditions_listbox.get(0, tk.END))

        # Обновляем данные
        if self.current_tech in self.dct_tech:
            tech_data = self.dct_tech[self.current_tech]

            # Если имя изменилось, обновляем его везде
            if new_name != self.current_tech:
                # Обновляем в словаре
                self.dct_tech[new_name] = self.dct_tech.pop(self.current_tech)

                # Обновляем в основном списке
                for tech in self.data['технологии']:
                    if tech['название'] == self.current_tech:
                        tech['название'] = new_name
                    # Обновляем условия в других технологиях
                    tech['условия'] = [new_name if cond == self.current_tech else cond for cond in tech['условия']]

                self.current_tech = new_name
                self.update_tech_list()

            # Обновляем остальные поля
            tech_data['название'] = new_name
            tech_data['описание'] = description
            tech_data['условия'] = conditions

    def add_condition(self):
        condition = simpledialog.askstring("Добавить условие", "Введите название технологии-условия:")
        if condition:
            self.conditions_listbox.insert(tk.END, condition)
            self.on_data_change()

    def remove_condition(self):
        if self.conditions_listbox.curselection():
            self.conditions_listbox.delete(self.conditions_listbox.curselection()[0])
            self.on_data_change()

    def new_technology(self):
        name = simpledialog.askstring("Новая технология", "Введите название технологии:")
        if name:
            name = name.strip()
            # Проверка на дубликаты
            for i, tech in enumerate(self.data['технологии']):
                if tech['название'] == name:
                    self.tech_listbox.selection_clear(0, tk.END)
                    self.tech_listbox.selection_set(i)
                    self.tech_listbox.see(i)
                    messagebox.showinfo("Информация", "Технология с таким названием уже существует!")
                    return

            # Добавление новой технологии
            new_tech = {
                'название': name,
                'описание': '',
                'условия': []
            }
            self.data['технологии'].append(new_tech)
            self.dct_tech[name] = new_tech
            self.update_tech_list()

    def delete_technology(self):
        if self.current_tech:
            # Удаляем из условий других технологий
            for tech in self.data['технологии']:
                tech['условия'] = [cond for cond in tech['условия'] if cond != self.current_tech]

            # Удаляем саму технологию
            self.data['технологии'] = [tech for tech in self.data['технологии'] if
                                       tech['название'] != self.current_tech]
            if self.current_tech in self.dct_tech:
                del self.dct_tech[self.current_tech]

            self.current_tech = None
            self.update_tech_list()
            self.update_viz()

            # Очищаем поля редактирования
            self.name_entry.delete(0, tk.END)
            self.desc_text.delete(1.0, tk.END)
            self.conditions_listbox.delete(0, tk.END)

    def save_json(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.data, file, ensure_ascii=False, indent=2)

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.data = json.load(file)
                self.dct_tech = {}
                for tech in self.data['технологии']:
                    self.dct_tech[tech['название']] = tech

                self.update_tech_list()
                self.current_tech = None
                self.name_entry.delete(0, tk.END)
                self.desc_text.delete(1.0, tk.END)
                self.conditions_listbox.delete(0, tk.END)

    def sort_alphabetical(self):
        self.data['технологии'].sort(key=lambda x: x['название'])
        self.update_tech_list()

    def sort_graph(self):
        # Сортировка по наличию родителей и потомков
        tech_with_parents = []
        tech_without_parents = []

        for tech in self.data['технологии']:
            if tech['условия']:
                tech_with_parents.append(tech)
            else:
                tech_without_parents.append(tech)

        # Технологии без родителей в начале
        self.data['технологии'] = tech_without_parents + tech_with_parents
        self.update_tech_list()

    def save_image(self):
        if hasattr(self, 'original_image'):
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            if file_path:
                self.original_image.save(file_path)
        else:
            messagebox.showwarning("Предупреждение", "Нет изображения для сохранения")


# Обработка закрытия окна
def on_closing():
    root.quit()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

# Запуск основного цикла
root.mainloop()