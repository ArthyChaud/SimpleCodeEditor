import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD  # Importez tkinterdnd2 ici
import subprocess
import datetime
import tempfile
import platform
import tkinter.tix
import json
import sys
import os
import re

class CodeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Code Editor")
        self.config_path = os.path.join(os.path.expanduser('~'), '.my_code_editor_config')
        self.python_interpreter_path = self.load_config()
        self.root.geometry("900x700")
        
        # Créer un Frame pour les boutons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        # Bouton Ouvrir
        self.open_button = tk.Button(self.button_frame, text="Open", command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Bouton Sauvegarder
        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_file)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_as_button = tk.Button(self.button_frame, text="Save As", command=self.save_file_as)
        self.save_as_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Bouton Version
        self.version_button = tk.Button(self.button_frame, text="Version", command=self.save_version)
        self.version_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Bouton Déplacer Gauche
        self.move_left_button = tk.Button(self.button_frame, text="<-", command=self.move_text_left)
        self.move_left_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Bouton Déplacer Droite
        self.move_right_button = tk.Button(self.button_frame, text="->", command=self.move_text_right)
        self.move_right_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.current_file_path = None  # Attribut pour garder la trace du fichier actuellement ouvert
        
        # Bouton Run
        self.run_button = tk.Button(self.button_frame, text="Run", command=self.run_code)
        self.run_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.python_path_button = tk.Button(self.button_frame, text="Python", command=self.change_python_path)
        self.python_path_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Dans la méthode __init__ de la classe CodeEditor
        self.search_text = tk.StringVar()
        self.search_entry = tk.Entry(self.button_frame, textvariable=self.search_text)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_button = tk.Button(self.button_frame, text="Search", command=self.search_next)
        self.search_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.text_area = tk.Text(self.root, undo=True, wrap='word', font=("Monaco", 14))
        self.text_area.pack(expand=True, fill='both')

        # Enregistrez la zone de texte comme cible de drop et liez l'événement de drop
        self.text_area.drop_target_register(DND_FILES)
        self.text_area.dnd_bind('<<Drop>>', self.on_file_drop)

        self.text_area.tag_configure("search_highlight", background="orange")
        self.text_area.bind('<Tab>', self.handle_tab)

        self.highlight_patterns()

        self.menu_bar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Ouvrir", command=self.open_file)
        self.file_menu.add_command(label="Sauvegarder", command=self.save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quitter", command=self.quit_app)
        self.menu_bar.add_cascade(label="Fichier", menu=self.file_menu)

        self.root.config(menu=self.menu_bar)
        self.text_area.bind('<KeyRelease>', self.on_key_release)

        # Création de la barre d'état
        self.status_bar = tk.Label(self.root, text="Prêt", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def highlight_patterns(self):
        self.patterns = [
            # Chaînes de caractères multilignes
            (r'(\"\"\"[^\"]*\"\"\"|\'\'\'[^\']*\'\'\')', 'python_multiline_string', 'lightgrey'),
            # Mots-clés Python
            (r'\b(def|class|import|if|else|elif|for|while|return|try|except|finally|with|as|pass|break|continue|lambda|from|async|await)\b', 'python_keyword', '#007ACC'),
            # CSS - Simplification pour les mots-clés
            (r'\b(display|justify-content|align-items|flex-direction|position|background|color|font-size|margin|padding|border)\b', 'css_keyword', '#007ACC'),
            # JavaScript - Mots-clés
            (r'\b(break|case|catch|class|const|continue|debugger|default|delete|do|else|export|extends|finally|for|function|if|import|in|instanceof|new|return|super|switch|this|throw|try|typeof|var|void|while|with|yield|async|await)\b', 'js_keyword', '#007ACC'),
            # Littéraux Python (True, False, None)
            (r'\b(True|False|None)\b', 'python_literal', 'red'),
            # Types de données et fonctions built-in
            (r'\b(int|str|float|list|dict|tuple|set|print|len|range|type)\b', 'python_builtin', 'orange'),
            # Nombres
            (r'\b\d+\b', 'python_number', 'red'),
            # Commentaires
            (r'#.*$', 'comment', 'green'),
        ]
    
        for _, tag, color in self.patterns:
            self.text_area.tag_configure(tag, foreground=color)

    def highlight_code(self, event=None):
        for pattern, tag, _ in self.patterns:
            self.text_area.tag_remove(tag, '1.0', tk.END)
            text = self.text_area.get('1.0', tk.END)
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = match.start()
                end = match.end()
                start_index = self.text_area.index(f"1.0+{start}c")
                end_index = self.text_area.index(f"1.0+{end}c")
                self.text_area.tag_add(tag, start_index, end_index)

    def on_file_drop(self, event):
        # Obtenez le chemin du fichier déposé
        file_path = event.data
        if file_path:
            self.open_file(file_path=file_path)
    
    def on_key_release(self, event=None):
        self.highlight_code(event)
        
    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"), ("Python files", "*.py"), ("All files", "*.*")])
        if not file_path:  # L'utilisateur a annulé
            return
        self.current_file_path = file_path  # Mise à jour du chemin du fichier courant
        self.save_file()  # Sauvegarde le fichier
        
    def handle_tab(self, event):
            self.text_area.insert(tk.INSERT, " " * 4)
            return 'break'  # Empêche l'événement Tab par défaut

    def change_python_path(self):
        """Permet à l'utilisateur de saisir manuellement le chemin de l'interpréteur Python."""
        python_path = simpledialog.askstring("Python Interpreter Path",
                                             "Please enter the path to the Python interpreter:")
        if python_path:
            # Vérifie si le chemin fourni est un fichier exécutable valide
            if os.path.isfile(python_path):
                self.save_config(python_path)  # Sauvegarde le nouveau chemin
                self.python_interpreter_path = python_path
                messagebox.showinfo("Python Path Updated", "The Python interpreter path has been updated.")
            else:
                messagebox.showerror("Invalid Path", "The path provided is not a valid file.")
        else:
            messagebox.showwarning("No Input", "No path was entered.")
    
    def open_file(self, file_path=None):
        # Modifié pour accepter un argument file_path
        if not file_path:
            file_path = filedialog.askopenfilename()
        if file_path:
            self.current_file_path = file_path
            self.status_bar['text'] = f"Ouvert : {file_path}"
            with open(file_path, 'r') as file:
                file_content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, file_content)
                self.highlight_code()
                
    def save_version(self):
        if self.current_file_path:
            # Générer le nom du fichier de version avec la date et l'heure
            version_suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_dir, file_name = os.path.split(self.current_file_path)
            file_name_without_ext, file_ext = os.path.splitext(file_name)
            version_file_name = f"{file_name_without_ext}_{version_suffix}{file_ext}"
            version_file_path = os.path.join(file_dir, version_file_name)

            # Sauvegarde du contenu actuel dans le fichier de version
            code_content = self.text_area.get("1.0", tk.END)
            with open(version_file_path, 'w') as version_file:
                version_file.write(code_content)
            messagebox.showinfo("Version sauvegardée", f"Une version du fichier a été sauvegardée sous : {version_file_path}")
        else:
            messagebox.showwarning("Aucun fichier", "Ouvrez ou sauvegardez le fichier avant de créer une version.")
    
    def load_config(self):
        """Charge la configuration du chemin de l'interpréteur Python."""
        try:
            with open(self.config_path, 'r') as config_file:
                try:
                    config = json.load(config_file)
                    return config.get('python_interpreter_path')
                except json.JSONDecodeError:
                    # Le fichier est vide ou mal formé ; vous pouvez choisir de le supprimer ou de le réinitialiser ici
                    return None
        except FileNotFoundError:
            # Le fichier de configuration n'existe pas
            return None

    def save_config(self, python_path):
        """Sauvegarde la configuration du chemin de l'interpréteur Python."""
        config = {'python_interpreter_path': python_path}
        with open(self.config_path, 'w') as config_file:
            json.dump(config, config_file)

    def find_python_interpreter(self):
        """Demande à l'utilisateur d'entrer le chemin de l'interpréteur Python."""
        if self.python_interpreter_path:
            # Si le chemin est déjà défini, l'utiliser
            return self.python_interpreter_path
    
        # Demander à l'utilisateur d'entrer le chemin
        python_path = simpledialog.askstring("Python Interpreter Path",
                                             "Please enter the path to the Python interpreter:")
        if python_path and os.path.isfile(python_path):
            # Sauvegarde le chemin pour les futures utilisations si un chemin valide est fourni
            self.save_config(python_path)
            self.python_interpreter_path = python_path
            return python_path
        else:
            # Si aucun chemin n'est fourni ou si le chemin n'est pas valide, afficher un message d'erreur
            messagebox.showerror("Error", "Invalid Python interpreter path.")
            return None
    
    def run_code(self):
        if not self.current_file_path:
            messagebox.showerror("Erreur", "Veuillez sauvegarder le fichier avant de l'exécuter.")
            return
    
        python_path = self.find_python_interpreter()  # Utilise la méthode find_python_interpreter pour obtenir le chemin de l'interpréteur Python
    
        try:
            # Exécute le script Python directement depuis le chemin actuel
            subprocess.run([python_path, os.path.abspath(self.current_file_path)], check=True, cwd=os.path.dirname(self.current_file_path))
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erreur pendant l'exécution", str(e))
            
    def move_text_left(self):
        try:
            selection_start, selection_end = self.text_area.tag_ranges(tk.SEL)
        except ValueError:
            return  # Pas de texte sélectionné

        selected_text = self.text_area.get(selection_start, selection_end)
        modified_text = '\n'.join([line[4:] if line.startswith('    ') else line for line in selected_text.split('\n')])

        self.text_area.delete(selection_start, selection_end)
        self.text_area.insert(selection_start, modified_text)

        # Conserver la sélection
        end_index = self.text_area.index(f"{selection_start}+{len(modified_text)}c")
        self.text_area.tag_add(tk.SEL, selection_start, end_index)
        self.text_area.mark_set(tk.INSERT, selection_start)
        self.text_area.see(tk.INSERT)

    def move_text_right(self):
        try:
            selection_start, selection_end = self.text_area.tag_ranges(tk.SEL)
        except ValueError:
            return  # Pas de texte sélectionné

        selected_text = self.text_area.get(selection_start, selection_end)
        modified_text = '\n'.join(['    ' + line for line in selected_text.split('\n')])

        self.text_area.delete(selection_start, selection_end)
        self.text_area.insert(selection_start, modified_text)

        # Conserver la sélection
        end_index = self.text_area.index(f"{selection_start}+{len(modified_text)}c")
        self.text_area.tag_add(tk.SEL, selection_start, end_index)
        self.text_area.mark_set(tk.INSERT, selection_start)
        self.text_area.see(tk.INSERT)
    
    def search_next(self):
        search_query = self.search_text.get()
        if not search_query:
            messagebox.showinfo("Search", "Please enter search text.")
            return

        start_index = self.text_area.index(tk.INSERT)
        pos = self.text_area.search(search_query, start_index, stopindex=tk.END)

        if not pos:
            pos = self.text_area.search(search_query, "1.0", stopindex=tk.END)
            if not pos:
                messagebox.showinfo("Search", "Text not found.")
                return

        end_pos = f"{pos}+{len(search_query)}c"
        self.text_area.tag_remove("search_highlight", "1.0", tk.END)  # Enlève les surlignages précédents
        self.text_area.tag_add("search_highlight", pos, end_pos)  # Applique le surlignage orange
        self.text_area.mark_set(tk.INSERT, end_pos)
        self.text_area.see(tk.INSERT)
    
    def save_file(self):
        if not self.current_file_path:
            # Comportement similaire à "Save As" s'il n'y a pas de fichier courant
            self.save_file_as()
        else:
            with open(self.current_file_path, 'w') as file:
                file_content = self.text_area.get(1.0, tk.END)
                file.write(file_content)
            self.status_bar['text'] = f"Sauvegardé : {self.current_file_path}"
            messagebox.showinfo("Sauvegardé", "Votre fichier a été sauvegardé.")
    
    def quit_app(self):
        self.root.quit()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CodeEditor(root)
    root.mainloop()

