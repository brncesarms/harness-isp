---
name: linux-failsafe
description: Automação segura em Linux (BNG/PPPoE, CGNAT, FRR/BIRD, nftables) com auto-rollback e proteção SSH.
---

# Skill: Linux Network Fail-Safe

## 1. Regra de Ouro do Firewall Linux
Ao modificar `nftables`, `iptables` ou `ufw`, nunca execute comandos sem rollback temporizado:
```bash
# Snapshot prévio
iptables-save > /tmp/iptables_backup.rules

# Disparo de auto-reversão após 60s
(sleep 60 && iptables-restore < /tmp/iptables_backup.rules) &
ROLLBACK_PID=$!

# Aplicação das novas regras
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Se confirmado o acesso:
kill $ROLLBACK_PID
```

## 2. Netplan & SSH
- Usar exclusivamente `netplan try --timeout 60` em vez de `netplan apply`.
- Executar `sshd -t` e `visudo -c` antes de reiniciar qualquer serviço do sistema.
