
# README: Uruchamianie projektu

## Opis projektu
Ten projekt realizuje grę "Zgadnij liczbę" z obsługą trybu jednoosobowego oraz wieloosobowego.

Wykorzystywane jest Telegram Bot API do tworzenia chat-bota.

## Wymagania systemowe
Do uruchomienia projektu potrzebujesz:
- Python w wersji 3.10 lub wyższej.
- Zainstalowany pakiet Telegram Bot API (`python-telegram-bot`).
- Dostęp do własnego tokena Telegram Bot (utworzonego za pomocą BotFather).

## Kroki instalacji

### 1. Klonowanie repozytorium

Sklonuj repozytorium na swój komputer:
```bash
$ git clone https://github.com/<twoje_repozytorium>.git
$ cd <nazwa_projektu>
```

### 2. Utworzenie i aktywacja środowiska wirtualnego

Utwórz i aktywuj środowisko wirtualne:
```bash
$ python -m venv venv
$ source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Instalacja zależności

Zainstaluj wszystkie wymagane pakiety:
```bash
$ pip install -r requirements.txt
```

### 4. Konfiguracja Tokena

Utwórz plik `.env` w głównym katalogu projektu i dodaj swój Telegram Bot Token:
```
TELEGRAM_BOT_TOKEN=<twój_token>
```

### 5. Uruchomienie projektu

Uruchom bota:
```bash
$ python main.py
```

Fokus projektu: bot rozpoczyna czat i oczekuje na wprowadzenie komend przez użytkownika.

## Dostępne komendy
- `/start` - rozpoczęcie gry jednoosobowej.
- `/restart` - ponowne uruchomienie gry.
- `/invite` - zaproszenie znajomego do gry wieloosobowej.
- `/join <kod>` - dołączenie do gry za pomocą kodu.
- `/setcode <liczba>` - ustawienie tajnej liczby w grze z przyjacielem.
- `/guess <liczba>` - zgadywanie tajnej liczby.
- `/endgame` - zakończenie gry wieloosobowej.
- `/help` - wyświetlenie listy dostępnych komend.

## Wsparcie
Skontaktuj się z [adminem](mailto:admin@example.com) w przypadku problemów.
