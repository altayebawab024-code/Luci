# -*- coding: utf-8 -*-
"""واجهة سطح مكتب لنظام مساعد لائحة الحوافز والمكافآت."""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from database import DB_PATH, get_all_rewards, get_reward_by_id, get_reward_types, init_db
from system_functions import (
    USERNAME,
    PASSWORD,
    add_reward,
    calculator,
    calculate_entitlement,
    delete_reward,
    export_csv,
    export_excel,
    get_greeting,
    get_statistics,
    search_jobs,
)


class RewardsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_db()
        self.title("مساعد لائحة الحوافز والمكافآت - جامعة البطانة")
        self.geometry("1200x750")
        self.configure(bg="#f4f6f8")
        self.show_login()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_window()
        frame = tk.Frame(self, bg="#f4f6f8")
        frame.pack(expand=True)
        card = tk.Frame(frame, bg="white", bd=1, relief="solid", padx=40, pady=30)
        card.pack()

        tk.Label(card, text="🏛 جامعة البطانة", bg="white", font=("Arial", 18, "bold")).pack(pady=5)
        tk.Label(card, text="تسجيل الدخول", bg="white", font=("Arial", 14)).pack(pady=10)

        form = tk.Frame(card, bg="white")
        form.pack()
        tk.Label(form, text="اسم المستخدم:", bg="white").grid(row=0, column=0, padx=5, pady=5)
        self.user_entry = ttk.Entry(form, width=30)
        self.user_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(form, text="كلمة المرور:", bg="white").grid(row=1, column=0, padx=5, pady=5)
        self.pass_entry = ttk.Entry(form, width=30, show="•")
        self.pass_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(card, text="تسجيل الدخول", command=self.do_login).pack(fill="x", pady=15)

    def do_login(self):
        if self.user_entry.get().strip() == USERNAME and self.pass_entry.get() == PASSWORD:
            self.show_dashboard()
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة.")

    def show_dashboard(self):
        self.clear_window()
        top = tk.Frame(self, bg="#1f4e78", height=60)
        top.pack(fill="x")
        tk.Label(top, text="مساعد لائحة الحوافز والمكافآت - جامعة البطانة", bg="#1f4e78", fg="white", font=("Arial", 15, "bold")).pack(side="right", padx=15, pady=10)
        tk.Label(top, text=get_greeting(), bg="#1f4e78", fg="white").pack(side="left", padx=15)

        body = tk.Frame(self, bg="#f4f6f8")
        body.pack(fill="both", expand=True, padx=10, pady=10)
        nav = tk.Frame(body, bg="white", width=200, bd=1, relief="solid")
        nav.pack(side="right", fill="y", padx=(0, 10))
        self.content = tk.Frame(body, bg="white", bd=1, relief="solid")
        self.content.pack(side="left", fill="both", expand=True)

        buttons = [
            ("🔎 البحث", self.page_search),
            ("🧮 استحقاق وظيفة", self.page_entitlement),
            ("➕ إضافة وظيفة", self.page_add),
            ("🧾 عرض البيانات", self.page_all),
            ("🧮 الحاسبة", self.page_calc),
            ("🚪 تسجيل الخروج", self.show_login),
        ]
        for txt, cmd in buttons:
            ttk.Button(nav, text=txt, command=cmd).pack(fill="x", padx=10, pady=5)

        self.page_search()

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def page_search(self):
        self._clear()
        tk.Label(self.content, text="🔎 البحث في اللائحة", bg="white", font=("Arial", 16, "bold")).pack(pady=10)
        box = tk.Frame(self.content, bg="white")
        box.pack(fill="x", padx=15, pady=5)
        entry = ttk.Entry(box, width=40)
        entry.pack(side="right", padx=5)
        t_box = ttk.Combobox(box, values=[""] + get_reward_types(), state="readonly", width=30)
        t_box.pack(side="right", padx=5)

        table_frame = tk.Frame(self.content, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        def search():
            for w in table_frame.winfo_children():
                w.destroy()
            rows = search_jobs(entry.get(), t_box.get()).to_dict("records")
            tree = ttk.Treeview(table_frame, columns=("id", "القسم", "النوع", "الوظيفة", "الفئة", "العملة"), show="headings")
            for c in ("id", "القسم", "النوع", "الوظيفة", "الفئة", "العملة"):
                tree.heading(c, text=c)
                tree.column(c, anchor="center")
            for r in rows:
                tree.insert("", "end", values=(r["id"], r["القسم"], r["نوع_المكافأة"], r["وظيفة"], r["الفئة_بالجنيه"], r["العملة"]))
            tree.pack(fill="both", expand=True)

        ttk.Button(box, text="بحث", command=search).pack(side="right", padx=5)
        search()

    def page_entitlement(self):
        self._clear()
        tk.Label(self.content, text="🧮 حساب استحقاق وظيفة", bg="white", font=("Arial", 16, "bold")).pack(pady=10)
        form = tk.Frame(self.content, bg="white")
        form.pack(pady=20)
        tk.Label(form, text="نوع المكافأة:", bg="white").grid(row=0, column=0, pady=5)
        t_box = ttk.Combobox(form, values=get_reward_types(), state="readonly", width=35)
        t_box.grid(row=0, column=1, pady=5)
        tk.Label(form, text="اسم الوظيفة:", bg="white").grid(row=1, column=0, pady=5)
        j_entry = ttk.Entry(form, width=37)
        j_entry.grid(row=1, column=1, pady=5)
        tk.Label(form, text="الكمية:", bg="white").grid(row=2, column=0, pady=5)
        q_entry = ttk.Entry(form, width=37)
        q_entry.insert(0, "1")
        q_entry.grid(row=2, column=1, pady=5)
        res_lbl = tk.Label(self.content, text="", bg="white", font=("Arial", 14, "bold"), fg="green")
        res_lbl.pack(pady=15)

        def calc():
            out = calculate_entitlement(j_entry.get(), t_box.get(), q_entry.get())
            if out["ok"]:
                res_lbl.config(text=f"المستحق: {out['total']:,.2f} {out['row']['العملة']}")
            else:
                res_lbl.config(text=out["message"])

        ttk.Button(form, text="احسب", command=calc).grid(row=3, column=1, pady=10)

    def page_add(self):
        self._clear()
        tk.Label(self.content, text="➕ إضافة بند جديد", bg="white", font=("Arial", 16, "bold")).pack(pady=10)
        form = tk.Frame(self.content, bg="white")
        form.pack(pady=10)
        fields = ["القسم", "نوع المكافأة", "الوظيفة", "الفئة", "العملة", "ملاحظات"]
        entries = {}
        for i, f in enumerate(fields):
            tk.Label(form, text=f"{f}:", bg="white").grid(row=i, column=0, pady=5)
            e = ttk.Entry(form, width=40)
            e.grid(row=i, column=1, pady=5)
            entries[f] = e

        def save():
            try:
                add_reward(entries["القسم"].get(), entries["نوع المكافأة"].get(), entries["الوظيفة"].get(), entries["الفئة"].get(), entries["العملة"].get() or "جنيه", entries["ملاحظات"].get())
                messagebox.showinfo("تم", "تمت الإضافة بنجاح")
            except Exception as ex:
                messagebox.showerror("خطأ", str(ex))

        ttk.Button(self.content, text="حفظ", command=save).pack(pady=10)

    def page_all(self):
        self._clear()
        tk.Label(self.content, text="🧾 جميع البيانات", bg="white", font=("Arial", 16, "bold")).pack(pady=10)
        rows = get_all_rewards()
        tree = ttk.Treeview(self.content, columns=("id", "القسم", "النوع", "الوظيفة", "الفئة", "العملة"), show="headings")
        for c in ("id", "القسم", "النوع", "الوظيفة", "الفئة", "العملة"):
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        for r in rows:
            tree.insert("", "end", values=(r["id"], r["القسم"], r["نوع_المكافأة"], r["وظيفة"], r["الفئة_بالجنيه"], r["العملة"]))
        tree.pack(fill="both", expand=True, padx=15, pady=10)

    def page_calc(self):
        self._clear()
        tk.Label(self.content, text="🧮 الحاسبة العامة", bg="white", font=("Arial", 16, "bold")).pack(pady=10)
        box = tk.Frame(self.content, bg="white")
        box.pack(pady=20)
        entry = ttk.Entry(box, width=40, font=("Arial", 14))
        entry.pack(side="left", padx=5)
        out = tk.Label(self.content, text="", bg="white", font=("Arial", 16, "bold"))
        out.pack(pady=10)

        def do_c():
            res = calculator(entry.get())
            out.config(text=f"النتيجة: {res['result']:,}" if res["ok"] else res["message"])

        ttk.Button(box, text="احسب", command=do_c).pack(side="left", padx=5)


if __name__ == "__main__":
    app = RewardsApp()
    app.mainloop()
