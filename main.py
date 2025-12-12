# Основной импорт
import MySQLdb

# Подлючаем все необходимые ui компоненты
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.clipboard import Clipboard
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.properties import StringProperty
from datetime import datetime

# Настраиваем подключения к базе данных MySQL
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'general_history'


# Функция для подключения к базе данных MySQL
def get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8'
    )

# Функция для загрузки рассказов по тегу
def fetch_stories_by_tag(tag):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Выполняем запрос для поиска рассказов по тегу с использованием LIKE
    cursor.execute("SELECT id, tag, story_text FROM stories_db WHERE tag LIKE %s", ('%' + tag + '%',))
    stories = cursor.fetchall()
    conn.close()
    return stories

# Функция для сохранения рассказа в таблицу истории
def save_story_to_history(tag, story_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Вставляем новую запись в таблицу истории с текущим временем
    cursor.execute(
        "INSERT INTO history (tag, story_text, created_at) VALUES (%s, %s, NOW())",
        (tag, story_text)
    )
    conn.commit()
    conn.close()

# Функция для получения всей истории рассказов, сортируем по времени (от новых к старым)
def fetch_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tag, story_text, created_at FROM history ORDER BY created_at DESC")
    records = cursor.fetchall()
    conn.close()
    return records

# Функция для очистки всей истории из базы данных
def clear_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Удаляем все записи из таблицы истории
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()


# Основной класс интерфейса, который показывает все элементы
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # =======================
        # HEADER: Название и описание
        # =======================
        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        header.add_widget(Label(
            text='Генератор рассказов',
            font_size='24sp',
            bold=True,
            halign='center'
        ))
        header.add_widget(Label(
            text='Создавайте и сохраняйте рассказы по тегам',
            font_size='14sp',
            halign='center'
        ))
        self.add_widget(header)

        # =======================
        # Основной контент
        # =======================
        main_content = BoxLayout(orientation='vertical', padding=15, spacing=15)

        # Ввод для тега — по нему ищем или создаем рассказ
        self.tag_input = TextInput(
            hint_text='Введите тег',          # Подсказка для пользователя
            size_hint_y=None,
            height=dp(40),
            multiline=False,                  # Одна строка
            background_normal='',
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            padding_x=10
        )
        main_content.add_widget(self.tag_input)

        # Кнопка для генерации или получения рассказа по тегу
        self.btn_generate_story = Button(
            text='Генерировать рассказ',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.6, 0.86, 1),
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        # Связываем кнопку с методом обработки нажатия
        self.btn_generate_story.bind(on_press=self.generate_or_fetch_story)
        main_content.add_widget(self.btn_generate_story)

        # Поле для отображения текста рассказа
        self.story_display = TextInput(
            readonly=True,                  # Только для чтения
            font_size='16sp',
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            size_hint_y=0.6
        )
        main_content.add_widget(self.story_display)

        # =======================
        # Нижняя панель с кнопками
        # =======================
        button_bar = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)

        # Кнопка "Сохранить рассказ"
        self.btn_save = Button(
            text='Сохранить рассказ',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.btn_save.bind(on_press=self.save_current_story)
        button_bar.add_widget(self.btn_save)

        # Кнопка "Копировать текст"
        self.btn_copy = Button(
            text='Копировать текст',
            background_color=(0.9, 0.9, 0.2, 1)
        )
        self.btn_copy.bind(on_press=self.copy_story_text)
        button_bar.add_widget(self.btn_copy)

        # Кнопка "Посмотреть историю рассказов"
        self.btn_view_history = Button(
            text='Посмотреть историю',
            background_color=(0.86, 0.2, 0.2, 1)
        )
        self.btn_view_history.bind(on_press=self.show_history_popup)
        button_bar.add_widget(self.btn_view_history)

        main_content.add_widget(button_bar)

        # Добавляем основной контент на главный слой
        self.add_widget(main_content)

        # =======================
        # FOOTER: советы о формулировке тега
        # =======================
        footer = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        footer.add_widget(Label(
            text='Совет: Используйте короткие и емкие теги.',
            font_size='12sp',
            halign='center'
        ))
        footer.add_widget(Label(
            text='Правильное формулирование тега помогает быстрее находить нужные рассказы.',
            font_size='12sp',
            halign='center'
        ))
        self.add_widget(footer)

    # =======================
    # Обработка нажатия "Генерировать рассказ"
    # =======================
    def generate_or_fetch_story(self, instance):
        tag = self.tag_input.text.strip()
        if not tag:
            # Если тег пустой, выводим сообщение
            self.story_display.text = 'Пожалуйста, введите тег для поиска или создания рассказа.'
            return

        # Получаем рассказы по тегу
        stories = fetch_stories_by_tag(tag)
        if stories:
            # Если есть истории, показываем первую
            story = stories[0]
            self.story_display.text = story[2]
            self.current_story_id = story[0]
        else:
            # Если рассказа нет, создаем новый и вставляем в базу
            new_text = f'Это новый рассказ по тегу "{tag}".'
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO stories_db (tag, story_text) VALUES (%s, %s)", (tag, new_text))
            conn.commit()
            self.current_story_id = cursor.lastrowid
            conn.close()
            self.story_display.text = new_text

    # =======================
    # Сохранение текущего рассказа в историю
    # =======================
    def save_current_story(self, instance):
        tag = self.tag_input.text.strip()
        story_text = self.story_display.text
        if tag and story_text:
            save_story_to_history(tag, story_text)

    # =======================
    # Копирование текста рассказа в буфер обмена
    # =======================
    def copy_story_text(self, instance):
        if self.story_display.text:
            Clipboard.copy(self.story_display.text)

    # =======================
    # Открытие окна с историей рассказов
    # =======================
    def show_history_popup(self, instance):
        records = fetch_history()
        print(f"Найдено записей в истории: {len(records)}")
        container = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        container.bind(minimum_height=container.setter('height'))

        # Таблица с 3 колонками: Время, Тег, Текст
        table = GridLayout(cols=3, size_hint_y=None, row_default_height=dp(40), spacing=5)
        table.bind(minimum_height=table.setter('height'))

        # Заголовки колонок
        headers = ['Время', 'Тег', 'Текст']
        for header in headers:
            lbl = Label(text=header, bold=True)
            table.add_widget(lbl)

        # Заполняем таблицу записями из истории
        for record in records:
            record_id, tag, text, created_at = record
            # Форматируем время
            if isinstance(created_at, datetime):
                created_str = created_at.strftime('%Y-%m-%d %H:%M')
            else:
                created_str = str(created_at)

            lbl_time = Label(text=created_str)
            lbl_tag = Label(text=tag)

            # Кнопка с сокращенным текстом рассказа
            btn_text = Button(
                text=text[:50] + ('...' if len(text) > 50 else ''),
                halign='left',
                size_hint_y=None,
                height=dp(40)
            )

            # Обработка текста при нажатии
            btn_text.bind(on_press=lambda btn, full_text=text, tag=tag: self.show_full_story(full_text, tag))

            # Добавляем в таблицу
            table.add_widget(lbl_time)
            table.add_widget(lbl_tag)
            table.add_widget(btn_text)

        container.add_widget(table)

        # Кнопка для очистки истории
        btn_clear_history = Button(
            text='Очистить историю',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_clear_history.bind(on_press=self.clear_history)
        container.add_widget(btn_clear_history)

        # Оборачиваем в ScrollView
        scroll_view = ScrollView(size_hint=(1, 0.7))
        scroll_view.add_widget(container)

        # Создаем всплывающее окно
        self.history_popup = Popup(
            title='История рассказов',
            content=scroll_view,
            size_hint=(0.9, 0.8)
        )
        self.history_popup.open()

    # =======================
    # Показ полного текста рассказа
    # =======================
    def show_full_story(self, full_text, tag):
        # Создаем Label с переносом строк и выравниванием по центру
        label = Label(
            text=full_text,
            text_size=(400, None),
            halign='center',  # Горизонтальное выравнивание
            valign='middle',  # Вертикальное (учитывайте, что valign работает при height)
            size_hint=(1, None),
            height=dp(300)  # Можно менять по необходимости
        )
        label.bind(size=label.setter('text_size'))  # Для переносов при изменении размера

        # Создаем popup для полного текста
        popup = Popup(
            title=f'Рассказывай: {tag}',
            content=label,
            size_hint=(0.8, 0.8)
        )
        popup.open()

    # =======================
    # Очистка истории
    # =======================
    def clear_history(self, instance):
        # Удаляем все записи из базы
        clear_history()
        # Обновляем окно истории, закрываем popup, если открыт
        if hasattr(self, 'history_popup'):
            self.history_popup.dismiss()
        self.show_history_popup(None)


# Основное приложение
class StoryApp(App):
    def build(self):
        self.title = "Генератор рассказов"
        return MainLayout()


# Запуск приложения
if __name__ == '__main__':
    import kivy
    kivy.require('2.0.0')
    StoryApp().run()

# Логика моей программы такова:
# Пользователь пишет определенный тег по которому хочет генерировать рассказ
# Нажимает на кнопку генерировать запрос отправляется к бд и выбирает тег по которому возвращает рассказ
# После нажатия на кнопку сохранить результат сохраняется в табл. stories и можно посмотреть
# время дату тег по которому был создан рассказ и сам рассказ
# После нажатие на кнопку очистить историю удаляются данные с истории и также с табл.