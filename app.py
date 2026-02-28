# --- SVG GENERATION FUNCTION ---
def generate_cross_section_svg(res, a_mm, b_max_mm, plate_margin_mm, cooling_plates_list, num_pancakes):
    """Generates a proportional SVG cross-section drawing with dynamic Light/Dark mode."""
    
    # Scale factor to convert physical mm to SVG pixels so it fits on screen
    max_dim_mm = max(b_max_mm * 1.1, res['ax_total_mm'] * 1.1)
    target_svg_size = 600 
    scale = target_svg_size / max_dim_mm 
    
    # Margins for labels
    pad_left = 80
    pad_right = 150
    pad_top = 50
    pad_bottom = 50

    # Calculate canvas dimensions
    svg_width = (b_max_mm * scale) + pad_left + pad_right
    svg_height = (res['ax_total_mm'] * scale) + pad_top + pad_bottom
    
    # Origin point (Center line at bottom)
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

    # Add Dimension Labels
    draw_dim_line(0, 0, a_mm, 0, f"Inner: {a_mm:.1f}", offset_mm=-20)
    draw_dim_line(0, 0, res['winding_b_actual_mm'], 0, f"Outer: {res['winding_b_actual_mm']:.1f}", offset_mm=-45)
    draw_dim_line(0, 0, b_max_mm, 0, f"Mold: {b_max_mm:.1f}", offset_mm=-70)
    draw_dim_line(b_max_mm, 0, b_max_mm, res['ax_total_mm'], f"Total Axial: {res['ax_total_mm']:.1f} mm", offset_mm=20, is_vertical=True)

    # SVG Header with embedded CSS for Light/Dark Mode
    svg_header = f"""<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        /* Light Mode (Default) */
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

        /* Dark Mode Override */
        @media (prefers-color-scheme: dark) {{
            .cu {{ fill: #C88343; }} /* Brighter copper */
            .al {{ fill: #606064; }} /* Darker aluminum */
            .epoxy {{ fill: #303030; }} /* Dark gray resin */
            .insul {{ fill: #B3A95B; }} /* Muted fiberglass */
            .mold-line {{ stroke: #FF5555; }}
            .box-border {{ stroke: #E0E0E0; }}
            .dim-line {{ stroke: #E0E0E0; }}
            .dim-line-thin {{ stroke: #A0A0A0; }}
            .dim-text {{ fill: #E0E0E0; }}
            .label-text {{ fill: #1E1E1E; }} /* Keeps contrast inside lighter boxes */
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
    
    return svg_header + "".join(svg_elements) + svg_footer# --- SVG GENERATION FUNCTION ---
def generate_cross_section_svg(res, a_mm, b_max_mm, plate_margin_mm, cooling_plates_list, num_pancakes):
    """Generates a proportional SVG cross-section drawing with dynamic Light/Dark mode."""
    
    # Scale factor to convert physical mm to SVG pixels so it fits on screen
    max_dim_mm = max(b_max_mm * 1.1, res['ax_total_mm'] * 1.1)
    target_svg_size = 600 
    scale = target_svg_size / max_dim_mm 
    
    # Margins for labels
    pad_left = 80
    pad_right = 150
    pad_top = 50
    pad_bottom = 50

    # Calculate canvas dimensions
    svg_width = (b_max_mm * scale) + pad_left + pad_right
    svg_height = (res['ax_total_mm'] * scale) + pad_top + pad_bottom
    
    # Origin point (Center line at bottom)
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

    # Add Dimension Labels
    draw_dim_line(0, 0, a_mm, 0, f"Inner: {a_mm:.1f}", offset_mm=-20)
    draw_dim_line(0, 0, res['winding_b_actual_mm'], 0, f"Outer: {res['winding_b_actual_mm']:.1f}", offset_mm=-45)
    draw_dim_line(0, 0, b_max_mm, 0, f"Mold: {b_max_mm:.1f}", offset_mm=-70)
    draw_dim_line(b_max_mm, 0, b_max_mm, res['ax_total_mm'], f"Total Axial: {res['ax_total_mm']:.1f} mm", offset_mm=20, is_vertical=True)

    # SVG Header with embedded CSS for Light/Dark Mode
    svg_header = f"""<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        /* Light Mode (Default) */
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

        /* Dark Mode Override */
        @media (prefers-color-scheme: dark) {{
            .cu {{ fill: #C88343; }} /* Brighter copper */
            .al {{ fill: #606064; }} /* Darker aluminum */
            .epoxy {{ fill: #303030; }} /* Dark gray resin */
            .insul {{ fill: #B3A95B; }} /* Muted fiberglass */
            .mold-line {{ stroke: #FF5555; }}
            .box-border {{ stroke: #E0E0E0; }}
            .dim-line {{ stroke: #E0E0E0; }}
            .dim-line-thin {{ stroke: #A0A0A0; }}
            .dim-text {{ fill: #E0E0E0; }}
            .label-text {{ fill: #1E1E1E; }} /* Keeps contrast inside lighter boxes */
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
