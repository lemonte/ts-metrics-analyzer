# 📊 TS Metrics Analyzer

Ferramenta de análise estática de código TypeScript para extração de métricas orientadas a objetos e complexidade de classes.

## 🔍 O que esse projeto faz?

Este analisador percorre todos os arquivos `.ts` da pasta `src/` de um repositório e gera um arquivo `class_metrics.json` contendo métricas detalhadas para cada classe encontrada. Ele calcula, entre outras:

- LOC (Linhas de Código)
- CBO ( acoplamento entre objetos)
- WMC (complexidade ciclomática total dos métodos)
- DIT (profundidade de herança)
- RFC (métodos acessados)
- LCOM (falta de coesão entre métodos)
- Número de métodos, campos, subclasses, operadores, loops, literais, etc.
- Profundidade máxima de blocos aninhados
- Quantidade de palavras únicas no corpo da classe

---

## 🚀 Como usar

### 1. Clone este repositório

```bash
git clone https://github.com/seu-usuario/ts-metrics-analyzer.git
cd ts-metrics-analyzer
