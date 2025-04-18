import psycopg2
import tkinter as tk
from tkinter import ttk, Entry, Toplevel, Label, Entry, Frame, Button, Listbox, messagebox
from tkinter.ttk import Combobox
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

current_check_id = 1

def get_next_check_id():
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(id_check), 0) FROM sale")
            max_id = cursor.fetchone()[0]
            return max_id + 1
    return 1

# І встановлюємо глобальний лічильник
current_check_id = get_next_check_id()

def get_client_id_by_name(name):
    if not name or name == "Гість":
        return None
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_client FROM client WHERE name_client = %s", (name,))
            result = cursor.fetchone()
            if result:
                return result[0]
    return None

def get_clients():
    clients = []
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name_client FROM client")
            result = cursor.fetchall()
            clients = [row[0] for row in result]
    return clients

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

id_label = Label(upper_frame, text="Фільтр за ID:")
id_label.pack(side=tk.LEFT)

id_entry = Entry(upper_frame)
id_entry.pack(side=tk.LEFT)

def search_by_id(event=None):
    search_id = id_entry.get()
    table.delete(*table.get_children())
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM goods WHERE CAST(id_goods AS TEXT) LIKE %s", ('%' + search_id + '%',))
            for row in cursor.fetchall():
                table.insert("", tk.END, values=row + ("➕",))

def insert_digit_to_payment(value):
    current = payment_entry.get()
    payment_entry.delete(0, tk.END)
    payment_entry.insert(0, current + value)
    calculate_change()


def open_clients_window():
    win = Toplevel(program)
    win.title("Клієнти")
    win.geometry("900x400")

    tree = ttk.Treeview(win, columns=("ID", "Ім'я", "Телефон", "Пошта", "Юр.адреса", "Правова форма", "IBAN"),
                        show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Встановлення ширини стовпців
    column_widths = {
        "ID": 10,
        "Ім'я": 130,
        "Телефон": 120,
        "Пошта": 150,
        "Юр.адреса": 200,
        "Правова форма": 120,
        "IBAN": 150
    }

    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100))

    def refresh_clients():
        tree.delete(*tree.get_children())
        if connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id_client, name_client, telephone_client, mail_client, legaladdress_client, legalforms_client, iban_client FROM client")
                for row in cursor.fetchall():
                    tree.insert("", tk.END, values=row)

    def add_client():
        add_win = Toplevel(win)
        add_win.title("Додати нового клієнта")
        add_win.geometry("400x250")

        # Фрейм для полів вводу
        input_frame = Frame(add_win)
        input_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Поля вводу
        fields = [
            ("Ім'я:", "name"),
            ("Телефон:", "phone"),
            ("Пошта:", "mail"),
            ("Юридична адреса:", "legaladdress"),
            ("Правова форма:", "legalforms"),
            ("IBAN:", "iban")
        ]

        entries = {}
        for text, field in fields:
            frame = Frame(input_frame)
            frame.pack(fill=tk.X, pady=5)

            label = Label(frame, text=text, width=15, anchor='w')
            label.pack(side=tk.LEFT)

            entry = Entry(frame)
            entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
            entries[field] = entry

        # Фрейм для кнопок
        button_frame = Frame(add_win)
        button_frame.pack(pady=10)

        def save_client():
            # Отримуємо дані з полів вводу
            data = {
                'name': entries['name'].get().strip(),
                'phone': entries['phone'].get().strip(),
                'mail': entries['mail'].get().strip(),
                'legaladdress': entries['legaladdress'].get().strip(),
                'legalforms': entries['legalforms'].get().strip(),
                'iban': entries['iban'].get().strip()
            }

            # Валідація даних
            if not data['name']:
                messagebox.showwarning("Увага", "Ім'я клієнта обов'язкове!")
                return

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO client 
                        (name_client, telephone_client, mail_client, legaladdress_client, legalforms_client, iban_client)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (data['name'], data['phone'], data['mail'],
                          data['legaladdress'], data['legalforms'], data['iban']))

                    # Зберігаємо зміни в базі даних
                    connection.commit()

                    messagebox.showinfo("Успіх", "Клієнта успішно додано!")
                    add_win.destroy()
                    refresh_clients()
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося додати клієнта: {str(e)}")

        # Кнопка "Додати клієнта"
        add_button = Button(button_frame, text="Додати клієнта", command=save_client,
                            bg='#4CAF50', fg='white', width=15)
        add_button.pack(side=tk.LEFT, padx=5)

        # Кнопка "Скасувати"
        cancel_button = Button(button_frame, text="Скасувати", command=add_win.destroy,
                               bg='#f44336', fg='white', width=15)
        cancel_button.pack(side=tk.RIGHT, padx=5)

    # Кнопка "Додати клієнта" у головному вікні
    add_button_main = Button(win, text="Додати клієнта", command=add_client,
                             bg='#4CAF50', fg='white', width=15)
    add_button_main.pack(pady=10)

    refresh_clients()

# кнопка праворуч
clients_button = Button(upper_frame, text="Клієнти", command=open_clients_window)
clients_button.pack(side='right', padx=10)



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

        if text == "Delete":
            btn.config(command=lambda e=btn: payment_entry.delete(0, tk.END))
        elif text == "Enter":
            btn.config(command=calculate_change)
        else:
            btn.config(command=lambda val=text: insert_digit_to_payment(val))

        btn.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, padx=2, pady=2, sticky="news")


left_bottom_frame = tk.Frame(program, width=210, height=302, bg="white", highlightbackground="gray", highlightthickness=1)
left_bottom_frame.place(relx=0.825, rely=0.985, anchor="se")  # Розташування зліва внизу
left_bottom_frame.pack_propagate(False)



# Додавання кнопки в нижній частині фрейма з відступами
def calculate_change(event=None):
    try:
        received = float(payment_entry.get())
        to_pay = float(total_label_var.get())
        change = received - to_pay
        change_label_var.set(f"{change:.2f}")
    except:
        change_label_var.set("0.00")


def update_total_to_pay():
    total = 0.0
    for item in table_down.get_children():
        values = table_down.item(item, "values")
        try:
            price = float(values[2])   # Ціна
            quantity = int(values[3])  # Кількість
            total += price * quantity
        except (ValueError, IndexError):
            continue
    total_label_var.set(f"{total:.2f}")
    calculate_change()



# 🔧 Фрейм оплати, розтягнутий на все місце
payment_frame = tk.Frame(left_bottom_frame, bg="#f0f0f0")
payment_frame.pack(fill="both", expand=True, padx=5, pady=5)

# 🔢 До сплати
tk.Label(payment_frame, text="До сплати:", font=("Arial", 12)).pack(anchor="w", padx=5, pady=(5, 0))
total_label_var = tk.StringVar(value="0.00")
tk.Label(payment_frame, textvariable=total_label_var, font=("Arial", 16, "bold"), fg="black").pack(anchor="w", padx=5)

# 💵 Отримано
tk.Label(payment_frame, text="Отримано:", font=("Arial", 12)).pack(anchor="w", padx=5, pady=(10, 0))
payment_entry = tk.Entry(payment_frame, font=("Arial", 12), width=10)
payment_entry.pack(fill="x", padx=5, pady=2)
payment_entry.bind("<KeyRelease>", calculate_change)

# 💰 Решта
tk.Label(payment_frame, text="Решта:", font=("Arial", 12)).pack(anchor="w", padx=5, pady=(10, 0))
change_label_var = tk.StringVar(value="0.00")
tk.Label(payment_frame, textvariable=change_label_var, font=("Arial", 16), fg="green").pack(anchor="w", padx=5)

tk.Label(left_bottom_frame, text="Клієнт:").pack()
client_combobox = Combobox(left_bottom_frame, values=get_clients())  # get_clients повертає лише імена
client_combobox.pack()

def process_payment():
    try:
        received = float(payment_entry.get())
        to_pay = float(total_label_var.get())

        if received < to_pay:
            messagebox.showwarning("Недостатньо коштів", "Сума отримана менша за суму до сплати!")
            return

    except ValueError:
        messagebox.showwarning("Помилка", "Некоректна сума в полі 'Отримано'")
        return

    client_name = client_combobox.get()
    client_id = get_client_id_by_name(client_name)

    if connection:
        try:
            with connection.cursor() as cursor:
                # 1. Створити запис у таблиці chek
                cursor.execute("""
                    INSERT INTO chek (data_sell, client, sum)
                    VALUES (CURRENT_TIMESTAMP, %s, %s)
                    RETURNING id_check
                """, (client_id, to_pay))

                new_check_id = cursor.fetchone()[0]

                # 2. Оновити записи у sale з status_check = 1
                cursor.execute("""
                    UPDATE sale SET status_check = 0, id_check = %s
                    WHERE status_check = 1
                """, (new_check_id,))

            messagebox.showinfo("Оплата", "Чек оплачено успішно!")
            update_table_down()
            payment_entry.delete(0, tk.END)
            calculate_change()

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося провести оплату: {e}")


tk.Button(left_bottom_frame, text="Оплатити", font=("Arial", 12), command=process_payment).pack(pady=10)

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


def update_table_down():
    table_down.delete(*table_down.get_children())

    if connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.id_goods, g.name_goods, g.selling_price_goods, s.number_sale
                FROM sale s
                JOIN goods g ON s.id_goods = g.id_goods
                WHERE s.status_check = 1
            """)
            for row in cursor.fetchall():
                table_down.insert("", tk.END, values=(row[0], row[1], row[2], row[3], "➕ ➖ 🗑"))

    # 🟢 ОНОВЛЮЄМО СУМУ ТІЛЬКИ ПІСЛЯ ЗАПОВНЕННЯ
    update_total_to_pay()

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
                INSERT INTO sale (id_goods, number_sale, id_check, status_check)
                VALUES (%s, %s, %s, %s)
                RETURNING id_sale
            """, (id_goods, 1, current_check_id, 1))

            id_sale = cursor.fetchone()[0]

            # Додаємо в нижню таблицю продажу
            table_down.insert("", tk.END, values=(id_goods, name_goods, price, 1, "➕ ➖ 🗑"))

        # Оновлюємо головну таблицю (товарів стало менше)
        update_table()

    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося додати товар у продаж: {e}")
    update_table_down()

def handle_down_action_click(event):
    item_id = table_down.identify_row(event.y)
    column = table_down.identify_column(event.x)

    if not item_id:
        return

    col_index = int(column.replace('#', '')) - 1
    if table_down["columns"][col_index] != "Дія":
        return

    values = table_down.item(item_id, "values")
    id_goods = values[0]
    name_goods = values[1]
    price = values[2]
    number = int(values[3])

    # Визначаємо позицію кліку в осі X (відносно ячейки)
    cell_x, _, cell_w, _ = table_down.bbox(item_id, column)
    click_offset = event.x - cell_x

    try:
        if click_offset < 25:
            # ➕ Додати 1 товар
            with connection.cursor() as cursor:
                cursor.execute("SELECT number_goods FROM goods WHERE id_goods = %s", (id_goods,))
                available = cursor.fetchone()[0]
                if available <= 0:
                    messagebox.showwarning("Недостатньо", "Товару більше нема на складі!")
                    return

                cursor.execute("UPDATE sale SET number_sale = number_sale + 1 WHERE id_goods = %s", (id_goods,))
                cursor.execute("UPDATE goods SET number_goods = number_goods - 1 WHERE id_goods = %s", (id_goods,))
            table_down.set(item_id, "Кількість", number + 1)
            update_table()

        elif click_offset < 50:
            # ➖ Мінус 1 товар
            if number > 1:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE sale SET number_sale = number_sale - 1 WHERE id_goods = %s", (id_goods,))
                    cursor.execute("UPDATE goods SET number_goods = number_goods + 1 WHERE id_goods = %s", (id_goods,))
                table_down.set(item_id, "Кількість", number - 1)
            else:
                messagebox.showinfo("Увага", "Використайте смітник, щоб повністю видалити товар.")
            update_table()

        else:
            # 🗑 Смітник — повертаємо весь товар
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM sale WHERE id_goods = %s", (id_goods,))
                cursor.execute("UPDATE goods SET number_goods = number_goods + %s WHERE id_goods = %s", (number, id_goods))
            table_down.delete(item_id)
            update_table()

    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося виконати дію: {e}")
    update_table_down()

table.pack(fill="both", expand=True)
table.bind("<Button-1>", handle_action_click)  # ← ось цей


down_frame = tk.Frame(main_frame)
down_frame.place(x=210, y=251, relwidth=0.50, height=302)

columns = ("ID", "Назва товару", "Ціна", "Кількість", "Дія")


# Словник зі своїми ширинами для колонок
column_widths = {
    "ID": 30,
    "Назва товару": 150,
    "Ціна ": 100,
    "Кількість": 80,
    "Дія": 10,

}
table_down = ttk.Treeview(down_frame, columns=columns, show="headings", height=15)

for col in columns:
    table_down.heading(col, text=col)
    table_down.column(col, anchor="center", width=column_widths.get(col, 100))  # Використовуємо значення зі словника

table_down.pack(fill="both", expand=True)
table_down.bind("<Button-1>", handle_down_action_click)

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
id_entry.bind("<KeyRelease>", search_by_id)


update_time()
add_buttons_to_frame(right_bottom_frame)
update_table()
update_table_down()
update_total_to_pay()
program.mainloop()



if connection:
    connection.close()
    print("[INFO] Підключення закрито")
