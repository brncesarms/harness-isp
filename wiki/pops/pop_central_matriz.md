---
id: POP-0001
titulo: POP Central Matriz - Topologia e Equipamentos
categoria: pops
impacto: critico
tags:
  - pop
  - core
  - bgp
  - dwdm
---

# 🏢 POP Central Matriz

## 1. Visão Geral
* **Localização:** Datacenter Principal - Rack 01 / Rack 02
* **Nobreak:** 10 kVA Online Dupla Conversão + Banco 24h
* **Gerador:** Diesel com transferência automática (QTA) em 15 segundos

## 2. Roteadores e Switches de Core
* **BGP Edge 01 (MikroTik CCR2116):** Trânsito IP Principal (Operadora A - 10 Gbps)
* **BGP Edge 02 (MikroTik CCR2116):** Trânsito IP Redundante (Operadora B - 10 Gbps) + IX.br (PTT)
* **Switch Core (Datacom DM4370):** Distribuição 10G/40G para OLTs

## 3. OLTs no POP
* **OLT-HUA-01 (Huawei MA5800-X7):** Atende Bairros Centro, Jardim América e Vila Nova (Slots 1 a 6 ativos).
