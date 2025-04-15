import psycopg2
import tkinter as tk
from tkinter import ttk, Entry, Button, Listbox, messagebox
from config import host, user, password, db_name, port
from datetime import datetime

# Підключення до бази даних
try:
    connection = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name
    )
    connection.autocommit = True
    print("[INFO] Підключено до бази даних")
except Exception as _ex:
    print("[ERROR] Помилка підключення:", _ex)
    connection = None

def update_table(category=None, name_filter=None, id_filter=None):
    table.delete(*table.get_children())
    if connection:
        with connection.cursor() as cursor:
            query = """
                SELECT g.id_goods, g.name_goods, c.name_category, g.number_goods, u.unit, 
                       g.selling_price_goods, g.purchase_price_goods, p.name_provider, g.description_goods
                FROM goods g
                JOIN category c ON g.id_category_goods = c.id_category
                JOIN provider p ON g.id_provider_goods = p.id_provider
                JOIN unit u ON g.units_goods = u.unit
                WHERE g.number_goods <> 0
            """
            params = []

            if category:
                query += " AND c.name_category = %s"
                params.append(category)

            if name_filter:
                query += " AND g.name_goods ILIKE %s"
                params.append(f"%{name_filter}%")

            if id_filter:
                query += " AND g.id_goods = %s"
                params.append(id_filter)

            cursor.execute(query, params)

            for row in cursor.fetchall():
                row = list(row)
                row.append("➕")  # додаємо значок у колонку "Дія"
                table.insert("", tk.END, values=row)


def update_category_list(event=None):
    """ Оновлює список категорій відповідно до введеного тексту або виводить всі, якщо поле порожнє """
    search_text = category_entry.get().strip().lower()
    category_listbox.delete(0, tk.END)

    if not search_text:  # Якщо поле пошуку порожнє, вивести всі товари
        for cat in categories:
            category_listbox.insert(tk.END, cat)
        update_table()  # Оновлюємо таблицю без фільтру
    else:
        for cat in categories:
            if search_text in cat.lower():
                category_listbox.insert(tk.END, cat)

def select_category(event):
    selected_index = category_listbox.curselection()
    if selected_index:
        selected = category_listbox.get(selected_index[0])
        category_entry.delete(0, tk.END)
        category_entry.insert(0, selected)
        update_table(category=selected)  # Передаємо параметр правильно
    else:
        update_table()  # Відображаємо всі товари

def fetch_categories():
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name_category FROM category")
            return [row[0] for row in cursor.fetchall()]
    return []

def update_time():
    """Оновлює час у віджеті Label кожну секунду."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=current_time)
    program.after(1000, update_time)  # Запускає оновлення кожну секунду
# Оновлення головної таблиці (додаємо поле "Опис товару" і кнопку редагування)



# Головне вікно
program = tk.Tk()
program.title('Авто під ключ')
program.geometry('1300x600')
program.resizable(width=False, height=False)

# Верхнє меню
upper_frame = tk.Frame(program)
upper_frame.pack(fill='x', padx=10, pady=5)

time_label = tk.Label(upper_frame, text="", font=("Arial", 14), bg="lightgray")
time_label.pack(side='left', padx=0)

search_label = tk.Label(upper_frame, text="Фільтр за назвою:")
search_label.pack(side='left', padx=10)

search_entry = Entry(upper_frame, width=40)
search_entry.insert(0, "Введіть назву товару")
search_entry.pack(side='left', padx=5)


# Головний контейнер
main_frame = tk.Frame(program)
main_frame.pack(fill='both', expand=True)

# Ліва панель (Пошук категорій)
left_frame = tk.Frame(main_frame, width=300, bg="#f0f0f0")
left_frame.pack(side='left', fill='y')

filter_label = tk.Label(left_frame, text="Пошук за категорією:", bg="#f0f0f0")
filter_label.pack(pady=10, padx=10, anchor='w')

category_entry = Entry(left_frame, width=30)
category_entry.insert(0, "Введіть категорію")
category_entry.bind("<FocusIn>", lambda event: category_entry.delete(0,
                                                                     tk.END) if category_entry.get() == "Введіть категорію" else None)
category_entry.bind("<FocusOut>",
                    lambda event: category_entry.insert(0, "Введіть категорію") if not category_entry.get() else None)
category_entry.bind("<KeyRelease>", update_category_list)
category_entry.pack(pady=5, padx=10, fill='x')

category_listbox = Listbox(left_frame, height=15)
category_listbox.pack(pady=5, padx=10, fill='both', expand=True)
category_listbox.bind("<<ListboxSelect>>", select_category)

# Завантаження категорій
categories = fetch_categories()
update_category_list(None)

# Таблиця нижня
right_frame = tk.Frame(main_frame)
right_frame.place(x=210, y=0, relwidth=0.83, height=250)

columns = ("ID", "Назва товару", "Категорія", "Кількість", "Одиниці",
           "Ціна продажу", "Ціна закупівлі", "Постачальник", "Опис товару", "Дія")


# Таблиця нижня права

# Створення фрейму в правому нижньому куті для циффр
right_bottom_frame = tk.Frame(program, width=100, height=300, bg="white", highlightbackground="gray", highlightthickness=1)
right_bottom_frame.place(relx=0.99, rely=0.985, anchor="se")
right_bottom_frame.grid_propagate(False)  # Запобігає зміні розміру фрейма


def add_buttons_to_frame(frame):
    # Створюємо внутрішній фрейм для кнопок (займає рівно половину `right_bottom_frame`)
    buttons_frame = tk.Frame(frame, bg="white", width=210, height=300)
    buttons_frame.pack(side="right", fill="both", expand=True)
    buttons_frame.grid_propagate(False)  # Фіксуємо розмір `buttons_frame`

    # Налаштування сітки
    for i in range(5):  # 5 рядків
        buttons_frame.grid_rowconfigure(i, weight=1, minsize=50)
    for i in range(3):  # 3 колонки
        buttons_frame.grid_columnconfigure(i, weight=1, minsize=50)

    # Дані про кнопки: текст, рядок, колонка, rowspan, colspan
    buttons = [
        ("7", 0, 0, 1, 1), ("8", 0, 1, 1, 1), ("9", 0, 2, 1, 1),
        ("4", 1, 0, 1, 1), ("5", 1, 1, 1, 1), ("6", 1, 2, 1, 1),
        ("1", 2, 0, 1, 1), ("2", 2, 1, 1, 1), ("3", 2, 2, 1, 1),
        ("0", 3, 0, 1, 1), (".", 3, 1, 1, 1), ("Enter", 3, 2, 2, 1),  # Enter 2x1 (широкий)
        ("Delete", 4, 0, 1, 2),  # Del 1x2 (високий)
    ]

    # Створення кнопок
    for text, row, col, rowspan, colspan in buttons:
        btn = tk.Button(buttons_frame, text=text, width=8, height=2)
        btn.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, padx=2, pady=2, sticky="news")

left_bottom_frame = tk.Frame(program, width=210, height=302, bg="white", highlightbackground="gray", highlightthickness=1)
left_bottom_frame.place(relx=0.825, rely=0.985, anchor="se")  # Розташування зліва внизу
left_bottom_frame.grid_propagate(False)  # Запобігає зміні розміру фрейма

# Додавання кнопки в нижній частині фрейма з відступами
button = tk.Button(left_bottom_frame, text="Оплата", command=lambda: print("Button clicked"), width=25, height=3)
button.place(relx=0.5, rely=1.0, anchor="s", x=0, y=-10)  # Відступ знизу

# Словник зі своїми ширинами для колонок
column_widths = {
    "ID": 30,
    "Назва товару": 150,
    "Категорія": 120,
    "Кількість": 80,
    "Одиниці": 80,
    "Ціна продажу": 100,
    "Ціна закупівлі": 100,
    "Постачальник": 150,
    "Опис товару": 200,
    "Дія": 20,
}

table = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)

for col in columns:
    table.heading(col, text=col)
    table.column(col, anchor="center", width=column_widths.get(col, 100))  # Використовуємо значення зі словника

def handle_action_click(event):
    item_id = table.identify_row(event.y)
    column = table.identify_column(event.x)

    if not item_id:
        return

    col_index = int(column.replace('#', '')) - 1
    if table["columns"][col_index] != "Дія":
        return

    values = table.item(item_id, "values")
    id_goods = values[0]
    name_goods = values[1]
    price = values[5]
    current_qty = int(values[3])

    if current_qty <= 0:
        messagebox.showwarning("Недостатньо", "Товару більше нема на складі!")
        return

    try:
        with connection.cursor() as cursor:
            # Зменшення кількості товару
            cursor.execute("UPDATE goods SET number_goods = number_goods - 1 WHERE id_goods = %s", (id_goods,))

            # Додавання до таблиці продажу (sale)
            cursor.execute("""
                INSERT INTO sale (id_goods, number_sale, id_check)
                VALUES (%s, %s, %s)
                RETURNING id_sale
            """, (id_goods, 1, 1))  # Поки що id_check = 1 як приклад

            id_sale = cursor.fetchone()[0]

            # Додаємо в нижню таблицю продажу
            table_down.insert("", tk.END, values=(id_goods, name_goods, price, 1))

        # Оновлюємо головну таблицю (товарів стало менше)
        update_table()

    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося додати товар у продаж: {e}")

table.pack(fill="both", expand=True)
table.bind("<Button-1>", handle_action_click)  # ← ось цей


down_frame = tk.Frame(main_frame)
down_frame.place(x=210, y=251, relwidth=0.50, height=302)

columns = ("ID", "Назва товару","Ціна ", "Кількість")

# Словник зі своїми ширинами для колонок
column_widths = {
    "ID": 30,
    "Назва товару": 150,
    "Ціна ": 100,
    "Кількість": 80,
}
table_down = ttk.Treeview(down_frame, columns=columns, show="headings", height=15)

for col in columns:
    table_down.heading(col, text=col)
    table_down.column(col, anchor="center", width=column_widths.get(col, 100))  # Використовуємо значення зі словника

table_down.pack(fill="both", expand=True)
# Обробка +


def on_search_entry_change(event):
    name_filter = search_entry.get().strip()
    update_table(name_filter=name_filter)

search_entry.bind("<KeyRelease>", on_search_entry_change)

# Функція для очищення тексту при фокусі
def on_search_entry_focus_in(event):
    if search_entry.get() == "Введіть назву товару":
        search_entry.delete(0, tk.END)
        search_entry.config(fg="black")  # Робимо текст чорним

# Функція для повернення тексту, якщо поле залишилось порожнім
def on_search_entry_focus_out(event):
    if not search_entry.get():
        search_entry.insert(0, "Введіть назву товару")
        search_entry.config(fg="gray")  # Робимо текст сірим

search_entry.bind("<FocusIn>", on_search_entry_focus_in)
search_entry.bind("<FocusOut>", on_search_entry_focus_out)
search_entry.bind("<KeyRelease>", on_search_entry_change)  # Залишаємо вашу функцію пошуку

update_time()
add_buttons_to_frame(right_bottom_frame)
update_table()
program.mainloop()

if connection:
    connection.close()
    print("[INFO] Підключення закрито")
