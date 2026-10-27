---
id: OLT-0001
titulo: Referência Técnica OLT Huawei SmartAX MA5800
categoria: olts
impacto: medio
tags:
  - huawei
  - ma5800
  - xpon
  - gpon
---

# 📡 OLT Huawei SmartAX MA5800

## 1. Comandos Mais Frequentes de Diagnóstico
```text
display board 0                     # Status das placas de serviço
display ont autofind all            # ONUs não autorizadas aguardando cadastro
display ont optical-info 0/1 0      # Potência de recepção (RX) e transmissão (TX)
display ont info summary 0/1        # Resumo de ONUs online/offline/LOS por porta
```

## 2. Padrões de Potência Óptica Recomendados
* **Excelente:** `-15.00 dBm` a `-22.00 dBm`
* **Aceitável:** `-22.00 dBm` a `-26.50 dBm`
* **Crítico (Alerta Vermelho):** Inferior a `-27.00 dBm` (Risco iminente de flapping/erros FEC) ou Superior a `-8.00 dBm` (Saturação do receptor óptico).
