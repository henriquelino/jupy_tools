#!/usr/bin/env python
# coding: utf-8

import json
import sys
import os
from subprocess import Popen, PIPE
import re
import time
import PySimpleGUI as sg

import threading
import threading, queue
import time
work_return = 0

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    
    application_path, _ = os.path.split(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    
# VARIAVEIS PARA ALTERAR
##################################################################################################################
maintainer_email = 'henrique@bpatechnologies.com'
maintainer_name = 'Henrique Lino'
libs_to_install = "pip install jupyterthemes nbopen keyboard mouse pyautoit opencv-python selenium pyautogui ahk unidecode system_hotkey import-ipynb pywinauto workalendar"

##################################################################################################################
print (f'aplication path é : "{application_path}"')

# salva local do arquivo contendo as extensoes
arquivo_json_exts = f"{application_path}\extensions.json"
print (f'O path para extensões é: "{arquivo_json_exts}"')

# salva local do arquivo contendo as bibliotecas
arquivo_json_libs = f"{application_path}\libs.json"
print (f'O path para bibliotecas é: "{arquivo_json_libs}"')

log_file = rf'{application_path}\install_log.txt'


def check_log_exists():
    """
    Checa se o arquivo de log existe, caso não, cria um arquivo
    """
    
    if not os.path.isfile(log_file):
        print(f"Arquivo '{log_file}' não existe, tentando criar!")
        try:
            with open(log_file, "w") as f:
                f.write("")
                f.close()
        except Exception as e:
            print(f"Falha ao criar arquivo {log_file}! O erro foi:\n\t'{e}'")
            
    return


def run_bash(command, show = False,*, log = False, mode = 'a'):
    """
    command : comando bash a rodar
    show : mostra o output em print
    log : save output to a file ?
    mode : (a)ppend [adiciona ao final do arquivo], (w)rite [apaga tudo e escreve]
    """

    try:
        retorno_bash = Popen(command, stdout=PIPE, stderr=PIPE)
    except Exception as e:
        print(f'Erro!\n>>{e}\nO comando existe? O caminho existe? Comando: {command}')
        return
    output_std, output_err = retorno_bash.communicate()
    
    if log:
        with open(log,mode) as f:
            f.write('*'*50 + '\n')
            f.write('>>>>COMANDO QUE ESTOU RODANDO "' + str(command) + '"<<<<\n')
            f.write('*'*50+ '\n\n')
            f.close()
            
    output_std = output_std.decode("utf-8")
    output_err = output_err.decode("utf-8")
    if output_std:
        if show:
            print(output_std)
        if log:
            with open(log,mode) as f:
                f.write(f'{output_std}')
                f.close()
        return output_std
    else:
        if show:
            print(output_err)
        if log:
            with open(log,mode) as f:
                f.write(f'{output_err}')
                f.close()
        return output_err


def stop_notebooks():
    print('Now stopping notebooks')
    # verifica quais portas o jupyter notebook está usando
    output_bash = run_bash("jupyter notebook stop 0")

    # faz um regex no retorno do comando, pegando as portas dos notebooks ativos
    active_notebooks = re.findall("\d{4}", output_bash)
    
    # passa por cada porta encerrando os notebooks
    for port in active_notebooks:
        run_bash(f'jupyter notebook stop {port}', show=False, log = log_file, mode = 'a')

    print('Done stopping notebooks')

    return


def install(json_extensions, libs_json):
    """
    json_extensions : lista com as extensoes a serem ativadas
    libs_json : lista com as libs para instalar
    """
    print('now installing')
    
    # passa por cada lib e instala
    for lib in libs_json:
        run_bash(f'pip install {lib}', show=False, log = log_file, mode = 'a')

    run_bash(libs_to_install)
    # configura pra abrir os notebooks com 2 clicks
    run_bash("python -m nbopen.install_win")

    # reinstala o matplotlib pro jupyter theme funcionar
    run_bash(f'python -m pip install -I matplotlib', show=False) #apenas se o jupyter theme não funcionar!!
    
    # realiza a instalação normal das extensões (nem sempre funciona, não consigo entender, por isso tem a versão local)
    run_bash(f'pip install jupyter_contrib_nbextensions --user --no-warn-script-location', show=False, log = log_file, mode = 'a')
    run_bash(f'jupyter contrib nbextension install --user', show=False, log = log_file, mode = 'a')
    run_bash(f'pip install jupyter_nbextensions_configurator --user', show=False, log = log_file, mode = 'a')
    run_bash(f'jupyter nbextensions_configurator enable --user', show=False, log = log_file, mode = 'a') #não rodar, causa bug, precisa de mais testes!

    # realiza a instalação "local" pois muitas vezes a anterior sozinha não dá certo!
    run_bash(rf'python "{application_path}\jupyter_contrib_nbextensions\application.py" install --user', show=False, log = log_file, mode = 'a')
    run_bash(rf'python "{application_path}\jupyter_nbextensions_configurator\application.py" enable --user', show=False, log = log_file, mode = 'a')
            
    #Loopa pelas extensões ATIVANDO cada uma
    for extension in json_extensions:
        run_bash(f'jupyter nbextension enable {extension}', show=False, log = log_file, mode = 'a')
        
    print('done installing')

    return


def uninstall(json_extensions):
    # Loopa pelas extensões DESATIVANDO cada uma
    for extension in json_extensions:
        run_bash(f'jupyter nbextension disable {extension}', show=False, log = log_file, mode = 'a')
    
    # desinstala as extensoes
    run_bash(f'jupyter nbextensions_configurator disable', show=False, log = log_file, mode = 'a')
    run_bash(f'jupyter contrib nbextension uninstall --user', show=False, log = log_file, mode = 'a')
    run_bash(f'jupyter contrib nbextension uninstall', show=False, log = log_file, mode = 'a')
    run_bash(f'pip uninstall jupyter_contrib_nbextensions -y', show=False, log = log_file, mode = 'a')
    run_bash(f'pip uninstall jupyter_nbextensions_configurator -y', show=False, log = log_file, mode = 'a')
        
    print('done uninstall')

    return


def _end_():
    """
    Finaliza alterando o log pro formato [HHh_MMm_SSs]_[user]
    """
    print('ending')
    who = run_bash(f'whoami', show = False)
    who = who.replace('\n','')
    who = who.replace('\r','')
    who = who.replace('\\','-')
    time_log = time.strftime('%Y-%m-%d--%Hh_%Mm_%Ss')
    output_path = rf'{application_path}\logs'
    
    if not os.path.isdir(output_path):
        try:
            os.makedirs(output_path)
        except Exception as e:
            print(f"Erro ao criar diretório '{output_path}'!\n\t'{e}'")
        
    try:
        os.rename(log_file, fr'{output_path}\{time_log}_{who}_log.txt')
    except Exception as e:
        print(f'Erro ao renomear arquivo!\n\t{e}')

    print('done')
    return


def worker(CLOSE_BOOKS,INSTALL,UNINSTALL,NOTHING):
    global work_return    
    global application_path

    print('now at worker')
    check_log_exists()

    try:
        with open(arquivo_json_exts) as j:
            json_extensions = json.load(j)
    except Exception as e:
        print(f"Erro ao ler arquivo {arquivo_json_exts}, o erro foi:\n\t>>{e}<<")
    
    try:
        with open(arquivo_json_libs) as j:
            json_libs = json.load(j)
    except Exception as e:
        print(f"Erro ao ler arquivo {arquivo_json_libs}, o erro foi:\n\t>>{e}<<")
    
    if CLOSE_BOOKS:
        stop_notebooks()
    if INSTALL:
        install(json_extensions, json_libs)
    elif UNINSTALL:
        uninstall(json_extensions)
    elif NOTHING:
        print('DO NOTHING')
        
    _end_()
        
    print('done working')
    work_return = 1
    return

 ###########################################################################################################
 ###########################################################################################################

theme_list = [
    'chesterish',
    'grade3',
    'gruvboxd',
    'gruvboxl',
    'monokai',
    'oceans16',
    'onedork',
    'solarizedd',
    'solarizedl'
]

lib_list = [


]
 ###########################################################################################################
 ###########################################################################################################

layout = [
#primeira linha, Status e %status%
[sg.Text('Status:', font='Any 13'), sg.Text('Idle', key="-STATUS-", size=(20, 1), font='Any 13')],

[sg.HorizontalSeparator()], # separador

[sg.Text('Extensões e Libs', font='Any 13'),], # Nome da seção

[sg.Radio('Instalar', "RADIO1",tooltip='  Instala as libs mais usadas  ',  key='-INSTALL-'),
 sg.Radio('Desinstalar', "RADIO1",tooltip='  Desinstala o NBExtensions e desativa as extensões  ', key='-UNINSTALL-'),
 sg.Radio('Não fazer nada', "RADIO1",tooltip='  Marcar para debug ou caso queira apenas fechar os notebooks abertos :)  ',default=True, key='-NOTHING-'),], # opções de instalar ou desinstalar
[sg.Checkbox('Fechar notebooks abertos', default=True,key='-CLOSE_BOOKS-', font='Any 13')], 
[sg.Button('Run', key='-RUN-', tooltip='Aplica a ação selecionada (instala ou desinstala)')],
[sg.HorizontalSeparator()], # separador

[sg.Text('Alterar tema do Notebook', font='Any 13'),], # Outra seção

[sg.Text('Tema: '),
 sg.Combo(theme_list, key='-THEME_TO_INSTALL-',tooltip='  Tema a ser aplicado  ', size=(30,1), default_value= 'onedork'),],

########################################## PRIMEIRO FRAME FRAME, TAMANHOS
[sg.Frame('Tamanho das Fontes/Editor',[ #cria um frame
[sg.Spin([i for i in range(1,20)],tooltip='  Tamanho da fonte para as células de código  ', key='-CODE_SIZE-', initial_value=13, size=(3,1)),
 sg.Text('Código'),
 sg.Spin([i for i in range(1,20)],tooltip='  Tamanho da fonte para o Output das células  ', key='-OUTPUT_SIZE-', initial_value=13, size=(3,1)),
 sg.Text('Output'),
 sg.Spin([i for i in range(1,20)],tooltip='  Tamanho da fonte para células markdown  ', key='-MARKDOWN_SIZE-', initial_value=13, size=(3,1)),
 sg.Text('MarkDown'),], # tamanho das fontes

[sg.Spin([i for i in range(1,100)],tooltip='  Tamanho da célula, em %  ', key='-CELL_W-', initial_value=90, size=(4,1)),
 sg.Text('Largura célula (%)'),
 sg.Spin([i for i in range(1,20)],tooltip='  Altura da linha, em pixels  ', key='-LINE_H-', initial_value=170, size=(4,1)),
 sg.Text('Altura da linha(pixel)'),], #tamanho das células e linha
],),], 
########################################## SEGUNDO FRAME, OUTROS
[sg.Frame('Outros',[ #cria outro frame
[sg.Text('Mostrar: ')],
[sg.Checkbox('Kernel logo',tooltip='  mostra o logo do Kernel', default=True, key='-SHOW_KERNEL_LOGO-'), 
 sg.Checkbox('Nome & Logo', tooltip='  Mostra o nome e o logo  ',default=True, key='-SHOW_NAME_LOGO-'), 
 sg.Checkbox('Toolbar',tooltip='  Mostra a barra de ferramenta  ', default=True, key='-SHOW_TOOLBAR_LOGO-'), ], # O que mostrar

[sg.HorizontalSeparator()],

[sg.Text('Backgrounds das celulas: ')],
[sg.Checkbox('Markdown',tooltip='  Ativa/Desativa o background das células markdown  ', default=True, key='-MARKDOWN_BG-'), 
 sg.Checkbox('Output',tooltip='  Ativa/Desativa o background das células de output  ', default=True, key='-OUTPUT_BG-'), 
 sg.Checkbox('Prompts',tooltip='  ', default=True, key='-PROMP_BG-'),], # Backgrounds
],),],


[sg.Button('Aplicar',tooltip='  Aplica o tema selecionado  ', key='-APLICAR_TEMA-'),
 sg.Button('Retirar',tooltip='  Reseta o tema do jupyter notebook  ', key='-RETIRA_TEMA-'),
 sg.Button('Sobre os temas', key='-ABOUT_THEMES-')], #Botões para aplicar ou retirar o tema

[sg.HorizontalSeparator()],


[sg.Button('Sobre o programa', key='-ABOUT-'), sg.Quit()],
]
 ###########################################################################################################
 ###########################################################################################################
window = sg.Window('Jupyter Extensions', layout)

window_info_active = False


# Event loop. Read buttons, make callbacks
while True:
    try:
        event, value = window.read(timeout=500)
#         event, value = window.read()

#         print("event: '" + str(event) + "'\nvalue: '" + str(value) + "'")
        if event in ('Quit', sg.WIN_CLOSED):
           break
        if event == '-ABOUT_THEMES-':
            os.system("start \"\" https://github.com/dunovank/jupyter-themes")

        if event == '-ABOUT-' and not window_info_active:          
            window_info_active = True
            layout_info = [
                
                [sg.Text('')],
                [sg.Text('-- Feito com carinho pelo Lino para facilitar a instalação das extensões no Jupyter e termos um ambiente bonito para trabalhar :)', font='any 13', size=(30,5))],
                [sg.Text('')],
                [sg.HorizontalSeparator()],
                [sg.Text('')],
                [sg.Text(f'-- Dúvidas, bugs ou sugestões, envie para "{maintainer_name}" no e-mail "{maintainer_email}"', font='any 13', size=(30,5))],
                [sg.Button('Sair', key='-SAIR_ABOUT-')],
            ]
            
            window_about = sg.Window('About', layout_info)
            while True:
                event_about, value_about = window_about.read()
                if event_about in ('Quit', sg.WIN_CLOSED, '-SAIR_ABOUT-'):
                    window_about.close()
                    window_info_active = False
                    break

        if event == '-APLICAR_TEMA-' :          
           
            if value['-MARKDOWN_BG-']:
                bg_markdown = '-altmd'
            else:
                bg_markdown = ''
                
            if value['-OUTPUT_BG-']:
                bg_output = '-altout'
            else:
                bg_output = ''
                
            if value['-PROMP_BG-']:
                bg_prompt = '-altp'
            else:
                bg_prompt = ''

            if value['-SHOW_KERNEL_LOGO-']:
                show_kernel = '-kl'
            else:
                show_kernel = ''

            if value['-SHOW_NAME_LOGO-']:
                show_name = '-N'
            else:
                show_name = ''

            if value['-SHOW_TOOLBAR_LOGO-']:
                show_toolbar = '-T'
            else:
                show_toolbar = ''

            code_to_run = f"jt -t {value['-THEME_TO_INSTALL-']} {show_kernel} {show_name} {show_toolbar} {bg_prompt} {bg_output} {bg_markdown} -fs {value['-CODE_SIZE-']} -nfs {value['-MARKDOWN_SIZE-']} -ofs {value['-OUTPUT_SIZE-']} -cellw {value['-CELL_W-']}% -lineh {value['-LINE_H-']}"
            run_bash(code_to_run)
            
        if event == '-RETIRA_TEMA-':
            code_to_run = 'jt -r'
            run_bash(code_to_run)
         
        if event == '-RUN-':
            threading.Thread(target=worker, 
                             args=(value['-CLOSE_BOOKS-'],
                                   value['-INSTALL-'],
                                   value['-UNINSTALL-'],
                                   value['-NOTHING-']),
                             daemon=True).start()
            window['-STATUS-'].update('Running', text_color='red')
            window['-RUN-'].update(disabled=True)
           
        if work_return == 1:
            sg.PopupAnnoying('Done!')
            work_return = 0
            window['-RUN-'].update(disabled=False)
            window['-STATUS-'].update('Done!', text_color='blue')
       
    except Exception as e:
        print(f'ERRO!!\n\t{e}')
        window.close()


window.close()