import math
import tkinter as tk
from tkinter import ttk

def calculate_max_current(w_mm, z_mm, k):
    """
    Core calculation for maximum current and current density.
    w_mm: Width in mm
    z_mm: Thickness in mm
    k: Number of cooling plates
    """
    if w_mm <= 0 or z_mm <= 0 or k < 0:
        return 0.0, 0.0
    
    # Recommended max current (Ampere) = 16.86 x Z x sqrt(K x W)
    max_current = 16.86 * z_mm * math.sqrt(k * w_mm)
    
    # Current density (A/mm2) = Current / (W x Z)
    current_density = max_current / (w_mm * z_mm)
    
    return max_current, current_density

class CoilCurrentTool(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="15")
        
        # Variables to store user inputs
        self.unit_var = tk.StringVar(value="Metric")
        self.width_var = tk.StringVar()
        self.thickness_var = tk.StringVar()
        self.plates_var = tk.IntVar(value=1)
        
        self.result_current = tk.StringVar(value="Recommended Max Current: 0.00 A")
        self.result_density = tk.StringVar(value="Current Density: 0.00 A/mm²")
        
        self.setup_ui()
        self.update_dropdowns()
        
    def setup_ui(self):
        # 1. Unit Toggle Selection
        ttk.Label(self, text="Measurement Units:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        unit_frame = ttk.Frame(self)
        unit_frame.grid(row=0, column=1, sticky="w", pady=5)
        ttk.Radiobutton(unit_frame, text="Metric (mm)", variable=self.unit_var, value="Metric", command=self.update_dropdowns).pack(side="left", padx=5)
        ttk.Radiobutton(unit_frame, text="Imperial (inch/thou)", variable=self.unit_var, value="Imperial", command=self.update_dropdowns).pack(side="left", padx=5)
        
        # 2. Copper Strip Width (W)
        ttk.Label(self, text="Copper Strip Width (W):").grid(row=1, column=0, sticky="w")
        self.width_cb = ttk.Combobox(self, textvariable=self.width_var, width=15)
        self.width_cb.grid(row=1, column=1, sticky="ew", pady=5)
        
        # 3. Copper Strip Thickness (Z)
        ttk.Label(self, text="Copper Strip Thickness (Z):").grid(row=2, column=0, sticky="w")
        self.thickness_cb = ttk.Combobox(self, textvariable=self.thickness_var, width=15)
        self.thickness_cb.grid(row=2, column=1, sticky="ew", pady=5)
        
        # 4. Number of Cooling Plates (K)
        ttk.Label(self, text="Number of Cooling Plates (K):").grid(row=3, column=0, sticky="w")
        self.plates_entry = ttk.Entry(self, textvariable=self.plates_var, width=17)
        self.plates_entry.grid(row=3, column=1, sticky="ew", pady=5)
        
        # 5. Calculate Button
        calc_btn = ttk.Button(self, text="Calculate Limit", command=self.calculate)
        calc_btn.grid(row=4, column=0, columnspan=2, pady=15)
        
        # 6. Results Display
        ttk.Label(self, textvariable=self.result_current, font=("Arial", 12, "bold"), foreground="blue").grid(row=5, column=0, columnspan=2, pady=2)
        ttk.Label(self, textvariable=self.result_density, font=("Arial", 11)).grid(row=6, column=0, columnspan=2, pady=2)

    def update_dropdowns(self):
        """Updates dropdown options based on selected unit toggle"""
        if self.unit_var.get() == "Metric":
            self.width_cb['values'] = ("50.8", "38.1")
            self.thickness_cb['values'] = ("0.787", "1.0", "1.194", "1.245", "1.372")
            
            # Default selections
            self.width_var.set("50.8")
            self.thickness_var.set("1.0")
        else:
            # Equivalent imperial values
            self.width_cb['values'] = ("2.0", "1.5") # inches
            self.thickness_cb['values'] = ("31", "39.37", "47", "49", "54") # thou
            
            # Default selections
            self.width_var.set("2.0")
            self.thickness_var.set("39.37")
            
    def calculate(self):
        try:
            w_input = float(self.width_var.get())
            z_input = float(self.thickness_var.get())
            k = int(self.plates_var.get())
            
            # Always convert back to metric for the formula calculation
            if self.unit_var.get() == "Imperial":
                w_mm = w_input * 25.4         # inches to mm
                z_mm = z_input * 0.0254       # thou to mm
            else:
                w_mm = w_input
                z_mm = z_input
                
            max_c, density = calculate_max_current(w_mm, z_mm, k)
            
            self.result_current.set(f"Recommended Max Current: {max_c:.2f} A")
            self.result_density.set(f"Current Density: {density:.2f} A/mm²")
            
        except ValueError:
            self.result_current.set("Error: Invalid Input")
            self.result_density.set("Please ensure all fields are numbers.")

# Standalone execution for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Coil Maximum Current Tool")
    app = CoilCurrentTool(root)
    app.pack(fill="both", expand=True)
    
    # Optional: Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    root.mainloop()
