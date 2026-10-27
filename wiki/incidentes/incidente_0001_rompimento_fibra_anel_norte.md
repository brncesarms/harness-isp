---
id: INC-0001
titulo: Rompimento de Fibra Óptica no Anel Norte (Av. Brasil)
categoria: incidentes
impacto: alto
tags:
  - fibra
  - post-mortem
  - anel
  - gpon
---

# ⚠️ INC-0001: Rompimento de Fibra Óptica no Anel Norte

## 1. Descrição do Incidente
Às 14:15, alarme generalizado de LOS (Loss of Signal) em 32 portas PON atingindo o anel Norte de distribuição após colisão de caminhão com poste na Av. Brasil.

## 2. Ação Imediata & Mitigação
1. **Comutação de Rota:** O tráfego de uplink dos switches secundários comutou automaticamente via MSTP pelo anel Sul.
2. **Localização do Dano:** O OTDR indicou evento de corte a 3.420 metros a partir do DIO Central.
3. **Equipe de Fusão:** Lançamento de 150m de cabo autosustentado (AS) 36 FO e fusão das 36 fibras em caixa de emenda selada (CEO).

## 3. Lição Aprendida (Pós-Incidente)
* Aumentar a altura mínima de travessia do vão de cabos de 5,5m para 6,0m conforme norma da concessionária de energia para prevenir impactos de veículos de grande porte.
