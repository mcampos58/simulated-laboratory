import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen.canvas import Canvas
import json
from numpy import random
from datetime import datetime
import os
from reportlab_qrcode import QRCodeImage
from pathlib import Path
import webbrowser
from PIL import Image, ImageTk

# Constantes
CONFIG_EXAMES_FOLDER = Path(__file__).parent / 'data' / 'exames'
PATIENT_DATA_FOLDER = Path(__file__).parent / 'data' / 'pacientes'



# Função para criar o PDF
def gerar_pdf_resultado_exame(nome_paciente, data_exame, exames):
    pdf_file = f"resultado_exame_{nome_paciente.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    estilo_titulo = styles['Title']
    estilo_normal = styles['Normal']

    titulo = Paragraph(f"Resultado de Exame Laboratorial", estilo_titulo)
    elements.append(titulo)
    
    paciente_info = Paragraph(f"Paciente: {nome_paciente}<br/>Data do Exame: {data_exame}", estilo_normal)
    elements.append(paciente_info)
    elements.append(Spacer(1, 12))
    
    for exame in exames:
        nome_exame = Paragraph(f"<b>{exame['name']}</b> <br/>Metodologia: {exame['method']}", estilo_normal)
        elements.append(nome_exame)
        elements.append(Spacer(1, 6))

        tabela_data = [['Elemento', 'Resultado', 'Unidade', 'Referência']]
        
        for item in exame['items']:
            resultado = item['resultado']
            ref = item['reference']

            # Determine the reference range text
            if 'min' in ref and 'max' in ref:
                range_text = f"{ref['min']} - {ref['max']}"
            elif 'max' in ref:
                range_text = f"< {ref['max']}"
            elif 'min' in ref:
                range_text = f"> {ref['min']}"
            elif 'expected' in ref:
                range_text = ref['expected']
            else:
                range_text = "N/A"

            # Append data to the table, using the computed reference range
            tabela_data.append([
                item['name'],
                f"{resultado}",
                ref.get('units', ''),
                range_text
            ])
        
        tabela = Table(tabela_data, colWidths=[2*inch, 1*inch, 1*inch, 2*inch])
        
        tabela.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black),  # Linha acima do cabeçalho
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),  # Linha abaixo do cabeçalho
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.grey),  # Linha abaixo da última linha
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        
        elements.append(tabela)
        elements.append(Spacer(1, 12))

    if(var_qrcode.get() == 1):
        qr = QRCodeImage("https://youtu.be/dQw4w9WgXcQ", size=30*mm)
        elements.append(Paragraph("A autenticidade dos resultados pode ser verificada acessando o QRCode abaixo:", estilo_normal))
        elements.append(qr)

    doc.build(elements)

    messagebox.showinfo("Sucesso", f"PDF gerado com sucesso: {pdf_file}")

# Função para coletar os dados da interface e gerar o PDF
def gerar_pdf():
    nome_paciente = entry_nome_paciente.get()
    data_exame = entry_data_exame.get()
    
    exames = []
    
    for exame_config, campos, checkbox in zip(exames_config, campos_exames, checkboxes):
        if checkbox.get() == 1:  # Verifica se o checkbox está marcado
            itens = []
            for campo, item in zip(campos, exame_config['items']):
                resultado = (campo.get())
                item_atualizado = item.copy()
                item_atualizado['resultado'] = resultado
                itens.append(item_atualizado)
            exame_atualizado = exame_config.copy()
            exame_atualizado['items'] = itens
            exames.append(exame_atualizado)
    
    gerar_pdf_resultado_exame(nome_paciente, data_exame, exames)


# Função para gerar o valor padrão do exame
def gerar_valor_padrao(item):
    gen = item.get('generate', {})
    method = gen.get('method')
    params = gen.get('parameters', {})
    
    if method == 'normal':
        mean = params.get('mean', 0)
        sd = params.get('sd', 1)
        precision = params.get('precision', 1)
        resultado = random.normal(mean, sd)
        return round(resultado, precision)        
    else:
        # For methods other than 'normal', adjust accordingly
        # Derived or other methods can have custom logic here
        return ''

# Função para salvar resultados do paciente
def salvar_paciente():
    # Ensure the directory exists
    os.makedirs(PATIENT_DATA_FOLDER, exist_ok=True)
    
    # Collect patient basic info
    nome_paciente = entry_nome_paciente.get().strip()
    data_exame = entry_data_exame.get().strip()
    
    # Basic validation
    if not nome_paciente:
        messagebox.showerror("Erro", "O nome do paciente é obrigatório.")
        return
    if not data_exame:
        messagebox.showerror("Erro", "A data do exame é obrigatória.")
        return
    # Gather exam data similar to gerar_pdf
    exames = []
    for exame_config, campos, checkbox in zip(exames_config, campos_exames, checkboxes):
        if checkbox.get() == 1:  # Check if the exam is selected
            itens = []
            for campo, item in zip(campos, exame_config['items']):
                resultado = campo.get()
                # Create a copy of the item and store the result
                item_atualizado = item.copy()
                item_atualizado['resultado'] = resultado
                itens.append(item_atualizado)
            exame_atualizado = exame_config.copy()
            exame_atualizado['items'] = itens
            exames.append(exame_atualizado)
    # Structure the patient data
    paciente_data = {
        "nome_paciente": nome_paciente,
        "data_exame": data_exame,
        "exames": exames
    }
    # Create a unique filename using patient name and current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_name = nome_paciente.replace(" ", "_")
    filename = f"{safe_name}_{timestamp}.json"
    filepath = os.path.join(PATIENT_DATA_FOLDER, filename)
    
    try:
        # Write patient data to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(paciente_data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Sucesso", f"Dados do paciente salvos com sucesso em {filepath}")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar os dados do paciente: {e}")   

def selecionar_arquivo():
    file_path = filedialog.askopenfilename(
        initialdir=PATIENT_DATA_FOLDER,
        title="Selecione o arquivo do paciente",
        filetypes=[("JSON Files", "*.json")]
    )
    if file_path:
        carregar_paciente(file_path)
        

def carregar_paciente(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            paciente_data = json.load(f)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível carregar os dados: {e}")
        return

    # Populate patient basic info
    nome_paciente = paciente_data.get("nome_paciente", "")
    data_exame = paciente_data.get("data_exame", "")
    entry_nome_paciente.delete(0, tk.END)
    entry_nome_paciente.insert(0, nome_paciente)
    entry_data_exame.delete(0, tk.END)
    entry_data_exame.insert(0, data_exame)

    # Reset all checkboxes and fields
    for checkbox in checkboxes:
        checkbox.set(0)
    for campos in campos_exames:
        for campo in campos:
            # For both Entry and Combobox widgets
            if isinstance(campo, ttk.Combobox):
                campo.set('')
            else:
                campo.delete(0, tk.END)

    # Populate exam data
    exames_carregados = paciente_data.get("exames", [])
    for exame_carregado in exames_carregados:
        # Find the index of the exam in exames_config by matching ID
        exam_id = exame_carregado.get("id")
        if not exam_id:
            continue
        try:
            idx = next(i for i, exam in enumerate(exames_config) if exam["id"] == exam_id)
        except StopIteration:
            continue  # Skip if exam not found in current config

        # Set checkbox for this exam
        checkboxes[idx].set(1)

        # Populate each field for the exam items
        for campo, item_carregado in zip(campos_exames[idx], exame_carregado.get("items", [])):
            resultado = item_carregado.get("resultado", "")
            if isinstance(campo, ttk.Combobox):
                # If the widget is a Combobox, set its value
                campo.set(resultado)
            else:
                campo.delete(0, tk.END)
                campo.insert(0, resultado)

    messagebox.showinfo("Sucesso", f"Dados do paciente carregados com sucesso de {os.path.basename(filepath)}")
        
    


# Carrega todos os arquivos da pasta de configuração de exames
arquivos_config_exames = [f for f in os.listdir(CONFIG_EXAMES_FOLDER) if f.endswith('.json')]


exames_config = []
for arquivo in arquivos_config_exames:
    try:
        with open((CONFIG_EXAMES_FOLDER / arquivo), 'r') as f:
            exames_config.extend(json.load(f))
    except Exception as e:
        messagebox.showinfo("Erro", f"Não foi possível carregar as configurações de exame: {e}")

exames_config = sorted(exames_config, key = lambda e: (e['category']))


# Criação da interface gráfica
app = ttk.Window()
app.title("Gerar PDF de Exames Laboratoriais")
#app.geometry("800x600")

## Estilo
style = ttk.Style("superhero")
# app.tk.call('source', 'forest-light.tcl')
# app.tk.call('source', 'forest-dark.tcl')
# style.theme_use('forest-dark')

ttk.Label(app, text="Nome do Paciente:").grid(row=0, column=0)
entry_nome_paciente = ttk.Entry(app)
entry_nome_paciente.grid(row=0, column=1)

ttk.Label(app, text="Data do Exame:").grid(row=1, column=0)
entry_data_exame = ttk.Entry(app)
entry_data_exame.grid(row=1, column=1)
entry_data_exame.insert(0, datetime.now().strftime('%d/%m/%Y %H:%M'))

campos_exames = []
checkboxes = []

categorias = sorted({e['category'] for e in exames_config})

tabCategoria = ttk.Notebook(app)
tabCategoria.grid(row=2, column=0, columnspan=8)
tabs = []

for categoria in categorias:
    tab = ttk.Frame(tabCategoria)
    tabCategoria.add(tab, text=categoria, padding=10)
    tabs.append(tab)

    linha = 3
    for exame in exames_config:
        if exame['category'] == categoria:
            var = tk.IntVar()
            checkbox = ttk.Checkbutton(tab, text=exame['name'], variable=var, bootstyle="round-toggle")
            checkbox.grid(row=linha, column=0, sticky="w", pady=5)
            checkboxes.append(var)
            linha += 1

            campos_elementos = []
            for elemento in exame['items']:
                if elemento['type'] == 'options':
                    ttk.Label(tab, text=f"{elemento['name']}:").grid(row=linha, column=0, pady=5)
                    entry = ttk.Combobox(tab, values=elemento['values'])
                    # Access the default value from the nested 'parameters'
                    default_value = elemento['generate']['parameters'].get('default', "")
                    entry.set(default_value)  # Use set() for ttk.Combobox to set initial value
                else:
                    # Use structured reference details for display
                    units = elemento['reference'].get('units', '')
                    ttk.Label(tab, text=f"{elemento['name']} ({units}):").grid(row=linha, column=0, pady=5)
                    entry = ttk.Entry(tab)
                    # Assume gerar_valor_padrao has been updated to use 'parameters'
                    entry.insert(0, gerar_valor_padrao(elemento))

                entry.grid(row=linha, column=1)
                campos_elementos.append(entry)
                linha += 1

            campos_exames.append(campos_elementos)

# Checkbox Incluir QRCode
var_qrcode = tk.IntVar()
checkbox_qr = ttk.Checkbutton(app, text='Gerar QRCode', variable=var_qrcode)
checkbox_qr.grid(row=linha, column=0, sticky="w", pady=10, padx=10)
linha +=1

# Botão para gerar o PDF
btn_gerar_pdf = ttk.Button(app, text="Gerar PDF", command=gerar_pdf, bootstyle=SUCCESS)
btn_gerar_pdf.grid(row=linha, column=0, columnspan=1)


# Botão para salvar JSON do paciente
btn_salvar_json = ttk.Button(app, text="Salvar", command=salvar_paciente, state="normal", bootstyle=(INFO, OUTLINE))
btn_salvar_json.grid(row=linha, column=1, columnspan=1)

btn_carregar_json = ttk.Button(app, text="Carregar", command=selecionar_arquivo, bootstyle=(INFO, OUTLINE))
btn_carregar_json.grid(row=linha, column=2, columnspan=1)  # Adjust grid placement as needed

linha += 1
# Label com texto de copyright
#ttk.Label(app, text="Elaboração: Prof. Mateus Rennó de Campos", padding=5).grid(row=linha, column=0, columnspan=2)

# Label com link para o GitHub
def open_github(event):
    webbrowser.open_new("https://github.com/mcampos58")

# Import the Image and ImageTk modules

# Load the GitHub icon image
github_icon_path = Path(__file__).parent / 'github_icon.png'
github_icon = Image.open(github_icon_path)
github_icon = github_icon.resize((16, 16))
github_icon = ImageTk.PhotoImage(github_icon)

# Create a label with the GitHub icon and text
link = ttk.Label(app, text=" GitHub: mcampos58", image=github_icon, compound='left', cursor='hand', padding=10)
link.grid(row=linha + 1, column=0, columnspan=2)
link.bind("<Button-1>", open_github)


# Iniciar a interface
app.mainloop()
