import sys
import tkinter as tk
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from utils import parse_sop, build_kmap, ascii_kmap, minimize_sop, _AXIS_SPLIT, get_variables

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SOP2KApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SOP2K – K-map Generator")
        self.geometry("1100x800")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(self.sidebar, text="SOP2K", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 10))
        ctk.CTkLabel(self.sidebar, text="Sum-of-Products to K-map", font=ctk.CTkFont(size=14, slant="italic")).pack(pady=(0, 30))

        # Input
        self.input_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20)
        ctk.CTkLabel(self.input_frame, text="SOP Expression:").pack(anchor="w")
        self.sop_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. xy + x'y'z", height=35)
        self.sop_entry.pack(fill="x", pady=(5, 15))
        self.sop_entry.insert(0, "xy + x'y'z")
        ctk.CTkLabel(self.input_frame, text="Variables (optional):").pack(anchor="w")
        self.vars_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. x y z", height=35)
        self.vars_entry.pack(fill="x", pady=(5, 20))

        # Buttons
        ctk.CTkButton(self.sidebar, text="Generate K-map", command=self.generate, height=40, font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self.sidebar, text="Clear", command=self.clear, fg_color="transparent", border_width=1).pack(fill="x", padx=20, pady=5)

        # Output
        ctk.CTkLabel(self.sidebar, text="Analysis & ASCII K-map:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(30, 0))
        self.output_text = ctk.CTkTextbox(self.sidebar, wrap="none", font=("Courier New", 12))
        self.output_text.pack(fill="both", expand=True, padx=20, pady=10)

        # Plot
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1a1a1a")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        ctk.CTkLabel(self.main_frame, text="Graphical Visualization", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        self.canvas_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.quit()
        plt.close('all')
        self.destroy()
        sys.exit(0)

    def clear(self):
        self.sop_entry.delete(0, tk.END)
        self.vars_entry.delete(0, tk.END)
        self.output_text.delete("1.0", tk.END)
        if self.canvas: self.canvas.get_tk_widget().destroy()
        self.canvas = None
        plt.close('all')

    def generate(self):
        expr = self.sop_entry.get().strip()
        var_str = self.vars_entry.get().strip()
        if not expr:
            self.update_output("Error: Please enter an SOP expression.")
            return
        try:
            variables = var_str.split() if var_str else None
            vars_list, minterms = parse_sop(expr, variables)
            min_sop_str = minimize_sop(vars_list, minterms)
            
            n_vars = len(vars_list)
            n_row_bits, n_col_bits = _AXIS_SPLIT[n_vars]
            row_vars, col_vars = "".join(vars_list[:n_row_bits]), "".join(vars_list[n_row_bits:])
            kmap, row_labels, col_labels, _, _ = build_kmap(minterms, n_vars)

            output_msg = [
                f"Variables: {', '.join(vars_list)}",
                f"Minterms (bin): {[format(m, f'0{n_vars}b') for m in minterms]}",
                f"Simplified SOP: {min_sop_str}",
                "",
                "--- ASCII K-map ---",
                ascii_kmap(kmap, row_labels, col_labels, row_vars, col_vars)
            ]
            self.update_output("\n".join(output_msg))
            self.plot_graph(kmap, row_labels, col_labels, row_vars, col_vars)
        except Exception as e:
            self.update_output(f"Error: {str(e)}")

    def update_output(self, text):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)

    def plot_graph(self, kmap, row_labels, col_labels, row_vars, col_vars):
        plt.close('all')
        if self.canvas: self.canvas.get_tk_widget().destroy()
        n_rows, n_cols = kmap.shape
        
        # Adjust for 1-variable case where n_cols might be 0 conceptually
        # but numpy array will be (2, 1) or similar if col_bits=0
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(6, 5), dpi=100)
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#1a1a1a')
        ax.set_aspect('equal')
        
        for r in range(n_rows + 1): ax.axhline(r, color='#444444', lw=1.5)
        for c in range(n_cols + 1): ax.axvline(c, color='#444444', lw=1.5)
        for r in range(n_rows):
            for c in range(n_cols):
                y_pos = n_rows - 1 - r
                if kmap[r, c] == 1:
                    ax.add_patch(plt.Rectangle((c, y_pos), 1, 1, color='#1f77b4', alpha=0.6))
                ax.text(c + 0.5, y_pos + 0.5, str(kmap[r, c]), va='center', ha='center', fontsize=16, color='white', fontweight='bold')

        ax.set_xticks(np.arange(n_cols) + 0.5)
        ax.set_xticklabels(col_labels, fontsize=10, color='#aaaaaa')
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        ax.set_xlabel(col_vars, fontsize=12, fontweight='bold', color='white', labelpad=10)
        ax.set_yticks(np.arange(n_rows) + 0.5)
        ax.set_yticklabels(row_labels[::-1], fontsize=10, color='#aaaaaa')
        ax.set_ylabel(row_vars, fontsize=12, fontweight='bold', color='white', labelpad=10)
        for spine in ax.spines.values(): spine.set_visible(False)
        plt.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    SOP2KApp().mainloop()
