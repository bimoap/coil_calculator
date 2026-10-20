%%writefile app.py
import streamlit as st
import numpy as np
import pandas as pd
import base64
import math

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Coil Design & Analysis Suite", page_icon="⚡", layout="wide")

# --- UNIT CONVERSIONS ---
MM_TO_THOU = 1000.0 / 25.4  # ~39.3700787
THOU_TO_MM = 0.0254

# =====================================================================
# 1. NEW COMPONENT: MAXIMUM CURRENT CALCULATIONS & UTILITIES
# =====================================================================
def calculate_max_current(width_mm, thickness_mm, cooling_plates):
    if width_mm <= 0 or thickness_mm <= 0 or cooling_plates < 0:
        return 0.0, 0.0
    # Formula: Recommended max current = 16.86 * Z * sqrt(K * W)
    max_current = 16.86 * thickness_mm * math.sqrt(cooling_plates * width_mm)
    # Cross-sectional Area = W * Z
    area_mm2 = width_mm * thickness_mm
    # Current density (A/mm^2) = max_current / area
    current_density = max_current / area_mm2 if area_mm2 > 0 else 0.0
    return max_current, current_density

# =====================================================================
# 2. ORIGINAL COMPONENT: SVG GENERATION FUNCTION
# =====================================================================
def generate_cross_section_svg(res, a_mm, b_max_mm, rad_dim_mode, plate_margin_mm, cooling_plates_list, num_pancakes):
    """Generates a proportional SVG cross-section drawing with dynamic Light/Dark mode and adaptive labels."""
    max_dim_mm = max(b_max_mm * 1.1, res['ax_total_mm'] * 1.1)
    target_svg_size = 600 
    scale = target_svg_size / max_dim_mm 
    
    pad_left = 80
    pad_right = 150
    pad_top = 50
    pad_bottom = 50

    svg_width = (b_max_mm * scale) + pad_left + pad_right
    svg_height = (res['ax_total_mm'] * scale) + pad_top + pad_bottom
    
    origin_x = pad_left
    origin_y = svg_height - pad_bottom

    svg_elements = []

    def draw_rect(x_mm, y_start_mm, w_mm, h_mm, css_class, label=None, opacity=1.0):
        x_px = origin_x + (x_mm * scale)
        y_px = origin_y - ((y_start_mm + h_mm) * scale) 
        w_px = w_mm * scale
        h_px = h_mm * scale
        rect = f'<rect x="{x_px:.1f}" y="{y_px:.1f}" width="{w_px:.1f}" height="{h_px:.1f}" class="{css_class} box-border" fill-opacity="{opacity}" />'
        svg_elements.append(rect)
        if label:
             svg_elements.append(f'<text x="{x_px + w_px/2:.1f}" y="{y_px + h_px/2 + 5:.1f}" class="label-text" text-anchor="middle">{label}</text>')

    def draw_dim_line(x1_mm, y1_mm, x2_mm, y2_mm, label_text, offset_mm=0, is_vertical=False):
        x1_px = origin_x + (x1_mm * scale)
        y1_px = origin_y - (y1_mm * scale)
        x2_px = origin_x + (x2_mm * scale)
        y2_px = origin_y - (y2_mm * scale)
        off_px = offset_mm * scale
        
        if is_vertical:
            line_x1 = x1_px + off_px
            line_x2 = x2_px + off_px
            line_y1 = y1_px
            line_y2 = y2_px
            text_x = line_x1 + (15 if off_px >= 0 else -15)
            text_y = (line_y1 + line_y2) / 2
            text_anchor = "start" if off_px >= 0 else "end"
            arrow_marker_start = "url(#arrow-up)" if off_px >= 0 else "url(#arrow-down)"
            arrow_marker_end = "url(#arrow-down)" if off_px >= 0 else "url(#arrow-up)"
        else:
            line_x1 = x1_px
            line_x2 = x2_px
            line_y1 = y1_px - off_px
            line_y2 = y2_px - off_px
            text_x = (line_x1 + line_x2) / 2
            text_y = line_y1 - 10
            text_anchor = "middle"
            arrow_marker_start = "url(#arrow-left)"
            arrow_marker_end = "url(#arrow-right)"

        line = f'<line x1="{line_x1:.1f}" y1="{line_y1:.1f}" x2="{line_x2:.1f}" y2="{line_y2:.1f}" class="dim-line" marker-start="{arrow_marker_start}" marker-end="{arrow_marker_end}" />'
        svg_elements.append(line)
        
        text = f'<text x="{text_x:.1f}" y="{text_y:.1f}" class="dim-text" text-anchor="{text_anchor}">{label_text}</text>'
        svg_elements.append(text)

    # Background Potting Block
    draw_rect(a_mm, 0, b_max_mm - a_mm, res['ax_total_mm'], "potting-box", label=None, opacity=0.15)

    # Draw Pancakes and Cooling Plates
    current_y = 0.0
    for i in range(num_pancakes):
        # 1. Draw Pancake Block
        draw_rect(a_mm + plate_margin_mm, current_y, res['b_actual_mm'] - a_mm - plate_margin_mm, res['t_mylar_mm'], "pancake-box", label=f"Pancake {i+1}")
        current_y += res['t_mylar_mm']
        
        # 2. Draw Interface Insulation (if any layer and not at overall top)
        if i < num_pancakes - 1:
            # Fiberglass Layer below next plate
            draw_rect(a_mm + plate_margin_mm, current_y, res['b_actual_mm'] - a_mm - plate_margin_mm, res['t_insul_interface_mm'], "insul-box")
            current_y += res['t_insul_interface_mm']
            
            # Cooling Plate
            if i < len(cooling_plates_list):
                plate_tk = cooling_plates_list[i]
                draw_rect(a_mm, current_y, b_max_mm - a_mm, plate_tk, "plate-box", label=f"Plate {i+1} ({plate_tk:.1f}mm)")
                current_y += plate_tk
                
            # Fiberglass Layer above plate
            draw_rect(a_mm + plate_margin_mm, current_y, res['b_actual_mm'] - a_mm - plate_margin_mm, res['t_insul_interface_mm'], "insul-box")
            current_y += res['t_insul_interface_mm']

    # Dimensions Annotation
    draw_dim_line(a_mm, 0, res['b_actual_mm'], 0, f"Active Winding Width: {res['b_actual_mm']-a_mm:.1f} mm", offset_mm=-30)
    draw_dim_line(a_mm + plate_margin_mm, 0, a_mm + plate_margin_mm, res['ax_total_mm'], f"Assembly Height: {res['ax_total_mm']:.1f} mm", offset_mm=-60, is_vertical=True)
    
    # Outer Limit OD/2
    draw_dim_line(a_mm, 0, b_max_mm, 0, f"Plate Outer Limit: {b_max_mm:.1f} mm", offset_mm=-45)

    svg_style = """
    <style>
        .pancake-box { fill: #FF8C00; stroke: #D2691E; stroke-width: 1.5; }
        .plate-box { fill: #A9A9A9; stroke: #808080; stroke-width: 1.5; }
        .insul-box { fill: #FAF0E6; stroke: #D3D3D3; stroke-width: 1; }
        .potting-box { fill: #87CEEB; stroke: #4682B4; stroke-width: 2; stroke-dasharray: 4,4; }
        .dim-line { stroke: #1E90FF; stroke-width: 1.5; }
        .dim-text { fill: #1E90FF; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 14px; font-weight: bold; }
        .label-text { fill: #000000; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; }
        @media (prefers-color-scheme: dark) {
            .label-text { fill: #FFFFFF; }
            .dim-text { fill: #00BFFF; }
            .dim-line { stroke: #00BFFF; }
        }
    </style>
    """

    svg_markers = """
    <defs>
        <marker id="arrow-left" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 10 0 L 0 5 L 10 10 z" fill="#1E90FF" />
        </marker>
        <marker id="arrow-right" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#1E90FF" />
        </marker>
        <marker id="arrow-up" viewBox="0 0 10 10" refX="5" refY="0" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 10 L 5 0 L 10 10 z" fill="#1E90FF" />
        </marker>
        <marker id="arrow-down" viewBox="0 0 10 10" refX="5" refY="10" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 5 10 L 10 0 z" fill="#1E90FF" />
        </marker>
    </defs>
    """

    svg_string = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width:.1f} {svg_height:.1f}" width="100%" height="100%">'
    svg_string += svg_markers + svg_style
    svg_string += "\n".join(svg_elements)
    svg_string += '</svg>'
    return svg_string

# =====================================================================
# 3. ORIGINAL COMPONENT: CORE PHYSICS ENGINE / OPTIMIZATION
# =====================================================================
def optimize_pancake_coil(a_mm, b_max_mm, plate_margin_mm, t_cu_mm, w_cu_mm, t_mylar_mm, w_mylar_mm, num_pancakes, cooling_plates_list, constraint_mode, target_turns, rho_cu, t_fiberglass_mm, fiberglass_layers, I_const, dT_water, MLT_input_m):
    # Core radial boundaries for windings
    inner_winding_boundary = a_mm + plate_margin_mm
    outer_winding_limit = b_max_mm - plate_margin_mm
    available_width_mm = outer_winding_limit - inner_winding_boundary
    
    # Layer buildup (Copper + Mylar turn insulation)
    t_turn_buildup_mm = t_cu_mm + t_mylar_mm
    
    # Determine number of turns per pancake based on constraints
    if constraint_mode == 1:  # Maximize Turns
        turns_per_pancake = int(np.floor(available_width_mm / t_turn_buildup_mm))
        constraint_type = "Maximize Space Fill"
    else:  # Target Specific Turns
        turns_per_pancake = int(target_turns)
        constraint_type = f"Target Specific Turns ({target_turns})"
        
    # Calculate physical actual boundaries based on realized turns
    radial_winding_span_mm = turns_per_pancake * t_turn_buildup_mm
    b_actual_mm = inner_winding_boundary + radial_winding_span_mm
    unused_space_mm = b_max_mm - b_actual_mm
    
    # Multi-Layer Turn (MLT)
    if MLT_input_m > 0:
        MLT_m = MLT_input_m
        shape_type = "Manual Override"
    else:
        # Circular coil average path
        d_mean_mm = (inner_winding_boundary + b_actual_mm)
        MLT_m = (np.pi * d_mean_mm) / 1000.0
        shape_type = "Circular Core (Auto)"
        
    # Stack buildup dimensions
    t_insul_interface_mm = t_fiberglass_mm * fiberglass_layers
    ax_pancakes_mm = num_pancakes * w_mylar_mm
    ax_plates_mm = sum(cooling_plates_list)
    ax_insul_mm = (num_pancakes - 1) * 2 * t_insul_interface_mm
    ax_total_mm = ax_pancakes_mm + ax_plates_mm + ax_insul_mm
    
    # Electrical Properties
    length_per_pancake_m = turns_per_pancake * MLT_m
    total_length_m = length_per_pancake_m * num_pancakes
    A_cu_mm2 = t_cu_mm * w_cu_mm
    A_cu_m2 = A_cu_mm2 * 1e-6
    
    R_total_20C = (rho_cu * total_length_m) / A_cu_m2
    # Temperature correction for general operating coil (approximated around 65C default thermal average)
    temp_coeff_cu = 0.00393
    R_total_65C = R_total_20C * (1 + temp_coeff_cu * (65 - 20))
    
    # Operating math
    I_const_val = float(I_const)
    V_drop = I_const_val * R_total_65C
    P_diss = I_const_val * V_drop
    J_A_mm2 = I_const_val / A_cu_mm2
    NI = I_const_val * turns_per_pancake * num_pancakes
    
    # Cooling Requirements (Water flow modeling based on volumetric cooling capacity)
    specific_heat_water = 4184.0  # J/kg.K
    density_water = 1000.0        # kg/m^3
    if dT_water > 0:
        flow_rate_kg_s = P_diss / (specific_heat_water * dT_water)
        flow_rate_L_min = (flow_rate_kg_s / density_water) * 1000.0 * 60.0
    else:
        flow_rate_L_min = 0.0
        
    # Materials Mass Weights
    density_cu = 8960.0       # kg/m^3
    density_al = 2700.0       # kg/m^3
    density_mylar = 1390.0    # kg/m^3
    density_epoxy = 1150.0    # kg/m^3
    
    vol_cu_m3 = A_cu_m2 * total_length_m
    wt_cu_kg = vol_cu_m3 * density_cu
    
    A_mylar_m2 = (t_mylar_mm * w_mylar_mm) * 1e-6
    vol_mylar_m3 = A_mylar_m2 * total_length_m
    wt_mylar_kg = vol_mylar_m3 * density_mylar
    
    # Estimated cooling plate weights (assuming aluminum solid plates with active flow channel cuts)
    wt_al_kg = 0.0
    vol_plates_total_m3 = 0.0
    for tk_p in cooling_plates_list:
        vol_p_m3 = (np.pi * ((b_max_mm/1000)**2 - (a_mm/1000)**2)) * (tk_p / 1000.0)
        # Deduct channels approx 15% volume for cooling pathways inside plate
        vol_plates_total_m3 += vol_p_m3 * 0.85
    wt_al_kg = vol_plates_total_m3 * density_al
    
    # Potting Resin Volume
    vol_total_assembly_m3 = (np.pi * ((b_max_mm/1000)**2 - (a_mm/1000)**2)) * (ax_total_mm / 1000.0)
    vol_potting_resin_m3 = max(0.0, vol_total_assembly_m3 - vol_cu_m3 - vol_mylar_m3 - vol_plates_total_m3)
    wt_epoxy_kg = vol_potting_resin_m3 * density_epoxy
    vol_epoxy_L = vol_potting_resin_m3 * 1000.0
    
    wt_total_kg = wt_cu_kg + wt_mylar_kg + wt_al_kg + wt_epoxy_kg
    
    return {
        'turns_per_pancake': turns_per_pancake,
        'total_turns': turns_per_pancake * num_pancakes,
        'b_actual_mm': b_actual_mm,
        'unused_space_mm': unused_space_mm,
        'MLT_m': MLT_m,
        'shape_type': shape_type,
        'constraint_type': constraint_type,
        'ax_pancakes_mm': ax_pancakes_mm,
        'ax_plates_mm': ax_plates_mm,
        'ax_insul_mm': ax_insul_mm,
        'ax_total_mm': ax_total_mm,
        'length_per_pancake_m': length_per_pancake_m,
        'total_length_m': total_length_m,
        'A_cu_mm2': A_cu_mm2,
        'R': R_total_65C,
        'V': V_drop,
        'P': P_diss,
        'J_A_mm2': J_A_mm2,
        'NI': NI,
        'Flow_LPM': flow_rate_L_min,
        'wt_cu_kg': wt_cu_kg,
        'wt_mylar_kg': wt_mylar_kg,
        'wt_al_kg': wt_al_kg,
        'wt_epoxy_kg': wt_epoxy_kg,
        'vol_epoxy_L': vol_epoxy_L,
        'wt_total_kg': wt_total_kg
    }

# =====================================================================
# 4. SIDEBAR CONFIGURATION (COMMON CONTROLS)
# =====================================================================
with st.sidebar:
    st.header("⚙️ Global Settings")
    unit_system = st.radio(
        "Preferred Unit System:", 
        ["Metric (mm / A/mm²)", "Imperial (thou / A/thou²)"]
    )
    is_metric = unit_system.startswith("Metric")

# Dynamic Title and Options depending on Unit
if is_metric:
    width_options = ["50.8 mm (2 in)", "38.1 mm (1.5 in)", "25.4 mm (1 in)", "12.7 mm (0.5 in)", "Custom"]
    thick_options = ["0.787 mm", "1.0 mm", "1.194 mm", "1.245 mm", "1.372 mm", "Custom"]
else:
    width_options = ["2000.0 thou (2 in)", "1500.0 thou (1.5 in)", "1000.0 thou (1 in)", "500.0 thou (0.5 in)", "Custom"]
    thick_options = ["31.0 thou (0.787 mm)", "39.4 thou (1.0 mm)", "47.0 thou (1.194 mm)", "49.0 thou (1.245 mm)", "54.0 thou (1.372 mm)", "Custom"]

# Master Preset reference lists in MM
width_presets_mm = [50.8, 38.1, 25.4, 12.7]
thick_presets_mm = [0.787, 1.0, 1.194, 1.245, 1.372]

# =====================================================================
# 5. NAVIGATION TABS (TOP LEVEL)
# =====================================================================
tool_tab1, tool_tab2 = st.tabs(["📊 Dynamic Pancake Coil Designer", "⚡ Copper Strip Max Current Limits"])

# ---------------------------------------------------------------------
# TAB 1: ORIGINAL PANCAKE COIL CALCULATOR
# ---------------------------------------------------------------------
with tool_tab1:
    st.subheader("Dynamic Multi-Pancake Coil Design Optimization Suite")
    st.markdown("Define magnetic constraints, cooling intervals, and conductor configurations to dynamically build your custom coil assembly.")

    # Split design parameters into sidebar expansion for Tab 1 specific settings
    st.sidebar.markdown("---")
    st.sidebar.header("🛠️ Pancake Designer Inputs")
    
    constraint_mode = st.sidebar.radio(
        "Optimization Goal:", 
        [1, 2], 
        index=1,
        format_func=lambda x: "Maximize Turns (Fill Space)" if x == 1 else "Target Specific Turns"
    )
    if constraint_mode == 2:
        target_turns_per_pancake = st.sidebar.number_input("Target Turns per Pancake", min_value=1, value=172, step=1)
    else:
        target_turns_per_pancake = 172 

    st.sidebar.subheader("Radial Geometry (mm)")
    rad_dim_mode = st.sidebar.radio("Input Mode:", ["Diameter", "Radius"], horizontal=True)
    
    col_r1, col_r2 = st.sidebar.columns(2)
    if rad_dim_mode == "Diameter":
        plate_in_mm = col_r1.number_input("Cooling Plate ID", value=100.0, step=1.0, format="%.1f")
        plate_out_mm = col_r2.number_input("Cooling Plate OD", value=259.0, step=1.0, format="%.1f")
        a_mm = plate_in_mm / 2.0
        b_max_mm = plate_out_mm / 2.0
    else:
        plate_in_mm = col_r1.number_input("Cooling Plate Inner Radius", value=50.0, step=1.0, format="%.1f")
        plate_out_mm = col_r2.number_input("Cooling Plate Outer Radius", value=129.5, step=1.0, format="%.1f")
        a_mm = plate_in_mm
        b_max_mm = plate_out_mm
        
    plate_margin_mm = st.sidebar.number_input("Epoxy Edge Margin", value=0.5, step=0.1, format="%.1f", help="Clearance to allow 2 layers of fiberglass between copper and inner/outer mold walls.")

    st.sidebar.subheader("Stack Configuration")
    num_pancakes = st.sidebar.number_input("Number of Pancakes", min_value=1, value=2, step=1)
    plates_input = st.sidebar.text_input("Cooling Plates (mm, comma-separated)", value="6.0, 6.0, 6.0", help="Define thickness of plates from bottom to top.")
    
    try:
        cooling_plates_mm = [float(x.strip()) for x in plates_input.split(',')]
    except ValueError:
        st.sidebar.error("Invalid format for cooling plates. Use numbers separated by commas.")
        st.stop()

    # Additional physical properties
    with st.sidebar.expander("Material Details (Advanced)", expanded=False):
        st.markdown("**Conductor & Turn Insulation**")
        col_m1, col_m2 = st.columns(2)
        t_cu_mm = col_m1.number_input("Cu Thickness", value=0.381, format="%.4f")
        w_cu_mm = col_m2.number_input("Cu Width", value=38.1, format="%.2f")
        t_mylar_mm = col_m1.number_input("Mylar Thickness", value=0.0762, format="%.4f")
        w_mylar_mm = col_m2.number_input("Mylar Width", value=38.8, format="%.2f")
        
        st.markdown("**Electrical Properties**")
        rho_cu = st.number_input("Copper Resistivity (Ω·m)", value=1.71211e-8, format="%.5e", help="Default matches 100.7% IACS standard commercial copper.")

        st.markdown("**Interface Insulation**")
        col_i1, col_i2 = st.columns(2)
        t_fiberglass_mm = col_i1.number_input("Fiberglass Tk.", value=0.23, format="%.3f")
        fiberglass_layers = col_i2.number_input("Layers/Interface", min_value=1, value=2)
        
        st.markdown("**Other**")
        MLT_input_m = st.number_input("Fixed MLT (m) [0=Auto]", value=0.0, format="%.3f", help="Set >0 for non-circular coils.")

    with st.sidebar.expander("Operating Conditions", expanded=False):
        I_const = st.number_input("Operating Current (A)", value=50.0, step=1.0, format="%.1f")
        dT_water = st.number_input("Allowed Water Temp Rise (°C)", value=10.0, step=1.0, format="%.1f")

    # Run Physics calculations
    res = optimize_pancake_coil(
        a_mm, b_max_mm, plate_margin_mm, t_cu_mm, w_cu_mm, t_mylar_mm, w_mylar_mm, 
        num_pancakes, cooling_plates_mm, constraint_mode, target_turns_per_pancake, 
        rho_cu, t_fiberglass_mm, fiberglass_layers, I_const, dT_water, MLT_input_m
    )

    # Top metrics display for Tab 1
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 1, 1, 1, 1.2])
    col1.metric("Total Ampere-Turns", f"{res['NI']:,.0f} AT", f"{res['total_turns']} turns @ {I_const} A", delta_color="off")
    col2.metric("Current Density", f"{res['J_A_mm2']:.2f} A/mm²", f"{I_const} A / {res['A_cu_mm2']:.2f} mm²", delta_color="off")
    col3.metric("Power Dissipation", f"{res['P']:.1f} W", f"{res['V']:.1f} V @ {I_const} A", delta_color="off")
    col4.metric("Total Resistance", f"{res['R']:.4f} Ω", f"{res['length_per_pancake_m']:.1f} m/pancake × {num_pancakes}", delta_color="off")
    col5.metric("Required Cooling", f"{res['Flow_LPM']:.1f} L/min", f"ΔT = {dT_water}°C", delta_color="off")
    
    # Generate and prepare CSV export data
    export_dict = {
        "Turns per Pancake": [res['turns_per_pancake']],
        "Total Turns": [res['total_turns']],
        "Power Dissipation (W)": [res['P']],
        "Total Copper Mass (kg)": [res['wt_cu_kg']],
        "Total Aluminum Mass (kg)": [res['wt_al_kg']],
        "Total Mylar Mass (kg)": [res['wt_mylar_kg']],
        "Epoxy Volume (Liters)": [res['vol_epoxy_L']],
        "Potting Epoxy Mass (kg)": [res['wt_epoxy_kg']],
        "Total Assembly Mass (kg)": [res['wt_total_kg']]
    }
    df_export = pd.DataFrame(export_dict)
    csv_data = df_export.to_csv(index=False).encode('utf-8')

    with col6:
        st.write("") 
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="pancake_coil_design.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    st.divider()
    
    # Sub-tabs within Tab 1 (Specs, Schematic, BOM)
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📊 Specs & Data", "📐 Engineering Schematic", "⚖️ Bill of Materials"])
    
    with sub_tab1:
        col_rad, col_ax = st.columns(2)
        
        with col_rad:
            st.subheader("Radial Dimensions & Turns")
            st.text(f"Mode: {res['constraint_type']}")
            
            df_rad = pd.DataFrame({
                "Parameter": [
                    "Cooling Plate Limit (Inner)", 
                    "Cooling Plate Limit (Outer)",
                    "Winding Start (including margin)",
                    "Winding Finish (actual outer radius)",
                    "Turns Per Pancake",
                    "Unused Outer Space Margin"
                ],
                "Value": [
                    f"{plate_in_mm:.1f} mm" if rad_dim_mode == "Diameter" else f"{plate_in_mm * 2.0:.1f} mm (ID equivalent)",
                    f"{plate_out_mm:.1f} mm" if rad_dim_mode == "Diameter" else f"{plate_out_mm * 2.0:.1f} mm (OD equivalent)",
                    f"{inner_winding_boundary:.2f} mm (Radius)",
                    f"{res['b_actual_mm']:.2f} mm (Radius)",
                    f"{res['turns_per_pancake']} turns",
                    f"{res['unused_space_mm']:.2f} mm"
                ]
            })
            st.table(df_rad.set_index("Parameter"))
            st.caption(f"Applied MLT: {res['MLT_m']:.3f} m ({res['shape_type']})")

        with col_ax:
            st.subheader("Axial Stack Dimensions (mm)")
            
            df_ax = pd.DataFrame({
                "Component Stack": ["Total Pancakes (Mylar width)", "Total Cooling Plates", "Total Interface Insul (Fiberglass)", "---", "OVERALL ASSEMBLY HEIGHT"],
                "Value": [
                    f"{res['ax_pancakes_mm']:.2f} mm",
                    f"{res['ax_plates_mm']:.2f} mm",
                    f"{res['ax_insul_mm']:.2f} mm",
                    "",
                    f"{res['ax_total_mm']:.2f} mm"
                ]
            })
            st.table(df_ax.set_index("Component Stack"))

    with sub_tab2:
        st.subheader("Cross-Sectional View (Proportional)")
        st.caption("Visual representation of the stack buildup based on current parameters. Epoxy potting dynamically adapts to Dark/Light mode.")
        
        svg_xml = generate_cross_section_svg(res, a_mm, b_max_mm, rad_dim_mode, plate_margin_mm, cooling_plates_mm, num_pancakes)
        b64 = base64.b64encode(svg_xml.encode('utf-8')).decode("utf-8")
        html = r'<img src="data:image/svg+xml;base64,%s" width="100%%"/>' % b64
        st.markdown(html, unsafe_allow_html=True)

    with sub_tab3:
        st.subheader("Estimated Assembly Weights & Volumes")
        
        col_w1, col_w2 = st.columns(2)
        col_w3, col_w4 = st.columns(2)
        
        col_w1.metric("Total Copper Mass", f"{res['wt_cu_kg']:.1f} kg", f"{res['total_turns']} total turns")
        col_w2.metric("Total Aluminum Mass", f"{res['wt_al_kg']:.1f} kg")
        col_w3.metric("Total Mylar Mass", f"{res['wt_mylar_kg']:.1f} kg")
        col_w4.metric("Potting Epoxy Mass", f"{res['wt_epoxy_kg']:.1f} kg", f"{res['vol_epoxy_L']:.1f} Liters")
        
        st.divider()
        st.metric("ESTIMATED TOTAL POTTED ASSEMBLY MASS", f"{res['wt_total_kg']:.1f} kg", delta_color="off")

# ---------------------------------------------------------------------
# TAB 2: NEW COPPER STRIP MAXIMUM CURRENT CAPACITY
# ---------------------------------------------------------------------
with tool_tab2:
    st.subheader("⚡ Copper Strip Maximum Recommended Current Calculator")
    st.markdown("""
    Analyze thermal limits, recommended current thresholds, and current densities 
    for standard or customized copper strips with parallel liquid/conduction cooling plates.
    """)

    c1, c2, c3 = st.columns(3)

    with c1:
        # Width UI Selection
        w_sel = st.selectbox("Copper Strip Width Preset (W)", options=width_options, index=1, key="strip_w_preset")
        if "Custom" in w_sel:
            if is_metric:
                w_mm = st.number_input("Custom Width (W) [mm]", min_value=0.1, value=38.1, step=1.0)
            else:
                w_thou = st.number_input("Custom Width (W) [thou]", min_value=1.0, value=1500.0, step=100.0)
                w_mm = w_thou * THOU_TO_MM
        else:
            # Extracts numeric preset from index
            preset_idx = width_options.index(w_sel)
            w_mm = width_presets_mm[preset_idx]

    with c2:
        # Thickness UI Selection
        t_sel = st.selectbox("Copper Strip Thickness Preset (Z)", options=thick_options, index=2, key="strip_z_preset")
        if "Custom" in t_sel:
            if is_metric:
                t_mm = st.number_input("Custom Thickness (Z) [mm]", min_value=0.01, value=1.0, step=0.1)
            else:
                t_thou = st.number_input("Custom Thickness (Z) [thou]", min_value=1.0, value=39.4, step=5.0)
                t_mm = t_thou * THOU_TO_MM
        else:
            preset_idx = thick_options.index(t_sel)
            t_mm = thick_presets_mm[preset_idx]

    with c3:
        # Cooling plates inputs
        k_plates = st.number_input("Number of Cooling Plates (K)", min_value=0, value=2, step=1, key="capacity_k")

    # Run capacity calculation
    max_i, density_mm2 = calculate_max_current(w_mm, t_mm, k_plates)

    st.divider()

    # --- DISPLAY METRICS WITH DYNAMIC UNITS ---
    mc1, mc2, mc3 = st.columns(3)

    # Display inputs for verification
    with mc1:
        st.markdown("### 📐 Geometry Verification")
        if is_metric:
            st.markdown(f"**Width ($W$):** {w_mm:.2f} mm")
            st.markdown(f"**Thickness ($Z$):** {t_mm:.4f} mm")
            st.markdown(f"**Cooling Plates ($K$):** {k_plates}")
            st.markdown(f"**Cross Section Area:** {w_mm*t_mm:.3f} mm²")
        else:
            st.markdown(f"**Width ($W$):** {w_mm * MM_TO_THOU:.1f} thou")
            st.markdown(f"**Thickness ($Z$):** {t_mm * MM_TO_THOU:.1f} thou")
            st.markdown(f"**Cooling Plates ($K$):** {k_plates}")
            st.markdown(f"**Cross Section Area:** {(w_mm*t_mm) * (MM_TO_THOU**2):.1f} thou²")

    # Recommended Max Current
    mc2.metric(
        label="🔥 Recommended Max Current",
        value=f"{max_i:.2f} A",
        help="Formula: Recommended Current (A) = 16.86 * Z (mm) * sqrt(K * W (mm))"
    )

    # Current Density
    if is_metric:
        mc3.metric(
            label="⚡ Recommended Current Density",
            value=f"{density_mm2:.3f} A/mm²",
            help="Formula: Recommended Max Current / W * Z (mm²)"
        )
    else:
        # Convert A/mm2 to A/thou2
        # 1 mm = 39.3700787 thou -> 1 mm² = 1550.0031 thou²
        # A/thou² = A/mm² / (MM_TO_THOU²)
        density_thou2 = density_mm2 / (MM_TO_THOU ** 2) if density_mm2 > 0 else 0.0
        mc3.metric(
            label="⚡ Recommended Current Density",
            value=f"{density_thou2:.6f} A/thou²",
            help="Formula: Recommended Max Current / W * Z (thou²)"
        )

    # Mathematical Explanation Card
    st.info("""
    **Equation & Standards Referenced:**
    1. **Recommended Current:** $I_{\text{max}} = 16.86 \times Z \times \sqrt{K \times W}$ (where dimensions are in millimeters).
    2. **Current Density:** $J = \frac{I_{\text{max}}}{\text{Area}}$
    """)
