# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from database import init_db, get_all_rewards, get_reward_types, add_reward, delete_reward
from system_functions import (
    USERNAME, PASSWORD, search_jobs, calculate_entitlement, 
    calculator, get_statistics, get_greeting
)

st.set_page_config(page_title="مساعد لائحة الحوافز والمكافآت - جامعة البطانة", page_icon="🏛", layout="wide")
init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🏛 جامعة البطانة</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>مساعد لائحة الحوافز والمكافآت</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("تسجيل الدخول للنظام")
        user = st.text_input("اسم المستخدم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("🔐 تسجيل الدخول", use_container_width=True):
            if user.strip() == USERNAME and pwd == PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        st.caption("للتجربة: admin / 1234")
    st.stop()

# الشريط الجانبي
st.sidebar.title("🏛 لوحة التحكم")
st.sidebar.caption(get_greeting())
menu = st.sidebar.radio(
    "القائمة الرئيسية:",
    [
        "📊 الإحصائيات",
        "🔎 البحث في اللائحة",
        "🧮 حساب استحقاق وظيفة",
        "➕ إضافة وظيفة / بند",
        "🗑️ حذف وظيفة / بند",
        "🧾 عرض وتصدير اللائحة",
        "🧮 الحاسبة العامة",
    ]
)

if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# 1. الإحصائيات
if menu == "📊 الإحصائيات":
    st.header("📊 إحصائيات النظام")
    stats = get_statistics()
    cols = st.columns(len(stats))
    for col, (k, v) in zip(cols, stats.items()):
        col.metric(label=k, value=v)
    st.divider()
    st.subheader("🧾 نظرة سريعة على البيانات")
    df = pd.DataFrame(get_all_rewards())
    st.dataframe(df, use_container_width=True)

# 2. البحث
elif menu == "🔎 البحث في اللائحة":
    st.header("🔎 البحث في اللائحة")
    c1, c2 = st.columns([2, 1])
    q = c1.text_input("ابحث باسم الوظيفة أو القسم أو القيمة:")
    rtype = c2.selectbox("تصفية حسب نوع المكافأة:", ["الكل"] + get_reward_types())
    
    filter_type = "" if rtype == "الكل" else rtype
    df = search_jobs(q, filter_type)
    st.dataframe(df, use_container_width=True)
    st.caption(f"عدد النتائج: {len(df)}")

# 3. حساب استحقاق
elif menu == "🧮 حساب استحقاق وظيفة":
    st.header("🧮 حساب استحقاق وظيفة")
    st.caption("يحسب استحقاق بند محدد بناءً على الكمية/التكرار.")
    
    rtype = st.selectbox("نوع المكافأة:", get_reward_types())
    job = st.text_input("اسم الوظيفة / البند (كما ورد في اللائحة):")
    qty = st.number_input("الكمية / عدد المرات:", min_value=1.0, value=1.0, step=1.0)
    
    if st.button("🧮 احسب الآن", use_container_width=True):
        res = calculate_entitlement(job, rtype, qty)
        if res["ok"]:
            st.success(f"### الإجمالي المستحق: {res['total']:,.2f} {res['row']['العملة']}")
            st.write(f"- **الوظيفة:** {res['row']['وظيفة']}")
            st.write(f"- **نوع المكافأة:** {res['row']['نوع_المكافأة']}")
            st.write(f"- **الفئة الفردية:** {res['amount']} {res['row']['العملة']}")
            st.write(f"- **الكمية:** {res['quantity']}")
        else:
            st.error(res["message"])

# 4. إضافة بند
elif menu == "➕ إضافة وظيفة / بند":
    st.header("➕ إضافة وظيفة / بند جديد")
    with st.form("add_record_form"):
        sec = st.text_input("القسم:")
        r_type = st.text_input("نوع المكافأة:")
        job = st.text_input("اسم الوظيفة / البند:")
        amount = st.text_input("قيمة المكافأة:")
        curr = st.selectbox("العملة:", ["جنيه", "دولار"])
        notes = st.text_area("ملاحظات (اختياري):")
        
        submitted = st.form_submit_button("💾 حفظ البند")
        if submitted:
            try:
                add_reward(sec, r_type, job, amount, curr, notes)
                st.success("✅ تم حفظ البند بنجاح في قاعدة البيانات!")
            except Exception as e:
                st.error(f"❌ خطأ: {str(e)}")

# 5. حذف بند
elif menu == "🗑️ حذف وظيفة / بند":
    st.header("🗑️ حذف وظيفة / بند")
    data = get_all_rewards()
    if data:
        items = {f"[{r['id']}] {r['وظيفة']} - {r['نوع_المكافأة']} ({r['الفئة_بالجنيه']} {r['العملة']})": r['id'] for r in data}
        selected = st.selectbox("اختر السجل المراد حذفه:", list(items.keys()))
        if st.button("🗑️ تأكيد الحذف نهائياً", type="primary"):
            delete_reward(items[selected])
            st.success("✅ تم حذف السجل بنجاح!")
            st.rerun()
    else:
        st.info("لا توجد بيانات متاحة للحذف.")

# 6. عرض وتصدير
elif menu == "🧾 عرض وتصدير اللائحة":
    st.header("🧾 جميع بيانات اللائحة")
    df = pd.DataFrame(get_all_rewards())
    st.dataframe(df, use_container_width=True)
    
    c1, c2 = st.columns(2)
    csv_bytes = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    c1.download_button(
        label="📥 تصدير كملف CSV",
        data=csv_bytes,
        file_name="Batana_Rewards.csv",
        mime="text/csv",
        use_container_width=True
    )

# 7. حاسبة عامة
elif menu == "🧮 الحاسبة العامة":
    st.header("🧮 الحاسبة العامة")
    st.caption("أدخل عمليات حسابية مباشرة مثل: 50000 + 30000 أو 420000 * 3")
    expr = st.text_input("العملية الحسابية:")
    if st.button("🧮 حساب", use_container_width=True):
        res = calculator(expr)
        if res["ok"]:
            st.success(f"النتيجة: {res['result']:,}")
        else:
            st.error(res["message"])
