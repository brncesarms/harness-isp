# ⚡ HarnessISP - Assistente Desktop Inteligente para ISPs

> **Arquitetura:** Híbrida (PySide6 + Antigravity CLI + Archimedes Zero-Leaks Engine)  
> **Especialidade:** Engenharia de Redes, FTTH/GPON & NOC Operacional  
> **Pilar Central:** Blindagem Anti-Lockout & Fail-Safe

---

## 1. Visão Geral

O **HarnessISP** é um assistente de desktop flutuante projetado especificamente para analistas de NOC, técnicos de campo e engenheiros de redes de Provedores de Internet (ISPs).

Ele combina:
1. **Esfera Interativa na Área de Trabalho (PySide6):** Widget flutuante com física elástica de mola (*spring/bounce*), deformação em arraste e halo dinâmico reagente aos estados da rede.
2. **Motor Antigravity CLI (`agy`):** Cognição avançada conectada a sessões persistentes e streaming contínuo.
3. **Blindagem Anti-Lockout (`core/failsafe_guard.py`):** Proteção ativa contra perda de acesso a roteadores (MikroTik, Huawei, Cisco, Datacom) e servidores Linux.
4. **Automação FTTH Multivendor (`core/ftth_engine.py`):** Diagnóstico de potência óptica dBm e provisionamento em OLTs Huawei, ZTE, Fiberhome e Datacom.
5. **Herança do Archimedes:**
   - **RTK Hook & Token Economy:** Compressão determinística de saídas extensas de rede (`jc` / regex).
   - **Memória RAG Isolada:** SQLite FTS5 com busca atômica de topologia, POPs e lições pós-incidente (`reflect`).
   - **Escudo Zero Leaks:** Cofre AES-256-GCM para credenciais de rede, injetadas estritamente em RAM.

---

## 2. Estrutura do Projeto

```text
harness-isp/
├── main.py                     # Entrypoint e inicialização da aplicação PySide6
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
│   ├── widget.py               # Esfera flutuante, física de mola e halo LED
│   ├── chat_panel.py           # Painel lateral expansível com atalhos de NOC
│   └── tray.py                 # Ícone na bandeja do sistema
├── wiki/                       # Base de conhecimento SSOT em Markdown (Obsidian)
│   ├── sops/                   # Procedimentos operacionais padrão (Lockout, GPON, etc.)
│   ├── pops/                   # Topologia e inventário de POPs
│   ├── incidentes/             # Post-mortems de rompimentos de fibra e flaps
│   ├── olts/                   # Referência técnica e perfis Huawei, ZTE, Fiberhome, Datacom
│   ├── notes/                  # Notas atômicas geradas pelo reflect (NOTA-XXXX)
│   └── dashboards/             # Painéis de telemetria compatíveis com Obsidian Dataview
├── skills/                     # Skills nativas para a Antigravity CLI
│   ├── mikrotik-safe/          # Safe mode e RouterOS v6 vs v7
│   ├── ftth-huawei-zte-fiberhome/ # OLTs e telemetria GPON
│   ├── bgp-peering/            # PTT, peering e comunidades
│   └── linux-failsafe/         # Auto-rollback temporizado em Linux
└── tests/                      # Suíte de testes automatizados com pytest
```

---

## 3. Instalação e Execução

### Requisitos Prévios
- Python 3.10+
- Ambiente Linux (X11 / Wayland) ou Windows 10/11
- `uv` ou `pip`

### Passo a Passo

```bash
# 1. Clone ou acesse o diretório
cd /home/brn/harness-isp

# 2. Crie e ative o ambiente virtual com uv
uv venv
source .venv/bin/activate

# 3. Instale as dependências
uv pip install -r requirements.txt

# 4. Execute a suíte de testes
pytest -v

# 5. Inicie o aplicativo
python main.py
```

> **Nota para ambientes Wayland (Linux/Omarchy):**
> O aplicativo detecta automaticamente o Wayland e define `QT_QPA_PLATFORM=xcb` para compatibilidade total de movimentação e janela flutuante sem bordas.

---

## 4. Cobertura de Testes

Os testes cobrem:
* **Anti-Lockout:** Detecção de regras de `drop` na chain `input` sem `established,related`, alteração de MTU e bloqueio de SSH.
* **Cofre Seguro:** Criptografia AES-256-GCM com derivação de chave PBKDF2 e isolamento contra vazamento de credenciais.
* **Token Economy (RTK):** Resumo sintético de tabelas de BGP, ping ICMP, traceroute e potências ópticas de OLT.
* **FTTH Engine:** Avaliação de níveis de atenuação óptica (Class B+/C+) e parsing de `display ont autofind`.
* **RAG SQLite FTS5:** Indexação e busca atômica de notas técnicas e topologia de POPs.
