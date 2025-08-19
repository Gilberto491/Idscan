# Scanner de Código – Relatórios

Este projeto é um **scanner de código-fonte Java** que percorre os arquivos `.java` de um repositório, aplica regras de análise (com base em `includes` e `excludes`), e gera um **relatório em CSV** (`reports/relatorio.csv`) contendo campos, parâmetros e variáveis locais relacionados a termos configurados.

---

## 📂 Estrutura do Projeto

configs/
├─ config.yaml # Configurações principais do scanner
├─ includes.txt # Palavras-chave que DEVEM aparecer (filtros positivos)
└─ excludes.txt # Palavras-chave que DEVEM ser ignoradas (filtros negativos)

reports/
└─ relatorio_cnpj.csv # Relatório final em CSV

cli.py # Entrada principal (CLI)
config.py # Leitura e parse das configs
loader.py # Carregamento de arquivos
models.py # Classes auxiliares para Findings
patterns.py # Regex para encontrar campos, params e locais
scan.py # Lógica principal do scanner
writer.py # Escrita do relatório CSV


---

## ⚙️ Como Funciona

1. O scanner percorre todos os arquivos `.java` dentro do projeto.
2. Para cada linha, aplica **regex** para identificar:
   - **Campos de classe (fields)**
   - **Parâmetros de métodos (params)**
   - **Variáveis locais (locals)**
3. Os resultados passam por filtros de:
   - `includes.txt` → só mantém os itens que contêm palavras-chave relevantes (ex.: `cnpj`)
   - `excludes.txt` → remove falsos positivos (ex.: `cnpjFake`, `cnpjTest`)
4. O resultado é salvo em `reports/relatorio_cnpj.csv`.

---

## 🔑 Destaques Técnicos

- **Case-insensitive**: o scanner encontra `cnpj`, `CNPJ`, `CnpjEmpresa`, etc.
- **Suporte a prefixo/sufixo**: regex permite `cnpjEmpresa`, `empresaCnpj`, etc.
- **Assinaturas multilinha**: parâmetros de métodos são capturados mesmo se o `(` abrir em uma linha e o `)` fechar em outra (graças ao contador de parênteses).
- **Exportação padronizada**: cada linha do CSV contém:
  - Projeto
  - Arquivo
  - Linha
  - Nome do campo/param/local
  - Classe/Tabela
  - Tipo
  - Status (OK / ISSUE)
  - Regra aplicada
  - Trecho de código

---

## ▶️ Como Rodar

### 1. Criar ambiente virtual (opcional, mas recomendado)
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```
---

## 🚀 Melhorias Futuras

 Suporte a análise de protected/private methods de forma seletiva.

 Configuração de múltiplos includes/excludes por regex.

 Integração com SonarQube ou outra ferramenta de qualidade.
 
---
## 📂📌 Observação Importante

Com a alteração do contador de parênteses, agora nenhum parâmetro válido é perdido em métodos com assinatura quebrada em múltiplas linhas (problema que ocorria em versões anteriores).


