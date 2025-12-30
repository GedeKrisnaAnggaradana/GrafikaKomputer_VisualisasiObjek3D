import tkinter as tk
from tkinter import filedialog, messagebox
import math
import os

# ==============================================================================
# BAGIAN 1: KONFIGURASI (SETTINGS)
# ==============================================================================
class Config:
    WIDTH = 900
    HEIGHT = 600
    BG_COLOR = "#000000"       # Hitam
    LINE_COLOR = "#00FF00"     # Hijau (Matrix style)
    VERTEX_COLOR = "#0055FF"   # Biru
    FOCAL_LENGTH = 400
    CAMERA_DIST = 500

# ==============================================================================
# BAGIAN 2: LIBRARY MATEMATIKA (MATH LIB)
# ==============================================================================
class MathLib:
    """Menangani operasi matriks murni tanpa ketergantungan pada UI."""
    
    @staticmethod
    def multiply_matrix(v, m):
        """Perkalian Vektor (1x4) x Matriks (4x4)."""
        return [
            v[0]*m[0][0] + v[1]*m[1][0] + v[2]*m[2][0] + v[3]*m[3][0],
            v[0]*m[0][1] + v[1]*m[1][1] + v[2]*m[2][1] + v[3]*m[3][1],
            v[0]*m[0][2] + v[1]*m[1][2] + v[2]*m[2][2] + v[3]*m[3][2],
            v[0]*m[0][3] + v[1]*m[1][3] + v[2]*m[2][3] + v[3]*m[3][3]
        ]

    @staticmethod
    def get_transform_matrix(type, val):
        """Menghasilkan matriks transformasi berdasarkan tipe."""
        # Matriks Identitas
        matrix = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]

        if type == 'rotX':
            c, s = math.cos(val), math.sin(val)
            matrix = [[1,0,0,0], [0,c,-s,0], [0,s,c,0], [0,0,0,1]]
        elif type == 'rotY':
            c, s = math.cos(val), math.sin(val)
            matrix = [[c,0,s,0], [0,1,0,0], [-s,0,c,0], [0,0,0,1]]
        elif type == 'rotZ':
            c, s = math.cos(val), math.sin(val)
            matrix = [[c,-s,0,0], [s,c,0,0], [0,0,1,0], [0,0,0,1]]
        elif type == 'scale':
            matrix = [[val,0,0,0], [0,val,0,0], [0,0,val,0], [0,0,0,1]]
        elif type == 'trans':
            dx, dy, dz = val
            matrix = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [dx,dy,dz,1]]
            
        return matrix

    @staticmethod
    def project_3d_to_2d(x, y, z, width, height):
        """Mengubah koordinat dunia 3D menjadi koordinat layar 2D."""
        if (z + Config.CAMERA_DIST) <= 0:
            return None # Clipping (di belakang kamera)
        
        scale = Config.FOCAL_LENGTH / (z + Config.CAMERA_DIST)
        cx, cy = width // 2, height // 2
        
        px = int(x * scale + cx)
        py = int(y * scale + cy)
        return (px, py)

# ==============================================================================
# BAGIAN 3: ALGORITMA RASTERISASI (GRAPHICS ALGORITHM)
# ==============================================================================
class Rasterizer:
    """Menangani manipulasi pixel langsung ke buffer gambar."""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Image buffer Tkinter (diset nanti oleh App)
        self.buffer = None 

    def set_buffer(self, photo_image):
        self.buffer = photo_image

    def clear_screen(self):
        if self.buffer:
            self.buffer.put(Config.BG_COLOR, to=(0, 0, self.width, self.height))

    def put_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer.put(color, (x, y))

    def draw_bresenham_line(self, x0, y0, x1, y1, color):
        """Algoritma Garis Bresenham (Integer Arithmetic)."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.put_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_thick_point(self, x, y, color):
        """Menggambar titik tebal (3x3 pixel) manual."""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                self.put_pixel(x + dx, y + dy, color)

# ==============================================================================
# BAGIAN 4: INTI PROGRAM (CORE LOGIC)
# ==============================================================================
class World3D:
    """Menyimpan state dunia 3D (Vertices & Edges)."""
    def __init__(self):
        self.vertices = []
        self.edges = []
        self.generate_dummy_files()

    def generate_dummy_files(self):
        """Auto-create file jika tidak ada."""
        if not os.path.exists("vertices.txt"):
            with open("vertices.txt", "w") as f:
                f.write("""-100,-100,-100\n100,-100,-100\n100,100,-100\n-100,100,-100\n-100,-100,100\n100,-100,100\n100,100,100\n-100,100,100""")
        if not os.path.exists("edges.txt"):
            with open("edges.txt", "w") as f:
                f.write("""0,1\n1,2\n2,3\n3,0\n4,5\n5,6\n6,7\n7,4\n0,4\n1,5\n2,6\n3,7""")

    def load_vertices_from_file(self, filepath):
        temp_v = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    p = line.strip().split(',')
                    temp_v.append([float(p[0]), float(p[1]), float(p[2]), 1.0])
        self.vertices = temp_v
        return len(self.vertices)

    def load_edges_from_file(self, filepath):
        temp_e = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    p = line.strip().split(',')
                    temp_e.append((int(p[0]), int(p[1])))
        self.edges = temp_e
        return len(self.edges)

    def apply_transformation(self, trans_type, val):
        """Menerapkan transformasi ke seluruh vertices."""
        if not self.vertices: return
        
        matrix = MathLib.get_transform_matrix(trans_type, val)
        new_vertices = []
        for v in self.vertices:
            new_vertices.append(MathLib.multiply_matrix(v, matrix))
        self.vertices = new_vertices

# ==============================================================================
# BAGIAN 5: APLIKASI GUI (APP) - [FIXED]
# ==============================================================================
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Modular 3D Engine - Pixel Manipulation")
        
        # 1. Inisialisasi Modul
        self.world = World3D()
        self.rasterizer = Rasterizer(Config.WIDTH, Config.HEIGHT)
        
        # 2. State Animasi & Referensi Tombol (DIPINDAHKAN KE ATAS)
        # Penting: Harus didefinisikan sebelum _setup_controls dipanggil
        self.is_animating = False
        self.anim_states = {
            'rot_x': False, 'rot_y': False, 'rot_z': False,    
            'mov_l': False, 'mov_r': False, 'mov_u': False, 'mov_d': False,
            'scl_up': False, 'scl_dn': False
        }
        self.btn_refs = {} 

        # 3. Setup UI (Baru dipanggil setelah btn_refs siap)
        self._setup_canvas()
        self._setup_controls()

    def _setup_canvas(self):
        """Setup area gambar Tkinter."""
        self.canvas = tk.Canvas(self.root, width=Config.WIDTH, height=Config.HEIGHT, bg="black")
        self.canvas.pack(side=tk.LEFT)
        
        # Inisialisasi Buffer Gambar
        self.image_buffer = tk.PhotoImage(width=Config.WIDTH, height=Config.HEIGHT)
        self.canvas.create_image((Config.WIDTH//2, Config.HEIGHT//2), image=self.image_buffer, state="normal")
        
        # Hubungkan buffer ke Rasterizer
        self.rasterizer.set_buffer(self.image_buffer)

    def _setup_controls(self):
        """Membuat panel kontrol."""
        panel = tk.Frame(self.root, width=250, bg="#222")
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(panel, text="KONTROL UTAMA", fg="white", bg="#222", font=("Arial", 12, "bold")).pack(pady=10)

        # File Controls
        fr_file = tk.LabelFrame(panel, text="Data Input", fg="cyan", bg="#222")
        fr_file.pack(fill=tk.X, padx=5)
        tk.Button(fr_file, text="Load Vertices", command=self.action_load_vertices).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(fr_file, text="Load Edges", command=self.action_load_edges).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Reset
        tk.Button(panel, text="RENDER / RESET", command=self.render_scene, bg="#27ae60", fg="white").pack(fill=tk.X, padx=5, pady=10)

        # Animation Controls
        self._create_toggle_group(panel, "Rotasi", [("X", 'rot_x'), ("Y", 'rot_y'), ("Z", 'rot_z')])
        self._create_toggle_group(panel, "Translasi", [("←", 'mov_l'), ("→", 'mov_r'), ("↑", 'mov_u'), ("↓", 'mov_d')])
        self._create_toggle_group(panel, "Skala", [("Zm+", 'scl_up'), ("Zm-", 'scl_dn')])
        
        # Master Switch
        self.btn_master = tk.Button(panel, text="▶ START ANIMASI", command=self.toggle_animation, bg="#e67e22", fg="white", font=("bold"))
        self.btn_master.pack(fill=tk.X, padx=5, pady=20)

    def _create_toggle_group(self, parent, title, items):
        fr = tk.LabelFrame(parent, text=title, fg="white", bg="#222")
        fr.pack(fill=tk.X, padx=5, pady=2)
        for text, key in items:
            btn = tk.Button(fr, text=text, width=4, font=("Arial", 8), command=lambda k=key: self.toggle_state(k))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            self.btn_refs[key] = btn
            self.update_btn_color(key)

    # --- ACTION HANDLERS ---
    def action_load_vertices(self):
        path = filedialog.askopenfilename(initialdir=os.getcwd(), title="Pilih File Vertices")
        if path:
            try:
                count = self.world.load_vertices_from_file(path)
                print(f"Loaded {count} vertices.")
            except Exception as e: messagebox.showerror("Error", str(e))

    def action_load_edges(self):
        path = filedialog.askopenfilename(initialdir=os.getcwd(), title="Pilih File Edges")
        if path:
            try:
                count = self.world.load_edges_from_file(path)
                self.render_scene()
            except Exception as e: messagebox.showerror("Error", str(e))

    def toggle_state(self, key):
        self.anim_states[key] = not self.anim_states[key]
        self.update_btn_color(key)

    def update_btn_color(self, key):
        color = "#e74c3c" if self.anim_states[key] else "#ecf0f1"
        self.btn_refs[key].config(bg=color)

    def toggle_animation(self):
        self.is_animating = not self.is_animating
        if self.is_animating:
            self.btn_master.config(text="⏹ STOP", bg="#c0392b")
            self.loop_animation()
        else:
            self.btn_master.config(text="▶ START", bg="#e67e22")

    # --- RENDER LOOP ---
    def loop_animation(self):
        if self.is_animating:
            # Apply Transformations
            if self.anim_states['rot_x']: self.world.apply_transformation('rotX', 0.05)
            if self.anim_states['rot_y']: self.world.apply_transformation('rotY', 0.05)
            if self.anim_states['rot_z']: self.world.apply_transformation('rotZ', 0.05)
            
            if self.anim_states['mov_l']: self.world.apply_transformation('trans', (-5, 0, 0))
            if self.anim_states['mov_r']: self.world.apply_transformation('trans', (5, 0, 0))
            if self.anim_states['mov_u']: self.world.apply_transformation('trans', (0, -5, 0))
            if self.anim_states['mov_d']: self.world.apply_transformation('trans', (0, 5, 0))

            if self.anim_states['scl_up']: self.world.apply_transformation('scale', 1.02)
            if self.anim_states['scl_dn']: self.world.apply_transformation('scale', 0.98)
            
            self.render_scene()
            self.root.after(40, self.loop_animation)

    def render_scene(self):
        if not self.world.vertices or not self.world.edges: return
        
        self.rasterizer.clear_screen()
        
        # 1. Projection Pipeline
        screen_points = []
        for v in self.world.vertices:
            # Menggunakan MathLib untuk proyeksi
            p = MathLib.project_3d_to_2d(v[0], v[1], v[2], Config.WIDTH, Config.HEIGHT)
            screen_points.append(p)

        # 2. Rasterization (Lines)
        for edge in self.world.edges:
            p1 = screen_points[edge[0]]
            p2 = screen_points[edge[1]]
            if p1 and p2:
                self.rasterizer.draw_bresenham_line(p1[0], p1[1], p2[0], p2[1], Config.LINE_COLOR)

        # 3. Rasterization (Vertices - Blue Dots)
        for p in screen_points:
            if p:
                self.rasterizer.draw_thick_point(p[0], p[1], Config.VERTEX_COLOR)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()