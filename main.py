import tkinter as tk
from tkinter import messagebox
import psycopg2
import subprocess
from config import host, user, password, db_name, port

# Підключення до бази
try:
    connection = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name
    )
except Exception as e:
    print("[ERROR] Підключення до БД:", e)
    connection = None

def login():
    name = entry_user.get().strip()
    pwd = entry_pass.get().strip()

    if not name or not pwd:
        messagebox.showwarning("Увага", "Уведіть ім'я та пароль!")
        return

    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT id_user, name_user, password_user, status_user FROM "users" WHERE name_user = %s',
            (name,))
        user_data = cursor.fetchone()

    if not user_data or user_data[2] != pwd:
        messagebox.showerror("Помилка", "Невірне ім'я або пароль!")
        return

    user_id, username, _, role = user_data

    # Запуск відповідної програми з параметрами
    if role == 1:
        subprocess.Popen(["python", "Program.py", str(user_id), username])
    else:
        subprocess.Popen(["python", "Sales.py", str(user_id), username])
    root.destroy()

# Вікно входу
root = tk.Tk()
root.title("Вхід у систему")
root.geometry("300x200")

tk.Label(root, text="Ім'я користувача").pack(pady=5)
entry_user = tk.Entry(root)
entry_user.pack(pady=5)

tk.Label(root, text="Пароль").pack(pady=5)
entry_pass = tk.Entry(root, show='*')
entry_pass.pack(pady=5)

tk.Button(root, text="Увійти", command=login).pack(pady=10)

root.mainloop()
