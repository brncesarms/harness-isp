# Prompt de Criação: HarnessISP (v3)
> **Base de Inspiração:** Arquitetura Híbrida Archimedes + Antigravity CLI  
> **Domínio:** Engenharia de Redes, FTTH/GPON & Operação de NOC para Provedores de Internet (ISPs)  
> **Pilares Integrados:** Anti-Lockout & Fail-Safe + FTTH/GPON Engine (Huawei, ZTE, Fiberhome, Datacom)

Você é um desenvolvedor sênior em automação Desktop em Python e engenheiro de redes sênior especializado em Provedores de Internet (ISPs), com vasto domínio em arquiteturas agênticas seguras, economia de tokens, fail-safe operacional, protocolos de roteamento (BGP/OSPF/MPLS) e redes de acesso óptico FTTH/GPON.

Sua tarefa é criar a estrutura inicial, modular e totalmente funcional (MVP Robusto) do **HarnessISP**, um assistente de área de trabalho flutuante interativo que utiliza a **Antigravity CLI** (`agy` / `antigravity`) como motor cognitivo para analistas de NOC e engenheiros de redes de ISPs.

---

## 1. Visão Geral do Projeto
- **Nome do Projeto**: `HarnessISP`
- **Público-Alvo**: Engenheiros de redes, analistas de NOC, técnicos de campo e provisionadores de FTTH de ISPs.
- **Conceito**: Um widget flutuante (esfera interativa na área de trabalho com física de mola e animações táteis) associado a um painel de chat de diagnósticos de rede e atalhos de NOC. O backend orquestra sessões com a Antigravity CLI de forma assíncrona, incorporando os princípios de resiliência, isolamento de memória, economia de tokens do projeto Archimedes, **blindagem estrita anti-lockout** e uma **esteira especializada em OLTs e provisionamento FTTH**.

---

## 2. Especialização FTTH/GPON & OLT Automation (Huawei, ZTE, Fiberhome, Datacom)

O módulo `core/ftth_engine.py` e as skills dedicadas no Antigravity devem suportar os principais fabricantes de OLT presentes em ISPs brasileiros e internacionais:

### A. Huawei SmartAX (MA5608T, MA5800, etc.)
- **Descoberta:** Parsing de `display ont autofind all`.
- **Telemetria Óptica:** Coleta e interpretação de `display ont optical-info` (RX/TX dBm, temperatura, tensão) com alertas de atenuação crítica (RX < -27 dBm ou > -8 dBm).
- **Provisionamento:** Templates automatizados de `ont-lineprofile`, `ont-srvprofile`, `dba-profile`, `traffic-table` e `service-port` (modo Bridge ou Router PPPoE).
- **Diagnóstico:** Análise de alarmes `display ont info summary`, detecção de fibra rompida (LOS - Loss of Signal) e quedas de energia (Dying Gasp).

### B. ZTE (C300, C320, C600)
- **Descoberta:** Parsing de `show gpon onu uncfg`.
- **Telemetria Óptica:** `show pon power attenuation gpon-onu_...` e `show gpon onu state`.
- **Provisionamento:** Automação de criação de `tcont`, `gemport`, `service-port` e `vlan` translation por interface PON.

### C. Fiberhome (AN5516 / UNM2000 / TL1 & CLI)
- **Descoberta:** Parsing de `show onu unauth` e listas de mac/SN.
- **Telemetria Óptica:** `show onu optical-power` e verificação de status das placas GPON (GC8B, GCOB).
- **Provisionamento:** Comandos CLI e comandos TL1 para associação de perfis de banda e PPPoE VLANs.

### D. Datacom (DM4610, DM4615)
- **Descoberta e Potência:** `show gpon unconfigured-onu` e `show gpon onu optical-power`.
- **Configuração:** Profile de DBA, VLAN mapping e provisionamento DmOS.

---

## 3. Pilar Anti-Lockout & Fail-Safe Engine (Zero Trancamentos)

O **HarnessISP** possui salvaguardas ativas de proteção para roteadores, OLTs e sistemas Linux:

### A. Proteção em Roteadores e OLTs
1. **Safe Mode & Commit Confirmed Mandatórios:**
   * **MikroTik (RouterOS):** Comandos em `/ip firewall`, `/ip route`, `/routing` ou `/interface` exigem obrigatoriamente **Safe Mode** (`<safe>` ou `Ctrl+X`).
   * **Cisco / Datacom / Huawei:** Adoção de `commit confirmed <minutos>` ou `reload in <minutos>` antes de alterações de risco.
2. **Pre-Flight Checks Anti-Suicídio:**
   * Bloqueio estrito de scripts que desativem a interface, bridge ou VLAN por onde a gerência/SSH atual trafega.
   * Proibição de regras de firewall `drop all` na chain `input` sem prévia validação de regras `established,related` e IP/porta de gerência.
   * Em OLTs: Proibição de remoção de VLAN inband ou alteração de porta de gerência sem validação de uplink ativo.

### B. Proteção em Distribuições Linux (BNG, CGNAT, FRR/BIRD, Debian/Ubuntu)
1. **Rollback Temporizado em Firewall (nftables / iptables / ufw):**
   * Regras de firewall são sempre aplicadas com timer de auto-reversão em background (ex: 60s), cancelado apenas após confirmação de conectividade.
   * Teste de sintaxe obrigatório (`nft -c -f` ou `iptables-restore --test`).
2. **Proteção SSH e Sudo:**
   * Validação de sintaxe antes de reiniciar serviços (`sshd -t` e `visudo -c`). Proibição de fechar a sessão corrente antes de testar nova sessão paralela.
3. **Interfaces de Rede:**
   * Uso exclusivo de `netplan try` com timeout automático em distribuições com Netplan.

---

## 4. Princípios Herdados da Arquitetura Archimedes

1. **Token Economy (RTK & Filtros Determinísticos):**
   - Saídas de `display ont autofind`, `show bgp summary`, tabelas de rotas extensas e MTR são filtradas e sintetizadas antes de alimentar o contexto da IA via parsers (`jc`, regex).
2. **Arquitetura de Memória Isolada (SSOT & RAG FTS5):**
   - Separação mandatória entre o workspace volátil e a base de conhecimento do provedor (SQLite FTS5 ou notas atômicas):
     - POPs, CTOs/CEOs, faixas de IP/ASN, VLANs canônicas, perfis de OLT e histórico de falhas.
3. **Escudo Zero Leaks (Cofre Seguro AES-256-GCM):**
   - Senhas de roteadores, OLTs, SNMP community e BGP MD5 salvas em cofre criptografado local (`core/vault.py`) com injeção apenas em memória durante comandos locais.
4. **Determinismo Tool-First:**
   - Ferramentas locais (`net_tools`: Ping, MTR, DNS, RDAP Whois) e checagens determinísticas de OLT executam antes de consultar a IA.
5. **Recursão de Lições Aprendidas (`reflect`):**
   - Registro pós-incidente/pós-ativação na base RAG.
6. **Regra de Emancipação:**
   - Detecção de tarefas repetidas 3 vezes para sugestão de automação em linha única.

---

## 5. Requisitos de Funcionalidades e Comportamento

### A. Primeira Execução e Persistência de Dados
- **Seleção de Workspace**: No primeiro start, abrir diálogo interativo solicitando a pasta do workspace (ex: `~/HarnessISP_Data` no Linux ou `C:\HarnessISP_Data` no Windows).
- **Estrutura do Workspace**:
  ```text
  HarnessISP_Data/
  ├── memory/              # Base SQLite FTS5 e notas atômicas do provedor
  ├── backups/             # Backups automáticos pré-alteração
  ├── scripts/             # Scripts gerados (MikroTik, Huawei, Cisco, OLTs, Linux)
  ├── logs/                # Histórico de incidentes e sessões de NOC
  ├── vault/               # Cofre criptografado de credenciais
  └── config.yaml          # Configurações do operador
  ```

### B. Widget Flutuante Interativo (PySide6)
- **Visual**: Esfera estilizada com gradientes modernos, brilho neon sutil (`Qt.FramelessWindowHint`, `Qt.WindowStaysOnTopHint`, `Qt.WA_TranslucentBackground`).
- **Compatibilidade Wayland / X11**: Fallback via `QT_QPA_PLATFORM=xcb` e atalho global de teclado (`F12` / `Super+N`).
- **Física & Animações**: Arraste suave com deformação elástica (squash & stretch), retorno elástico (*spring bounce*) e oscilação flutuante ociosa (*idle float*).
- **Estados Visuais de Rede (LED / Halo Dinâmico)**:
  - **Verde/Ciano:** Nominal / Estável.
  - **Amarelo Pulsante:** Diagnóstico em andamento / Streaming da CLI ativo.
  - **Vermelho/Laranja:** Alerta crítico / Perda de pacotes / Sinal de fibra degradado / Risco alto de lockout.
- **System Tray (Bandeja):** Ícone na bandeja para minimizar e restaurar a esfera.

### C. Integração com a Antigravity CLI (`agy`)
- **Setup Assistido**: Verificação de instalação e login de `antigravity` / `agy`.
- **Daemon / Sessão Persistente**: Streaming NDJSON bidirecional contínuo.
- **Skills Nativas**:
  - `skills/mikrotik-safe/`
  - `skills/ftth-huawei-zte-fiberhome/`
  - `skills/bgp-peering/`
  - `skills/linux-failsafe/`

### D. Painel de Chat & Ações Rápidas de NOC / FTTH
- Botões de Ação Rápida:
  - `[🔍 MTR / Ping]`
  - `[🌐 Consulta BGP / ASN]`
  - `[📶 Diagnóstico Óptico ONU / OLT]` (Sinal dBm, LOS, Dying Gasp)
  - `[➕ Provisionar ONU (Huawei/ZTE/FH)]`
  - `[⚙️ Validar Script MikroTik ROS v6/v7]`
  - `[🛡️ Gerar Regras Bogon / Anti-DDoS]`
  - `[🔄 Backup de Emergência]`
- **Two-Man Rule (Diff de Segurança & Lockout Risk Indicator)** com níveis de risco 🟢 Baixo, 🟡 Médio e 🔴 Crítico.

---

## 6. Arquitetura Modular Proposta

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
│   ├── failsafe_guard.py       # Validador Anti-Lockout, Safe Mode e Rollbacks
│   └── ftth_engine.py          # Automação e diagnósticos OLT (Huawei/ZTE/Fiberhome/Datacom)
├── gui/
│   ├── __init__.py
│   ├── widget.py               # Esfera flutuante, física de mola e drag & drop
│   ├── chat_panel.py           # Janela de chat, Markdown, diffs e alertas
│   ├── tray.py                 # Ícone na bandeja do sistema
│   └── styles.py               # Tema escuro e paleta de cores para NOC
└── skills/                     # Skills embutidas para o Antigravity
    ├── mikrotik-safe/SKILL.md
    ├── ftth-huawei-zte-fiberhome/SKILL.md
    ├── bgp-peering/SKILL.md
    └── linux-failsafe/SKILL.md
```

---

## 7. Entregáveis Esperados
1. Código Python modular, tipado e pronto para execução.
2. Arquivo `requirements.txt` completo.
3. Arquivo `README.md` com arquitetura e manual de uso.
4. Suíte de testes com `pytest` cobrindo o validador Anti-Lockout, diagnósticos de FTTH/potência óptica, cofre de senhas e otimizador de tokens.
