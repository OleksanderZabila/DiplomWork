import psycopg2
import tkinter as tk
from tkinter import ttk, Entry, Button, Listbox, messagebox, Toplevel, Label, Text
from config import host, user, password, db_name, port
from datetime import datetime

open_window = None
#test
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

def open_unique_window(title, create_window_func):
    """Функція, яка дозволяє відкрити лише одне вікно"""
    global open_window

    if open_window and open_window.winfo_exists():
        open_window.lift()
        return

    open_window = create_window_func()
    open_window.title(title)
    open_window.protocol("WM_DELETE_WINDOW", lambda: close_window())

def close_window():
    """Закриває відкрите вікно і скидає змінну"""
    global open_window
    if open_window:
        open_window.destroy()
        open_window = None

# Функції отримання даних
def fetch_categories():
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name_category FROM category")
            return [row[0] for row in cursor.fetchall()]
    return []

def fetch_units():
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT unit FROM unit")
            return [row[0] for row in cursor.fetchall()]
    return []

def fetch_providers():
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name_provider FROM provider")
            return [row[0] for row in cursor.fetchall()]
    return []


# Функція додавання товару
def add_product():

    def add_provider_of_product():
        {}
    def submit():
        name = name_entry.get()
        category = category_combobox.get()
        quantity = quantity_entry.get()
        unit = unit_combobox.get()
        selling_price = selling_price_entry.get()
        purchase_price = purchase_price_entry.get()
        provider = provider_combobox.get()
        description = description_entry.get("1.0", "end-1c")  # Виправлена помилка


        if not all([name, category, quantity, unit, selling_price, purchase_price, provider]):
            messagebox.showerror("Помилка", "Усі поля обов'язкові для заповнення!")
            return

        try:
            quantity = int(quantity)
            selling_price = float(selling_price)
            purchase_price = float(purchase_price)
        except ValueError:
            messagebox.showerror("Помилка", "Некоректні числові значення!")
            return

        if connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO goods (name_goods, id_category_goods, number_goods, units_goods, 
                                       selling_price_goods, purchase_price_goods, id_provider_goods, description_goods)
                    VALUES (
                        %s, (SELECT id_category FROM category WHERE name_category = %s),
                        %s, (SELECT unit FROM unit WHERE unit = %s),
                        %s, %s, (SELECT id_provider FROM provider WHERE name_provider = %s), %s)
                """, (name, category, quantity, unit, selling_price, purchase_price, provider, description))
                messagebox.showinfo("Успіх", "Товар додано успішно!")
                add_window.destroy()
                update_table()

    add_window = tk.Toplevel(program)
    add_window.title("Додати товар")
    add_window.geometry("720x200")  # Оптимальний розмір вікна

    def add_provider_button():
        provider_window = tk.Toplevel(add_window)
        provider_window.title("Додати постачальника")
        provider_window.geometry("600x270")

        labels = ["Назва", "Телефон", "Email", "Менеджер", "Юр. адреса", "Правова форма", "IBAN"]
        entries = {}

        for i, label in enumerate(labels):
            tk.Label(provider_window, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = tk.Entry(provider_window, width=30)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[label] = entry

        def add_provider():
            if connection:
                with connection.cursor() as cursor:
                    # Додаємо нового постачальника
                    cursor.execute("""
                        INSERT INTO provider (name_provider, telephone_provider, mail_provider, menedger_provider, 
                                               legaladdress_provider, legalfrom_provider, iban_provider) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (entries["Назва"].get(), entries["Телефон"].get(), entries["Email"].get(),
                          entries["Менеджер"].get(), entries["Юр. адреса"].get(),
                          entries["Правова форма"].get(), entries["IBAN"].get()))

                update_table()

            load_providers()  # Оновлюємо таблицю

        def load_providers():
            """Очищає таблицю та завантажує імена постачальникі."""
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT name_provider FROM provider")
                    providers = cursor.fetchall()

            provider_table.delete(*provider_table.get_children())  # Очищення таблиці

            for provider in providers:
                provider_table.insert("", "end", values=provider)  # Додаємо постачальників у таблицю

        # Кнопка для додавання постачальника
        tk.Button(provider_window, text="Додати", command=add_provider).grid(row=7, column=0, columnspan=2, pady=10)

        # Таблиця постачальників
        provider_table = ttk.Treeview(provider_window, columns=("name",), show="headings", height=8)
        provider_table.heading("name", text="Постачальники")
        provider_table.grid(row=0, column=2, rowspan=8, padx=10, pady=5)

        load_providers()  # Завантажуємо дані при запуску

    frame = tk.Frame(add_window, padx=10, pady=10)
    frame.pack(fill="both", expand=True)
    # Верхній ряд
    tk.Label(frame, text="Назва товару:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    name_entry = Entry(frame, width=20)
    name_entry.grid(row=0, column=1, padx=5, pady=2)

    tk.Label(frame, text="Категорія:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
    category_combobox = ttk.Combobox(frame, values=fetch_categories(), width=20)
    category_combobox.grid(row=0, column=3, padx=5, pady=2)
    category_combobox.bind("<KeyRelease>", lambda event: filter_combobox(category_combobox, fetch_categories()))

    tk.Label(frame, text="Кількість:").grid(row=0, column=4, sticky="w", padx=5, pady=2)
    quantity_entry = Entry(frame, width=10)
    quantity_entry.grid(row=0, column=5, padx=5, pady=2)

    # Середній ряд
    tk.Label(frame, text="Одиниця вимірювання:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    unit_combobox = ttk.Combobox(frame, values=fetch_units(), state="readonly", width=12)
    unit_combobox.grid(row=1, column=1, padx=5, pady=2)

    tk.Label(frame, text="Ціна продажу:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
    selling_price_entry = Entry(frame, width=10)
    selling_price_entry.grid(row=1, column=3, padx=5, pady=2)

    tk.Label(frame, text="Ціна закупівлі:").grid(row=1, column=4, sticky="w", padx=5, pady=2)
    purchase_price_entry = Entry(frame, width=10)
    purchase_price_entry.grid(row=1, column=5, padx=5, pady=2)

    # Нижній ряд (Постачальник + Опис)
    tk.Label(frame, text="Постачальник:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    provider_combobox = ttk.Combobox(frame, values=fetch_providers(), width=25)
    provider_combobox.grid(row=2, column=1, columnspan=2, padx=5, pady=2)
    provider_combobox.bind("<KeyRelease>", lambda event: filter_combobox(provider_combobox, fetch_providers()))

    provider_button = Button(frame, text="Додати Постачальника", command=add_provider_button, width=20)
    provider_button.grid(row=2, column=3, padx=5, pady=2)

    tk.Label(frame, text="Опис товару:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
    description_entry = tk.Text(frame, width=65, height=3)  # Збільшено поле опису
    description_entry.grid(row=3, column=1, columnspan=5, padx=5, pady=2)

    # Кнопки
    button_frame = tk.Frame(frame)
    button_frame.grid(row=4, column=0, columnspan=6, pady=10)

    submit_button = Button(button_frame, text="Додати", command=submit, width=12)
    submit_button.pack(side="left", padx=5)

    cancel_button = Button(button_frame, text="Скасувати", command=add_window.destroy, width=12)
    cancel_button.pack(side="left", padx=5)

def add_settings():
    add_window_settings = tk.Toplevel(program)
    add_window_settings.title("Нaлаштування")
    add_window_settings.geometry("900x500")

    notebook = ttk.Notebook(add_window_settings)

    tab1 = ttk.Frame(notebook)  # Категорії
    tab2 = ttk.Frame(notebook)  # Клієнти
    tab3 = ttk.Frame(notebook)  # Постачальники
    tab4 = ttk.Frame(notebook)  # Одиниці

    # Додавання вкладок до `Notebook`
    notebook.add(tab1, text="Категорії")
    notebook.add(tab2, text="Клієнти")
    notebook.add(tab3, text="Постачальники")
    notebook.add(tab4, text="Одиниці")

    notebook.pack(expand=True, fill="both")  # Робимо `Notebook` розтягнутим

    # Функції для отримання даних
    def fetch_categories():
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_category, name_category FROM category")
            return cursor.fetchall()

    def fetch_clients():
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_client, name_client, telephone_client, mail_client, 
                       legaladdress_client, legalforms_client, iban_client FROM client
            """)
            return cursor.fetchall()

    def fetch_providers():
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_provider, name_provider, telephone_provider, mail_provider, menedger_provider, legaladdress_provider, legalfrom_provider, iban_provider
                FROM provider
            """)
            return cursor.fetchall()

    def fetch_units():
        with connection.cursor() as cursor:
            cursor.execute("SELECT unit FROM unit")
            return cursor.fetchall()


    # Функція створення таблиці
    def create_table(tab, columns, column_widths, fetch_function, add_function):
        frame = ttk.Frame(tab)
        frame.pack(expand=True, fill="both")

        tree = ttk.Treeview(frame, columns=columns, show="headings")

        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            tree.column(col, width=column_widths[i], anchor="w")

        tree.pack(expand=True, fill="both", side="top")

        def update_table():
            for row in tree.get_children():
                tree.delete(row)
            for row in fetch_function():
                tree.insert("", "end", values=row)

        update_table()  # Заповнюємо таблицю при створенні

        # Додаємо кнопку "Додати"
        add_button = tk.Button(frame, text="Додати", command=lambda: add_function(update_table))
        add_button.pack(pady=5)

        return tree

    # Функція для додавання нових записів
    def add_entry(title, fields, insert_query, update_func):
        add_window = tk.Toplevel(add_window_settings)
        add_window.title(title)
        add_window.geometry("400x300")

        entries = {}

        for i, field in enumerate(fields):
            tk.Label(add_window, text=field).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = tk.Entry(add_window, width=30)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[field] = entry

        def save_entry():
            values = [entry.get() for entry in entries.values()]
            if not all(values):
                messagebox.showerror("Помилка", "Усі поля повинні бути заповнені!")
                return

            with connection.cursor() as cursor:
                cursor.execute(insert_query, values)
                connection.commit()

            messagebox.showinfo("Успіх", "Дані додано!")
            add_window.destroy()
            update_func()  # Оновлення таблиці

        tk.Button(add_window, text="Зберегти", command=save_entry).grid(row=len(fields), column=0, columnspan=2, pady=10)

    # Створюємо таблиці у вкладках
    create_table(
        tab1,
        ("ID", "Назва Категорії"),
        [20, 800],
        fetch_categories,
        lambda update: add_entry("Додати категорію", ["Назва Категорії"],
                                 "INSERT INTO category (name_category) VALUES (%s)", update)
    )

    create_table(
        tab2,
        ("ID", "Назва", "Телефон", "Email", "Юр. адреса", "Правова форма", "IBAN"),
        [10, 100, 100, 100, 100, 100, 100],  # Ширини стовпців
        fetch_clients,
        lambda update: add_entry("Додати клієнта", ["Назва", "Телефон", "Email", "Юр. адреса", "Правова форма", "IBAN"],
                                 "INSERT INTO client (id_client, name_client, telephone_client, mail_client, legaladdress_client, legalforms_client, iban_client) VALUES (%s, %s, %s, %s, %s, %s)",
                                 update)
    )

    create_table(
        tab3,
        ("ID", "Назва", "Телефон", "Email", "Менеджер", "Юр. адреса", "Правова форма", "IBAN"),
        [10, 100, 100, 100, 100, 100, 100, 100],  # Ширини стовпців
        fetch_providers,
        lambda update: add_entry("Додати постачальника",
                                 ["Назва", "Телефон", "Email", "Менеджер", "Юр. адреса", "Правова форма", "IBAN"],
                                 "INSERT INTO provider (name_provider, telephone_provider, mail_provider, menedger_provider, legaladdress_provider, legalfrom_provider, iban_provider) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                 update)

    )

    create_table(
        tab4,
        ("Одиниця вимірювання",),
        [200],  # Ширина одного стовпця
        fetch_units,
        lambda update: add_entry("Додати одиницю вимірювання", ["Одиниця вимірювання"],
                                 "INSERT INTO unit (unit) VALUES (%s)", update)
    )


#звіт
def report():
    {}
#списаний товар
def written_off():
    """Відкриває вікно зі списаними товарами"""
    def load_written_off_goods():
        """Завантажує дані про списані товари"""
        table.delete(*table.get_children())  # Очищаємо таблицю перед оновленням

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT g.id_goods, g.name_goods, c.name_category, w.number_written_off_goods, u.unit, 
                       g.selling_price_goods, g.purchase_price_goods, p.name_provider, 
                       g.description_goods, w.data, w.description
                FROM written_off_goods w
                JOIN goods g ON w.id_goods = g.id_goods
                JOIN category c ON g.id_category_goods = c.id_category
                JOIN provider p ON g.id_provider_goods = p.id_provider
                JOIN unit u ON g.units_goods = u.unit
                
            """)
            for row in cursor.fetchall():
                table.insert("", "end", values=row)

    off_window = Toplevel()
    off_window.title("Списані товари")
    off_window.geometry("1200x500")
    off_window.resizable(width=False, height=False)

    # Верхнє меню
    upper_frame_delet = tk.Frame(off_window)
    upper_frame_delet.pack(fill='x', padx=10, pady=5)

    delet_this = Button(upper_frame_delet, text="Видалити обране", command=2)
    delet_this.pack(side='right', padx=5)

    put_oll = Button(upper_frame_delet, text="Вибрати все", command=3)
    put_oll.pack(side='right', padx=5)

    dosent_put_oll = Button(upper_frame_delet, text="Відмінити все", command=4)
    dosent_put_oll.pack(side='right', padx=5)



    # Головний контейнер

    columns = ("ID", "Назва товару", "Категорія", "Кількість", "Одиниці",
               "Ціна продажу", "Ціна закупівлі", "Постачальник", "Опис товару", "Дата списання", "Опис списання")

    # 🔹 Визначаємо ширину для кожного стовпця
    column_widths = {
        "ID": 30,
        "Назва товару": 150,
        "Категорія": 100,
        "Кількість": 80,
        "Одиниці": 60,
        "Ціна продажу": 90,
        "Ціна закупівлі": 100,
        "Постачальник": 100,
        "Опис товару": 180,
        "Дата списання": 120,
        "Опис списання": 180
    }

    table = ttk.Treeview(off_window, columns=columns, show="headings", height=15)

    for col in columns:
        table.heading(col, text=col)
        table.column(col, anchor="center", width=column_widths.get(col, 100))  # Використовуємо ширину зі словника

    table.pack(fill="both", expand=True)

    load_written_off_goods()  # Завантажуємо списані товари при відкритті


# Функція для фільтрації категорій і постачальників
def filter_combobox(combobox, data_source):
    search_text = combobox.get().lower()
    filtered_data = [item for item in data_source if search_text in item.lower()]
    combobox["values"] = filtered_data
    combobox.event_generate("<Down>")  # Автоматично відкриває список
def edit_product(product_id):
    def update_product():
        if not messagebox.askyesno("Підтвердження", "Ви впевнені, що хочете зберегти зміни?"):
            return

        new_name = name_entry.get()
        new_category = category_combobox.get()
        new_quantity = quantity_entry.get()
        new_unit = unit_combobox.get()
        new_selling_price = selling_price_entry.get()
        new_purchase_price = purchase_price_entry.get()
        new_provider = provider_combobox.get()
        new_description = description_entry.get("1.0", "end-1c")

        try:
            new_quantity = int(new_quantity)
            new_selling_price = float(new_selling_price)
            new_purchase_price = float(new_purchase_price)
        except ValueError:
            messagebox.showerror("Помилка", "Некоректні числові значення!")
            return

        if connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE goods 
                    SET name_goods=%s, id_category_goods=(SELECT id_category FROM category WHERE name_category=%s),
                        number_goods=%s, units_goods=(SELECT unit FROM unit WHERE unit=%s),
                        selling_price_goods=%s, purchase_price_goods=%s,
                        id_provider_goods=(SELECT id_provider FROM provider WHERE name_provider=%s),
                        description_goods=%s
                    WHERE id_goods=%s
                """, (new_name, new_category, new_quantity, new_unit, new_selling_price,
                      new_purchase_price, new_provider, new_description, product_id))
                connection.commit()
                messagebox.showinfo("Успіх", "Зміни успішно збережені!")
                edit_window.destroy()
                update_table()

    # Отримання поточних даних товару
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name_goods, (SELECT name_category FROM category WHERE id_category=id_category_goods), 
                   number_goods, (SELECT unit FROM unit WHERE unit=units_goods),
                   selling_price_goods, purchase_price_goods, 
                   (SELECT name_provider FROM provider WHERE id_provider=id_provider_goods),
                   description_goods
            FROM goods WHERE id_goods=%s
        """, (product_id,))
        product_data = cursor.fetchone()

    if not product_data:
        messagebox.showerror("Помилка", "Не вдалося отримати дані товару!")
        return

    edit_window = tk.Toplevel(program)
    edit_window.title("Редагувати товар")
    edit_window.geometry("600x300")

    frame = tk.Frame(edit_window, padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    # Поля для редагування (вже заповнені)
    tk.Label(frame, text="Назва товару:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    name_entry = Entry(frame, width=20)
    name_entry.insert(0, product_data[0])
    name_entry.grid(row=0, column=1, padx=5, pady=2)

    tk.Label(frame, text="Категорія:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
    category_combobox = ttk.Combobox(frame, values=fetch_categories(), width=20)
    category_combobox.set(product_data[1])
    category_combobox.grid(row=0, column=3, padx=5, pady=2)
    category_combobox.bind("<KeyRelease>", lambda event: filter_combobox(category_combobox, fetch_categories()))

    tk.Label(frame, text="Кількість:").grid(row=0, column=4, sticky="w", padx=5, pady=2)
    quantity_entry = Entry(frame, width=10)
    quantity_entry.insert(0, product_data[2])
    quantity_entry.grid(row=0, column=5, padx=5, pady=2)

    tk.Label(frame, text="Одиниця вимірювання:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    unit_combobox = ttk.Combobox(frame, values=fetch_units(), state="readonly", width=12)
    unit_combobox.set(product_data[3])
    unit_combobox.grid(row=1, column=1, padx=5, pady=2)

    tk.Label(frame, text="Ціна продажу:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
    selling_price_entry = Entry(frame, width=10)
    selling_price_entry.insert(0, product_data[4])
    selling_price_entry.grid(row=1, column=3, padx=5, pady=2)

    tk.Label(frame, text="Ціна закупівлі:").grid(row=1, column=4, sticky="w", padx=5, pady=2)
    purchase_price_entry = Entry(frame, width=10)
    purchase_price_entry.insert(0, product_data[5])
    purchase_price_entry.grid(row=1, column=5, padx=5, pady=2)

    tk.Label(frame, text="Постачальник:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    provider_combobox = ttk.Combobox(frame, values=fetch_providers(), width=25)
    provider_combobox.set(product_data[6])
    provider_combobox.grid(row=2, column=1, columnspan=2, padx=5, pady=2)
    provider_combobox.bind("<KeyRelease>", lambda event: filter_combobox(provider_combobox, fetch_providers()))

    tk.Label(frame, text="Опис товару:").grid(row=3, column=0, sticky="nw", padx=5, pady=2)
    description_entry = tk.Text(frame, width=65, height=3)
    description_entry.insert("1.0", product_data[7])
    description_entry.grid(row=3, column=1, columnspan=5, padx=5, pady=2)

    # Кнопки
    button_frame = tk.Frame(frame)
    button_frame.grid(row=4, column=0, columnspan=6, pady=10)

    save_button = Button(button_frame, text="Зберегти", command=update_product, width=12)
    save_button.pack(side="left", padx=5)

    cancel_button = Button(button_frame, text="Скасувати", command=edit_window.destroy, width=12)
    cancel_button.pack(side="left", padx=5)

def update_time():
    """Оновлює час у віджеті Label кожну секунду."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=current_time)
    program.after(1000, update_time)  # Запускає оновлення кожну секунду
# Оновлення головної таблиці (додаємо поле "Опис товару" і кнопку редагування)
def update_table(category=None):
    for item in table.get_children():
        table.delete(item)

    with connection.cursor() as cursor:
        cursor.execute("SELECT id_goods, name_goods, id_category_goods, number_goods, units_goods, selling_price_goods, purchase_price_goods, id_provider_goods, description_goods FROM goods")
        for row in cursor.fetchall():
            table.insert("", "end", values=row)


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
search_label.pack(side='left', padx=5)

search_entry = Entry(upper_frame, width=40)
search_entry.insert(0, "Введіть назву товару")
search_entry.pack(side='left', padx=5)

add_product_button = Button(upper_frame, text="Додати товар", command=add_product)
add_product_button.pack(side='right', padx=5)

settings_button = Button(upper_frame, text="Налаштування", command=add_settings)
settings_button.pack(side='right', padx=5)

settings_button = Button(upper_frame, text="Звіт", command=report)
settings_button.pack(side='right', padx=5)

settings_button = Button(upper_frame, text="Списане", command=written_off)
settings_button.pack(side='right', padx=5)


# Головний контейнер
main_frame = tk.Frame(program)
main_frame.pack(fill='both', expand=True)

# Ліва панель (Пошук категорій)
left_frame = tk.Frame(main_frame, width=300, bg="#f0f0f0")
left_frame.pack(side='left', fill='y')

filter_label = tk.Label(left_frame, text="Пошук за категорією:", bg="#f0f0f0")
filter_label.pack(pady=10, padx=10, anchor='w')


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

# Таблиця
right_frame = tk.Frame(main_frame)
right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=5)

columns = ("ID", "Назва товару", "Категорія", "Кількість", "Одиниці",
           "Ціна продажу", "Ціна закупівлі", "Постачальник", "Опис товару", "Дії")

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
    "Дії": 50
}

table = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)

for col in columns:
    table.heading(col, text=col)
    table.column(col, anchor="center", width=column_widths.get(col, 100))  # Використовуємо значення зі словника

table.pack(fill="both", expand=True)

def update_table(category=None, name_filter=None):
    table.delete(*table.get_children())  # Очищуємо таблицю перед оновленням

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

            cursor.execute(query, params)

            for row in cursor.fetchall():
                table.insert("", "end", values=row + ("✏️  🗑️",))  # Додаємо іконки у колонку "Дії"


#Функція карандаша, смітника
def on_item_click(event):
    item_id = table.identify_row(event.y)  # Отримуємо рядок
    column_id = table.identify_column(event.x)  # Отримуємо колонку

    if not item_id:
        return

    values = table.item(item_id, "values")  # Отримуємо значення рядка
    if not values or len(values) < 10:  # Перевіряємо, чи є дані
        return

    product_id = values[0]  # ID товару
    action = values[-1]  # Остання колонка містить "✏️  🗑️"

    if column_id == "#10":  # Колонка "Дії"
        x_pos = event.x - table.bbox(item_id, column=9)[0]  # Визначаємо позицію кліку в колонці "Дії"

        if x_pos < 25:  # Якщо клік ближче до лівого краю - "✏️"
            edit_goods(product_id)
        else:  # Якщо клік ближче до правого краю - "🗑️"
            delete_goods(product_id)

def edit_goods(product_id):
    """Відкриває вікно редагування товару з уже заповненими полями"""
    def create_edit_window():
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT g.name_goods, c.name_category, g.number_goods, u.unit, 
                       g.selling_price_goods, g.purchase_price_goods, p.name_provider, g.description_goods
                FROM goods g
                JOIN category c ON g.id_category_goods = c.id_category
                JOIN provider p ON g.id_provider_goods = p.id_provider
                JOIN unit u ON g.units_goods = u.unit
                WHERE g.id_goods = %s
            """, (product_id,))
            product_data = cursor.fetchone()

        if not product_data:
            messagebox.showerror("Помилка", "Не вдалося завантажити дані товару!")
            return None

        window = Toplevel()
        window.title("Редагувати товар")

        # Поля введення
        Label(window, text="Назва товару:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        name_entry = Entry(window, width=20)
        name_entry.insert(0, product_data[0])
        name_entry.grid(row=0, column=1, padx=5, pady=2)

        Label(window, text="Категорія:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        category_combobox = ttk.Combobox(window, values=fetch_categories(), width=20)
        category_combobox.set(product_data[1])
        category_combobox.grid(row=0, column=3, padx=5, pady=2)

        Label(window, text="Кількість:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        quantity_entry = Entry(window, width=10)
        quantity_entry.insert(0, product_data[2])
        quantity_entry.grid(row=1, column=1, padx=5, pady=2)

        Label(window, text="Одиниця вимірювання:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        unit_combobox = ttk.Combobox(window, values=fetch_units(), width=12)
        unit_combobox.set(product_data[3])
        unit_combobox.grid(row=1, column=3, padx=5, pady=2)

        Label(window, text="Ціна продажу:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        selling_price_entry = Entry(window, width=10)
        selling_price_entry.insert(0, product_data[4])
        selling_price_entry.grid(row=2, column=1, padx=5, pady=2)

        Label(window, text="Ціна закупівлі:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        purchase_price_entry = Entry(window, width=10)
        purchase_price_entry.insert(0, product_data[5])
        purchase_price_entry.grid(row=2, column=3, padx=5, pady=2)

        Label(window, text="Постачальник:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        provider_combobox = ttk.Combobox(window, values=fetch_providers(), width=25)
        provider_combobox.set(product_data[6])
        provider_combobox.grid(row=3, column=1, columnspan=2, padx=5, pady=2)

        Label(window, text="Опис товару:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        description_entry = Text(window, width=65, height=3)
        description_entry.insert("1.0", product_data[7])
        description_entry.grid(row=4, column=1, columnspan=3, padx=5, pady=2)

        # Функція оновлення товару
        def update_product():
            if not messagebox.askyesno("Підтвердження", "Ви впевнені, що хочете зберегти зміни?"):
                return

            new_data = (
                name_entry.get(), category_combobox.get(), quantity_entry.get(),
                unit_combobox.get(), selling_price_entry.get(), purchase_price_entry.get(),
                provider_combobox.get(), description_entry.get("1.0", "end-1c"), product_id
            )

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE goods 
                    SET name_goods=%s, id_category_goods=(SELECT id_category FROM category WHERE name_category=%s),
                        number_goods=%s, units_goods=(SELECT unit FROM unit WHERE unit=%s),
                        selling_price_goods=%s, purchase_price_goods=%s,
                        id_provider_goods=(SELECT id_provider FROM provider WHERE name_provider=%s),
                        description_goods=%s
                    WHERE id_goods=%s
                """, new_data)
                connection.commit()
                messagebox.showinfo("Успіх", "Зміни успішно збережені!")
                close_window()
                update_table()

        # Кнопки
        Button(window, text="Зберегти", command=update_product, width=12).grid(row=5, column=0, columnspan=2, pady=10)
        Button(window, text="Скасувати", command=close_window, width=12).grid(row=5, column=2, columnspan=2, pady=10)

        return window

    open_unique_window("Редагувати товар", create_edit_window)


def delete_goods(product_id):
    def confirm_deletion():
        try:
            amount_to_write_off = int(amount_entry.get().strip())
            if amount_to_write_off <= 0:
                messagebox.showerror("Помилка", "Кількість списання має бути більше 0!")
                return
        except ValueError:
            messagebox.showerror("Помилка", "Введіть коректну кількість!")
            return

        reason = reason_entry.get("1.0", "end-1c").strip()
        if not reason:
            messagebox.showerror("Помилка", "Вкажіть причину списання!")
            return

        with connection.cursor() as cursor:
            # Отримуємо поточну кількість товару
            cursor.execute("SELECT number_goods FROM goods WHERE id_goods=%s", (product_id,))
            result = cursor.fetchone()
            if not result:
                messagebox.showerror("Помилка", "Товар не знайдено!")
                return

            current_amount = result[0]
            if amount_to_write_off > current_amount:
                messagebox.showerror("Помилка", "На складі недостатньо товару для списання!")
                return

            # Оновлюємо кількість товару в таблиці goods
            cursor.execute("""
                UPDATE goods SET number_goods = number_goods - %s WHERE id_goods = %s
            """, (amount_to_write_off, product_id))

            # Перевіряємо, чи товар вже є у written_off_goods
            cursor.execute("SELECT id_goods FROM written_off_goods WHERE id_goods = %s", (product_id,))
            existing = cursor.fetchone()

            if existing:
                # Оновлюємо запис, якщо товар вже списувався раніше
                cursor.execute("""
                    UPDATE written_off_goods 
                    SET number_written_off_goods = number_written_off_goods + %s, 
                        data = CURRENT_DATE, 
                        description = %s 
                    WHERE id_goods = %s
                """, (amount_to_write_off, reason, product_id))
            else:
                # Додаємо новий запис, якщо товар ще не був списаний
                cursor.execute("""
                    INSERT INTO written_off_goods (id_goods, data, description, number_written_off_goods)
                    VALUES (%s, CURRENT_DATE, %s, %s)
                """, (product_id, reason, amount_to_write_off))

            connection.commit()
            messagebox.showinfo("Успіх", "Товар списано!")
            close_window()
            update_table()

    # Створюємо вікно введення даних
    delete_window = Toplevel()
    delete_window.title("Списання товару")
    delete_window.geometry("300x200")

    Label(delete_window, text="Кількість для списання:").pack()
    amount_entry = Entry(delete_window)
    amount_entry.pack()

    Label(delete_window, text="Причина списання:").pack()
    reason_entry = Text(delete_window, height=3, width=30)
    reason_entry.pack()

    Button(delete_window, text="Підтвердити", command=confirm_deletion).pack()

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

# Додаємо поведінку до існуючого search_entry
search_entry.bind("<FocusIn>", on_search_entry_focus_in)
search_entry.bind("<FocusOut>", on_search_entry_focus_out)
search_entry.bind("<KeyRelease>", on_search_entry_change)  # Залишаємо вашу функцію пошуку

update_time()
table.bind("<Button-1>", on_item_click)
update_table()
program.mainloop()


if connection:
    connection.close()
    print("[INFO] Підключення закрито")
