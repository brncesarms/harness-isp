---
id: DASH-0001
titulo: Painel Geral de Operações NOC & ISP (Dataview)
categoria: dashboards
impacto: alto
---

# 📊 Painel Geral de Operações NOC & ISP

> **Obsidian Dataview Ativo:** Consolidação automática de POPs, SOPs de emergência e incidentes.

---

## 🏢 Status dos POPs e Infraestrutura
```dataview
TABLE file.name as "Documento", categoria as "Categoria", impacto as "Criticidade", tags as "Tags"
FROM "pops"
SORT impacto DESC
```

---

## 🛡️ Procedimentos Operacionais Padrão (SOPs)
```dataview
TABLE id as "ID", titulo as "Título", impacto as "Nível", tags as "Escopo"
FROM "sops"
SORT id ASC
```

---

## ⚠️ Histórico de Incidentes & Post-Mortems
```dataview
TABLE id as "ID", titulo as "Incidente", data as "Data", impacto as "Gravidade"
FROM "incidentes" or "notes"
SORT data DESC
```

---

## 📡 Inventário de OLTs e Perfis FTTH
```dataview
TABLE id as "Código", titulo as "Fabricante / Modelo", tags as "Tecnologia"
FROM "olts"
```
