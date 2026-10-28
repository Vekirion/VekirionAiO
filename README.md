# Vekirion AiO 2.3.1 – paczka modów do MT2009 PLUS

Zestaw modów klienta i serwera do **MT2009 PLUS** (singleplayer Metin2 z botami), z instalatorem,
w którym wybierasz, które mody wgrać.

| | Wersja |
|---|---|
| Klient | MT2009 PLUS **2.0.70** |
| Serwer | MT2009 PLUS **VERSION 2.39.0** (linux-port, Docker) |
| Licencja | [CC BY-NC-SA 4.0](LICENSE) |

> Starsze wersje klienta (2.0.68 i niżej) są nieaktualne – paczka ich nie obsługuje. Najpierw zaktualizuj
> klienta `MT2009-Patcher.exe`, na starszym kliencie/serwerze użyj poprzedniej wersji paczki.

> **Uwaga:** przed instalacją zrób kopię folderu `pack` klienta i folderu `linux-port` serwera.
> Instalator robi własną kopię zapasową (`backup_mody_<data>`), ale druga nie zaszkodzi.

---

## Mody

**K** = klient, **S** = serwer. Mody K+S trzeba wgrać po obu stronach.

| Nr | Mod | Gdzie |
|---|---|---|
| 01 | **FPS 60/120/144/240** – wybór w Opcje Gry > System (z łatką `metin2client.exe`) | K |
| 02 | **Ruch bez zatrzymywania** – po buffie, wsiadaniu na konia/mounta, po ciosie, przy LPM i po edycji sklepu | K |
| 03 | **Autołowy bez skakania** między celami przy ścianach | K |
| 04 | **Ctrl+PPM** otwiera też karty i skrzynki 50283, 50284, 79604, 79506, 79508 | K |
| 05 | **Wykrywacz Bossów (przedmiot 76009) i zmiany wykrywacza metinów** + znaczniki metinów/bossów na całej mapie, nie tylko w zasięgu widzenia (też wykrywacze metinów 27989 i 76006) | K+S |
| 06 | **Wykrywacz sam otwiera mapę** (do wyłączenia w Opcje Gry > Dodatkowe; wymaga 05) | K+S |
| 07 | **Wyraźniejszy znacznik celu** na mapie i minimapie | K |
| 08 | **Poprawka mgły** na mapach (msenv) | K |
| 09 | **Depozyt i stakowanie** – zakupy z Domu Aukcyjnego / sklepów offline dokładają się do stosów, przycisk „Depozyt (N)” | K+S |
| 10 | **Przenoszenie przedmiotów** w ekwipunku przy otwartym sklepie / Domu Aukcyjnym / sklepie NPC | S |
| 11 | **Mapa M w Czerwonym Lesie** | K |
| 12 | **Drop bez limitu poziomu** – drop nie maleje z różnicą poziomów; księga i Zwój Błogosławieństwa z metina, Cor Draconis i szarfy bez limitu 15 poziomów (tylko gracze, boty bez zmian) | S |
| 13 | **Puste kwadraty pod Protonem/Wine** (Steam Deck) na końcu napisów | K |
| 14 | **Towarzysz – przebudowa** – szybsze dołączanie, Shift+P plecak, Ctrl+P efekty, Alt+P drużyna i ławka, kilku towarzyszy naraz, portrety nad oknem P | K+S |
| 15 | **Bez kontroli speedhacka** (ruch i szybkość ataku; chodzenie przez ściany dalej zablokowane) | S |
| 16 | **Zwoje powrotu 5 min** zamiast 15, **Biała Flaga** bez blokady 3 min, **szybkie karty** potworów | S |
| 17 | **Ulepszanie co 0,2 s** zamiast co 1 s | S |
| 18 | **Nieodpychanie bossów** – boss nie odjeżdża po ciosach i skillach gracza, a jego skille nie odpychają gracza | S |
| 19 | **Nieodpychanie mobów (wszystkich)** – to samo co 18 dla każdego potwora (obejmuje 18) | S |
| 20 | **Kupowanie ze stosów** – boty porównują oferty po cenie za sztukę i częściej kupują część stosu zamiast droższej pojedynczej sztuki | S |

> **2.2.1: mody mają nowe numery** (po kolei, bez przerw): 06→04, 11→05, 12→06, 13→07, 14→08, 18→09,
> 19→10, 22→11, 23→12, 25→13, 26→14, 27→15, 28→16, 29→17. Instalator sam przelicza zapisany wybór
> ze starszej paczki.

Szczegóły każdego moda (pliki, wersje, zachowanie): [CZYTAJ.txt](CZYTAJ.txt).

**Mod 14 musi być po obu stronach albo po żadnej.** Przed pierwszym startem serwera z modem 14 zrób
kopię tabel towarzysza (migracja bazy robi się sama przy starcie):

```bash
mysqldump player playerbot_sidekick playerbot_sidekick_gift playerbot_sidekick_pin > sidekick_backup.sql
```

Limity towarzyszy ustawiasz w `docker/.env`: `M2_SIDEKICK_MAX_ACTIVE=2` (1–6),
`M2_SIDEKICK_ROSTER=4` (1–8).

---

## Instalacja

Pobierz paczkę z [Releases](../../releases) albo `git clone` i rozpakuj folder `Vekirion_AiO_2.3.1`.

### Windows – wybrane mody (zalecane)

1. Zamknij grę i patcher.
2. Uruchom `Wybierz_mody.bat`.
3. Wybierz: klient, serwer albo oba; podaj folder klienta (z `metin2client.exe`) i/lub `linux-port`.
4. Na liście wpisuj numery modów, żeby je włączyć/wyłączyć (np. `03 11`), `A` – wszystkie,
   `N` – żaden, **Enter** – instaluj.
5. Na końcu instalator pokazuje wynik każdego moda: `[OK]`, `[!!]` (z powodem) albo `[--]` (usunięty).

Wybór jest zapamiętywany – przy następnym uruchomieniu lista startuje od niego, a odznaczony mod
zostaje usunięty. **Po każdym użyciu `MT2009-Patcher.exe` uruchom instalator jeszcze raz**
(patcher przywraca oryginalny root).

### Windows – wszystkie mody ręcznie (drag&drop)

- **Klient:** przeciągnij zawartość `klient/pack` na folder `pack` klienta i zgódź się na podmianę.
  Potem skopiuj `klient/Ustaw_FPS.bat` do folderu klienta, uruchom i wpisz `1` (łatka FPS).
  `Ustaw_FPS.bat` czyta wersję z pliku `CLIENT_VERSION` klienta i działa tylko na 2.0.70 – starszą
  wersję zgłasza jako nieaktualną i niczego nie zmienia.
- **Serwer:** patrz niżej – kroki są takie same jak na Linuxie.

### Serwer ręcznie (Windows albo Linux)

1. Skopiuj zawartość `serwer/linux-port` do folderu `linux-port` serwera (z podmianą plików).
   Na Linuxie (Debian/Ubuntu):
   ```bash
   cp -a --backup=numbered serwer/linux-port/. /opt/mt2009/linux-port/
   ```
2. Na koniec `docker/game/src/serverfiles/share/locale/poland/locale_string.txt` dopisz 2 linie
   z `serwer/wykrywacz/locale_string_dodatek.txt` (mod 05).
3. Mod 05, raz: dodaj przedmiot 76009 do bazy (`INSERT IGNORE` – istniejący wpis zostaje):
   ```bash
   cd /opt/mt2009/linux-port/docker
   docker cp /sciezka/do/serwer/wykrywacz/wykrywacz_bossow.sql metin2-db:/tmp/w.sql
   docker exec metin2-db sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" < /tmp/w.sql'
   ```
   Potem w panelu (edytor bazy) przy 76009: nazwa i opis, stackowanie włączone, blokada stacku zdjęta (te zmiany trzeba wprowadzić ręcznie).
   Query na dodanie stackowania i zdjęta blokada stacku:
   ```sql
   UPDATE world.item_proto
    SET flag = flag | 4,              -- ITEM_FLAG_STACKABLE
        antiflag = antiflag & ~32768, -- zdjęta ITEM_ANTIFLAG_STACK
        stack = GREATEST(stack, 200)  -- ile sztuk w jednym polu
    WHERE vnum IN (76009, 27989, 76006);
    ```
4. Przebuduj i uruchom serwer:
   ```bash
   cd /opt/mt2009/linux-port/docker && docker compose up -d --build
   ```

Ręczne kopiowanie wgrywa **wszystkie** mody serwera (z 18 i 19 – wersję 19, która obejmuje bossów; także 20). Żeby wybrać tylko niektóre, użyj
`Wybierz_mody.bat` (część „serwer”) na komputerze, który widzi folder `linux-port`.

---

## Jak działa instalator

- **Klient:** pliki `.py` gry są w `pack/root` – `root.data` (zawartość) i `root.index` (spis, co
  gdzie leży). `klient/pack/root.data` z paczki zawiera każde połączenie modów każdego zmienionego
  pliku (np. `game.py` ma 15 wariantów). Instalator składa nowy `root.index` z czystego indeksu
  2.0.70 (`instalator/root.base`) i wpisów wybranych wariantów (`instalator/root.var`), po czym
  pakuje go i szyfruje jak oryginał. Gra czyta tylko to, na co wskazuje indeks. Tak samo
  `pack/etc` (mody 07, 08); `pack/gamedata` (ikona 76009) jest kopiowany przy modzie 05.
- **Serwer:** dla każdego pliku źródłowego wybiera wersję z wybranymi modami albo czystą
  (`instalator/serwer.var`, `instalator/serwer/*.bin`). Plik, którego nie rozpoznaje (własne
  zmiany), nadpisuje tylko po pytaniu.
- `Wybierz_mody.bat` uruchamia `instalator/Instalator.cs` przez PowerShell (kompilacja w pamięci,
  bez pliku `.exe`, więc Windows 11 go nie blokuje).

---

## Struktura

```
Vekirion_AiO_2.3.1/
  Wybierz_mody.bat        instalator z wyborem modów (Windows)
  CZYTAJ.txt              opis modów i instalacji
  klient/
    pack/                 root, etc, gamedata z modami (root.data z wszystkimi wariantami)
    root/                 pliki .py root luzem (dla klienta z rozpakowanym rootem)
    Ustaw_FPS.bat         łatka FPS w metin2client.exe (mod 01)
  serwer/
    linux-port/           pliki serwera z wszystkimi modami
    wykrywacz/            locale_string, SQL przedmiotu 76009, dane panelu
  instalator/             dane i kod instalatora
```

Zmienione miejsca w kodzie są oznaczone markerami `MT2009_PLUS_*`.

---

## Autorzy i licencja

- **Vekirion AiO** – Vekirion
- na podstawie **MT2009 PLUS** – ZAXEP/SIZOWSKI – <https://github.com/zaxerrrr-dot/mt2009-sp-plus>
- na podstawie **Metin2 Playerbots** – Tieru – <https://github.com/TieruYT/metin2-playerbots>
- pomysł portretów towarzyszy nad oknem P (mod 14): Mur4s

Część kodu i narzędzi (instalator, łączenie modów, część zmian serwera) powstała z pomocą
Claude (Anthropic).

Licencja: **CC BY-NC-SA 4.0** – użycie niekomercyjne, z podaniem autorów, przeróbki na tej samej
licencji. Pełny tekst i zakres: [LICENSE](LICENSE). Licencja nie obejmuje Metin2
(Ymir Interactive, Webzen), paczek plików serwerowych ani bibliotek stron trzecich.
