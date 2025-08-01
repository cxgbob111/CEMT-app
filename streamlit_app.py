import streamlit as st
import pandas as pd
import os

# 配置常量
EXCEL_FILE = "cemt_data_final_replaced.xlsx"
IMG_FOLDER = "images"

# 读取Excel（缓存10分钟）
@st.cache_data(ttl=600)
def load_excel(file):
    return pd.read_excel(file)

# 文件上传或本地读取
uploaded_file = st.file_uploader("上传或选择本地Excel数据文件", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    try:
        df = load_excel(EXCEL_FILE)
    except Exception as e:
        st.error(f"未找到默认数据文件，请上传Excel文件。错误信息：{e}")
        st.stop()  # 防止df未定义后续代码出错

# 此时df已正确定义，可以安全使用

# 2. 可编辑表格
st.subheader("📝 当前Excel数据（可编辑）")
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="excel_edit"
)

# 3. 保存
if st.button("💾 保存修改到本地Excel"):
    edited_df.to_excel(EXCEL_FILE, index=False)
    st.success("修改已保存到本地Excel！")

# 4. 刷新按钮
if st.button("🔄 刷新数据（重新加载Excel）"):
    st.cache_data.clear()
    st.experimental_rerun()

# 5. 船舶参数分析区
st.divider()
st.subheader("🔍 输入船舶长度后，自动显示对应宽度范围与等级分析")

# 输入船舶长度
length = st.number_input("船舶长度（米）", min_value=10.0, max_value=300.0, step=0.1)

# 根据长度查找可选宽度区间
width_options = edited_df[
    (edited_df['最小长度(m)'] <= length) & (length <= edited_df['最大长度(m)'])
]
if not width_options.empty:
    width_ranges = []
    for _, row in width_options.iterrows():
        width_ranges.append(f"CEMT {row['CEMT等级']}: {row['最小宽度(m)']}~{row['最大宽度(m)']} m")
    st.info("对应的宽度范围如下：\n" + "\n".join(width_ranges))
    # 选项型宽度输入，支持自由输入和推荐
    width = st.number_input("船舶宽度（米）（建议参考上方宽度范围）", min_value=2.0, max_value=50.0, step=0.1)
else:
    width = st.number_input("船舶宽度（米）", min_value=2.0, max_value=50.0, step=0.1)

# 分析等级
if st.button("🚀 匹配CEMT等级"):
    match = edited_df[
        (edited_df['最小长度(m)'] <= length) & (length <= edited_df['最大长度(m)']) &
        (edited_df['最小宽度(m)'] <= width) & (width <= edited_df['最大宽度(m)'])
    ]
    if not match.empty:
        info = match.iloc[0]
        st.success(f"等级：CEMT {info['CEMT等级']}")
        st.info(f"典型航道：{info['典型航道']}")
        st.info(f"运营船只数量：{info['运营船只数量']}")
        st.info(f"典型航段距离：{info['典型航段距离(km)']} km")
        st.info(f"单次航行时间：{info['单次航行时间(h)']} 小时")
    else:
        st.error("未匹配到CEMT等级，请调整尺寸重试。")

# 6. CEMT 等级信息+图片
st.divider()
st.subheader("🛳️ 选择CEMT等级，查看详细信息及船型图片")

cemt_options = edited_df['CEMT等级'].dropna().unique().tolist()
selected_cemt = st.selectbox("请选择CEMT等级", options=cemt_options)

if selected_cemt:
    info = edited_df[edited_df['CEMT等级'] == selected_cemt]
    if not info.empty:
        st.write("### 该等级Excel信息：")
        st.dataframe(info, use_container_width=True)
        # 显示图片
        img_jpg = os.path.join(IMG_FOLDER, f"cemt_{selected_cemt}.jpg")
        img_png = os.path.join(IMG_FOLDER, f"cemt_{selected_cemt}.png")
        if os.path.exists(img_jpg):
            st.image(img_jpg, caption=f"CEMT {selected_cemt} 典型船型", use_column_width=True)
        elif os.path.exists(img_png):
            st.image(img_png, caption=f"CEMT {selected_cemt} 典型船型", use_column_width=True)
        else:
            st.warning("暂无该级别船型图片。请在images目录下放置 cemt_等级.jpg 或 .png")
    else:
        st.error("未找到对应等级信息。")
