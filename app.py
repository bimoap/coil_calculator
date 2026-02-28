import streamlit as st
import numpy as np
import pandas as pd
import base64

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Dynamic Coil Designer", page_icon="⚡", layout="wide")

# --- SVG GENERATION FUNCTION ---
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
            svg_elements.append(f'<line x1="{x1_px+off_px}" y1="{y1_px}" x2="{x2_px+off_px}" y2="{y2_px}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
            svg_elements.append(f'<line x1="{x1_px}" y1="{y1_px}" x2="{x1_px+off_px+5}" y2="{y1_px}" class="dim-line-thin"/>')
            svg_elements.append(f'<line x1="{x2_px}" y1="{y2_px}" x2="{x2_px+off_px+5}" y2="{y2_px}" class="dim-line-thin"/>')
            svg_elements.append(f'<text x="{x1_px+off_px+10}" y="{(y1_px+y2_px)/2}" class="dim-text" dominant-baseline="middle">{label_text}</text>')
        else:
            svg_elements.append(f'<line x1="{x1_px}" y1="{y1_px+off_px}" x2="{x2_px}" y2="{y2_px+off_px}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
            svg_elements.append(f'<line x1="{x1_px}" y1="{y1_px}" x2="{x1_px}" y2="{y1_px+off_px+5}" class="dim-line-thin"/>')
            svg_elements.append(f'<line x1="{x2_px}" y1="{y2_px}" x2="{x2_px}" y2="{y2_px+off_px+5}" class="dim-line-thin"/>')
            svg_elements.append(f'<text x="{(x1_px+x2_px)/2}" y="{y1_px+off_px+15}" class="dim-text" text-anchor="middle">{label_text}</text>')

    # Background / Mold Limits
    svg_elements.append(f'<line x1="{origin_x}" y1="{pad_top}" x2="{origin_x}" y2="{svg_height-pad_bottom}" class="dim-line" stroke-dasharray="5,5"/>')
    draw_rect(a_mm, 0, b_max_mm-a_mm, res['ax_total_mm'], "epoxy", opacity=0.5) 
    svg_elements.append(f'<line x1="{origin_x + a_mm*scale}" y1="{pad_top}" x2="{origin_x + a_mm*scale}" y2="{svg_height-pad_bottom}" class="mold-line"/>')
    svg_elements.append(f'<line x1="{origin_x + b_max_mm*scale}" y1="{pad_top}" x2="{origin_x + b_max_mm*scale}" y2="{svg_height-pad_bottom}" class="mold-line"/>')

    # Draw The Stack
    current_y_mm = 0.0
    pancake_height_mm = res['ax_pancakes_mm'] / num_pancakes
    insul_height_mm = res['ax_insul_mm'] / (num_pancakes * 2)

    plate_idx = 0
    for i in range(num_pancakes):
        if plate_idx < len(cooling_plates_list):
             h_plate = cooling_plates_list[plate_idx]
             draw_rect(a_mm, current_y_mm, b_max_mm-a_mm, h_plate, "al")
             current_y_mm += h_plate
             plate_idx += 1
        
        draw_rect(a_mm, current_y_mm, b_max_mm-a_mm, insul_height_mm, "insul")
        current_y_mm += insul_height_mm

        draw_rect(res['winding_a_mm'], current_y_mm, res['build_mm'], pancake_height_mm, "cu", label="Cu")
        current_y_mm += pancake_height_mm
        
        draw_rect(a_mm, current_y_mm, b_max_mm-a_mm, insul_height_mm, "insul")
        current_y_mm += insul_height_mm
        
    if plate_idx < len(cooling_plates_list):
         h_plate = cooling_plates_list[plate_idx]
         draw_rect(a_mm, current_y_mm, b_max_mm-a_mm, h_plate, "al")
         current_y_mm += h_plate

    # Adaptive Labels
    if rad_dim_mode == "Diameter":
        label_in = f"Plate ID: {a_mm*2:.1f}"
        label_out = f"Plate OD: {b_max_mm*2:.1f}"
        label_wind = f"Winding OD: {res['winding_b_actual_mm']*2:.1f}"
    else:
        label_in = f"Plate Inner Rad: {a_mm:.1f}"
        label_out = f"Plate Max Rad: {b_max_mm:.1f}"
        label_wind = f"Winding Outer Rad: {res['winding_b_actual_mm']:.1f}"

    draw_dim_line(0, 0, a_mm, 0, label_in, offset_mm=-20)
    draw_dim_line(0, 0, res['winding_b_actual_mm'], 0, label_wind, offset_mm=-45)
    draw_dim_line(0, 0, b_max_mm, 0, label_out, offset_mm=-70)
    draw_dim_line(b_max_mm, 0, b_max_mm, res['ax_total_mm'], f"Total Axial: {res['ax_total_mm']:.1f} mm", offset_mm=20, is_vertical=True)

    svg_header = f"""<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .cu {{ fill: #B87333; }}
        .al {{ fill: #A0A0A4; }}
        .epoxy {{ fill: #E0E0E0; }}
        .insul {{ fill: #F0E68C; }}
        .mold-line {{ stroke: #FF0000; stroke-width: 2px; }}
        .box-border {{ stroke: #000000; stroke-width: 1px; }}
        .dim-line {{ stroke: #000000; stroke-width: 1px; }}
        .dim-line-thin {{ stroke: #000000; stroke-width: 0.5px; }}
        .dim-text {{ font-family: Arial; font-size: 14px; fill: #000000; }}
        .label-text {{ font-family: Arial; font-size: 12px; fill: #000000; font-weight: bold; }}
        .title-text {{ font-family: Arial; font-size: 20px; font-weight: bold; fill: #000000; }}
        .arrow-head {{ fill: #000000; }}

        @media (prefers-color-scheme: dark) {{
            .cu {{ fill: #C88343; }}
            .al {{ fill: #606064; }}
            .epoxy {{ fill: #303030; }}
            .insul {{ fill: #B3A95B; }}
            .mold-line {{ stroke: #FF5555; }}
            .box-border {{ stroke: #E0E0E0; }}
            .dim-line {{ stroke: #E0E0E0; }}
            .dim-line-thin {{ stroke: #A0A0A0; }}
            .dim-text {{ fill: #E0E0E0; }}
            .label-text {{ fill: #1E1E1E; }}
            .title-text {{ fill: #FFFFFF; }}
            .arrow-head {{ fill: #E0E0E0; }}
        }}
    </style>
    <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L0,6 L9,3 z" class="arrow-head" />
        </marker>
    </defs>
    <text x="{svg_width/2}" y="30" class="title-text" text-anchor="middle">Dynamic Cross-Section Schematic</text>
    """
    svg_footer = "</svg>"
    
    return svg_header + "".join(svg_elements) + svg_footer


# ================= MAIN STREAMLIT APP =================

st.title("⚡ Pancake Coil Designer & Optimizer")
st.markdown("Design stacked, potted pancake coils. Adjust parameters to see instant results and download a complete BOM.")

# --- SIDEBAR / INPUTS ---
with st.sidebar:
    st.header("⚙️ Design Parameters")
    
    st.subheader("1. Goal & Constraints")
    constraint_mode = st.radio(
        "Optimization Goal:", 
        [1, 2], 
        format_func=lambda x: "Maximize Turns (Fill Space)" if x == 1 else "Target Specific Turns"
    )
    if constraint_mode == 2:
        target_turns_per_pancake = st.number_input("Target Turns per Pancake", min_value=1, value=45, step=1)
    else:
        target_turns_per_pancake = 45 

    st.subheader("2. Radial Geometry (mm)")
    rad_dim_mode = st.radio("Input Mode:", ["Diameter", "Radius"], horizontal=True)
    
    col_r1, col_r2 = st.columns(2)
    
    if rad_dim_mode == "Diameter":
        plate_in_mm = col_r1.number_input("Cooling Plate ID", value=1200.0, step=1.0, format="%.1f")
        plate_out_mm = col_r2.number_input("Cooling Plate OD", value=1400.0, step=1.0, format="%.1f")
        a_mm = plate_in_mm / 2.0
        b_max_mm = plate_out_mm / 2.0
        plate_id_mm = plate_in_mm
        plate_od_mm = plate_out_mm
    else:
        plate_in_mm = col_r1.number_input("Cooling Plate Inner Radius", value=600.0, step=1.0, format="%.1f")
        plate_out_mm = col_r2.number_input("Cooling Plate Outer Radius", value=700.0, step=1.0, format="%.1f")
        a_mm = plate_in_mm
        b_max_mm = plate_out_mm
        plate_id_mm = a_mm * 2.0
        plate_od_mm = b_max_mm * 2.0
        
    plate_margin_mm = st.number_input("Epoxy Edge Margin", value=1.0, step=0.1, format="%.1f", help="Clearance between copper and inner/outer mold walls.")

    st.subheader("3. Stack Config")
    num_pancakes = st.number_input("Number of Pancakes", min_value=1, value=4, step=1)
    plates_input = st.text_input("Cooling Plates (mm, comma-separated)", value="10.0, 8.0, 8.0, 8.0, 10.0", help="Define thickness of plates from bottom to top.")
    
    try:
        cooling_plates_mm = [float(x.strip()) for x in plates_input.split(',')]
    except ValueError:
        st.error("Invalid format for cooling plates. Use numbers separated by commas.")
        st.stop()

    with st.expander("4. Material Details (Advanced)", expanded=False):
        st.markdown("**Conductor & Turn Insulation**")
        col_m1, col_m2 = st.columns(2)
        t_cu_mm = col_m1.number_input("Cu Thickness", value=0.318, format="%.4f")
        w_cu_mm = col_m2.number_input("Cu Width", value=50.8, format="%.2f")
        t_mylar_mm = col_m1.number_input("Mylar Thickness", value=0.0508, format="%.4f")
        w_mylar_mm = col_m2.number_input("Mylar Width", value=52.0, format="%.2f")
        
        st.markdown("**Interface Insulation**")
        col_i1, col_i2 = st.columns(2)
        t_fiberglass_mm = col_i1.number_input("Fiberglass Tk.", value=0.23, format="%.3f")
        fiberglass_layers = col_i2.number_input("Layers/Interface", min_value=1, value=2)
        
        st.markdown("**Other**")
        MLT_input_m = st.number_input("Fixed MLT (m) [0=Auto]", value=0.0, format="%.3f", help="Set >0 for non-circular coils.")

    with st.expander("5. Operating Conditions", expanded=False):
        I_const = st.number_input("Operating Current (A)", value=60.0, step=1.0, format="%.1f")
        dT_water = st.number_input("Allowed Water Temp Rise (°C)", value=10.0, step=1.0, format="%.1f")

    # --- SIGNATURE ---
    st.divider()
    st.caption("⚡ **Pancake Coil Optimizer v1.0**")
    st.caption("Designed by Bimo Adhi Prastya")

# --- CONSTANTS ---
rho = 1.68e-8
density_cu = 8960.0       # kg/m^3
density_al = 2700.0       # kg/m^3
density_epoxy = 1150.0    # kg/m^3
density_mylar = 1390.0    # kg/m^3 
cp_water = 4186.0
rho_water = 1000.0

# ================= CALCULATION LOGIC =================
def optimize_pancake_coil():
    if w_mylar_mm < w_cu_mm:
        st.error(f"**Design Error:** Mylar width ({w_mylar_mm} mm) cannot be smaller than copper width ({w_cu_mm} mm).")
        return None
        
    winding_a_mm = a_mm + plate_margin_mm
    winding_b_max_mm = b_max_mm - plate_margin_mm
    available_build_mm = winding_b_max_mm - winding_a_mm
    layer_thickness_mm = t_cu_mm + t_mylar_mm
    
    if constraint_mode == 1:
        N_per_pancake = int(np.floor(available_build_mm / layer_thickness_mm))
        constraint_type = "Space Constrained (Max Turns)"
    else:
        N_per_pancake = int(target_turns_per_pancake)
        constraint_type = "Turns Constrained"
        
    if N_per_pancake <= 0:
        st.error("**Design Error:** Available radial space is too small for even one turn.")
        return None
        
    actual_build_mm = N_per_pancake * layer_thickness_mm
    winding_b_actual_mm = winding_a_mm + actual_build_mm
    unused_space_mm = available_build_mm - actual_build_mm
    fits_window = actual_build_mm <= available_build_mm
    
    if MLT_input_m > 0:
        MLT_m = MLT_input_m
        shape_type = "Irregular (Fixed MLT)"
    else:
        mean_radius_mm = winding_a_mm + (actual_build_mm / 2.0)
        MLT_m = (2 * np.pi * mean_radius_mm) / 1000.0
        shape_type = "Circular (Dynamic MLT)"
        
    w_pancake_axial_mm = w_mylar_mm
    total_pancakes_axial_mm = num_pancakes * w_pancake_axial_mm
    total_plates_axial_mm = sum(cooling_plates_mm)
    interface_thickness_mm = fiberglass_layers * t_fiberglass_mm
    num_interfaces = num_pancakes * 2
    total_insulation_axial_mm = num_interfaces * interface_thickness_mm
    total_assembly_axial_mm = total_pancakes_axial_mm + total_plates_axial_mm + total_insulation_axial_mm
    
    total_turns = N_per_pancake * num_pancakes
    total_length_m = total_turns * MLT_m
    
    # Weight & Volume Math
    t_cu_m = t_cu_mm / 1000.0
    w_cu_m = w_cu_mm / 1000.0
    A_cu = t_cu_m * w_cu_m
    volume_cu_m3 = A_cu * total_length_m
    weight_cu_kg = volume_cu_m3 * density_cu

    # Mylar Weight Math
    t_mylar_m = t_mylar_mm / 1000.0
    w_mylar_m = w_mylar_mm / 1000.0
    A_mylar = t_mylar_m * w_mylar_m
    volume_mylar_m3 = A_mylar * total_length_m
    weight_mylar_kg = volume_mylar_m3 * density_mylar
    
    r_in_m = a_mm / 1000.0
    plate_r_out_m = (winding_a_mm + actual_build_mm + plate_margin_mm) / 1000.0
    area_plate_m2 = np.pi * (plate_r_out_m**2 - r_in_m**2)
    total_plates_axial_m = total_plates_axial_mm / 1000.0
    volume_al_m3 = area_plate_m2 * total_plates_axial_m
    weight_al_kg = volume_al_m3 * density_al
    
    r_out_max_m = b_max_mm / 1000.0
    v_gross_mold_m3 = np.pi * (r_out_max_m**2 - r_in_m**2) * (total_assembly_axial_mm / 1000.0)
    winding_a_m = winding_a_mm / 1000.0
    winding_b_m = winding_b_actual_mm / 1000.0
    v_winding_block_m3 = np.pi * (winding_b_m**2 - winding_a_m**2) * (total_pancakes_axial_mm / 1000.0)
    v_plates_insul_m3 = np.pi * (plate_r_out_m**2 - r_in_m**2) * ((total_plates_axial_mm + total_insulation_axial_mm) / 1000.0)
    
    volume_epoxy_m3 = max(0.0, v_gross_mold_m3 - v_winding_block_m3 - v_plates_insul_m3)
    vol_epoxy_L = volume_epoxy_m3 * 1000.0
    weight_epoxy_kg = volume_epoxy_m3 * density_epoxy
    
    total_weight_kg = weight_cu_kg + weight_al_kg + weight_mylar_kg + weight_epoxy_kg
    
    # Electrical Math
    R_total = rho * (total_length_m / A_cu)
    V_req = I_const * R_total
    P_total = (I_const ** 2) * R_total
    NI_total = total_turns * I_const
    mass_flow_kg_per_s = P_total / (cp_water * dT_water)
    vol_flow_L_per_min = (mass_flow_kg_per_s / rho_water) * 1000.0 * 60.0
    
    return {
        "constraint_type": constraint_type,
        "winding_a_mm": winding_a_mm,
        "winding_b_actual_mm": winding_b_actual_mm,
        "available_space_mm": available_build_mm,
        "unused_space_mm": unused_space_mm,
        "fits_window": fits_window,
        "turns_per_pancake": N_per_pancake,
        "total_turns": total_turns,
        "MLT_m": MLT_m,
        "shape_type": shape_type,
        "length_m": total_length_m,
        "build_mm": actual_build_mm,
        "wt_cu_kg": weight_cu_kg,
        "wt_al_kg": weight_al_kg,
        "wt_mylar_kg": weight_mylar_kg,
        "vol_epoxy_L": vol_epoxy_L,
        "wt_epoxy_kg": weight_epoxy_kg,
        "wt_total_kg": total_weight_kg,
        "R": R_total,
        "V": V_req,
        "P": P_total,
        "NI": NI_total,
        "Flow_LPM": vol_flow_L_per_min,
        "ax_pancakes_mm": total_pancakes_axial_mm,
        "ax_plates_mm": total_plates_axial_mm,
        "ax_insul_mm": total_insulation_axial_mm,
        "ax_total_mm": total_assembly_axial_mm
    }

# ================= OUTPUT & VISUALIZATION =================

res = optimize_pancake_coil()

if res:
    if not res['fits_window']:
        st.warning(f"⚠️ **Warning:** Winding build exceeds available space by {abs(res['unused_space_mm']):.2f} mm!")
    
    # --- EXPORT DATA LOGIC ---
    export_dict = {
        "Constraint Mode": [res['constraint_type']],
        "Pancakes in Series": [num_pancakes],
        "Turns per Pancake": [res['turns_per_pancake']],
        "Total Turns": [res['total_turns']],
        "Operating Current (A)": [I_const],
        "Ampere-Turns (AT)": [res['NI']],
        "Resistance (Ohms)": [res['R']],
        "Voltage Drop (V)": [res['V']],
        "Power (W)": [res['P']],
        "Required Cooling (LPM)": [res['Flow_LPM']],
        "Input Mode Used": [rad_dim_mode],
        "Cooling Plate ID (mm)": [plate_id_mm],
        "Cooling Plate OD (mm)": [plate_od_mm],
        "Winding Inner Radius (mm)": [res['winding_a_mm']],
        "Winding Inner Diameter (mm)": [res['winding_a_mm'] * 2.0],
        "Radial Build (mm)": [res['build_mm']],
        "Final Outer Radius (mm)": [res['winding_b_actual_mm']],
        "Final Outer Diameter (mm)": [res['winding_b_actual_mm'] * 2.0],
        "Remaining Radial Slack (mm)": [res['unused_space_mm']],
        "Total Axial Height (mm)": [res['ax_total_mm']],
        "Applied MLT (m)": [res['MLT_m']],
        "Total Conductor Length (m)": [res['length_m']],
        "Total Copper Mass (kg)": [res['wt_cu_kg']],
        "Total Aluminum Mass (kg)": [res['wt_al_kg']],
        "Total Mylar Mass (kg)": [res['wt_mylar_kg']],
        "Epoxy Volume (Liters)": [res['vol_epoxy_L']],
        "Potting Epoxy Mass (kg)": [res['wt_epoxy_kg']],
        "Total Assembly Mass (kg)": [res['wt_total_kg']]
    }
    
    df_export = pd.DataFrame(export_dict)
    csv_data = df_export.to_csv(index=False).encode('utf-8')

    # --- TOP LEVEL METRICS & EXPORT BUTTON ---
    col1, col2, col3, col4, col5 = st.columns([1,1,1,1, 1.2])
    col1.metric("Total Ampere-Turns", f"{res['NI']:,.0f} AT")
    col2.metric("Power Dissipation", f"{res['P']:.1f} W")
    col3.metric("Total Resistance", f"{res['R']:.4f} Ω")
    col4.metric("Required Cooling", f"{res['Flow_LPM']:.1f} L/min")
    
    with col5:
        st.write("") 
        st.download_button(
            label="📥 Download CSV Report",
            data=csv_data,
            file_name="pancake_coil_design.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    st.divider()
    
    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 Specs & Data", "📐 Engineering Schematic", "⚖️ Bill of Materials"])
    
    with tab1:
        col_rad, col_ax = st.columns(2)
        
        with col_rad:
            st.subheader("Radial Dimensions (mm)")
            st.text(f"Mode: {res['constraint_type']}")
            
            df_rad = pd.DataFrame({
                "Parameter": [
                    "Cooling Plate Limit (Inner)", 
                    "Winding Inner Border", 
                    "Actual Radial Build", 
                    "Winding Outer Border", 
                    "Cooling Plate Limit (Outer)", 
                    "Remaining 'Slack'"
                ],
                "Value (mm)": [
                    f"{a_mm:.2f} Rad (ID: {plate_id_mm:.2f})",
                    f"{res['winding_a_mm']:.2f} Rad (ID: {res['winding_a_mm']*2:.2f})",
                    f"{res['build_mm']:.2f} (x{num_pancakes})",
                    f"{res['winding_b_actual_mm']:.2f} Rad (OD: {res['winding_b_actual_mm']*2:.2f})",
                    f"{b_max_mm:.2f} Rad (OD: {plate_od_mm:.2f})",
                    f"{res['unused_space_mm']:.2f}"
                ]
            })
            st.table(df_rad.set_index("Parameter"))
            st.caption(f"Applied MLT: {res['MLT_m']:.3f} m ({res['shape_type']})")

        with col_ax:
            st.subheader("Axial Stack Dimensions (mm)")
            
            df_ax = pd.DataFrame({
                "Component Stack": ["Total Pancakes (Mylar width)", "Total Cooling Plates", "Total Interface Insul (Fiberglass)", "---", "OVERALL ASSEMBLY HEIGHT"],
                "Value (mm)": [
                    f"{res['ax_pancakes_mm']:.2f}",
                    f"{res['ax_plates_mm']:.2f}",
                    f"{res['ax_insul_mm']:.2f}",
                    "",
                    f"{res['ax_total_mm']:.2f}"
                ]
            })
            st.table(df_ax.set_index("Component Stack"))

    with tab2:
        st.subheader("Cross-Sectional View (Proportional)")
        st.caption("Visual representation of the stack buildup based on current parameters. Epoxy potting dynamically adapts to Dark/Light mode.")
        
        svg_xml = generate_cross_section_svg(res, a_mm, b_max_mm, rad_dim_mode, plate_margin_mm, cooling_plates_mm, num_pancakes)
        b64 = base64.b64encode(svg_xml.encode('utf-8')).decode("utf-8")
        html = r'<img src="data:image/svg+xml;base64,%s" width="100%%"/>' % b64
        st.markdown(html, unsafe_allow_html=True)

    with tab3:
        st.subheader("Estimated Assembly Weights & Volumes")
        
        col_w1, col_w2 = st.columns(2)
        col_w3, col_w4 = st.columns(2)
        
        col_w1.metric("Total Copper Mass", f"{res['wt_cu_kg']:.1f} kg", f"{res['total_turns']} total turns")
        col_w2.metric("Total Aluminum Mass", f"{res['wt_al_kg']:.1f} kg")
        col_w3.metric("Total Mylar Mass", f"{res['wt_mylar_kg']:.1f} kg")
        col_w4.metric("Potting Epoxy Mass", f"{res['wt_epoxy_kg']:.1f} kg", f"{res['vol_epoxy_L']:.1f} Liters")
        
        st.divider()
        st.metric("ESTIMATED TOTAL POTTED ASSEMBLY MASS", f"{res['wt_total_kg']:.1f} kg", delta_color="off")
