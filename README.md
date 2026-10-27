# ⚡ HarnessISP - Desktop Companion Inteligente para Redes e Provedores (ISPs)

> **Arquitetura:** Híbrida (PySide6 + Antigravity CLI + Archimedes Zero-Leaks Engine)  
> **Especialidade:** Engenharia de Redes, FTTH/GPON & NOC Operacional  
> **Pilar Central:** Blindagem Anti-Lockout & Desktop Companion (Inspirado no Coucou)

---

## 1. Visão Geral

O **HarnessISP** é um assistente de desktop flutuante projetado para analistas de NOC, técnicos de campo e engenheiros de redes de Provedores de Internet (ISPs).

Inspirado no design minimalista e tátil do projeto **Coucou**, ele combina:
1. **Desktop Companion Expressivo (PySide6):**
   - **Mascote Reativo NOC:** Olhos expressivos com piscada natural e halo dinâmico reagindo a estados da rede (Normal, Escaneando/Processando, Alerta de Lockout, Safe Mode).
   - **Context Dropping:** Arraste e solte arquivos de rede (.rsc, .backup, .log, .csv, .txt) diretamente sobre o mascote para auditoria instantânea de firewall, detecção de lockout ou diagnóstico óptico de OLT.
   - **Dynamic Island / Pill Mode:** Alternância com duplo-clique entre mascote esférico (80px) e pílula horizontal (320px) com telemetria viva (BGP Up, Ping, Atenuação dBm).
2. **Pílula de Pré-flight Approval (HITL com 1 Clique):**
   - Diálogo flutuante acoplado ao companion que intercepta comandos de alto risco (ip route, interface disable, mtu, firewall drop).
   - Autorização imediata via teclado ou clique: [Safe-Mode (Enter)] com rollback automático, [Forçar] ou [Abortar (Esc)].
3. **Motor Antigravity CLI (agy):** Cognição avançada conectada a sessões persistentes e streaming contínuo.
4. **Blindagem Anti-Lockout (core/failsafe_guard.py):** Proteção ativa contra perda de acesso a roteadores (MikroTik, Huawei, Cisco, Datacom) e servidores Linux.
5. **Automação FTTH Multivendor (core/ftth_engine.py):** Diagnóstico de potência óptica dBm e provisionamento em OLTs Huawei, ZTE, Fiberhome e Datacom.
6. **Herança do Archimedes:**
   - **RTK Hook & Token Economy:** Compressão determinística de saídas extensas de rede.
   - **Memória RAG Isolada:** SQLite FTS5 com busca atômica de topologia, POPs e lições pós-incidente.
   - **Escudo Zero Leaks:** Cofre AES-256-GCM para credenciais de rede, injetadas estritamente em RAM.

---

## 2. Estrutura do Projeto

```text
harness-isp/
├── main.py                     # Entrypoint e orquestração do Desktop Companion e Approval Pill
├── AGENTS.md                   # Contrato de governança, comandos determinísticos e zero leaks
├── requirements.txt            # Dependências pinadas (PySide6, pydantic, cryptography, jc, pytest)
├── README.md                   # Documentação do projeto
├── prompt-harness-isp-v3.md    # Especificação master (Anti-Lockout, OLTs Multivendor, RAG)
├── core/
│   ├── storage.py              # Gestão do workspace (~/HarnessISP_Data) e backups prévios
│   ├── vault.py                # Cofre AES-256-GCM (Zero Leaks)
│   ├── token_optimizer.py      # Hook e compressor RTK nativo (Rust v1.1.0)
│   ├── memory_rag.py           # Ingestor SQLite FTS5 sincronizado com Markdown
│   ├── reflect.py              # Gerador de notas atômicas pós-incidente / post-mortem
│   ├── failsafe_guard.py       # Validador Anti-Lockout, Safe Mode e Rollbacks
│   ├── ftth_engine.py          # Diagnósticos ópticos e provisionamento OLT
│   ├── net_tools.py            # Utilitários determinísticos (Ping, MTR, DNS, RDAP)
│   ├── session.py              # Máquina de estados e histórico do chat
│   └── cli_bridge.py           # Ponte assíncrona streaming com Antigravity CLI
├── gui/
│   ├── styles.py               # QSS Dark Mode e design system NOC
│   ├── widget.py               # Desktop Companion: Mascote com olhos expressivos, Context Drop e Dynamic Island
│   ├── approval_pill.py        # Pílula flutuante de autorização rápida pré-flight (Coucou-style)
│   ├── chat_panel.py           # Painel lateral expansível com atalhos de NOC
│   └── tray.py                 # Ícone na bandeja do sistema
├── wiki/                       # Base de conhecimento SSOT em Markdown (Obsidian)
└── tests/                      # Suíte de testes automatizados com pytest (20 testes)
```

---

## 3. Instalação e Execução

```bash
# 1. Clone ou acesse o diretório
git clone https://github.com/brncesarms/harness-isp.git
cd harness-isp

# 2. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a suíte de testes
pytest -v

# 5. Inicie o companion
python main.py
```

---

## 4. Cobertura de Testes

Os 20 testes cobrem:
* **Coucou-Style Companion:** Instanciação, física de arraste, alternância Dynamic Island e renderização facial.
* **Pre-flight Approval Pill:** Disparo de popup flutuante, atalhos de teclado e decisões Safe-Mode/Abort.
* **Context Dropping:** Recepção de arquivos de script e rotas.
* **Anti-Lockout:** Detecção de regras de drop na chain input, alteração de MTU e bloqueio de SSH.
* **Cofre Seguro:** Criptografia AES-256-GCM com isolamento contra vazamento de credenciais.
* **Token Economy (RTK):** Resumo sintético de tabelas de BGP, ping ICMP, traceroute e potências ópticas de OLT.
* **FTTH Engine:** Avaliação de níveis de atenuação óptica (Class B+/C+) e parsing de display ont autofind.
* **RAG SQLite FTS5:** Indexação e busca atômica de notas técnicas e topologia de POPs.
