import json
import io
import os
import sys
import contextlib
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure current working directory is in sys.path
sys.path.insert(0, os.getcwd())

nb_file = "IPL_Matchup_and_Value_Audit.ipynb"
with open(nb_file, "r", encoding="utf-8") as f:
    nb = json.load(f)

global_scope = {}

print("[*] Executing notebook code cells and capturing visual scorecards...")
exec_count = 1

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        print(f"--- Running Cell {i+1} (Exec #{exec_count}) ---")
        
        stdout_capture = io.StringIO()
        plt.close('all')
        
        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(source, global_scope)
        except Exception as e:
            print(f"Error in cell {i+1}: {e}")
            import traceback
            traceback.print_exc()

        stdout_text = stdout_capture.getvalue()
        outputs = []
        
        # If text printed
        if stdout_text:
            outputs.append({
                "output_type": "stream",
                "name": "stdout",
                "text": [line + "\n" for line in stdout_text.splitlines()]
            })
            
        # If matplotlib figures created
        figs = [plt.figure(n) for n in plt.get_fignums()]
        for fig in figs:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), dpi=140)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode('utf-8')
            outputs.append({
                "output_type": "display_data",
                "data": {
                    "image/png": img_b64,
                    "text/plain": ["<Figure size ...>"]
                },
                "metadata": {}
            })
            plt.close(fig)
            
        cell['outputs'] = outputs
        cell['execution_count'] = exec_count
        exec_count += 1

with open(nb_file, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print(f"[+] All notebook cells executed with real outputs & visual cards saved to {nb_file}!")
