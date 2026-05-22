# 🎙️ mikrofon

Pływająca ikona stanu mikrofonu dla Linuksa (X11). Siedzi nad wszystkimi oknami i pokazuje w czasie rzeczywistym czy mikrofon jest aktywny czy wyciszony.

![zielona = aktywny](https://img.shields.io/badge/aktywny-zielona-2ecc40)
![czerwona = wyciszony](https://img.shields.io/badge/wyciszony-czerwona-e74c3c)

## Jak działa

- 🟢 **Zielona** — mikrofon aktywny
- 🔴 **Czerwona** — mikrofon wyciszony

Reaguje na zdarzenia PipeWire/PulseAudio w czasie rzeczywistym (bez pollingu) przez `pactl subscribe`.

## Wymagania

- Linux z X11
- Python 3.10+
- PyQt6
- PipeWire lub PulseAudio (`pactl`)

```bash
pip install PyQt6
```

## Instalacja

```bash
# Sklonuj repo
git clone https://github.com/dzejsej88/mikrofon.git
cd mikrofon

# Wstaw do PATH
cp mikrofon.py ~/.local/bin/mikrofon
chmod +x ~/.local/bin/mikrofon
```

## Użycie

```bash
mikrofon &
```

| Akcja | Efekt |
|-------|-------|
| Przeciągnij lewym przyciskiem | Przesuń ikonę |
| Podwójny klik lewym | Wycisz / odcisz mikrofon |
| Prawy przycisk | Menu (stan, toggle, zamknij) |

## Aktualizacja po zmianach w kodzie

```bash
cp ~/mikrofon/mikrofon.py ~/.local/bin/mikrofon
```
