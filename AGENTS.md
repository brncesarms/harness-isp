# ⚡ HarnessISP — Assistente Desktop & Motor Operacional para ISPs

> **Ambiente:** CT 252 (`archimedes`) / Workstation (Acer Aspire 5 / Alienware) | **Autoridade:** Bruno Cesar  
> **Motores:** Antigravity CLI (`agy`) + PySide6 + Archimedes Core Engine  
> **Token Economy:** RTK Hook (`core/token_optimizer.py`) | **Escudo:** Zero Leaks (`core/vault.py`)  
> **Pilar Central:** Blindagem Anti-Lockout & Fail-Safe

---

## 1. Diretrizes Mestras de Operação e Comportamento

1. **Comunicação Cirúrgica (pt-BR):** Responda sempre em português do Brasil, conciso e com foco estritamente técnico em engenharia de redes e NOC.
2. **Blindagem Anti-Lockout (Regra Inegociável):** Toda e qualquer proposta de alteração em firewalls, interfaces, MTU, SSH ou roteamento deve ser validada preventivamente via `core/failsafe_guard.py`. Nunca recomende ou execute scripts sem Safe Mode (`/system script` temporizado, `safe-mode` no RouterOS ou rollback daemon no Linux).
3. **Escudo Zero Leaks:** Credenciais de roteadores, OLTs e switches devem ser gerenciadas via `core/vault.py` (AES-256-GCM com PBKDF2) e injetadas exclusivamente em RAM. Jamais imprima senhas em logs, chats ou arquivos de versão.
4. **Token Economy & Compressão:** Saídas extensas de rede (`show ip bgp`, dumps de OLT, tabelas de rotas, MTR/Ping) devem ser filtradas e sintetizadas com `core/token_optimizer.py` antes de trafegar pelo LLM.
5. **Automação FTTH Multivendor:** Suporte estrito aos padrões de telemetria óptica (Class B+/C+) e comandos de descoberta/provisionamento para Huawei, ZTE, Fiberhome e Datacom em `core/ftth_engine.py`.

---

## 2. Catálogo de Skills Nativas (`skills/`)

| Skill | Escopo |
| :--- | :--- |
| **`mikrotik-safe`** | Geração e validação de scripts RouterOS v6/v7 com safe-mode e proteção anti-lockout. |
| **`ftth-huawei-zte-fiberhome`** | Comandos de OLT, detecção de atenuação óptica, LOS e Dying Gasp. |
| **`bgp-peering`** | Validação de filtros de prefixos, comunidades BGP e políticas de PTT/Trânsito. |
| **`linux-failsafe`** | Rollbacks automatizados de interfaces de rede e firewall iptables/nftables via timers. |

---

## 3. Comandos Canônicos

* **Executar Suíte de Testes:**
  ```bash
  source .venv/bin/activate && pytest -v
  ```
* **Testes de Módulo Específico:**
  ```bash
  pytest tests/test_failsafe_guard.py -v
  pytest tests/test_ftth_engine.py -v
  ```
* **Inicializar Assistente Desktop:**
  ```bash
  python3 main.py
  ```
* **Verificação de Sintaxe & Linter:**
  ```bash
  ruff check .
  ```

---

## 4. Mapa de Navegação e Arquitetura

* **Entrypoint GUI:** [main.py](file:///home/brn/harness-isp/main.py)
* **Guarda Anti-Lockout:** [core/failsafe_guard.py](file:///home/brn/harness-isp/core/failsafe_guard.py)
* **Motor FTTH & OLTs:** [core/ftth_engine.py](file:///home/brn/harness-isp/core/ftth_engine.py)
* **Cofre Criptografado (Zero Leaks):** [core/vault.py](file:///home/brn/harness-isp/core/vault.py)
* **Compressor RTK:** [core/token_optimizer.py](file:///home/brn/harness-isp/core/token_optimizer.py)
* **Memória RAG FTS5:** [core/memory_rag.py](file:///home/brn/harness-isp/core/memory_rag.py)
* **Especificação Master:** [prompt-harness-isp-v3.md](file:///home/brn/harness-isp/prompt-harness-isp-v3.md)
