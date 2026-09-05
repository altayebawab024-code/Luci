# -*- coding: utf-8 -*-
import ast
import operator as op
import re
from datetime import datetime
import pandas as pd

from database import (
    add_reward as db_add_reward,
    delete_reward as db_delete_reward,
    get_all_rewards,
    get_reward_types as db_get_reward_types,
    get_statistics as db_get_statistics,
    search_rewards,
)

USERNAME = "admin"
PASSWORD = "1234"


def login(username, password):
    return (username or "").strip() == USERNAME and (password or "") == PASSWORD


def get_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 10:
        return "🌅 صباح الخير"
    if 10 <= hour < 17:
        return "☀️ نهارك سعيد"
    return "🌙 مساء الخير"


def normalize_text(text):
    text = str(text or "").strip().lower()
    text = "".join(
        char
        for char in __import__("unicodedata").normalize("NFD", text)
        if __import__("unicodedata").category(char) != "Mn"
    )
    replacements = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _as_df(rows):
    return pd.DataFrame(rows, columns=["id", "القسم", "نوع_المكافأة", "وظيفة", "الفئة_بالجنيه", "العملة", "ملاحظات"])


def get_dataframe():
    return _as_df(get_all_rewards())


def get_reward_types():
    return db_get_reward_types()


def search_jobs(query, reward_type=""):
    rows = search_rewards(query, reward_type)
    return _as_df(rows)


def calculate_entitlement(job, reward_type, quantity=1):
    job = (job or "").strip()
    reward_type = (reward_type or "").strip()
    if not job or not reward_type:
        return {"ok": False, "message": "يرجى اختيار نوع المكافأة واسم الوظيفة."}
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return {"ok": False, "message": "الكمية يجب أن تكون رقماً."}
    if quantity <= 0:
        return {"ok": False, "message": "الكمية يجب أن تكون أكبر من صفر."}

    rows = search_rewards(job, reward_type)
    if not rows:
        return {"ok": False, "message": "لم يتم العثور على الوظيفة ضمن نوع المكافأة المحدد."}

    norm_job = normalize_text(job)
    exact = [r for r in rows if normalize_text(r["وظيفة"]) == norm_job]
    if len(exact) == 1:
        row = exact[0]
    elif len(rows) == 1:
        row = rows[0]
    else:
        return {"ok": False, "message": "وجدت أكثر من نتيجة؛ استخدم اسم الوظيفة بصورة أدق."}

    amount = _number(row["الفئة_بالجنيه"])
    if amount is None:
        return {"ok": False, "message": f"الفئة المسجلة لهذه الوظيفة ليست رقماً: {row['الفئة_بالجنيه']}"}
    total = amount * quantity
    return {
        "ok": True,
        "row": row,
        "amount": amount,
        "quantity": quantity,
        "total": total,
    }


def _number(value):
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").replace(",", "").replace("٬", "")
    match = re.fullmatch(r"\s*[-+]?\d+(?:\.\d+)?\s*", text)
    if not match:
        return None
    try:
        return float(text)
    except ValueError:
        return None


_ALLOWED = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


def calculator(expression):
    expression = str(expression or "").strip()
    if not expression:
        return {"ok": False, "message": "اكتب العملية الحسابية أولاً."}
    expression = expression.replace("×", "*").replace("÷", "/").replace("٪", "%")
    expression = expression.replace("،", ",")
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_ast(tree.body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return {"ok": True, "result": result}
    except ZeroDivisionError:
        return {"ok": False, "message": "لا يمكن القسمة على صفر."}
    except Exception:
        return {"ok": False, "message": "عملية غير صحيحة. استخدم أرقاماً و + - × ÷ فقط."}


def _eval_ast(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("exponent too large")
        return _ALLOWED[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED:
        return _ALLOWED[type(node.op)](_eval_ast(node.operand))
    raise ValueError("unsupported expression")


def get_statistics():
    return db_get_statistics()


def export_csv(path):
    get_dataframe().to_csv(path, index=False, encoding="utf-8-sig")
    return path


def export_excel(path):
    get_dataframe().to_excel(path, index=False, engine="openpyxl")
    return path


def add_reward(section, reward_type, job, amount, currency="جنيه", notes=""):
    return db_add_reward(section, reward_type, job, amount, currency, notes)


def delete_reward(record_id):
    return db_delete_reward(record_id)
