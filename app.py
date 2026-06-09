import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

def connect_db():
    """Подключение к твоей базе данных"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",        
            password="1234",     
            database="Черемша"
        )
        return connection
    except Error as e:
        messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к БД:\n{e}")
        return None

class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление складом - Таблица Товары")
        self.root.geometry("900x500")
        
        self.table_name = "Products"
        self.columns = [
            {"name": "id_product", "label": "ID", "pk": True},
            {"name": "name", "label": "Название"},
            {"name": "article", "label": "Артикул"},
            {"name": "unit", "label": "Ед. изм."}
        ]

        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10, fill=tk.X)

        self.entries = {}
        for i, col in enumerate(self.columns):
            if not col.get('pk'):
                label = tk.Label(input_frame, text=f"{col['label']}:")
                label.grid(row=0, column=i*2, padx=5, pady=5, sticky="e")
                
                entry = tk.Entry(input_frame, width=25)
                entry.grid(row=0, column=i*2+1, padx=5, pady=5)
                self.entries[col['name']] = entry

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Добавить", command=self.add_record,
                  bg="#90EE90").grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Обновить", command=self.update_record,
                  bg="#FFD700").grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Удалить", command=self.delete_record,
                  bg="#FF6347").grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Очистить", command=self.clear_entries).grid(row=0, column=3, padx=5)
        tk.Button(button_frame, text="Показать все", command=self.refresh_table).grid(row=0, column=4, padx=5)

        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scroll_y = tk.Scrollbar(tree_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        columns_display = [col['name'] for col in self.columns]
        self.tree = ttk.Treeview(tree_frame, columns=columns_display, show='headings', yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)

        for col in self.columns:
            self.tree.heading(col['name'], text=col['label'])
            self.tree.column(col['name'], width=150, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select) # Событие выбора строки

    def refresh_table(self):
        """Обновляет таблицу данными из базы"""
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM {self.table_name}"
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                values = tuple(row[col['name']] for col in self.columns)
                self.tree.insert("", tk.END, values=values)
        except Error as e:
            messagebox.showerror("Ошибка запроса", str(e))
        finally:
            cursor.close()
            conn.close()

    def on_select(self, event):
        """Заполняет поля ввода значениями из выделенной строки"""
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])['values']
        for i, col in enumerate(self.columns):
            if col['name'] in self.entries:
                self.entries[col['name']].delete(0, tk.END)
                self.entries[col['name']].insert(0, str(values[i]))

    def add_record(self):
        """Добавляет новую запись в базу"""
        data = {k: v.get() for k, v in self.entries.items()}
        if not all(data.values()):
            messagebox.showwarning("Внимание", "Пожалуйста, заполните все поля!")
            return

        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        cols = ', '.join(data.keys())
        vals = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {self.table_name} ({cols}) VALUES ({vals})"
        try:
            cursor.execute(query, list(data.values()))
            conn.commit()
            messagebox.showinfo("Успех", "Запись добавлена!")
            self.clear_entries()
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()

    def update_record(self):
        """Обновляет выбранную запись"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для обновления!")
            return

        pk_value = self.tree.item(selected[0])['values'][0] # ID всегда первый столбец
        new_data = {k: v.get() for k, v in self.entries.items()}

        set_clause = ', '.join([f"{key}=%s" for key in new_data])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id_product=%s"
        params = list(new_data.values()) + [pk_value]

        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            messagebox.showinfo("Успех", "Запись обновлена!")
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()

    def delete_record(self):
        """Удаляет выбранную запись"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для удаления!")
            return
        if not messagebox.askyesno("Подтверждение", "Вы уверены?"):
            return

        pk_value = self.tree.item(selected[0])['values'][0]
        query = f"DELETE FROM {self.table_name} WHERE id_product=%s"

        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute(query, (pk_value,))
            conn.commit()
            messagebox.showinfo("Успех", "Запись удалена!")
            self.clear_entries()
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()

    def clear_entries(self):
        """Очищает все поля ввода"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()
