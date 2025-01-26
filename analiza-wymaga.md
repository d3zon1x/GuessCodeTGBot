
# README: Telegram Bot for "Guess the Number"

## Cel Projektu
Celem projektu "Telegram Bot for 'Guess the Number'" jest dostarczenie narzędzia, które umożliwia użytkownikom grę w zgadywanie liczby w trybie jednoosobowym lub wieloosobowym, z wykorzystaniem platformy Telegram.

## Funkcjonalności

### Gra jednoosobowa:
- **Losowanie Liczby:** Bot losuje 4-cyfrową liczbę, a użytkownik próbuje ją odgadnąć.
- **Podpowiedzi:** Bot podaje informacje o ilości cyfr na właściwym miejscu i o ilości cyfr występujących w złej pozycji.

### Gra wieloosobowa:
- **Zaproszenia do Gry:**
  - Użytkownicy mogą zaprosić znajomego za pomocą komendy `/invite`.
  - Kod zaproszenia umożliwia dołączenie drugiego gracza.
- **Ustawianie Tajnego Kodu:** Każdy gracz ustawia swoją tajną 4-cyfrową liczbę.
- **Zgadywanie:** Gracze na zmianę próbują odgadnąć tajną liczbę przeciwnika.
- **Wyniki Gry:** Bot informuje o wygranej gracza, który odgadnie tajną liczbę przeciwnika.

### Dodatkowe funkcjonalności:
- **Pomoc:** Komenda `/help` wyświetla dostępne polecenia.
- **Restart Gry:** Możliwość restartu gry za pomocą `/restart`.
- **Zakończenie Gry:** Komenda `/endgame` kończy rozgrywkę w trybie wieloosobowym.

## Struktura Danych

- **Słowniki:**
  - Przechowywanie informacji o aktywnych grach, takich jak kody tajne, liczba prób i kolejność graczy.
  - Logowanie kodów zaproszeń.
- **Listy:** Przechowywanie zgadywanych liczb i wyników dla każdego gracza.
- **Ciągi znaków:** Wykorzystywane do generowania unikalnych kodów zaproszeń.

## Interakcje Pomiędzy Komponentami

### Komunikacja z Użytkownikami:
- Użytkownicy wprowadzają komendy do bota, takie jak `/start`, `/guess`, czy `/invite`.
- Bot odpowiada na komendy, zarządza grami i wyświetla wyniki zgadywania.

### Obsługa Gry:
- **Jednoosobowa:** Bot losuje liczbę i podaje wskazówki w odpowiedzi na zgadywanie użytkownika.
- **Wieloosobowa:**
  - Bot zarządza zaproszeniami do gry i przypisuje graczy do sesji.
  - Przechowuje tajne kody obu graczy oraz ich zgadywania.

## Podstawy Python

- **Biblioteki:** Projekt wykorzystuje `python-telegram-bot`, `random` oraz `string`.
- **Klasy i Funkcje:**
  - Funkcje odpowiadające za każdą komendę, np. `start`, `guess`, `invite`.
  - Struktura oparta na słownikach do przechowywania danych sesji gry.

