---
name: ftth-huawei-zte-fiberhome
description: Diagnóstico óptico, telemetria e provisionamento de ONUs em OLTs Huawei, ZTE, Fiberhome e Datacom.
---

# Skill: FTTH & OLT Multivendor

## 1. Janela Óptica Padrão (GPON Class B+ / C+)
- **Sinal Ideal (RX):** Entre `-15.0 dBm` e `-24.0 dBm`.
- **Alerta de Atenuação:** Abaixo de `-27.0 dBm`.
- **Rompimento / Sem Sinal:** Abaixo de `-30.0 dBm` (Loss of Signal / LOS).
- **Saturação:** Acima de `-8.0 dBm` (inserir atenuador óptico).

## 2. Comandos Canônicos de Descoberta
- **Huawei:** `display ont autofind all`
- **ZTE:** `show gpon onu uncfg`
- **Fiberhome:** `show onu unauth`
- **Datacom:** `show gpon unconfigured-onu`
