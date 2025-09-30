import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os

class ImageJoinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Juntador de Imagens Vertical")

        self.selected_folders = []
        self.output_folder = ""

        # --- Frames para organização ---
        self.folder_frame = tk.LabelFrame(root, text="Seleção de Pastas")
        self.folder_frame.pack(pady=10, padx=10, fill="x")

        self.options_frame = tk.LabelFrame(root, text="Opções de Geração")
        self.options_frame.pack(pady=10, padx=10, fill="x")

        self.actions_frame = tk.LabelFrame(root, text="Ações")
        self.actions_frame.pack(pady=10, padx=10, fill="x")

        # --- Seleção de Pastas ---
        self.add_folder_btn = tk.Button(self.folder_frame, text="Adicionar Pasta", command=self.add_folder)
        self.add_folder_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.remove_folder_btn = tk.Button(self.folder_frame, text="Remover Selecionada", command=self.remove_selected_folder)
        self.remove_folder_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.folder_listbox_label = tk.Label(self.folder_frame, text="Pastas Selecionadas:")
        self.folder_listbox_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.folder_listbox = tk.Listbox(self.folder_frame, height=5, selectmode=tk.MULTIPLE)
        self.folder_listbox.pack(side=tk.LEFT, expand=True, fill="both", padx=5, pady=5)
        self.folder_listbox_scrollbar = tk.Scrollbar(self.folder_frame, orient="vertical", command=self.folder_listbox.yview)
        self.folder_listbox_scrollbar.pack(side=tk.LEFT, fill="y")
        self.folder_listbox.config(yscrollcommand=self.folder_listbox_scrollbar.set)

        # --- Quantidade Final de Imagens ---
        self.num_images_label = tk.Label(self.options_frame, text="Número máximo de imagens por fita (0 para ilimitado):")
        self.num_images_label.pack(pady=5, padx=5, anchor="w")
        self.num_images_entry = tk.Entry(self.options_frame)
        self.num_images_entry.insert(0, "0") # Valor padrão
        self.num_images_entry.pack(pady=5, padx=5, fill="x")

        # --- Pasta de Saída ---
        self.output_folder_btn = tk.Button(self.options_frame, text="Selecionar Pasta de Saída", command=self.select_output_folder)
        self.output_folder_btn.pack(pady=5, padx=5, anchor="w")

        self.output_folder_label = tk.Label(self.options_frame, text="Pasta de Saída: Nenhuma selecionada")
        self.output_folder_label.pack(pady=5, padx=5, anchor="w")

        # --- Botão de Juntar Imagens ---
        self.join_button = tk.Button(self.actions_frame, text="Juntar Imagens", command=self.process_folders)
        self.join_button.pack(pady=10, padx=10)

    def add_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path and folder_path not in self.selected_folders:
            self.selected_folders.append(folder_path)
            self.update_folder_listbox()

    def remove_selected_folder(self):
        selected_indices = self.folder_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Atenção", "Nenhuma pasta selecionada para remover.")
            return

        # Remove em ordem reversa para não alterar os índices enquanto remove
        for index in sorted(selected_indices, reverse=True):
            del self.selected_folders[index]
        self.update_folder_listbox()

    def update_folder_listbox(self):
        self.folder_listbox.delete(0, tk.END)
        for folder in self.selected_folders:
            self.folder_listbox.insert(tk.END, folder)

    def select_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_folder = folder_path
            self.output_folder_label.config(text=f"Pasta de Saída: {self.output_folder}")

    def get_image_files(self, folder_path):
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]
        files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(char.isdigit() for char in x) else x)
        return [os.path.join(folder_path, f) for f in files]

    def process_folders(self):
        if not self.selected_folders:
            messagebox.showerror("Erro", "Por favor, adicione pelo menos uma pasta com imagens.")
            return
        if not self.output_folder:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de saída.")
            return

        try:
            max_images_per_strip_str = self.num_images_entry.get()
            max_images_per_strip = int(max_images_per_strip_str) if max_images_per_strip_str.isdigit() else 0
            if max_images_per_strip < 0:
                raise ValueError("O número máximo de imagens não pode ser negativo.")
        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido para 'Número máximo de imagens': {e}")
            return

        total_processed_strips = 0
        for folder_path in self.selected_folders:
            image_paths = self.get_image_files(folder_path)
            if not image_paths:
                messagebox.showinfo("Atenção", f"Nenhuma imagem encontrada na pasta: {folder_path}")
                continue

            current_strip_images = []
            strip_count_for_folder = 0
            current_strip_width = -1 # Para a primeira imagem definir a largura

            for i, img_path in enumerate(image_paths):
                try:
                    img = Image.open(img_path)
                    img = img.convert("RGB") # Garante consistência no modo de cor
                except Exception as e:
                    print(f"Não foi possível abrir a imagem {img_path}: {e}")
                    continue

                if current_strip_width == -1: # Primeira imagem da fita
                    current_strip_width = img.width
                    current_strip_images.append(img)
                elif img.width == current_strip_width: # Mesma largura, junta
                    current_strip_images.append(img)
                else: # Largura diferente, salva a fita atual e inicia uma nova
                    if current_strip_images:
                        self.save_image_strip(current_strip_images, folder_path, strip_count_for_folder)
                        total_processed_strips += 1
                        strip_count_for_folder += 1
                    current_strip_images = [img]
                    current_strip_width = img.width

                if max_images_per_strip > 0 and len(current_strip_images) >= max_images_per_strip:
                    if current_strip_images:
                        self.save_image_strip(current_strip_images, folder_path, strip_count_for_folder)
                        total_processed_strips += 1
                        strip_count_for_folder += 1
                    current_strip_images = []
                    current_strip_width = -1 # Reset para a próxima fita

            # Salva qualquer fita restante no final da pasta
            if current_strip_images:
                self.save_image_strip(current_strip_images, folder_path, strip_count_for_folder)
                total_processed_strips += 1
                strip_count_for_folder += 1

        messagebox.showinfo("Sucesso", f"Processo concluído! Foram criadas {total_processed_strips} fitas de imagem.")


    def save_image_strip(self, images, original_folder_path, strip_index):
        if not images:
            return

        widths, heights = zip(*(i.size for i in images))
        max_width = images[0].width # Já garantimos que todas têm a mesma largura
        total_height = sum(heights)

        new_im = Image.new('RGB', (max_width, total_height))

        y_offset = 0
        for im in images:
            new_im.paste(im, (0, y_offset))
            y_offset += im.height

        # Gerar nome do arquivo baseado na pasta original
        folder_name = os.path.basename(original_folder_path)
        output_filename = f"{folder_name}_fita_{strip_index + 1:03d}.jpg" # Nome padronizado
        output_path = os.path.join(self.output_folder, output_filename)

        new_im.save(output_path)
        print(f"Fita salva: {output_path}")

# --- Iniciar a Aplicação ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageJoinerApp(root)
    root.mainloop()