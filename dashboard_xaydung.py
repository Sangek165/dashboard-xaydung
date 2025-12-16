import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="Dashboard Quản Lý Dự Án Xây Dựng", layout="wide", page_icon="🏗️")

# --- 2. HÀM TẢI DỮ LIỆU ---
@st.cache_data(ttl=60)
def load_data():
    # Link Google Sheet của bạn (Tôi đã điền sẵn cho bạn)
    sheet_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQXaLjtrG-ZY3I-6tlpZytfaG1t-Q9DCKxT_5U6G7jjUS1wxXsQHFLF7hy5_sSm39_Vj7AET8qJyBHy/pub?gid=1622102571&single=true&output=tsv'
    
    try:
        # Tự động nhận diện dấu phẩy hoặc dấu tab (sep=None)
        df = pd.read_csv(sheet_url, sep=None, engine='python')
        
        # Xóa khoảng trắng thừa ở tên cột
        df.columns = df.columns.str.strip()
        
        # Kiểm tra cột bắt buộc
        if 'Start' not in df.columns:
            st.error("❌ Không tìm thấy cột 'Start'.")
            return pd.DataFrame()

        # Xử lý ngày tháng
        df['Start'] = pd.to_datetime(df['Start'], dayfirst=True, errors='coerce')
        df['Finish'] = pd.to_datetime(df['Finish'], dayfirst=True, errors='coerce')
        
        # Xử lý số liệu (Budget, Actual, Completion)
        cols_num = ['Budget', 'Actual', 'Completion']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Tính toán KPI
        df['EV'] = df['Budget'] * (df['Completion'] / 100)
        df['CV'] = df['EV'] - df['Actual']
        
        return df

    except Exception as e:
        st.error(f"⚠️ Lỗi: {e}")
        return pd.DataFrame()

# Tải dữ liệu
df = load_data()

# --- 3. KIỂM TRA DỮ LIỆU ---
if df is None:
    st.warning("👈 Bạn chưa dán Link CSV!")
    st.stop()
elif df.empty:
    st.warning("Dữ liệu trống hoặc lỗi đọc file.")
    st.stop()

# --- 4. GIAO DIỆN DASHBOARD (PHẦN BẠN BỊ THIẾU) ---

# Tiêu đề
st.title("🏗️ Dashboard Quản Lý Dự Án Xây Dựng")
st.markdown(f"*Cập nhật lúc: {datetime.now().strftime('%H:%M %d/%m/%Y')}*")
st.markdown("---")

# Bộ lọc bên trái
st.sidebar.header("🔍 Bộ lọc hiển thị")
if "Phase" in df.columns:
    all_phases = df["Phase"].unique()
    selected_phase = st.sidebar.multiselect(
        "Chọn Giai đoạn:",
        options=all_phases,
        default=all_phases
    )
    df_filtered = df[df["Phase"].isin(selected_phase)]
else:
    df_filtered = df

# Tính toán các chỉ số tổng
total_budget = df_filtered['Budget'].sum()
total_actual = df_filtered['Actual'].sum()
total_ev = df_filtered['EV'].sum()
cpi = total_ev / total_actual if total_actual > 0 else 0
avg_progress = df_filtered['Completion'].mean()

# Hiển thị 4 thẻ KPI
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Tổng Ngân Sách", f"{total_budget:,.0f} VND")
with col2:
    st.metric("💸 Chi Phí Thực Tế", f"{total_actual:,.0f} VND", delta=f"{total_budget - total_actual:,.0f}")
with col3:
    st.metric("📊 CPI (Hiệu quả)", f"{cpi:.2f}", delta="Tốt (>1)" if cpi >= 1 else "Kém (<1)")
with col4:
    st.metric("🚧 % Hoàn thành TB", f"{avg_progress:.1f}%")

st.markdown("---")

# Vẽ biểu đồ
col_left, col_right = st.columns((2, 1))

with col_left:
    st.subheader("📅 Tiến độ thi công (Gantt Chart)")
    if not df_filtered.empty:
        fig_gantt = px.timeline(
            df_filtered, x_start="Start", x_end="Finish", y="Task", color="Completion",
            title="Biểu đồ Gantt", color_continuous_scale="RdYlGn", range_color=[0, 100]
        )
        fig_gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_gantt, use_container_width=True)

with col_right:
    st.subheader("💰 Ngân sách vs Thực chi")
    if not df_filtered.empty:
        fig_cost = go.Figure(data=[
            go.Bar(name='Ngân sách', x=df_filtered['Task'], y=df_filtered['Budget'], marker_color='#2ecc71'),
            go.Bar(name='Thực tế', x=df_filtered['Task'], y=df_filtered['Actual'], marker_color='#e74c3c')
        ])
        fig_cost.update_layout(barmode='group')
        st.plotly_chart(fig_cost, use_container_width=True)

# Bảng chi tiết
st.subheader("📋 Bảng dữ liệu chi tiết")
st.dataframe(df_filtered.style.background_gradient(subset=['Completion'], cmap='Greens'), use_container_width=True)