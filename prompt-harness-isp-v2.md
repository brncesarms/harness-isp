# Prompt de Criação: HarnessISP (v2)
> **Base de Inspiração:** Arquitetura Híbrida Archimedes + Antigravity CLI  
> **Domínio:** Engenharia de Redes & Operação de NOC para Provedores de Internet (ISPs)  
> **Pilar Crítico Adicionado:** Anti-Lockout & Fail-Safe Engine (Proteção Absoluta contra Trancamento de Roteadores e Linux)

Você é um desenvolvedor sênior em automação Desktop em Python e engenheiro de redes sênior especializado em Provedores de Internet (ISPs), com domínio em arquiteturas agênticas seguras, economia de tokens, fail-safe operacional e frameworks gráficos modernos.

Sua tarefa é criar a estrutura inicial, modular e totalmente funcional (MVP Robusto) do **HarnessISP**, um assistente de área de trabalho flutuante interativo que utiliza a **Antigravity CLI** (`agy` / `antigravity`) como motor cognitivo para analistas de NOC e engenheiros de redes de ISPs.

---

## 1. Visão Geral do Projeto
- **Nome do Projeto**: `HarnessISP`
- **Público-Alvo**: Engenheiros de redes, analistas de NOC e técnicos de campo de ISPs.
- **Conceito**: Um widget flutuante (esfera interativa na área de trabalho com física de mola e animações táteis) associado a um painel de chat de diagnósticos de rede e atalhos de NOC. O backend orquestra sessões com a Antigravity CLI de forma assíncrona, incorporando os princípios de resiliência, isolamento de memória, economia de tokens do projeto Archimedes e uma **blindagem estrita anti-lockout** em roteadores e sistemas Linux.

---

## 2. Pilar Fundamental: Anti-Lockout & Fail-Safe Engine (Zero Trancamentos)

O pesadelo número um de um ISP é o técnico ou a automação aplicar uma regra e ficar trancado fora do roteador de borda, concentrador PPPoE ou servidor Linux em produção. O **HarnessISP** possui mecanismos ativos de proteção em duas frentes:

### A. Proteção em Roteadores (MikroTik RouterOS, Cisco IOS, Huawei VRP, Datacom)
1. **Safe Mode & Commit Confirmed Mandatórios:**
   * **MikroTik (RouterOS):** Qualquer comando gerado ou executado que envolva firewall (`/ip firewall`), roteamento (`/ip route`, `/routing`), interfaces (`/interface`) ou serviços (`/ip service`) deve obrigatoriamente instruir ou utilizar **Safe Mode** (`<safe>` via API/SSH ou atalho `Ctrl+X` no terminal). Se a conexão cair, o roteador desfaz tudo automaticamente.
   * **Cisco / Datacom / Huawei:** Comandos de alteração devem obrigatoriamente adotar o padrão `commit confirmed <minutos>` ou a salvaguarda de `reload in <minutos>` antes de intervenções de alto risco.
2. **Pre-Flight Checks Anti-Suicídio:**
   * **Proteção de Interface de Gerência:** Bloqueio estrito de scripts que desativem a interface, bridge ou VLAN por onde a gerência/SSH atual trafega.
   * **Firewall "Drop All" Suicida:** A IA é proibida de gerar regras de `drop` na chain `input` sem validar previamente a existência da regra permitindo conexões ativas (`connection-state=established,related`) e aceitação explícita do bloco/IP de gerência na porta correta.
   * **Alterações de MTU e MSS:** Aviso sonoro e visual antes de alterações de MTU que possam quebrar túneis OSPF, MPLS ou sessões BGP.

### B. Proteção em Distribuições Linux (BNG/PPPoE, CGNAT, Proxies, DNS, FRR/BIRD, Debian/Ubuntu/Arch)
1. **Rollback Temporizado em Firewall (nftables / iptables / ufw):**
   * Nunca aplicar regras de firewall de forma direta e definitiva. O assistente gera/aplica sempre com script com **timer de auto-reversão** (ex: `sleep 60 && iptables-restore < backup.rules &`, cancelado apenas após o operador confirmar via heartbeat que a conectividade permanece ativa).
   * Teste de sintaxe prévio obrigatório (`nft -c -f` ou `iptables-restore --test`).
2. **Proteção de Acesso SSH e Sudo:**
   * Modificações em `/etc/ssh/sshd_config` ou `/etc/sudoers` exigem validação prévia de sintaxe (`sshd -t` e `visudo -c`).
   * Alerta explícito para **NUNCA** fechar a sessão SSH corrente antes de validar um login paralelo de teste.
3. **Gerenciamento de Rede Linux (Netplan, NetworkManager, systemd-networkd):**
   * Em distribuições modernas com Netplan, exigir sempre `netplan try` (com rollback automático após timeout) em vez de `netplan apply`.

---

## 3. Princípios Herdados da Arquitetura Archimedes

1. **Token Economy (RTK & Filtros Determinísticos):**
   - Saídas cruas de diagnósticos (`ip route print`, `show bgp summary`, tabelas de rotas extensas de BGP, MTR longo) **nunca** devem ser despejadas sem tratamento no LLM.
   - O core inclui pré-processamento via parsers estruturados (`jc`, filtros regex ou hooks estilo `rtk`) para resumir métricas de estado antes de despachar para o contexto do Antigravity.
2. **Arquitetura de Memória Isolada (SSOT & RAG FTS5):**
   - Separação mandatória entre o **workspace de trabalho** (onde ficam logs e scripts temporários) e a **base de conhecimento persistente do provedor** (armazenada em SQLite FTS5 ou notas atômicas em Markdown):
     - Dicionário de POPs, topologia de enlaces, faixas de IP/ASN, VLANs canônicas e histórico de incidentes.
3. **Escudo Zero Leaks (Cofre Seguro AES-256-GCM):**
   - Senhas de roteadores (MikroTik, Huawei, Cisco, OLTs), comunidades SNMP e senhas de peering BGP **jamais** devem ser salvas em texto puro nem enviadas ao prompt do modelo.
   - Implementar módulo `core/vault.py` para armazenar credenciais criptografadas localmente com injeção apenas em memória durante comandos locais.
4. **Determinismo Tool-First:**
   - Antes de consultar a inteligência artificial, o assistente prioriza a execução de ferramentas de rede locais (`net_tools`: ICMP ping, MTR, DNS resolution, RDAP Whois de ASN/prefixo) para coletar dados empíricos reais.
5. **Recursão de Lições Aprendidas (`reflect`):**
   - Registro atômico pós-incidente salvando causa raiz, impacto e solução para enriquecer a base RAG.
6. **Regra de Emancipação:**
   - Sugestão de conversão automática em skill de automação determinística para rotinas executadas 3 vezes.

---

## 4. Requisitos de Funcionalidades e Comportamento

### A. Primeira Execução e Persistência de Dados
- **Seleção de Workspace**: No primeiro start, abrir diálogo interativo solicitando a pasta do workspace (ex: `~/HarnessISP_Data` no Linux ou `C:\HarnessISP_Data` no Windows).
- **Estrutura do Workspace**:
  ```text
  HarnessISP_Data/
  ├── memory/              # Base SQLite FTS5 e notas atômicas do provedor
  ├── backups/             # Backups automáticos de configuração pré-alteração
  ├── scripts/             # Scripts gerados (MikroTik, Huawei, Cisco, Linux)
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
  - **Vermelho/Laranja (Alerta NOC / Risco Alto):** Falha de conexão, perda crítica de pacotes ou alerta de script de alto risco de lockout.
- **System Tray (Bandeja):**
  - Ícone na bandeja do sistema para ocultar/exibir a esfera e acessar rapidamente o status sem ocupar a tela durante o uso do WinBox/SSH.

### C. Integração com a Antigravity CLI (`agy`)
- **Verificação e Setup Assistido**:
  - Checar presença de `antigravity` ou `agy` no `$PATH`. Caso ausente, guiar instalação automatizada e fluxo de login.
- **Comunicação por Daemon / Sessão Persistente**:
  - Manter sessão contínua assíncrona (via `QProcess` ou `asyncio.subprocess` com streaming NDJSON), preservando contexto multi-turn sem overhead de inicialização repetida.
- **Skills Nativas Especializadas com Proteção Anti-Lockout**:
  - Carregamento de skills nativas do Antigravity (`.gemini/skills/`):
    - `mikrotik-safe-ops`: Automação RouterOS v6/v7 sempre com safe mode, validação de filter chains e pre-flight checks.
    - `linux-net-failsafe`: Configuração de BNG/CGNAT e roteamento Linux com timer de rollback automático.
    - `huawei-cisco-peering`: Configurações de BGP e MPLS com commit confirmed.
    - `ftth-diagnostics`: Leitura e diagnóstico de OLT/ONU.

### D. Painel de Chat & Ações Rápidas de NOC
- Balão acoplado à esfera com visual Dark Mode profissional de NOC.
- **Botões de Ação Rápida**:
  - `[🔍 MTR / Ping]`: Teste de latência e perda em múltiplos saltos.
  - `[🌐 Consulta BGP / ASN]`: Checagem de anúncios de rota e filtros.
  - `[⚙️ Validar Script MikroTik]`: Checagem estática de sintaxe ROS v6 vs v7 e auditoria anti-lockout.
  - `[🛡️ Gerar Regras Bogon / Anti-DDoS]`: Listas de proteção de infraestrutura com safe mode.
  - `[🔄 Backup de Emergência]`: Disparo de snapshot/backup antes de qualquer aplicação.
- **Two-Man Rule (Diff de Segurança & Lockout Risk Indicator)**:
  - Scripts gerados exibem um Diff claro (`antes vs depois`) com medidor de risco:
    - 🟢 Baixo (consultas, aliases)
    - 🟡 Médio (criação de VLANs secundárias, pools)
    - 🔴 Crítico (firewall, default route, BGP neighbor, MTU) — Exige confirmação explícita de safe mode e backup prévio!

---

## 5. Arquitetura Modular Proposta

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
│   ├── token_optimizer.py      # Compressão e filtros determinísticos (RTK Hook)
│   └── failsafe_guard.py       # Validador Anti-Lockout, Safe Mode e Rollbacks
├── gui/
│   ├── __init__.py
│   ├── widget.py               # Esfera flutuante, física de mola e drag & drop
│   ├── chat_panel.py           # Janela de chat, renderizador Markdown, diffs e alertas de risco
│   ├── tray.py                 # Ícone na bandeja do sistema
│   └── styles.py               # Tema escuro e paleta de cores para NOC
└── skills/                     # Skills embutidas para o Antigravity
    ├── mikrotik-safe/SKILL.md
    ├── linux-failsafe/SKILL.md
    └── bgp-peering/SKILL.md
```

---

## 6. Entregáveis Esperados
1. Código Python completo, modular, tipado (`type hints`) e documentado.
2. Arquivo `requirements.txt` com todas as dependências pinadas.
3. Arquivo `README.md` completo com guia de instalação para Linux e Windows.
4. Suíte inicial de testes com `pytest` cobrindo:
   - Validador Anti-Lockout (`failsafe_guard.py`): detecção de regras suicidas de firewall e falta de safe mode.
   - Cofre (`vault.py`): criptografia e injeção segura.
   - Otimizador de tokens (`token_optimizer.py`): compressão de saídas de rede.
   - Ponte da CLI (`cli_bridge.py`): testes de inicialização e streaming.
