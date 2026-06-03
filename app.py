import streamlit as st
import pandas as pd
from datetime import datetime
import os

EXCEL_FILE = "Fire Extinguisher Checklist - Apr 2026.xlsx"
LOG_FILE = "daily_inspection_history.csv"

@st.cache_data
def load_and_clean_data():
    df = pd.read_excel(EXCEL_FILE, skiprows=2)
    df.columns = ['No', 'Floor', 'Location', 'Type', 'Capacity', 'Comment']
    df = df.dropna(subset=['No', 'Floor', 'Location'])
    df['Zone'] = df['Location'].apply(lambda x: str(x).split('–')[0].strip() if '–' in str(x) else (str(x).split('-')[0].strip() if '-' in str(x) else "General Zone"))
    df['Room_Details'] = df['Location'].apply(lambda x: str(x).split('–')[1].strip() if '–' in str(x) else (str(x).split('-')[1].strip() if '-' in str(x) else str(x)))
    df['No'] = df['No'].astype(int).astype(str)
    return df

df_master = load_and_clean_data()
today_date = datetime.now().strftime("%Y-%m-%d")

if os.path.exists(LOG_FILE):
    df_history = pd.read_csv(LOG_FILE)
    df_history['No'] = df_history['No'].astype(str)
else:
    df_history = pd.DataFrame(columns=["Date", "Time", "Floor", "Zone", "No", "Room_Details", "Status"])

done_today = df_history[df_history["Date"] == today_date]["No"].tolist()

st.set_page_config(page_title="🧯 Fire Walk Automation", layout="centered")
st.title("🧯 Fire Extinguisher Rounds")

selected_floor = st.selectbox("📍 Select Floor", df_master["Floor"].unique())
available_zones = df_master[df_master["Floor"] == selected_floor]["Zone"].unique()
selected_zone = st.selectbox("🧩 Select Zone", available_zones)

working_list = df_master[(df_master["Floor"] == selected_floor) & (df_master["Zone"] == selected_zone)]

st.write("---")
st.subheader(f"Extinguishers on {selected_floor} ({selected_zone})")

for _, row in working_list.iterrows():
    ext_id = row["No"]
    room = row["Room_Details"]
    ext_info = f"{row['Type']} | {row['Capacity']}"
    
    with st.container():
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            # FIXED: Changed unsafe_allowed_html to unsafe_allow_html
            st.markdown(f"**No. {ext_id}** — {room}<br><small style='color:gray;'>{ext_info}</small>", unsafe_allow_html=True)
        with col_btn:
            if ext_id in done_today:
                st.button("Saved", key=f"done_{ext_id}", disabled=True)
            else:
                if st.button("Log", key=f"btn_{ext_id}", type="primary"):
                    if os.path.exists(LOG_FILE):
                        check_db = pd.read_csv(LOG_FILE)
                        check_db['No'] = check_db['No'].astype(str)
                        is_duplicate = not check_db[(check_db["Date"] == today_date) & (check_db["No"] == ext_id)].empty
                    else:
                        is_duplicate = False
                        
                    if not is_duplicate:
                        now_time = datetime.now().strftime("%H:%M:%S")
                        new_log = pd.DataFrame([{
                            "Date": today_date,
                            "Time": now_time,
                            "Floor": selected_floor,
                            "Zone": selected_zone,
                            "No": ext_id,
                            "Room_Details": room,
                            "Status": "Passed/Good"
                        }])
                        new_log.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)
                        st.rerun()
