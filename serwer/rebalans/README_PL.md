# MT2009_PLUS_BOT_REBALANCE_V1: rebalans botów (28.10.2026, wersja 2)

Paczka zmian do moda playerbot, przygotowana do włączenia do paczki modów.
Plików serwera nie zmieniałem. Wszystkie zmiany leżą w tej paczce.

**Ważne:** kod **nie był kompilowany**. Na komputerze, na którym go pisałem, nie było kompilatora ani obrazu buildera. Dlatego po scaleniu trzeba zbudować rdzeń gry i przejrzeć ostrzeżenia. Wszystkie wywołania sprawdziłem ręcznie z istniejącym kodem: każda użyta funkcja, stała i pole struktury istnieje w źródłach i ma taką sygnaturę, jakiej używam.

## Baza

- Mod: `MOD_VERSION` = `mod-60`, `VERSION` = `2.39.0`.
- Pliki źródłowe: `linux-port/overlays/playerbot/src/game/src/`. Kopia w `linux-port/docker/game/src/server/game/src/` była w chwili pisania identyczna.
- SHA-256 plików bazowych (przed zmianą):

```
b2b7e346d454347848d8f3fb872368912ed5fc048ec600a1ef0b3a91d2edcc0d  playerbot_alchemy.h
2cb9398707524969ac848e7179323872a5ca7da3560cd87dc0d6f4cd09995eb8  playerbot_economy.h
7452d3178d377a23ea7f52a1d7f66303e96882b2dfaa6680e2a123451ff7fbd3  playerbot_config.h
74d594ca3c023a38841d48433a1f69d277b32e0743cbbe48208fd7237cc961d7  playerbot_consumables.h
3f2f230099f6d88b2d5b60a961a45ba9b7321653360973ed5573cdec5b918085  playerbot_farmer_link.h
d2bd455de85cd7f75f93cf4663eca6d0ea1988ff1d19dd8adf38a9a202beb61f  playerbot_gear.h
0f4d93e9602884ee0d74cba7b493d9c0a92de0dfef0df0f80238edb9fdbf5fd9  playerbot_manager.cpp
1c3ea162c611191cd589d8e81110de484674ee293412d6608dcd4ac1038cd286  playerbot_offline_shop.h
19f44abb1ef61e6da0172b5a30fc7c6aa47d81b48f4a23115f0362e1ceb2e3b3  playerbot_survival.h
3ee4331aac67e39e80a6e43a5c0558209b36019e9c53a81fea746ed2990dff13  playerbot_types.h
26f374ff6cf713559644baa370f42264ea13ba1cb947687105543bda6bd9c710  playerbot_upstream_botlogic.h
87b7d9a70a67c3f8d107f856e5ca4e311b826671fd0782fb387bb6324e2f6c18  playerbot_workshop.h
```

## Zawartość paczki

| Ścieżka | Co to jest |
|---|---|
| `rebalance.patch` | unified diff (`diff -ruN`, ścieżki `a/…`, `b/…` od katalogu głównego repo). Najwygodniejszy sposób scalania. |
| `files/linux-port/overlays/playerbot/src/game/src/*` | pełne pliki po zmianie, w tym nowy `playerbot_rebalance.h` |
| `README_PL.md` | ten opis |

## Jak scalić (dla Claude na drugim komputerze)

1. Sprawdź, czy pliki bazowe mają hashe podane wyżej.
   - Jeśli tak, możesz po prostu podmienić pliki z katalogu `files/`.
   - Jeśli się różnią (bo paczka modów poszła dalej), nałóż `rebalance.patch` z katalogu głównego repo: `patch -p1 --dry-run < rebalance.patch`, a potem bez `--dry-run`. Ewentualne odrzucone fragmenty (`*.rej`) wstaw ręcznie. Każda zmiana jest oznaczona komentarzem `MT2009_PLUS_BOT_REBALANCE_V1`, więc łatwo ją znaleźć.
2. Te same zmiany muszą trafić do kopii w `linux-port/docker/game/src/server/game/src/`, jeśli paczka jej nie odtwarza sama z overlayu.
3. Zbuduj rdzeń gry (MT2009, `PLAYERBOT_ENGINE_MT2009`) i popraw ewentualne błędy kompilacji.
4. Wszystkie zmiany są w jednej jednostce kompilacji (`playerbot_manager.cpp` i nagłówki, które dołącza). Żaden plik silnika ani schemat bazy się nie zmienia.

## Flagi (event flagi questów, ustawiane z panelu lub `/eventflag`)

| Flaga | Domyślnie | Działanie |
|---|---|---|
| `reb_lock_break_days` | 0 = 3 dni | Co ile dni stania na blokadzie Grindera blokada idzie o 5 poziomów w górę. Wartość `100` lub większa wyłącza tę funkcję. |
| `m2_bot_craft_errand_off` | 0 | `1` wyłącza wyprawy botów po Radę, Egzorcyzm i Zwój Wojny. |
| `m2_bot_rotation` | 0 | `1` włącza rotację botów (C2). Działa tylko razem z ustawionym `LIFE_HOURS` (np. 7). |
| `crafting_price<vnum>` | — | Istniejąca flaga. Boty płacą za crafting tyle samo co gracz. |

---

## Zmiany punkt po punkcie

### A1: blokady expa jako przerwy, a nie stały stan
- Plik: `playerbot_rebalance.h` (`AdjustPlayerBotRebalanceLock`), wywołanie w `playerbot_manager.cpp` (`ManagePlayerBotExpLock`, `GetPlayerBotShownExpLock`).
- Bot stojący na blokadzie Grindera (persona) dłużej niż `reb_lock_break_days` dni (domyślnie 3) dostaje blokadę wyżej o 5 poziomów. Łącznie maksymalnie +40.
- Stan trzymają flagi questów bota: `playerbot.reb_lock_lv`, `playerbot.reb_lock_at`, `playerbot.reb_lock_add`.
- Nie dotyczy dropków, spot-farmerów, towarzyszy ani kohorty dropków medali.
- Log: `PLAYERBOT_REBALANCE: lock break ...`

### A2: postać główna nigdy poniżej swojego dropka
- Plik: `playerbot_farmer_link.h`: `GetPlayerBotFarmerHoldLevel`, `GetPlayerBotActiveFarmerOfMain`, `GetPlayerBotMainLockFloor`. Zmiana w `ChoosePlayerBotFarmerMain`.
- Blokada postaci głównej nie może być niższa niż poziom, na którym stoi jej dropek, plus 5. Dla dropka gildyjnego to 61/66/72, dla medalowego 33.
- Przy łączeniu wybierana jest postać główna o co najmniej 5 poziomów wyżej niż docelowa blokada dropka, a nie tylko jego obecny poziom.

### A3: Rada Pustelnika i Egzorcyzm (uniwersalnie)
- Plik: `playerbot_rebalance.h` (moduł wyprawy craftingowej). Wywołanie `ManagePlayerBotCraftErrand` w `playerbot_manager.cpp`, obok warsztatu.
- **Kolejność źródeł:** crafting, potem targ, potem czytanie bez zwoju.
  1. **Crafting.** Bot czyta w trakcie gry z Lua globalną tabelę `crafting_data` (okna NPC, odświeżane co 10 minut). Przepis rozpoznaje **po działaniu przedmiotu, nie po vnumie**: `USE_AFFECT` z `AFFECT_SKILL_BOOK_BONUS` to Rada, z `AFFECT_SKILL_NO_BOOK_DELAY` to Egzorcyzm.
     - Jeśli serwer nie ma takiego przepisu (np. #85002 i #85003), lista przepisów jest pusta i bot przechodzi do następnego źródła.
     - Okno NPC jest mapowane na NPC (`GetPlayerBotCraftWindowNpc`): 101 Kowal 20016, 111 Uriel 20011, 109 Alchemik 20001 itd.
     - Jeśli NPC nie stoi na mapie bota, bot idzie do swojej pierwszej wioski.
     - Bot sprawdza materiały, poziom, wiedzę z przepisu i cenę (z flagą `crafting_price<vnum>`). Nie zużywa materiału potrzebnego do kolejnego ulepszenia noszonego eq.
     - Szansa i koszt są takie jak u gracza.
  2. **Targ.** Gdy nie da się nic wytworzyć, bot kupuje na straganie. Na Radę wydaje najwyżej 25% wolnego yang, na Egzorcyzm 10%. Rynek wie o tych vnumach: 71094/39030/71294, 71001/39008/71201/72310 oraz o produktach znalezionych przepisów.
  3. **Bez zwoju.** Gdy nie ma ani przepisu, ani oferty, bot czyta księgę bez zwoju, tak jak dotąd.
- Bot trzyma 2 Rady, gdy ma czytelną księgę klasową. Egzorcyzm trzyma tylko przy wyłączonych szybkich księgach.
- **Pergamin (30366), wersja 2.** Gdy przepis na Radę albo Egzorcyzm nie wychodzi tylko z powodu brakującego materiału, bot go dorabia:
  - **Wiersz zasilający:** dowolny wiersz craftingu w dowolnym oknie NPC, który produkuje brakujący materiał. Jeśli dodasz u Uriela „Pergamin ze Zagadkowej Szkatułki 50033”, bot go użyje, a kontrola skrzyń (`playerbot_consumables.h`) **nie otworzy** tylu szkatułek, ile wiersz potrzebuje. Te sztuki nie idą też do handlarza ani na stragan.
  - **Wymiana u Soona (NPC 20023):** to SKILLBOOK_EXCHANGE z `item_exchange.lua`, czyli dowolna księga za 1 Pergamin i 1000 yang. Bot oddaje **wyłącznie bezużyteczne księgi** (`IsPlayerBotUselessBook`): innej klasy lub buildu, umiejętności powyżej Mistrza albo ponad limit ksiąg na umiejętność (5).
  - Po wymianie u Soona bot od razu idzie dalej, do Uriela.
  - Logi: `PLAYERBOT_REBALANCE: book exchange ...` i `crafting rows ... feeders=`.

### A4: księgi
- `PLAYERBOT_BOOK_KEEP_PER_SKILL` 12 → 5 (`playerbot_types.h`). Bot nie kupuje już dwunastu ksiąg naraz.

### B1: Zwój Wojny z craftingu (uniwersalnie) i zwoje od +4
- Ten sam moduł co w A3. Produkt jest rozpoznawany po funkcji: `USE_TUNING` z `UP_TO_3TH_LEVEL_SCROLL` (100% na +0…+3). U Ciebie to przepisy #1 (25044) i #4 (71021).
- Bot trzyma 3 Zwoje Wojny, gdy ma noszony przedmiot na +0…+3 z celem wyżej albo broń przygotowywaną do ręki (B4).
- `playerbot_economy.h` (pętla ulepszania):
  - Gdy w torbie jest Zwój Wojny, **każdy** krok noszonego przedmiotu poniżej +4 idzie pod niego, także kroki z 90% szansą.
  - „Moneta” Iwakury nigdy nie odkłada wtedy zwoju na rzecz zwykłego kowadła.
- `PLAYERBOT_SCROLL_REFINE_MIN_PLUS` 6 → 4: Zwoje Błogosławieństwa od +4 (w torbach leży ich 62 tys.).
- `playerbot_gear.h`: blokada persony „hełm, buty i biżuteria najwyżej +4, dopóki broń, zbroja i tarcza nie mają +7” zmieniona z +7 na **+5**.

### B2: bonusy od +4
- `playerbot_types.h`:
  - `PLAYERBOT_BONUS_WEAPON_MIN_LEVEL` 45 → 30;
  - `PLAYERBOT_BONUS_WEAPON_MIN_PLUS` 6 → 4;
  - `PLAYERBOT_BONUS_ARMOUR_MIN_PLUS` 6 → 4 (zbroja, hełm, tarcza);
  - `PLAYERBOT_BONUS_EAR_MIN_PLUS` 6 → 4.
- Broń ze średnią z 30 lv (`PLAYERBOT_BONUS_L30_MIX_MIN_PLUS` = 6) zostaje bez zmian, żeby nie mieszać średnich za wcześnie.

### B3: Kamienie Duszy od +4
- `PLAYERBOT_SOUL_STONE_MIN_GEAR_REFINE` 6 → 4.

### B4: broń oceniana po obrażeniach, bez sztywnej różnicy poziomów
- `playerbot_upstream_botlogic.h`: nowa funkcja `GetPlayerBotWearableUpgradePlus`. Rozszerzone `GetPlayerBotFutureSlot` i `GetPlayerBotFutureProjectTarget`.
- Mechanizm:
  - Broń, którą bot może już założyć, o wyższym poziomie niż broń w ręce, staje się „projektem”, jeśli **po ulepszeniu** (najwyżej +7) zadaje większe obrażenia niż broń w ręce. Porównanie liczy ten sam model obrażeń co reszta botów (`GetPlayerBotWeaponHitDamageAt`).
  - Projekt jest ulepszany dokładnie do plusa, przy którym wygrywa, a potem zakładany przez zwykłą ocenę ekwipunku.
- To rozwiązuje przypadek „30 lv +6 w ręce, 50 lv +0 w torbie”: bot doprowadzi 50 lv do +4 i ją założy.
- **Żaden próg różnicy poziomów** niczego tu nie decyduje. Liczą się tylko obrażenia, więc dobra broń 30/50/65/75 ze średnią zostaje w ręce, dopóki nic jej nie przebije. Projekt nie jest sprzedawany ani wystawiany.

### B5: alchemia
- `playerbot_alchemy.h`:
  - Otwierane są **wszystkie** Cor Draconis: 50255–50260, czyli także szlifowane, rzadkie, antyczne i legendarne. Bot sprawdza miejsce na stronie właściwego stopnia. W torbach leżało 16 336 Cor antycznych, każdy daje kamień Antyczny.
  - Cele: 30–54 lv Antyczny (krok 4), 55–74 lv Legendarny (krok 4, siła 1), 75–89 lv Legendarny (siła 3), 90+ lv bez zmian (Mityczny).
  - `PLAYERBOT_ALCHEMY_PERCENT` 75 → 100: każdy bot od 30 lv „klika” alchemię. Działa istniejący mechanizm: dobre kamienie bot zostawia sobie, nadmiar i miksy o słabych liniach wystawia, a do 8 sztuk każdego rodzaju zostawia jako materiał do ulepszania (np. matowy → przejrzysty).
  - `PLAYERBOT_DS_KEEP_GRADE` 3 → 4: eliksir czasu (5 mln) dostają automatycznie kamienie od Legendarnego. Antyczny dostaje eliksir tylko wtedy, gdy jego odtworzenie kosztowałoby ponad 2 eliksiry. Bez tego boty z sześcioma kamieniami Antycznymi przepalałyby 30 mln dziennie.

### B6: sprzątanie torby bez sztywnej różnicy poziomów
- Zgodnie z Twoją uwagą nie ma reguły „sprzedaj, co jest X poziomów niżej”. Torbę odciąża punkt D1 (nadmiar +0…+2 trafia do handlarza), a broń wartościowa po obrażeniach jest chroniona przez B4.

### C1: zgony w Lochu Małp
- Plik: `playerbot_rebalance.h`. Wywołania w `playerbot_manager.cpp` (`NotePlayerBotRebalanceLife`) i `playerbot_survival.h` (`NotePlayerBotRebalanceRevived` po `restart_here`).
- Drugi zgon w ciągu 4 minut na tej samej mapie: bot wstaje w punkcie restartu mapy (`GetRecallPositionByEmpire`), a nie w środku stada, które go zabiło. Tak samo działa to już w Ochao i Arezzo.
  - Nie dotyczy wiosek, instancji, wojny gildii, Ochao, Arezzo, biegów lochów, towarzyszy ani grupy z graczem.
- Dropek, który ginie co najmniej 6 razy na godzinę, zatrzymuje 70% zarobku zamiast 30%. Pieniądze idą na jego własne eq, bo działa już mechanizm inwestowania dropka.
- Log: `PLAYERBOT_REBALANCE: restart point ...`

### C2: rotacja botów (opcjonalnie)
- `playerbot_manager.cpp` (`ManageLifeSchedule`), pamięć ławki w `playerbot_rebalance.h`.
- Włączenie: `m2_bot_rotation = 1` i ustawione `LIFE_HOURS` (np. 7).
- Mechanizm:
  - Gdy botowi kończy się sesja, idzie na odpoczynek i **oddaje miejsce** botowi z tego samego królestwa, który najdłużej był poza grą. Najpierw biorą je boty, które nigdy nie grały.
  - Liczba botów w grze się nie zmienia, ale przez sloty przechodzi cała pula 4 500 postaci.
  - Kohorta dropków medali nie rotuje.
- Log: `PLAYERBOT_LIFE: rotation out=... in=...` oraz `rotation=1 rotated_in=N` w censusie.
- **Ryzyko:** zakładam, że każde królestwo ma swoją pulę postaci na jednym rdzeniu danego kanału, tak jak w `SpawnRegistered`. Najpierw włącz to na próbę i sprawdź w `log.playerbot_session`, czy żaden pid nie jest zalogowany dwa razy.

### C4: więcej gildii
- `PLAYERBOT_GUILD_FOUNDER_SHARE` 12 → 6: gildię zakłada co szósty uprawniony bot (od 40 lv). Na serwerze było 12 gildii.

### D1: śmieci na straganach
- `playerbot_economy.h`: istniejący limit „glut” (dotąd tylko eq poniżej 30 lv, 20 sztuk na vnum) obejmuje teraz także **zwykłe eq od 30 lv na +0…+2**: hełmy, buty, tarcze, zbroje i broń bez bonusów i bez nagrody.
- Takiego przedmiotu może być na straganach najwyżej **4 sztuki na vnum**. Nadwyżka:
  - wraca ze straganu do torby po jednej linii na wizytę;
  - nie jest wystawiana ponownie;
  - trafia do handlarza.
- Kilka sztuk zostaje na rynku dla młodych botów i graczy. To odpowiedź na pytanie „inny pomysł niż limit liczby przedmiotów”: limit liczony **według popytu na dany vnum**, a nie limit sklepu.
- Wyjątki: broń 30 lv ze średnią, Stalki, projekt B4 i zapasowe sztuki, które bot ulepsza do +4 na sprzedaż.

### D2: ceny
- `playerbot_offline_shop.h` (pętla przeceny) i `playerbot_rebalance.h`.
- **5–8 zmian ceny jednej linii dziennie**, zależnie od pid. Linię poniżej progu bot zawsze poprawia.
- Bot z wolnym yang poniżej 1 mln wystawia cenę bliżej dołu widełek: próg plus 30% drogi od progu do ceny docelowej.

### E1: polityka przedmiotów „limit” (pierścienie z dyń i podobne)
- Pliki: `playerbot_config.h` (parser), `playerbot_types.h` (`PLAYERBOT_ITEM_POLICY_LIMIT`), `playerbot_economy.h` (`IsPlayerBotOverItemLimit`, reguła złomu, odrzucanie u handlarza).
- **Dlaczego `71135 merchant` nie działa:** Pierścień Półksiężyca (71135) i Lizak Potęgi (71136) mają flagi NIE_SPRZEDAWAJ, NIE_WYRZUCAJ, NIE_DAWAJ i NIE_NA_STRAGAN (antiflag 106880 / 106624). Handlarz ich nie kupuje, więc bot oznacza je jako złom, ale nigdy ich nie pozbywa. 28.10 w torbach 227 botów leżało 618 pierścieni.
- **Nowa składnia** w `/opt/m2spool/playerbot_item_policy.tsv`:
  ```
  71135	limit	2	dynia	# jeden noszony, jeden zapasowy
  71136	limit	2	dynia	# lizak liczy się razem z pierścieniem
  ```
  - `limit N [grupa]`: bot trzyma łącznie N przedmiotów z grupy, noszone liczą się pierwsze, potem torba w kolejności komórek.
  - Bez nazwy grupy limit dotyczy tylko tego vnumu, a bez liczby N = 1.
  - Nadmiar, który handlarz kupuje, bot sprzedaje.
  - Nadmiar ze znacznikiem NIE_SPRZEDAWAJ bot **niszczy przy wizycie u handlarza**, tak samo jak przy polityce `drop`. Log: `PLAYERBOT_AI: discarded over its limit ...`.
  - Nie dotyczy towarzyszy graczy.
- Uwaga: nie używaj na tych pierścieniach polityki `drop`. W mieście bot zdejmuje pierścień, więc `drop` zniszczyłby również ten jedyny.
- Sprawdź, czy panel /ai/items nie wycina nieznanego mu słowa `limit` przy zapisie. Jeśli wycina, dopisz te linie ręcznie.

### C3, C5, C6: bez zmian
- C3 zgodnie z Twoją uwagą: część skoków po kanałach to szukanie metinów i bossów oraz koordynacja sklepów, więc zostawiłem to bez zmian.
- C5 (szkatułki) i C6 (mikstury): wstrzymane na Twoją prośbę. Szkatułki zaczną się opłacać same, bo boty otworzą Cor antyczne i będą używać Zaczarowań i Wzmocnień od +4.

---

## Więcej botów naraz: szacunek

Stan z 28.10 około 21:00:
- 16 rdzeni CPU, 24 GB RAM;
- kontener gry używa łącznie 1,4 rdzenia i 8 GB;
- trzy główne procesy `game` po około 40% **jednego** rdzenia (silnik jest jednowątkowy na proces);
- na kanale 1, game1 ok. 334–348 botów;
- baza danych 13% CPU.

**Pojemność.** Wąskim gardłem jest jednowątkowy proces na kanał i rdzeń, a nie maszyna. Przy obecnym obciążeniu (~0,12% rdzenia na bota) jeden proces pociągnie bezpiecznie ok. 600–650 botów przy 75–80% rdzenia. Daje to ok. **1,6–1,8 tys. botów jednocześnie** zamiast ~1,1–1,3 tys., czyli +40–60% bez zmiany sprzętu. Ostrożnie: zwiększaj co 200 i obserwuj `PLAYERBOT_OFFLINE: budget ... refused` oraz lag ticka.

**Wpływ na rynek:**
- **Plusy:**
  - więcej kupujących na tanie rzeczy, bo nowe boty zaczynają od 1 lv, a dziś towar +0…+2 sprzedaje się w ~9%;
  - więcej dropu z potworów, który dziś wynosi ok. 3,9 mld yang dziennie przy ~1,2 tys. botów online, więc ok. 3,3 mln na bota online;
  - więcej materiałów, Cor i kamieni na rynku;
  - świat wygląda na żywszy.
- **Minusy i ryzyka:**
  - produkcja yang rośnie liniowo z liczbą botów, a realne ujścia (ulepszanie 0,22 mld dziennie, NPC 0,02 mld) są małe;
  - ceny rzeczy rzadkich (księgi, szkatułki, szarfy) pójdą w górę przy większej liczbie kupujących, jeśli podaż nie nadąży;
  - więcej linii na straganach i więcej przecen, ale D1 i D2 to ograniczają.
- **Moja ocena:** przy wdrożeniu tej paczki wpływ będzie **raczej pozytywny**, bo paczka dodaje ujścia yang:
  - crafting zwojów (400 tys. za Zwój Wojny);
  - opłaty za ulepszanie od +4 i za kamienie;
  - eliksiry do kamieni Legendarnych;
  - opłaty u alchemika.
- Bez tych ujść większa liczba botów przyspieszyłaby inflację. Najlepiej podnieść liczbę razem z rotacją C2: więcej postaci przewija się przez sloty i rozwija, a jednocześnie online jest ich tylko trochę więcej.

## Jak sprawdzić po wdrożeniu (SELECT-y)

```sql
-- zbroja i biżuteria: plusy botów 40+ (powinny wyjść powyżej +4)
SELECT i.vnum%10 plus, COUNT(*) FROM player.item i JOIN player.player p ON p.id=i.owner_id
 WHERE i.window='EQUIPMENT' AND p.level>=40 AND p.id<9000 GROUP BY plus;
-- alchemia: stopnie noszonych kamieni
SELECT FLOOR(vnum/1000)%10 grade, COUNT(*) FROM player.item WHERE window='EQUIPMENT' AND vnum BETWEEN 110000 AND 169999 GROUP BY grade;
-- Cor antyczne w torbach (powinno spadać)
SELECT SUM(count) FROM player.item WHERE vnum=50258;
-- blokady głównych postaci
SELECT EXISTS(SELECT 1 FROM player.affect a WHERE a.dwPID=l.main_pid AND a.bType=310) locked, COUNT(*)
 FROM player.playerbot_farmer_link l WHERE l.active=1 GROUP BY locked;
-- zmiany cen dziennie (było ok. 319 tys.)
SELECT COUNT(*) FROM log.ikarusshop_log WHERE what='EDIT_PRICE' AND time > NOW() - INTERVAL 1 DAY;
```

W syslogu szukaj: `PLAYERBOT_REBALANCE:` (craft, craft errand, restart point, lock break, crafting rows) oraz `PLAYERBOT_LIFE: rotation`.
