import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import os
from natsort import natsorted
from pathlib import Path 

JPEG_MAX_DIMENSION = 65000

class MultiFolderSelector(tk.Toplevel):
    def __init__(self, parent, title="Selecione as pastas", initial_dir='.'):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        self.selected_folders = []
        self.current_path = os.path.abspath(initial_dir)
        top_frame = ttk.Frame(self, padding=5)
        top_frame.pack(fill=tk.X)
        self.path_label = ttk.Label(top_frame, text=self.current_path, anchor='w')
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        up_button = ttk.Button(top_frame, text=" Cima ", command=self._go_up)
        up_button.pack(side=tk.RIGHT)
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        bottom_frame = ttk.Frame(self, padding=5)
        bottom_frame.pack(fill=tk.X)
        ok_button = ttk.Button(bottom_frame, text="Selecionar", command=self._on_ok)
        ok_button.pack(side=tk.RIGHT, padx=5)
        cancel_button = ttk.Button(bottom_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT)
        self._populate_list()
        self.wait_window(self)
    def _populate_list(self):
        self.listbox.delete(0, tk.END)
        self.path_label.config(text=self.current_path)
        try:
            dirs = natsorted([d for d in os.listdir(self.current_path) if os.path.isdir(os.path.join(self.current_path, d))])
            for d in dirs:
                self.listbox.insert(tk.END, f"📁 {d}")
        except OSError as e:
            self.listbox.insert(tk.END, f"Erro ao acessar: {e}")
    def _go_up(self):
        new_path = os.path.dirname(self.current_path)
        if new_path != self.current_path:
            self.current_path = new_path
            self._populate_list()
    def _on_double_click(self, event):
        selection_indices = self.listbox.curselection()
        if not selection_indices: return
        selected_item = self.listbox.get(selection_indices[0]).replace("📁 ", "")
        new_path = os.path.join(self.current_path, selected_item)
        if os.path.isdir(new_path):
            self.current_path = new_path
            self._populate_list()
    def _on_ok(self):
        selection_indices = self.listbox.curselection()
        if selection_indices:
            for i in selection_indices:
                folder_name = self.listbox.get(i).replace("📁 ", "")
                full_path = os.path.join(self.current_path, folder_name)
                self.selected_folders.append(full_path)
        self.destroy()

class AdvancedImageJoinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎞️ Juntador de Imagens Vertical v4.1")
        self.root.geometry("650x550")
        
        self.default_path = self._get_default_path()

        style = ttk.Style(self.root)
        style.theme_use('clam')
        self.selected_folders = []
        self.base_output_folder = ""
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto para começar!")
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        input_frame = ttk.LabelFrame(main_frame, text=" 📂 1. Pastas de Entrada ", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        self.add_folder_btn = ttk.Button(buttons_frame, text="Adicionar Pasta(s)", command=self.add_folders)
        self.add_folder_btn.pack(side=tk.LEFT, padx=5)
        self.remove_folder_btn = ttk.Button(buttons_frame, text="Remover Selecionada", command=self.remove_selected_folder)
        self.remove_folder_btn.pack(side=tk.LEFT, padx=5)
        self.clear_folders_btn = ttk.Button(buttons_frame, text="Limpar Lista", command=self.clear_folders)
        self.clear_folders_btn.pack(side=tk.LEFT, padx=5)
        listbox_frame = ttk.Frame(input_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.folder_listbox = tk.Listbox(listbox_frame, height=8, selectmode=tk.EXTENDED)
        self.folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.folder_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.folder_listbox.config(yscrollcommand=scrollbar.set)
        options_frame = ttk.LabelFrame(main_frame, text=" ⚙️ 2. Opções de Geração ", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        ttk.Label(options_frame, text="Número máximo de imagens por fita (0 para ilimitado):").pack(anchor='w', padx=5)
        self.num_images_entry = ttk.Entry(options_frame, width=10)
        self.num_images_entry.insert(0, "0")
        self.num_images_entry.pack(anchor='w', padx=5, pady=(0, 10))
        self.output_folder_btn = ttk.Button(options_frame, text="Selecionar Pasta de Saída Principal", command=self.select_output_folder)
        self.output_folder_btn.pack(anchor='w', padx=5)
        self.output_folder_label = ttk.Label(options_frame, text="Nenhuma pasta de saída selecionada.", wraplength=600)
        self.output_folder_label.pack(anchor='w', padx=5, pady=5)
        action_frame = ttk.LabelFrame(main_frame, text=" ✨ 3. Iniciar Processo ", padding="10")
        action_frame.pack(fill=tk.X, pady=5)
        self.join_button = ttk.Button(action_frame, text="Juntar Imagens!", command=self.process_folders)
        self.join_button.pack(pady=10)
        self.progress_bar = ttk.Progressbar(action_frame, orient='horizontal', length=300, mode='determinate')
        self.progress_bar.pack(pady=5)
        self.status_label = ttk.Label(action_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)

    def _get_default_path(self):
        """Encontra a pasta de Downloads do usuário de forma segura e cross-platform."""
        downloads_path = Path.home() / "Downloads"
        
        if downloads_path.is_dir():
            return str(downloads_path)
        else:
            return str(Path.home())

    def add_folders(self):
        """Abre o seletor de múltiplas pastas personalizado."""
        dialog = MultiFolderSelector(self.root, initial_dir=self.default_path)
        
        newly_selected = dialog.selected_folders
        if newly_selected:
            for folder_path in newly_selected:
                if folder_path not in self.selected_folders:
                    self.selected_folders.append(folder_path)
            self.update_folder_listbox()

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(
            title="Selecione a pasta principal onde os resultados serão salvos",
            initialdir=self.default_path
        )
        if folder_path:
            self.base_output_folder = folder_path
            self.output_folder_label.config(text=f"Salvar em: {self.base_output_folder}")
            
    def remove_selected_folder(self):
        selected_indices = self.folder_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Atenção", "Nenhuma pasta selecionada para remover.")
            return
        for index in sorted(selected_indices, reverse=True):
            del self.selected_folders[index]
        self.update_folder_listbox()

    def clear_folders(self):
        self.selected_folders.clear()
        self.update_folder_listbox()

    def update_folder_listbox(self):
        self.folder_listbox.delete(0, tk.END)
        for folder in self.selected_folders:
            self.folder_listbox.insert(tk.END, folder)
            
    def get_sorted_image_files(self, folder_path):
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
        try:
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]
            sorted_files = natsorted(files)
            return [os.path.join(folder_path, f) for f in sorted_files]
        except (IOError, OSError):
            return []

    def process_folders(self):
        if not self.selected_folders or not self.base_output_folder:
            messagebox.showerror("Erro", "Por favor, selecione as pastas de entrada e a de saída.")
            return
        try:
            max_images_per_strip = int(self.num_images_entry.get())
        except ValueError:
            messagebox.showerror("Erro", "O 'Número máximo de imagens' deve ser um número inteiro.")
            return
        
        self.join_button.config(state="disabled")
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(self.selected_folders)
        total_strips_created = 0

        for i, folder_path in enumerate(self.selected_folders):
            folder_name = os.path.basename(folder_path)
            self.status_var.set(f"Processando pasta: {folder_name}...")
            self.root.update_idletasks()
            sub_output_folder = os.path.join(self.base_output_folder, folder_name)
            os.makedirs(sub_output_folder, exist_ok=True)
            image_paths = self.get_sorted_image_files(folder_path)
            if not image_paths:
                self.progress_bar['value'] = i + 1
                continue
            current_strip_images = []
            strip_count = 0
            current_strip_width = 0
            current_strip_height = 0
            for img_path in image_paths:
                try:
                    img = Image.open(img_path).convert("RGB")
                except Exception as e:
                    print(f"Aviso: Não foi possível abrir a imagem {img_path}: {e}")
                    continue
                if not current_strip_images:
                    current_strip_images.append(img)
                    current_strip_width = img.width
                    current_strip_height = img.height
                    continue
                width_matches = (img.width == current_strip_width)
                limit_not_reached = (max_images_per_strip == 0 or len(current_strip_images) < max_images_per_strip)
                height_limit_ok = (current_strip_height + img.height) <= JPEG_MAX_DIMENSION
                if width_matches and limit_not_reached and height_limit_ok:
                    current_strip_images.append(img)
                    current_strip_height += img.height
                else:
                    self.save_image_strip(current_strip_images, sub_output_folder, strip_count)
                    total_strips_created += 1
                    strip_count += 1
                    current_strip_images = [img]
                    current_strip_width = img.width
                    current_strip_height = img.height
            if current_strip_images:
                self.save_image_strip(current_strip_images, sub_output_folder, strip_count)
                total_strips_created += 1
            self.progress_bar['value'] = i + 1
        self.status_var.set("Processo concluído!")
        self.join_button.config(state="normal")
        messagebox.showinfo("Sucesso", f"Processo finalizado! Foram criadas {total_strips_created} fitas de imagem.")

    def save_image_strip(self, images, output_folder, strip_index):
        if not images: return
        total_height = sum(im.height for im in images)
        strip_width = images[0].width
        new_im = Image.new('RGB', (strip_width, total_height))
        y_offset = 0
        for im in images:
            new_im.paste(im, (0, y_offset))
            y_offset += im.height
        output_filename = f"fita_{strip_index + 1:03d}.jpg"
        output_path = os.path.join(output_folder, output_filename)
        new_im.save(output_path, "JPEG", quality=95, optimize=True)
        self.status_var.set(f"Salvo: ...{os.path.sep}{os.path.basename(output_folder)}{os.path.sep}{output_filename}")
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedImageJoinerApp(root)
    root.mainloop()