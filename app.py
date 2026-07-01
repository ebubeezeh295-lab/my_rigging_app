import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="Rigging & Power Tool", page_icon="⚡")
st.title("⚡ Rigging & Power Utility")

# 2. Security Configuration
# Ensure you have a .streamlit/secrets.toml file with GOOGLE_API_KEY = "your_key_here"
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("API Key not found. Please set up your .streamlit/secrets.toml file.")

# 3. Tabs
tab1, tab2, tab3 = st.tabs(["Power Calculator", "Voltage Drop Tool", "AI Cable Scanner"])

# --- TAB 1: POWER CALCULATOR ---
with tab1:
     # Assuming Tab 1 is your Power Calculator
    st.header("⚡ Load & Distribution Calculator")
   
    col1, col2 = st.columns(2)
    with col1:
        num_beams = st.number_input("Number of beams", value=80)
        watts_per_beam = st.number_input("Watts per beam", value=200)
    with col2:
        voltage = st.selectbox("Voltage", [120, 230, 240])
        breaker_size = st.number_input("Breaker Size (Amps)", value=20)
       
    if st.button("Calculate Distribution"):
        total_watts = num_beams * watts_per_beam
        total_amps = total_watts / voltage
       
        # Applying the 80% Rule
        safe_capacity_per_circuit = breaker_size * 0.8
        circuits_needed = -(-total_amps // safe_capacity_per_circuit) # Ceiling division
       
        st.subheader("Results:")
        st.metric("Total System Draw", f"{total_amps:.2f} Amps")
        st.info(f"To stay safe, you need at least **{int(circuits_needed)} circuits**.")
       
        # Load Distribution Breakdown
        st.write("---")
        st.write(f"**Recommended Split:**")
        beams_per_circuit = num_beams / circuits_needed
        st.write(f"Distribute your 80 beams across the {int(circuits_needed)} circuits.")
        st.write(f"Aim for roughly **{round(beams_per_circuit)} beams per circuit**.")
       
        if total_amps > (safe_capacity_per_circuit * circuits_needed):
            st.error("⚠️ Warning: You are pushing the limits! Consider adding an extra circuit.")

        chart_data = pd.DataFrame(
            {
                "circuits": range(1, int(circuits_needed) + 1),
                "Load": [total_amps / circuits_needed] * int(circuits_needed),
            }
        )
        st.bar_chart(chart_data.set_index("circuits"))
    if 'devices' not in st.session_state:
        st.session_state.devices = []

    with st.form("add_device_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        name = col1.text_input("Device Name", placeholder="e.g. Beam 250")
        watts = col2.number_input("Watts per unit", min_value=1, value=100)
        count = col3.number_input("Quantity", min_value=1, value=1)
        
        if st.form_submit_button("Add Device"):
            st.session_state.devices.append({"name": name, "watts": watts, "count": count, "total": watts * count})

    if st.session_state.devices:
        df = pd.DataFrame(st.session_state.devices)
        st.table(df)
        total_watts = df['total'].sum()
        total_amps = total_watts / 230
        
        st.metric("Total Current Draw", f"{round(total_amps, 2)} A")
        
        breaker_limit = st.number_input("Circuit Breaker (Amps)", value=16)
        if total_amps > (breaker_limit * 0.8):
            st.error(f"⚠️ DANGER: Load exceeds safe 80% limit of {breaker_limit * 0.8}A!")
        else:
            st.success("✅ Load is within safe limits.")

        if st.button("Clear List"):
            st.session_state.devices = []
            st.rerun()

# --- TAB 2: VOLTAGE DROP TOOL ---
with tab2:
    st.subheader("Voltage Drop Calculator")
    # Group inputs in columns or just list them vertically in the main tab
    # This keeps everything for this tool in one place!
    current_load = st.number_input("Current Load (Amps)", min_value=0.0)
    length = st.number_input("Cable Length (Meters)", min_value=0.0)
    cable_size = st.selectbox("Cable Size (mm²)", [1.5, 2.5, 4.0, 6.0, 10.0])

    # Formula
    v_drop = (2 * length * current_load * 0.0175) / cable_size if cable_size else 0
    v_drop_percent = (v_drop / 230) * 100 if cable_size else 0

    st.write("---")
    st.metric("Voltage Drop", f"{round(v_drop, 2)} V")
    st.metric("Drop Percentage", f"{round(v_drop_percent, 2)} %")

    if v_drop_percent > 5:
        st.error("❌ WARNING: Voltage drop > 5%. Performance issues likely.")
    elif v_drop_percent > 3:
        st.warning("⚠️ NOTICE: Voltage drop is significant (3-5%).")
    else:
        st.success("✅ OPTIMAL: Voltage drop is within safe levels.")

# --- TAB 3: AI CABLE SCANNER ---
with tab3:
    # Text Input
    user_input = st.text_area("Ask the AI about a cable or rigging issue:")

    # Image Input
    uploaded_file = st.file_uploader("Or upload a photo of the cable/wire:", type=["jpg", "png", "jpeg"])

    if st.button("Generate Response"):
        if not user_input and not uploaded_file:
            st.warning("Please enter a question or upload an image first!")
        else:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')

                with st.spinner("Thinking..."):
                    # Logic: If image is provided, use it. Otherwise, use text.
                    if uploaded_file:
                        image = Image.open(uploaded_file)
                        st.image(image, caption="Analyzing...", use_container_width=True)
                        prompt = user_input if user_input else "Analyze this cable cross-section and identify the gauge and potential wear."
                        response = model.generate_content([prompt, image])
                    else:
                        response = model.generate_content(user_input)

                    st.write(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")
