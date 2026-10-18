# Guia de tradução PT-BR

Vale para qualquer pessoa ou agente que preencha um lote em `traducao/`.
Termos fixos estão em `glossario.md` e são obrigatórios.

## Tom

- Português do Brasil natural e informal, como num jogo da Nintendo
  localizado. Use "você". Contrações faladas ("pra", "tá") só em falas
  informais de personagens, nunca em menus ou textos de sistema.
- Mantenha a personalidade de cada fala: piadas, gírias e trocadilhos devem
  virar algo equivalente em português, não uma tradução literal sem graça.
- Luigi chama o Mario de "mano". O jogador é sempre o MARIO (masculino).
  Para outras pessoas de gênero desconhecido, prefira construções neutras.
- Nomes em MAIÚSCULAS continuam em MAIÚSCULAS.

## O que não traduzir

- Nomes de personagens e de CAPTURAS (GOOMBA, KOOPA, BOO...).
- Nomes próprios de lugares (NEW DONK CITY, KONG KAPITAL...). Os
  descritivos são traduzidos com a grafia de `00_lugares.json`.
- Bordões do Mario (WAHOO!, LET'S-A-GO!...).
- Nomes de itens, golpes e habilidades: use exatamente o nome de
  `traducao/nomes/*.json` (procure pelo "en", ignorando maiúsculas). Nos
  diálogos eles aparecem em MAIÚSCULAS; mantenha em MAIÚSCULAS. Se o nome
  da tabela estiver abreviado só para caber no menu ("Dança d. Espadas",
  "Compart. Exp."), no diálogo use a forma completa ("DANÇA DAS ESPADAS"),
  a menos que o próprio diálogo também tenha limite apertado.
- Texto herdado do Pokémon (POKéMON, POKé BALL, POKéMON CENTER...) é
  adaptado ao hack conforme o glossário (CAPTURA, CAP, CENTRO CAPTURA...).

## Formato

- `\p` abre uma nova caixa de texto. Mantenha a mesma divisão em caixas do
  original, inclusive um `\p` no final quando o original termina com `\p`.
- Dentro de uma caixa, você pode omitir `\n` e `\l`: parágrafos sem eles
  são quebrados automaticamente em 208 px. Se usar quebras manuais, a
  primeira da caixa é `\n` e as seguintes são `\l`.
- Copie todas as tags `{...}` exatamente como estão: `{PLAYER}`,
  `{STR_VAR_1}`, `{COLOR 07}{COLOR 08}`... (pares de cor marcam o trecho
  colorido; mantenha-os em volta da palavra equivalente), `{PAUSE 10}`,
  `{PLAY_SE 00 00}`, `{FD 0E}` etc.
- Entradas com `max_width` são rótulos de menu: a tradução precisa caber
  nessa largura (o build avisa). Entradas com `max_lines` ficam em caixas de
  tamanho fixo (descrições, Tattledex): use no máximo esse número de linhas,
  escrevendo as quebras `\n` à mão, e condense o texto se precisar.
- Acentos disponíveis: á à â ã é ê í ó ô õ ú ç e maiúsculas. Não há outros
  símbolos além dos que já aparecem nos textos originais.
- Se uma entrada não for texto de verdade (lixo binário, códigos
  soltos), deixe `pt` vazio e cite no relatório.

## Como preencher e validar

1. Escreva um JSON `{"OFFSET": "tradução", ...}` com as traduções.
2. `python3 tools/preencher.py traducao/mapas/<lote>.json <seu_json>`
3. `python3 tools/build.py "<ROM>" --check` e corrija os erros que apontam
   para o seu lote (erros de outros lotes não são seus).
