---
name: mikrotik-safe
description: Operações seguras em MikroTik RouterOS v6 e v7 com Safe Mode mandatório e proteção anti-lockout.
---

# Skill: MikroTik Safe Operations

## 1. Diretrizes Críticas
- **Safe Mode Mandatório:** Toda intervenção em firewall, roteamento, bridges e interfaces exige `Ctrl+X` ou wrapper de safe mode.
- **Diferenciação v6 vs v7:**
  - **v6:** Usa `/routing bgp peer` e `/routing filter`.
  - **v7:** Usa `/routing bgp connection` e `/routing filter rule` (sintaxe estruturada nova).

## 2. Pre-Flight Check de Firewall
Ao criar qualquer regra `action=drop` na chain `input`, garanta:
```routeros
/ip firewall filter
add action=accept chain=input comment="Aceitar conexoes estabelecidas/relacionadas" connection-state=established,related
add action=accept chain=input comment="Aceitar SSH/WinBox de gerencia" dst-port=22,8291 protocol=tcp src-address-list=ADMIN_MGMT
```
Nunca aplicar regras de drop sem essas duas regras prévias.
