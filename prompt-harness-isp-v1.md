# Prompt de Criação: HarnessISP (v1)
> **Base de Inspiração:** Arquitetura Híbrida Archimedes + Antigravity CLI  
> **Domínio:** Engenharia de Redes & Operação de NOC para Provedores de Internet (ISPs)

Você é um desenvolvedor sênior em automação Desktop em Python e engenheiro de redes especializado em Provedores de Internet (ISPs), com domínio em arquiteturas agênticas seguras, economia de tokens e frameworks gráficos modernos.

Sua tarefa é criar a estrutura inicial, modular e totalmente funcional (MVP Robusto) do **HarnessISP**, um assistente de área de trabalho flutuante interativo que utiliza a **Antigravity CLI** (`agy` / `antigravity`) como motor cognitivo para analistas de NOC e engenheiros de redes de ISPs.

---

## 1. Visão Geral do Projeto
- **Nome do Projeto**: `HarnessISP`
- **Público-Alvo**: Engenheiros de redes, analistas de NOC e técnicos de campo de ISPs.
- **Conceito**: Um widget flutuante (esfera interativa na área de trabalho com física de mola e animações táteis) associado a um painel de chat de diagnósticos de rede e atalhos de NOC. O backend orquestra sessões com a Antigravity CLI de forma assíncrona, incorporando os princípios de resiliência, isolamento de memória e economia de tokens herdados do projeto Archimedes.

---

## 2. Princípios Herdados da Arquitetura Archimedes

O HarnessISP deve incorporar diretamente os padrões de sucesso do ecossistema Archimedes:

1. **Token Economy (RTK & Filtros Determinísticos):**
   - Saídas cruas de diagnósticos (`ip route print`, `show bgp summary`, tabelas de rotas extensas de BGP, MTR longo) **nunca** devem ser despejadas sem tratamento no LLM.
   - O core deve incluir pré-processamento via parsers estruturados (`jc`, filtros regex ou hooks estilo `rtk`) para resumir métricas de estado antes de despachar para o contexto do Antigravity.
2. **Arquitetura de Memória Isolada (SSOT & RAG FTS5):**
   - Separação mandatória entre o **workspace de trabalho** (onde ficam logs e scripts temporários) e a **base de conhecimento persistente do provedor** (armazenada em SQLite FTS5 ou notas atômicas em Markdown):
     - Dicionário de POPs, topologia de enlaces, faixas de IP/ASN, VLANs canônicas e histórico de incidentes.
3. **Escudo Zero Leaks (Cofre Seguro AES-256-GCM):**
   - Senhas de roteadores (MikroTik, Huawei, Cisco, OLTs), comunidades SNMP e senhas de peering BGP **jamais** devem ser salvas em texto puro nem enviadas ao prompt do modelo.
   - Implementar módulo `core/vault.py` para armazenar credenciais criptografadas localmente com injeção apenas em memória durante comandos locais.
4. **Determinismo Tool-First:**
   - Antes de consultar a inteligência artificial, o assistente prioriza a execução de ferramentas de rede locais (`net_tools`: ICMP ping, MTR, DNS resolution, RDAP Whois de ASN/prefixo) para coletar dados empíricos reais.
5. **Recursão de Lições Aprendidas (`reflect`):**
   - Após a resolução de incidentes ou configuração complexa, o operador pode salvar uma lição atômica na memória persistente (causa raiz, impacto, solução aplicada), enriquecendo o RAG do assistente.
6. **Regra de Emancipação:**
   - Detecção de rotinas recorrentes de NOC: caso o operador execute uma validação manual 3 vezes, o sistema deve sugerir a criação de um atalho/skill determinística.

---

## 3. Requisitos de Funcionalidades e Comportamento

### A. Primeira Execução e Persistência de Dados
- **Seleção de Workspace**: No primeiro start, se não configurado, abrir diálogo interativo solicitando a pasta do workspace (ex: `~/HarnessISP_Data` no Linux ou `C:\HarnessISP_Data` no Windows).
- **Estrutura do Workspace**:
  ```text
  HarnessISP_Data/
  ├── memory/              # Base SQLite FTS5 e notas atômicas do provedor
  ├── scripts/             # Scripts gerados (MikroTik, Huawei, Cisco, etc.)
  ├── logs/                # Histórico de incidentes e sessões de NOC
  ├── vault/               # Cofre criptografado de credenciais
  └── config.yaml          # Configurações do operador
  ```

### B. Widget Flutuante Interativo (PySide6)
- **Visual**: Esfera estilizada com gradientes modernos, brilho neon sutil (`Qt.FramelessWindowHint`, `Qt.WindowStaysOnTopHint`, `Qt.WA_TranslucentBackground`).
- **Compatibilidade Wayland / X11**:
  - Detecção de ambiente Linux: se rodando em Wayland sem suporte direto a posicionamento absoluto via mouse, prever fallback via `QT_QPA_PLATFORM=xcb` ou atalho global de teclado (`F12` / `Super+N`).
- **Física & Animações**:
  - Arraste suave com deformação elástica (efeito squash & stretch) na direção do movimento.
  - Ao soltar o cursor, animação de retorno elástico (*spring bounce*) e transição suave para oscilação flutuante ociosa (*idle float*).
  - Clique esquerdo: expande/contrai o painel lateral de chat e ações rápidas.
- **Estados Visuais de Rede (LED / Halo Dinâmico)**:
  - **Verde/Ciano (Estável):** Enlaces ativos, CLI pronta, telemetria nominal.
  - **Amarelo Pulsante (Processando):** Streaming ativo com a CLI ou diagnóstico de rede em execução.
  - **Vermelho/Laranja (Alerta NOC):** Falha de conexão, perda crítica de pacotes, erro em sintaxe de script ou alerta de BGP down.
- **System Tray (Bandeja):**
  - Ícone na bandeja do sistema para ocultar/exibir a esfera e acessar rapidamente o status sem ocupar a tela durante o uso do WinBox/SSH.

### C. Integração com a Antigravity CLI (`agy`)
- **Verificação e Setup Assistido**:
  - Checar presença de `antigravity` ou `agy` no `$PATH`. Caso ausente, guiar instalação automatizada e fluxo de login.
- **Comunicação por Daemon / Sessão Persistente**:
  - Manter sessão contínua assíncrona (via `QProcess` ou `asyncio.subprocess` com streaming NDJSON), preservando contexto multi-turn sem overhead de inicialização repetida.
- **Skills Nativas Especializadas**:
  - Suporte ao carregamento de skills nativas do Antigravity (`.gemini/skills/`):
    - `mikrotik-ros`: Diferenciação rigorosa entre RouterOS v6 e v7 (routing filters e BGP).
    - `huawei-vrp`: VRP CLI para roteadores NE e switches CloudEngine.
    - `cisco-ios`: Configuração de BGP, VRF, subinterfaces e ACLs.
    - `datacom-dm`: Switches e roteadores DmOS.
    - `ftth-diagnostics`: Leitura de potência óptica de ONUs/OLTs e atenuação.

### D. Painel de Chat & Ações Rápidas de NOC
- Balão acoplado à esfera com visual Dark Mode profissional de NOC.
- **Botões de Ação Rápida**:
  - `[🔍 MTR / Ping]`: Teste de latência e perda em múltiplos saltos.
  - `[🌐 Consulta BGP / ASN]`: Checagem de anúncios de rota e filtros.
  - `[⚙️ Validar Script MikroTik]`: Checagem estática de sintaxe ROS v6 vs v7.
  - `[🛡️ Gerar Regras Bogon / Anti-DDoS]`: Listas de proteção de infraestrutura.
- **Two-Man Rule (Diff de Segurança)**:
  - Scripts gerados que causem alteração de tabelas de roteamento ou firewall exibem um Diff claro (`antes vs depois`) com marcação de risco antes de permitir cópia ou exportação.

---

## 4. Arquitetura Modular Proposta

```text
harness-isp/
├── main.py                     # Inicialização da aplicação PySide6
├── requirements.txt            # PySide6, pydantic, pyyaml, cryptography, jc
├── README.md                   # Instruções para Linux (Wayland/X11) e Windows
├── core/
│   ├── __init__.py
│   ├── cli_bridge.py           # Conexão assíncrona streaming com Antigravity CLI
│   ├── session.py              # Gestão de contexto e turnos de chat
│   ├── storage.py              # Gestão de workspace e diretórios de dados
│   ├── memory_rag.py           # SQLite FTS5 para documentação e lições aprendidas
│   ├── vault.py                # Cofre AES-256-GCM para credenciais
│   ├── net_tools.py            # Execução de ping, mtr, whois e parsers (jc)
│   └── token_optimizer.py      # Compressão e filtros determinísticos (RTK Hook)
├── gui/
│   ├── __init__.py
│   ├── widget.py               # Esfera flutuante, física de mola e drag & drop
│   ├── chat_panel.py           # Janela de chat, renderizador Markdown e diffs
│   ├── tray.py                 # Ícone na bandeja do sistema
│   └── styles.py               # Tema escuro e paleta de cores para NOC
└── skills/                     # Skills embutidas para o Antigravity
    ├── mikrotik/SKILL.md
    ├── huawei/SKILL.md
    └── bgp-peering/SKILL.md
```

---

## 5. Entregáveis Esperados
1. Código Python completo, modular, tipado (`type hints`) e documentado.
2. Arquivo `requirements.txt` com todas as dependências pinadas.
3. Arquivo `README.md` completo com guia de instalação para Linux e Windows.
4. Suíte inicial de testes com `pytest` cobrindo o cofre (`vault.py`), otimizador de tokens (`token_optimizer.py`) e conexão da CLI (`cli_bridge.py`).
