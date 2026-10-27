---
name: bgp-peering
description: Configuração e auditoria de sessões BGP com IX.br (PTT), trânsitos IP e filtros de comunidade.
---

# Skill: BGP Peering & Routing Filters

## 1. Boas Práticas BGP para ISPs
- **Max Prefix Limit:** Sempre configurar limite máximo de prefixos por peer (`max-prefix 100` ou similar) com `warning-only` ou shutdown.
- **Filtros Anti-Spoofing & BOGON:** Bloquear RFC 1918 e prefixos privados na saída da WAN e na entrada de trânsitos.
- **Commit Confirmed:** Em Cisco/Huawei/Datacom, use sempre `commit confirmed 5`.
