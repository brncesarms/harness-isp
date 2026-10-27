---
id: SOP-0002
titulo: Provisionamento de ONUs em OLT Huawei SmartAX
categoria: sops
impacto: alto
tags:
  - ftth
  - gpon
  - huawei
  - provisioning
---

# 🌐 SOP-0002: Provisionamento de ONUs em OLT Huawei SmartAX

## 1. Descoberta de ONU
Execute no terminal da OLT:
```text
display ont autofind all
```
Identifique o F/S/P (Frame/Slot/Port), número de série (SN) e modelo do equipamento.

## 2. Validação de Potência Óptica Pré-Ativação
A potência deve estar entre `-14.00 dBm` e `-26.00 dBm`.
Valores abaixo de `-27.00 dBm` indicam curvatura excessiva, conector sujo ou atenuação elevada no divisor óptico (splitter).

## 3. Provisionamento da ONT (Modo Bridge / PPPoE no Roteador)
```text
interface gpon 0/1
 ont add 0 sn-auth "48575443ABC12345" omci ont-lineprofile-id 10 ont-srvprofile-id 10 desc "CLIENTE_RESIDENCIAL"
quit
service-port vlan 100 gpon 0/1/0 ont 0 gemport 1 multi-service user-vlan 100 tag-transform translate
save
```
