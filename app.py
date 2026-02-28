import streamlit as st
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Coil Optimizer", page_icon="⚡", layout="centered")
st.title("⚡ Pancake Coil Optimizer")
st.markdown("Calculate radial, axial, thermal, and electrical properties for potted stacked pancake electromagnets.")

# --- SIDEBAR / INPUTS ---
st.header("⚙️ Design Parameters")

with st.expander("1. Constraint Mode", expanded=True):
    constraint_mode = st.radio(
        "Select constraint:", 
        [1, 2], 
        format_func=lambda x: "1 - Space Constrained (Fill Window)" if x == 1 else "2 - Turns Constrained (Target Turns)"
    )
    target_turns_per_pancake = st.number_input("Target Turns per Pancake", min_value=1, value=45, step=1, disabled=(constraint_mode == 1))

with st.expander("2. Coil & Mold Constraints", expanded=False):
    a_mm = st.number_input("Mold Inner Radius (mm)", value=600.0, format="%.2f")
    b_max_mm = st.number_input("Mold Outer Radius (mm)", value=700.0, format="%.2f")
    plate_margin_mm = st.number_input("Edge Clearance Margin (mm)", value=1.0, format="%.2f")
    MLT_input_m = st.number_input("Fixed MLT (m) [0 = Auto Circular]", value=0.0, format="%.3f")

with st.expander("3. Material Dimensions", expanded=False):
    t_cu_mm = st.number_input("Copper Thickness (mm)", value=0.318, format="%.4f")
    w_cu_mm = st.number_input("Copper Width (mm)", value=50.8, format="%.2f")
    t_mylar_mm = st.number_input("Mylar Thickness (mm)", value=0.0508, format="%.4f")
    w_mylar_mm = st.number_input("Mylar Width (mm)", value=52.0, format="%.2f")

with st.expander("4. Stack & Cooling Plates", expanded=False):
    num_pancakes = st.number_input("Number of Pancakes in Series", min_value=1, value=4, step=1)
    plates_input = st.text_input("Cooling Plates Thicknesses (comma separated mm)", value="10.0, 8.0, 8.0, 8.0, 10.0")
    t_fiberglass_mm = st.number_input("Fiberglass Layer Thickness (mm)", value=0.23, format="%.3f")
    fiberglass_layers = st.number_input("Fiberglass Layers per Interface", min_value=0, value=2, step=1)

with st.expander("5. Electrical & Thermal", expanded=False):
    I_const = st.number_input("Constant Current (A)", value=60.0, format="%.1f")
    dT_water = st.number_input("Allowed Water Temp Rise (°C)", value=10.0, format="%.1f")

# --- FIXED CONSTANTS ---
rho = 1.68e-8
density_cu = 8960.0
density_al = 2700.0
density_epoxy = 1150.0
cp_water = 4186.0
rho_water = 1000.0

# --- PARSE PLATES ---
try:
    cooling_plates_mm = [float(x.strip()) for x in plates_input.split(',')]
except ValueError:
    st.error("Error parsing cooling plates. Please ensure it is a comma-separated list of numbers (e.g., '10, 8, 8, 10').")
    st.stop()

# --- CALCULATION LOGIC ---
if st.button("Calculate Core Design", type="primary"):
    
    if w_mylar_mm < w_cu_mm:
        st.error(f"Error: Mylar width ({w_mylar_mm} mm) cannot be smaller than copper width ({w_cu_mm} mm).")
        st.stop()

    winding_a_mm = a_mm + plate_margin_mm
    winding_b_max_mm = b_max_mm - plate_margin_mm
    available_build_mm = winding_b_max_mm - winding_a_mm
    layer_thickness_mm = t_cu_mm + t_mylar_mm
    
    if constraint_mode == 1:
        N_per_pancake = int(np.floor(available_build_mm / layer_thickness_mm))
        constraint_type = "Space Constrained"
    else:
        N_per_pancake = int(target_turns_per_pancake)
        constraint_type = "Turns Constrained"
        
    if N_per_pancake <= 0:
        st.error("Calculation resulted in 0 turns. Check your available space and material thicknesses.")
        st.stop()
        
    actual_build_mm = N_per_pancake * layer_thickness_mm
    winding_b_actual_mm = winding_a_mm + actual_build_mm
    unused_space_mm = available_build_mm - actual_build_mm
    
    if MLT_input_m > 0:
        MLT_m = MLT_input_m
        shape_type = "Irregular (Fixed MLT)"
    else:
        mean_radius_mm = winding_a_mm + (actual_build_mm / 2.0)
        MLT_m = (2 * np.pi * mean_radius_mm) / 1000.0
        shape_type = "Circular (Dynamic MLT)"
        
    # Axial Math
    total_pancakes_axial_mm = num_pancakes * w_mylar_mm
    total_plates_axial_mm = sum(cooling_plates_mm)
    interface_thickness_mm = fiberglass_layers * t_fiberglass_mm
    total_insulation_axial_mm = (num_pancakes * 2) * interface_thickness_mm
    total_assembly_axial_mm = total_pancakes_axial_mm + total_plates_axial_mm + total_insulation_axial_mm
    
    # Weight Math
    total_turns = N_per_pancake * num_pancakes
    total_length_m = total_turns * MLT_m
    A_cu = (t_cu_mm / 1000.0) * (w_cu_mm / 1000.0)
    weight_cu_kg = (A_cu * total_length_m) * density_cu
    
    r_in_m = a_mm / 1000.0
    plate_r_out_m = (winding_a_mm + actual_build_mm + plate_margin_mm) / 1000.0
    area_plate_m2 = np.pi * (plate_r_out_m**2 - r_in_m**2)
    weight_al_kg = (area_plate_m2 * (total_plates_axial_mm / 1000.0)) * density_al
    
    r_out_max_m = b_max_mm / 1000.0
    v_gross_mold_m3 = np.pi * (r_out_max_m**2 - r_in_m**2) * (total_assembly_axial_mm / 1000.0)
    v_winding_block_m3 = np.pi * ((winding_b_actual_mm/1000)**2 - (winding_a_mm/1000)**2) * (total_pancakes_axial_mm / 1000.0)
    v_plates_insul_m3 = np.pi * (plate_r_out_m**2 - r_in_m**2) * ((total_plates_axial_mm + total_insulation_axial_mm) / 1000.0)
    
    volume_epoxy_m3 = max(0.0, v_gross_mold_m3 - v_winding_block_m3 - v_plates_insul_m3)
    vol_epoxy_L = volume_epoxy_m3 * 1000.0
    weight_epoxy_kg = volume_epoxy_m3 * density_epoxy
    
    total_weight_kg = weight_cu_kg + weight_al_kg + weight_epoxy_kg
    
    # Electrical Math
    R_total = rho * (total_length_m / A_cu)
    V_req = I_const * R_total
    P_total = (I_const ** 2) * R_total
    NI_total = total_turns * I_const
    Flow_LPM = (P_total / (cp_water * dT_water) / rho_water) * 1000.0 * 60.0

    # --- RESULTS DISPLAY ---
    st.divider()
    st.header("📊 Results")
    
    if actual_build_mm > available_build_mm:
        st.warning(f"⚠️ WARNING: Coil build ({actual_build_mm:.2f} mm) exceeds available space by {abs(unused_space_mm):.2f} mm.")
    else:
        st.success("✅ Coil fits within the defined mold and constraints.")

    st.subheader("Electrical & Performance")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Turns", f"{total_turns}", f"{N_per_pancake} per pancake")
    col2.metric("Resistance", f"{R_total:.5f} Ω")
    col3.metric("Voltage Drop", f"{V_req:.2f} V")
    
    col4, col5, col6 = st.columns(3)
    col4.metric("Power Dissipation", f"{P_total:.1f} W")
    col5.metric("Ampere-Turns (NI)", f"{NI_total:,.0f} AT")
    col6.metric("Cooling Required", f"{Flow_LPM:.2f} L/min", f"ΔT {dT_water}°C")

    st.subheader("Radial Dimensions (mm)")
    st.code(f"""
Constraint Mode:        {constraint_type}
Winding Inner Radius:   {winding_a_mm:.5f}
Available Radial Space: {available_build_mm:.5f}
Actual Radial Build:    {actual_build_mm:.5f}
Final Outer Radius:     {winding_b_actual_mm:.5f}
Remaining Slack Space:  {unused_space_mm:.5f}
Applied MLT:            {MLT_m:.5f} m ({shape_type})
    """)

    st.subheader("Axial Stack Dimensions (mm)")
    st.code(f"""
Total Pancakes Width:   {total_pancakes_axial_mm:.5f}
Total Cooling Plates:   {total_plates_axial_mm:.5f}
Total Interface Insul:  {total_insulation_axial_mm:.5f}
OVERALL ASSEMBLY AXIAL: {total_assembly_axial_mm:.5f}
    """)

    st.subheader("Assembly Mass (kg)")
    st.code(f"""
Total Copper Weight:    {weight_cu_kg:.5f} kg
Total Aluminum Weight:  {weight_al_kg:.5f} kg
Total Epoxy Weight:     {weight_epoxy_kg:.5f} kg ({vol_epoxy_L:.2f} Liters)
OVERALL POTTED MASS:    {total_weight_kg:.5f} kg
    """)
