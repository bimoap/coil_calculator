import streamlit as st
import numpy as np
import pandas as pd
import base64
import math

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Coil Engineering Tools", page_icon="⚡", layout="wide")

# --- NAVIGATION ---
st.sidebar.title("🧰 Navigation")
app_mode = st.sidebar.radio("Select Engineering Tool:", ["Dynamic Coil Designer", "Maximum Current & Sizing Calculator"])
st.sidebar.divider()

# =====================================================================
# TOOL 1: DYNAMIC COIL DESIGNER
# =====================================================================
if app_mode == "Dynamic Coil Designer":
    
    # --- SVG GENERATION FUNCTION ---
    def generate_cross_section_svg(res, a_mm, b_max_mm, rad_dim_mode, plate_margin_mm, cooling_plates_list, num_pancakes):
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

        svg_elements.append(f'<line x1="{origin_x}" y1="{pad_top}" x2="{origin_x}" y2="{svg_height-pad_bottom}" class="dim-line" stroke-dasharray="5,5"/>')
        draw_rect(a_mm, 0, b_max_mm-a_mm, res['ax_total_mm'], "epoxy", opacity=0.5) 
        svg_elements.append(f'<line x1="{origin_x + a_mm*scale}" y1="{pad_top}" x2="{origin_x + a_mm*scale}" y2="{svg_height-pad_bottom}" class="mold-line"/>')
        svg_elements.append(f'<line x1="{origin_x + b_max_mm*scale}" y1="{pad_top}" x2="{origin_x + b_max_mm*scale}" y2="{svg_height-pad_bottom}" class="mold-line"/>')

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

    st.title("⚡ Pancake Coil Designer & Optimizer")
    st.markdown("Design stacked, potted pancake coils. Adjust parameters to see instant results and download a complete BOM.")

    with st.sidebar:
        st.header("⚙️ Design Parameters")
        
        constraint_mode = st.radio("Optimization Goal:", [1, 2], index=1, format_func=lambda x: "Maximize Turns (Fill Space)" if x == 1 else "Target Specific Turns")
        if constraint_mode == 2:
            target_turns_per_pancake = st.number_input("Target Turns per Pancake", min_value=1, value=172, step=1)
        else:
            target_turns_per_pancake = 172 

        rad_dim_mode = st.radio("Input Mode:", ["Diameter", "Radius"], horizontal=True)
        col_r1, col_r2 = st.columns(2)
        
        if rad_dim_mode == "Diameter":
            plate_in_mm = col_r1.number_input("Cooling Plate ID", value=100.0, step=1.0, format="%.1f")
            plate_out_mm = col_r2.number_input("Cooling Plate OD", value=259.0, step=1.0, format="%.1f")
            a_mm = plate_in_mm / 2.0
            b_max_mm = plate_out_mm / 2.0
            plate_id_mm = plate_in_mm
            plate_od_mm = plate_out_mm
        else:
            plate_in_mm = col_r1.number_input("Cooling Plate Inner Radius", value=50.0, step=1.0, format="%.1f")
            plate_out_mm = col_r2.number_input("Cooling Plate Outer Radius", value=129.5, step=1.0, format="%.1f")
            a_mm = plate_in_mm
            b_max_mm = plate_out_mm
            plate_id_mm = a_mm * 2.0
            plate_od_mm = b_max_mm * 2.0
            
        plate_margin_mm = st.number_input("Epoxy Edge Margin", value=0.5, step=0.1, format="%.1f")
        num_pancakes = st.number_input("Number of Pancakes", min_value=1, value=2, step=1)
        plates_input = st.text_input("Cooling Plates (mm, comma-separated)", value="6.0, 6.0, 6.0")
        
        try:
            cooling_plates_mm = [float(x.strip()) for x in plates_input.split(',')]
        except ValueError:
            st.error("Invalid format for cooling plates.")
            st.stop()

        with st.expander("4. Material Details", expanded=False):
            col_m1, col_m2 = st.columns(2)
            t_cu_mm = col_m1.number_input("Cu Thickness", value=0.381, format="%.4f")
            w_cu_mm = col_m2.number_input("Cu Width", value=38.1, format="%.2f")
            t_mylar_mm = col_m1.number_input("Mylar Thickness", value=0.0762, format="%.4f")
            w_mylar_mm = col_m2.number_input("Mylar Width", value=38.8, format="%.2f")
            rho_cu = st.number_input("Copper Resistivity (Ω·m)", value=1.71211e-8, format="%.5e")
            col_i1, col_i2 = st.columns(2)
            t_fiberglass_mm = col_i1.number_input("Fiberglass Tk.", value=0.23, format="%.3f")
            fiberglass_layers = col_i2.number_input("Layers/Interface", min_value=1, value=2)
            MLT_input_m = st.number_input("Fixed MLT (m) [0=Auto]", value=0.0, format="%.3f")

        with st.expander("5. Operating Conditions", expanded=False):
            I_const = st.number_input("Operating Current (A)", value=50.0, step=1.0, format="%.1f")
            dT_water = st.number_input("Allowed Temp Rise (°C)", value=10.0, step=1.0, format="%.1f")

        st.divider()
        st.caption("⚡ **Pancake Coil Optimizer v1.0**\nDesigned by Bimo Adhi Prastya")

    # --- CONSTANTS ---
    density_cu = 8960.0       
    density_al = 2700.0       
    density_epoxy = 1150.0    
    density_mylar = 1390.0     
    cp_water = 4186.0
    rho_water = 1000.0

    # ================= CALCULATION LOGIC =================
    def optimize_pancake_coil():
        if w_mylar_mm < w_cu_mm:
            st.error(f"Design Error: Mylar width cannot be smaller than copper width.")
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
            st.error("Design Error: Radial space too small for one turn.")
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
            
        total_pancakes_axial_mm = num_pancakes * w_mylar_mm
        total_plates_axial_mm = sum(cooling_plates_mm)
        total_insulation_axial_mm = (num_pancakes * 2) * (fiberglass_layers * t_fiberglass_mm)
        total_assembly_axial_mm = total_pancakes_axial_mm + total_plates_axial_mm + total_insulation_axial_mm
        
        total_turns = N_per_pancake * num_pancakes
        total_length_m = total_turns * MLT_m
        
        A_cu_mm2 = t_cu_mm * w_cu_mm
        J_A_mm2 = I_const / A_cu_mm2
        weight_cu_kg = ((t_cu_mm/1000.0) * (w_cu_mm/1000.0) * total_length_m) * density_cu
        weight_mylar_kg = ((t_mylar_mm/1000.0) * (w_mylar_mm/1000.0) * total_length_m) * density_mylar
        
        r_in_m = a_mm / 1000.0
        plate_r_out_m = (winding_a_mm + actual_build_mm + plate_margin_mm) / 1000.0
        weight_al_kg = (np.pi * (plate_r_out_m**2 - r_in_m**2) * (total_plates_axial_mm/1000.0)) * density_al
        
        v_gross_mold = np.pi * ((b_max_mm/1000.0)**2 - r_in_m**2) * (total_assembly_axial_mm / 1000.0)
        v_winding = np.pi * ((winding_b_actual_mm/1000.0)**2 - (winding_a_mm/1000.0)**2) * (total_pancakes_axial_mm / 1000.0)
        v_plates_insul = np.pi * (plate_r_out_m**2 - r_in_m**2) * ((total_plates_axial_mm + total_insulation_axial_mm) / 1000.0)
        
        vol_epoxy_L = max(0.0, v_gross_mold - v_winding - v_plates_insul) * 1000.0
        weight_epoxy_kg = (vol_epoxy_L / 1000.0) * density_epoxy
        
        R_total = rho_cu * (total_length_m / ((t_cu_mm/1000.0) * (w_cu_mm/1000.0)))
        V_req = I_const * R_total
        P_total = (I_const ** 2) * R_total
        NI_total = total_turns * I_const
        vol_flow_L_per_min = ((P_total / (cp_water * dT_water)) / rho_water) * 1000.0 * 60.0
        
        return {
            "constraint_type": constraint_type, "winding_a_mm": winding_a_mm, "winding_b_actual_mm": winding_b_actual_mm,
            "unused_space_mm": unused_space_mm, "fits_window": fits_window, "turns_per_pancake": N_per_pancake,
            "total_turns": total_turns, "MLT_m": MLT_m, "shape_type": shape_type, "length_m": total_length_m,
            "length_per_pancake_m": total_length_m / num_pancakes, "A_cu_mm2": A_cu_mm2, "J_A_mm2": J_A_mm2,
            "build_mm": actual_build_mm, "wt_cu_kg": weight_cu_kg, "wt_al_kg": weight_al_kg, "wt_mylar_kg": weight_mylar_kg,
            "vol_epoxy_L": vol_epoxy_L, "wt_epoxy_kg": weight_epoxy_kg, "wt_total_kg": weight_cu_kg + weight_al_kg + weight_mylar_kg + weight_epoxy_kg,
            "R": R_total, "V": V_req, "P": P_total, "NI": NI_total, "Flow_LPM": vol_flow_L_per_min,
            "ax_pancakes_mm": total_pancakes_axial_mm, "ax_plates_mm": total_plates_axial_mm, "ax_insul_mm": total_insulation_axial_mm,
            "ax_total_mm": total_assembly_axial_mm
        }

    res = optimize_pancake_coil()
    if res:
        if not res['fits_window']: st.warning(f"⚠️ Warning: Winding build exceeds available space by {abs(res['unused_space_mm']):.2f} mm!")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Ampere-Turns", f"{res['NI']:,.0f} AT")
        col2.metric("Current Density", f"{res['J_A_mm2']:.2f} A/mm²")
        col3.metric("Power Dissipation", f"{res['P']:.1f} W")
        col4.metric("Resistance", f"{res['R']:.4f} Ω")
        col5.metric("Cooling Flow", f"{res['Flow_LPM']:.1f} LPM")
        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["📊 Specs & Data", "📐 Engineering Schematic", "⚖️ Bill of Materials"])
        with tab1:
            col_rad, col_ax = st.columns(2)
            with col_rad:
                st.subheader("Radial Dimensions")
                st.table(pd.DataFrame({"Parameter": ["Winding Inner", "Actual Radial Build", "Winding Outer", "Remaining 'Slack'"],
                                     "Value": [f"{res['winding_a_mm']:.2f} mm", f"{res['build_mm']:.2f} mm", f"{res['winding_b_actual_mm']:.2f} mm", f"{res['unused_space_mm']:.2f} mm"]}).set_index("Parameter"))
            with col_ax:
                st.subheader("Axial Stack (mm)")
                st.table(pd.DataFrame({"Stack": ["Total Pancakes", "Total Plates", "Total Insul", "OVERALL HEIGHT"],
                                     "Value": [f"{res['ax_pancakes_mm']:.2f} mm", f"{res['ax_plates_mm']:.2f} mm", f"{res['ax_insul_mm']:.2f} mm", f"{res['ax_total_mm']:.2f} mm"]}).set_index("Stack"))
        with tab2:
            st.subheader("Cross-Sectional View")
            svg_xml = generate_cross_section_svg(res, a_mm, b_max_mm, rad_dim_mode, plate_margin_mm, cooling_plates_mm, num_pancakes)
            st.markdown(r'<img src="data:image/svg+xml;base64,%s" width="100%%"/>' % base64.b64encode(svg_xml.encode('utf-8')).decode("utf-8"), unsafe_allow_html=True)
        with tab3:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Copper Mass", f"{res['wt_cu_kg']:.1f} kg")
            c2.metric("Aluminum Mass", f"{res['wt_al_kg']:.1f} kg")
            c3.metric("Mylar Mass", f"{res['wt_mylar_kg']:.1f} kg")
            c4.metric("Epoxy Mass", f"{res['wt_epoxy_kg']:.1f} kg")
            st.metric("TOTAL MASS", f"{res['wt_total_kg']:.1f} kg")


# =====================================================================
# TOOL 2: MAXIMUM CURRENT & SIZING CALCULATOR
# =====================================================================
elif app_mode == "Maximum Current & Sizing Calculator":
    
    st.title("⚡ Coil Current & Sizing Tool")
    
    # --- FORMULAS PROMINENTLY AT THE TOP ---
    st.info("### Governing Formulas")
    st.latex(r"I_{max} = 16.86 \times Z \times \sqrt{K \times W}")
    st.latex(r"W = \frac{(I_{max} / (16.86 \times Z))^2}{K}")
    st.latex(r"Z = \frac{I_{max}}{16.86 \times \sqrt{K \times W}}")
    st.caption("*Where: $I$ = Current (A), $W$ = Width (mm), $Z$ = Thickness (mm), $K$ = Cooling Plates*")
    st.divider()

    # 1. Mode Selection
    calc_mode = st.radio("What do you want to calculate?", 
                         ["Maximum Current", "Required Copper Width", "Required Copper Thickness"], 
                         horizontal=True)
    
    # 2. Unit Toggle
    unit = st.radio("Measurement Units:", ["Metric (mm)", "Imperial (inch/thou)"], horizontal=True)

    if unit == "Metric (mm)":
        width_opts = ["50.8", "38.1"]
        thick_opts = ["0.787", "1.0", "1.194", "1.245", "1.372"]
    else:
        width_opts = ["2.0", "1.5"]
        thick_opts = ["31", "39.37", "47", "49", "54"]

    # 3. Input Fields
    col1, col2 = st.columns(2)

    with col1:
        # Show inputs based on the calculation mode
        if calc_mode in ["Maximum Current", "Required Copper Thickness"]:
            w_input = st.selectbox("Copper Strip Width (W):", width_opts) if calc_mode == "Maximum Current" else st.number_input("Copper Strip Width (W):", value=float(width_opts[0]), format="%.3f")
            
        if calc_mode in ["Maximum Current", "Required Copper Width"]:
            z_input = st.selectbox("Copper Strip Thickness (Z):", thick_opts) if calc_mode == "Maximum Current" else st.number_input("Copper Strip Thickness (Z):", value=float(thick_opts[1]), format="%.3f")
            
        if calc_mode in ["Required Copper Width", "Required Copper Thickness"]:
            i_input = st.number_input("Target Maximum Current (A):", value=50.0, min_value=0.1, step=1.0)

    with col2:
        # Strictly limit to 1 or 2, default to index 1 (which is 2)
        k = st.selectbox("Number of Cooling Plates (K):", options=[1, 2], index=1)

    # 4. Calculation Logic
    if st.button(f"Calculate {calc_mode}", type="primary"):
        
        # Helper: Convert input to metric for math
        def to_metric_w(val): return val * 25.4 if unit == "Imperial (inch/thou)" else val
        def to_metric_z(val): return val * 0.0254 if unit == "Imperial (inch/thou)" else val
        
        # Helper: Convert output back to imperial if needed
        def from_metric_w(val): return val / 25.4 if unit == "Imperial (inch/thou)" else val
        def from_metric_z(val): return val / 0.0254 if unit == "Imperial (inch/thou)" else val
        
        try:
            if calc_mode == "Maximum Current":
                w_mm = to_metric_w(float(w_input))
                z_mm = to_metric_z(float(z_input))
                
                max_c = 16.86 * z_mm * math.sqrt(k * w_mm)
                density = max_c / (w_mm * z_mm)
                
                st.success(f"**Recommended Max Current:** {max_c:.2f} A")
                st.info(f"**Current Density:** {density:.2f} A/mm²")
                
            elif calc_mode == "Required Copper Width":
                z_mm = to_metric_z(float(z_input))
                
                # Formula: W = (I / (16.86 * Z))^2 / K
                w_req_mm = (i_input / (16.86 * z_mm))**2 / k
                w_final = from_metric_w(w_req_mm)
                
                density = i_input / (w_req_mm * z_mm)
                unit_label = "inches" if unit == "Imperial (inch/thou)" else "mm"
                
                st.success(f"**Required Copper Width:** {w_final:.3f} {unit_label}")
                st.info(f"**Resulting Current Density:** {density:.2f} A/mm²")
                
            elif calc_mode == "Required Copper Thickness":
                w_mm = to_metric_w(float(w_input))
                
                # Formula: Z = I / (16.86 * sqrt(K * W))
                z_req_mm = i_input / (16.86 * math.sqrt(k * w_mm))
                z_final = from_metric_z(z_req_mm)
                
                density = i_input / (w_mm * z_req_mm)
                unit_label = "thou" if unit == "Imperial (inch/thou)" else "mm"
                
                st.success(f"**Required Copper Thickness:** {z_final:.3f} {unit_label}")
                st.info(f"**Resulting Current Density:** {density:.2f} A/mm²")
                
        except Exception as e:
            st.error("Error in calculation. Please check your inputs.")

    # --- SIGNATURE ---
    st.divider()
    st.caption("⚡ **Coil Current & Sizing Tool v1.1**\nDesigned by Bimo Adhi Prastya")
