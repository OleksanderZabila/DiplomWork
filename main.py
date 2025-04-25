import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess

def open_admin():
    password = simpledialog.askstring("Пароль адміністратора", "Введіть пароль:", show='*')
    if password == "admin":
        subprocess.Popen(["python", "Program.py"])
        root.after(100, root.destroy)  # Закрити після запуску
    else:
        messagebox.showerror("Помилка", "Невірний пароль!")

def open_sales():
    subprocess.Popen(["python", "Sales.py"])
    root.after(100, root.destroy)  # Закрити після запуску


root = tk.Tk()
root.title("Вибір ролі")
root.geometry("300x150")

tk.Label(root, text="Виберіть роль", font=("Arial", 14)).pack(pady=20)

btn_admin = tk.Button(root, text="Адміністратор", font=("Arial", 12), command=open_admin)
btn_admin.pack(pady=5, fill="x", padx=20)

btn_sales = tk.Button(root, text="Продавець", font=("Arial", 12), command=open_sales)
btn_sales.pack(pady=5, fill="x", padx=20)

root.mainloop()