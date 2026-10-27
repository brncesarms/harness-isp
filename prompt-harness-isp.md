# Prompt de Criação: HarnessISP

Você é um desenvolvedor especialista em automação Desktop em Python e engenheiro de redes sênior especializado em Provedores de Internet (ISPs).

Sua tarefa é criar a estrutura inicial e funcional (MVP) do **HarnessISP**, um assistente de área de trabalho flutuante e interativo que utiliza a **Antigravity CLI** (`agy` / `antigravity`) como motor de inteligência artificial para profissionais e técnicos de redes/infraestrutura de ISPs.

---

## 1. Visão Geral do Projeto
- **Nome do Projeto**: `HarnessISP`
- **Público-Alvo**: Engenheiros de redes, analistas de NOC e técnicos de provedores de internet (ISPs).
- **Conceito**: Um widget flutuante (uma esfera interativa na área de trabalho) que serve como interface visual para o Harness de IA, executando e gerenciando a Antigravity CLI em segundo plano.

---

## 2. Requisitos de Funcionalidades e Comportamento

### A. Primeira Execução e Persistência de Dados
- **Seleção de Diretório**: Na primeira inicialização, se a pasta do projeto ainda não estiver configurada, o assistente deve solicitar interativamente ao usuário em qual diretório da máquina ele deseja salvar o workspace do HarnessISP (ex: `~/HarnessISP_Data` ou `C:\HarnessISP_Data`).
- **Persistência Local**: Todos os logs de rede, histórico de conversas, scripts de roteadores gerados (MikroTik, Huawei, Cisco, Datacom) e a evolução de conhecimento do harness devem ser salvos estritamente dentro da pasta escolhida pelo usuário.

### B. Widget Flutuante Interativo (Interface Gráfica)
- **Visual**: Esfera estilizada na área de trabalho desenvolvida com **PySide6** (`Qt.FramelessWindowHint`, `Qt.WindowStaysOnTopHint`, `Qt.WA_TranslucentBackground`).
- **Interação de Clique**:
  - Clique rápido com botão esquerdo abre/fecha o painel de chat de redes.
  - Animação ou resposta visual imediata ao clicar (ex: leve pulso ou mudança de brilho).
- **Interação de Arraste (Drag & Drop)**:
  - Movimentação suave ao arrastar a bola com o mouse.
  - Efeito visual de deformação elástica/extensão durante o arraste para indicar movimento.
  - Ao soltar o mouse, a bola deve retornar suavemente à posição final com efeito de mola (*bounce*) e voltar à animação de flutuação (*idle*).
- **Estados Visuais / Emocionais de Rede**:
  - **Estável / OK** (Verde/Azul suave): Operação normal, links estáveis.
  - **Em Processamento / Análise** (Amarelo pulsante): Executando diagnósticos ou consultando a CLI.
  - **Alerta / Erro** (Vermelho/Laranja): Falha de conexão, perda de pacotes ou erro em scripts de roteadores.

### C. Integração com a Antigravity CLI (Motor do Harness)
- **Instalação e Login Assistidos**:
  - O assistente deve verificar se a CLI do Antigravity (`antigravity` ou `agy`) está instalada no sistema.
  - Se não estiver, deve guiar o usuário na execução dos scripts de instalação automática no Windows (`install.ps1`) ou Linux (`install.sh`) e no login interativo.
- **Especialização em Redes e ISP**:
  - O HarnessISP deve ser pré-configurado com prompts e contexto voltados para infraestrutura de ISP:
    - Geração e validação de configurações em **MikroTik (RouterOS)**, **Huawei (VRP)**, **Cisco (IOS)** e **Datacom**.
    - Análise de BGP (Peering, ASN, rotas), OSPF, VLANs, MPLS e sinais de fibra/FTTH (OLT/ONU).
    - Interpretação de logs de terminal e saídas de comandos (`ping`, `traceroute`, `mtr`, `nslookup`).

### D. Interface de Chat / Terminal
- Balão de conversa fixado ao lado da bola flutuante.
- Suporte a mensagens de texto e botões com atalhos rápidos para tarefas comuns de NOC (ex: *"Validar Script MikroTik"*, *"Analisar Log BGP"*, *"Checar Latência"*).

---

## 3. Arquitetura do Código

Organize o projeto de forma modular em Python:
- `main.py`: Ponto de entrada do aplicativo.
- `gui/widget.py`: Implementação da janela flutuante PySide6, animações e eventos de mouse.
- `gui/chat.py`: Interface de chat e botões de ação do NOC.
- `core/storage.py`: Gerenciador de arquivos, seleção de pasta inicial e persistência de dados.
- `core/cli_bridge.py`: Wrapper para execução e comunicação com a Antigravity CLI (`subprocess` / `QProcess`).

---

## 4. Entregáveis Esperados
1. Código Python completo, modular e documentado.
2. Arquivo `requirements.txt` (incluindo `PySide6` e dependências necessárias).
3. Arquivo `README.md` com instruções detalhadas de instalação e execução para Windows e Linux.
