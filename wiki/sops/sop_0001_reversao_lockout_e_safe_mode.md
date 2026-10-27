---
id: SOP-0001
titulo: Procedimento de Reversão de Lockout e Safe Mode Operacional
categoria: sops
impacto: critico
tags:
  - anti-lockout
  - mikrotik
  - linux
  - safe-mode
---

# 🛡️ SOP-0001: Reversão de Lockout e Safe Mode Operacional

## 1. Contexto & Regra de Ouro
Qualquer modificação em firewalls, interfaces de rede, MTU ou portas de gerência (SSH/Winbox) possui risco de desconectar o analista do roteador. Nenhuma alteração pode ser executada sem um mecanismo ativo de reversão automática.

## 2. No MikroTik (RouterOS)
1. **Sempre ativar Safe Mode antes de qualquer comando de risco:**
   * Via CLI terminal: pressione `[CTRL] + [X]`. O prompt mudará para `[safe]`.
   * Se a sessão cair por erro de filtro ou IP, o RouterOS faz o rollback automático em segundos.
2. **Alternativa via Script Temporizado (Watchdog/Rollback):**
   ```routeros
   /system script add name="auto_rollback" source={/ip firewall filter reset; /system script remove auto_rollback}
   /system scheduler add name="revert_lockout" interval=3m on-event="auto_rollback"
   ```

## 3. No Linux / VyOS
1. **Regra de Rollback com Systemd Run:**
   ```bash
   nohup bash -c 'sleep 180 && iptables-restore < /etc/iptables.rules.bak' > /dev/null 2>&1 &
   ```
2. Após confirmar que a conexão continua operando, encerre o processo do rollback ou confirme a gravação persistente.
