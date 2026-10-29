// MT2009 Plus - instalator z wyborem modow (Wybierz_mody.bat kompiluje ten plik).
// C# 5 / .NET Framework 4 (csc.exe z Windowsa albo Add-Type w PowerShellu).
//
// KLIENT: pack\root.index jest skladany na nowo z czystego indeksu klienta 2.0.70
// (instalator\root.base) i rekordow wybranych modow (instalator\root.var). Dane
// (klient\pack\root.data z paczki) maja w sobie kazdy wariant kazdego pliku, wiec
// root.data jest zawsze ten sam, a o tym, ktore pliki gra czyta, decyduje tylko indeks.
// Tak samo pack\etc (mody 13, 14). gamedata (ikona 76009, mod 11) jest kopiowany jak dawniej.
// SERWER: pliki z instalator\serwer (czysty plik albo wariant z wybranymi modami);
// plik, ktorego nie rozpoznaje (Twoje wlasne zmiany), nadpisuje tylko po pytaniu.
// Wszystko, co podmienia, najpierw idzie do kopii zapasowej.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace MT2009
{
	public static class Instalator
	{
		class Mod
		{
			public string Id; public string Nazwa; public bool K; public bool S;
			public Mod(string id, bool k, bool s, string nazwa) { Id = id; K = k; S = s; Nazwa = nazwa; }
		}

		static readonly Mod[] Mody = new Mod[] {
			new Mod("01", true, false, "FPS 60/120/144/240 (Opcje Gry > System) + latka exe"),
			new Mod("02", true, false, "Ruch bez zatrzymywania (buff, kon/mount, cios, LPM)"),
			new Mod("03", true, false, "Autolowy bez skakania miedzy celami przy scianach"),
			new Mod("04", true, false, "Ctrl+PPM otwiera tez karty i skrzynki"),
			new Mod("05", true, true,  "Wykrywacz Bossow 76009 + znaczniki na calej mapie"),
			new Mod("06", true, true,  "Wykrywacz sam otwiera mape (wymaga 05)"),
			new Mod("07", true, false, "Wyrazniejszy znacznik celu na mapie (pack etc)"),
			new Mod("08", true, false, "Poprawka mgly na mapach (pack etc)"),
			new Mod("09", true, true,  "Depozyt i stakowanie (sklepy offline / Dom Aukcyjny)"),
			new Mod("10", false, true, "Przenoszenie przedmiotow przy otwartym sklepie"),
			new Mod("11", true, false, "Mapa M w Czerwonym Lesie"),
			new Mod("12", false, true, "Drop bez limitu poziomu"),
			new Mod("13", true, false, "Puste kwadraty pod Proton/Wine (Steam Deck)"),
			new Mod("14", true, true,  "Towarzysz - przebudowa (druzyna, lawka, Shift/Ctrl/Alt+P)"),
			new Mod("15", false, true, "Bez kontroli speedhacka (ruch i szybkosc ataku)"),
			new Mod("16", false, true, "Zwoje powrotu 5 min, biala flaga bez blokady, szybkie karty"),
			new Mod("17", false, true, "Ulepszanie co 0,2 s zamiast co 1 s"),
			new Mod("18", false, true, "Nieodpychanie bossow"),
			new Mod("19", false, true, "Nieodpychanie mobow (wszystkich)"),
			new Mod("20", false, true, "Kupowanie ze stosow (boty kupia czesc stosu taniej)"),
			new Mod("21", false, true, "Wieza Demonow: wyjscie po 15 min / u Straznika, szybsze pieczecie"),
			new Mod("22", false, true, "Panel: drop - zmiana masowa + ksiega z metinow"),
			new Mod("23", false, true, "Rebalans botow (blokady, zwoje, bonusy, alchemia, ceny...)"),
		};

		// wersja klienta, na ktora jest ta paczka (CLIENT_VERSION)
		const string ClientVersion = "2.0.70";

		static readonly uint[] IndexKey = new uint[] { 533489241, 64592187, 413438084, 181131063 };

		// klient\pack z paczki (sprawdzenie, czy wszystkie czesci zip sa rozpakowane)
		const string PkgRootData = "E09DD68C29E9352ED7B2C6BAEBB522B5";
		const string PkgEtcData = "BA9319906DA1F1EED275A6315FBFEAD4";
		const string PkgGdIndex = "70B23A9B350E2719CB3D50E4C0C35A4D";
		const string PkgGdData = "ED5F7419B5740DF83DD2D7D544F79B69";
		// root.index, nad ktorym wolno pracowac bez pytania: czysty 2.0.70 i ta paczka (2.0.70, wszystkie mody).
		// Inny zestaw modow z tej paczki rozpoznaje po root= w mt2009_mody.txt.
		static readonly string[] KnownRoot = new string[] {
			"E82FB838C2BBC4B825FB67C201F58B3B", "0BB8B7C3E95E62D6A9E23A8A3D31DCFD", "201F308BA2EE0DA99D23304E51A6DC75",
			"C84596D4DCDED2C1B9C3F9E24D3A20BB" };
		// etc.index: czysty (2.0.66-2.0.70 maja ten sam etc), z poprawka mgly, z mgla i znacznikiem
		static readonly string[] KnownEtc = new string[] {
			"3D5E1E22A73C42DAF0825A0D6BD311C8", "A748EC48CFD78076FEADF7AE2556EAB6", "1FCE8FCDF557EE4B25ABE32A2E2A0980" };
		const string CleanGdIndex = "698DEBD1C4A65E84ED563D0ED5E03F4F";
		// gamedata podmieniany jak czysty: czysty 2.0.68, pierwsze wydanie 2.1.2 (ikona byla, ale item_list.txt
		// nie wskazywal na nia - 76009 mial ikone Zwoju Boga Smokow) i paczki 2.1.2-2.2.2 (2.0.68 z ikona)
		static readonly string[] OldGdIndex = new string[] {
			"3028F9B6BB409FCBACAA814ECF8E5B8E", "0E10A126D0B47073C1D95C811A14C974", "4BE217B51149B21DC41B7FE16B944759" };

		const string ClientSave = "mt2009_mody.txt";
		const string ServerSave = "mt2009_mody_serwer.txt";

		static string Pkg;
		static string Backup;
		static readonly Encoding Latin = Encoding.GetEncoding(28591);

		// wynik instalacji: co sie udalo (Good) i co nie (Bad), per mod
		static readonly Dictionary<string, List<string>> Good = new Dictionary<string, List<string>>();
		static readonly Dictionary<string, List<string>> Bad = new Dictionary<string, List<string>>();

		static void Done(string id, string note)
		{
			List<string> l;
			if (!Good.TryGetValue(id, out l)) { l = new List<string>(); Good[id] = l; }
			if (!l.Contains(note)) l.Add(note);
		}

		static void Fail(string id, string note)
		{
			List<string> l;
			if (!Bad.TryGetValue(id, out l)) { l = new List<string>(); Bad[id] = l; }
			if (!l.Contains(note)) l.Add(note);
		}

		static Mod FindMod(string id)
		{
			foreach (Mod m in Mody) if (m.Id == id) return m;
			return null;
		}

		static void Say(ConsoleColor c, string prefix, string msg)
		{
			ConsoleColor o = Console.ForegroundColor;
			Console.ForegroundColor = c;
			Console.Write(prefix);
			Console.ForegroundColor = o;
			Console.WriteLine(msg);
		}

		static void SayAll(ConsoleColor c, string msg)
		{
			ConsoleColor o = Console.ForegroundColor;
			Console.ForegroundColor = c;
			Console.WriteLine(msg);
			Console.ForegroundColor = o;
		}

		static void Ok(string m) { Say(ConsoleColor.Green, "  [OK] ", m); }
		static void Warn(string m) { Say(ConsoleColor.Yellow, "  [UWAGA] ", m); }
		static void Info(string m) { Console.WriteLine("       " + m); }

		static void Title(string m)
		{
			Console.WriteLine();
			SayAll(ConsoleColor.Cyan, "  " + m);
			SayAll(ConsoleColor.Cyan, "  " + new string('-', m.Length));
		}

		static void Clear()
		{
			try { Console.Clear(); } catch (Exception) { Console.WriteLine(); }
		}

		public static int Main(string[] args)
		{
			try { return Run(); }
			catch (Exception e)
			{
				Console.WriteLine();
				Say(ConsoleColor.Red, "  [BLAD] ", e.Message);
				return 1;
			}
		}

		static int Run()
		{
			Pkg = Environment.GetEnvironmentVariable("M2_PKG");
			if (string.IsNullOrEmpty(Pkg)) Pkg = AppDomain.CurrentDomain.BaseDirectory;
			Pkg = Pkg.TrimEnd('\\', '/');
			if (!File.Exists(Path.Combine(Pkg, "instalator\\root.var")))
				throw new Exception("Brak " + Pkg + "\\instalator - uruchom Wybierz_mody.bat z rozpakowanej paczki Vekirion AiO.");

			Clear();
			Title("MT2009 Plus - instalacja wybranych modow");
			Console.WriteLine();
			Console.WriteLine("  Co instalujesz?");
			Console.WriteLine("    1 = klient (gra)");
			Console.WriteLine("    2 = serwer (folder linux-port)");
			Console.WriteLine("    3 = klient i serwer");
			Console.WriteLine();
			string co = Ask("  Wybor (Enter = 1) > ");
			bool doK = co == "" || co == "1" || co == "3";
			bool doS = co == "2" || co == "3";
			if (!doK && !doS) { Warn("Nic nie wybrano."); return 1; }

			string client = null, lp = null;
			HashSet<string> saved = null;
			if (doK)
			{
				client = AskClient();
				saved = LoadSaved(Path.Combine(client, ClientSave));
			}
			if (doS)
			{
				lp = AskLinuxPort();
				HashSet<string> s2 = LoadSaved(Path.Combine(lp, ServerSave));
				if (saved == null) saved = s2;
				else if (s2 != null) saved.UnionWith(s2);
			}
			HashSet<string> prevClient = doK ? LoadSaved(Path.Combine(client, ClientSave)) : null;

			HashSet<string> sel = Menu(doK, doS, saved);
			if (sel == null) { Warn("Przerwano - nic nie zostalo zmienione."); return 1; }

			string stamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
			if (doK)
			{
				Backup = Path.Combine(client, "backup_mody_" + stamp);
				InstallClient(client, sel, prevClient);
			}
			if (doS)
			{
				Backup = Path.Combine(lp, "backup_mody_" + stamp);
				InstallServer(lp, sel);
			}
			return Summary(doK, doS, sel, saved);
		}

		// ------------------------------------------------------------------ wybor

		static HashSet<string> Menu(bool doK, bool doS, HashSet<string> saved)
		{
			List<Mod> list = new List<Mod>();
			foreach (Mod m in Mody) if ((doK && m.K) || (doS && m.S)) list.Add(m);
			HashSet<string> sel = new HashSet<string>();
			foreach (Mod m in list) if (saved == null || saved.Contains(m.Id)) sel.Add(m.Id);
			List<string> msgs = new List<string>();
			while (true)
			{
				Clear();
				Title("MT2009 Plus - wybor modow (" + (doK && doS ? "klient i serwer" : (doK ? "klient" : "serwer")) + ")");
				Console.WriteLine(saved == null ? "  Na start zaznaczone sa wszystkie mody." : "  Zaznaczone jak przy ostatniej instalacji.");
				Console.WriteLine();
				foreach (Mod m in list) PrintMod(m, sel.Contains(m.Id));
				Console.WriteLine();
				Console.WriteLine("  Zaznaczone: " + sel.Count + " z " + list.Count);
				foreach (string msg in msgs) Say(ConsoleColor.Cyan, "  >> ", msg);
				msgs.Clear();
				Console.WriteLine();
				Console.WriteLine("  Wpisz numer(y) moda, zeby go wlaczyc/wylaczyc, np.: 03   albo   03 22");
				Console.WriteLine("  A = zaznacz wszystkie    N = odznacz wszystkie    Q = wyjdz bez zmian");
				string a = Ask("  Enter = INSTALUJ zaznaczone > ");
				if (a == "") break;
				string u = a.ToUpperInvariant();
				if (u == "Q") return null;
				if (u == "A") { foreach (Mod m in list) sel.Add(m.Id); msgs.Add("Zaznaczono wszystkie mody."); continue; }
				if (u == "N") { sel.Clear(); msgs.Add("Odznaczono wszystkie mody."); continue; }
				foreach (string tok in a.Split(new char[] { ' ', ',', ';', '\t' }, StringSplitOptions.RemoveEmptyEntries))
				{
					int n;
					if (!int.TryParse(tok.Trim(), out n)) { msgs.Add("Nie rozumiem \"" + tok + "\" - wpisz numer moda z listy."); continue; }
					string id = n.ToString("00", System.Globalization.CultureInfo.InvariantCulture);
					Mod found = null;
					foreach (Mod m in list) if (m.Id == id) found = m;
					if (found == null) { msgs.Add("Na liscie nie ma moda " + tok + "."); continue; }
					if (sel.Contains(id)) { sel.Remove(id); msgs.Add("Mod " + id + " (" + found.Nazwa + ") - WYLACZONY"); }
					else { sel.Add(id); msgs.Add("Mod " + id + " (" + found.Nazwa + ") - WLACZONY"); }
				}
			}

			Clear();
			Title("Podsumowanie wyboru");
			Console.WriteLine();
			if (sel.Contains("06") && !sel.Contains("05"))
			{
				sel.Add("05");
				Warn("Mod 06 wymaga moda 05 - wlaczono tez 05.");
			}
			if (sel.Contains("18") && sel.Contains("19"))
				Info("Mod 19 obejmuje tez bossow - z 18 i 19 serwer dostaje wersje z 19.");
			List<Mod> on = new List<Mod>(), off = new List<Mod>();
			foreach (Mod m in list) if (sel.Contains(m.Id)) on.Add(m); else off.Add(m);
			Console.WriteLine("  Zostana zainstalowane (" + on.Count + "):");
			if (on.Count == 0) SayAll(ConsoleColor.DarkGray, "      (zaden - " + (doK ? "klient" : "serwer") + " wroci do wersji bez modow)");
			foreach (Mod m in on) Say(ConsoleColor.Green, "    + ", m.Id + "  " + m.Nazwa);
			if (off.Count > 0)
			{
				Console.WriteLine();
				Console.WriteLine("  Nie beda instalowane" + (saved != null ? " (wczesniej zainstalowane zostana usuniete)" : "") + " (" + off.Count + "):");
				foreach (Mod m in off)
				{
					bool was = saved != null && saved.Contains(m.Id);
					Say(was ? ConsoleColor.Yellow : ConsoleColor.DarkGray, was ? "    - " : "      ", m.Id + "  " + m.Nazwa + (was ? "   <- zostanie USUNIETY" : ""));
				}
			}
			if (!sel.Contains("14"))
			{
				Console.WriteLine();
				Warn("Bez 14 wraca stary towarzysz. Klient i serwer musza miec 14 oba albo zaden.");
			}
			Console.WriteLine();
			string ok = Ask("  Instalowac? [T/n] > ");
			if (ok.StartsWith("n", StringComparison.OrdinalIgnoreCase)) return null;
			return sel;
		}

		static void PrintMod(Mod m, bool on)
		{
			string gdzie = m.K && m.S ? "klient+serwer" : (m.K ? "klient" : "serwer");
			ConsoleColor o = Console.ForegroundColor;
			Console.ForegroundColor = on ? ConsoleColor.Green : ConsoleColor.DarkGray;
			Console.Write(on ? "   [x] " : "   [ ] ");
			Console.Write(m.Id + "  " + m.Nazwa.PadRight(60) + " ");
			Console.ForegroundColor = on ? ConsoleColor.Gray : ConsoleColor.DarkGray;
			Console.WriteLine(gdzie);
			Console.ForegroundColor = o;
		}

		static int Summary(bool doK, bool doS, HashSet<string> sel, HashSet<string> saved)
		{
			Title("WYNIK INSTALACJI");
			Console.WriteLine();
			int bad = 0;
			foreach (Mod m in Mody)
			{
				if (!((doK && m.K) || (doS && m.S))) continue;
				if (sel.Contains(m.Id))
				{
					List<string> b, g;
					if (Bad.TryGetValue(m.Id, out b))
					{
						bad++;
						Say(ConsoleColor.Yellow, "  [!!] ", m.Id + "  " + m.Nazwa);
						foreach (string x in b) SayAll(ConsoleColor.Yellow, "         " + x);
						if (Good.TryGetValue(m.Id, out g)) Info("  udalo sie: " + string.Join(", ", g.ToArray()));
					}
					else if (Good.TryGetValue(m.Id, out g))
						Say(ConsoleColor.Green, "  [OK] ", m.Id + "  " + m.Nazwa + "   (" + string.Join(", ", g.ToArray()) + ")");
					else
						Say(ConsoleColor.Green, "  [OK] ", m.Id + "  " + m.Nazwa);
				}
				else if (saved != null && saved.Contains(m.Id))
					Say(ConsoleColor.Gray, "  [--] ", m.Id + "  " + m.Nazwa + "   - usuniety");
			}
			Console.WriteLine();
			if (bad == 0)
				SayAll(ConsoleColor.Green, "  *** INSTALACJA ZAKONCZONA POMYSLNIE - zainstalowano " + sel.Count + " mod(ow) ***");
			else
				SayAll(ConsoleColor.Yellow, "  *** ZAINSTALOWANO, ALE " + bad + " MOD(Y) NIE W CALOSCI - opis przy [!!] wyzej ***");
			if (doS) Console.WriteLine("  Serwer: zmiany dzialaja po przebudowie (docker compose up -d --build).");
			if (doK) Console.WriteLine("  Klient: po uzyciu MT2009-Patcher.exe uruchom Wybierz_mody.bat jeszcze raz.");
			return 0;
		}

		// Numery modow do paczki 2.1.2 (stare) -> od 2.2.1 (po kolei). Plik wyboru bez linii
		// "numeracja=2" jest ze starej paczki - jego numery sa zamieniane na nowe.
		static readonly string[,] StareNumery = new string[,] {
			{ "06", "04" }, { "11", "05" }, { "12", "06" }, { "13", "07" }, { "14", "08" }, { "18", "09" },
			{ "19", "10" }, { "22", "11" }, { "23", "12" }, { "25", "13" }, { "26", "14" }, { "27", "15" },
			{ "28", "16" }, { "29", "17" } };

		static HashSet<string> LoadSaved(string path)
		{
			if (!File.Exists(path)) return null;
			bool nowe = false;
			string mody = null;
			foreach (string l in File.ReadAllLines(path))
			{
				if (l.Trim() == "numeracja=2") nowe = true;
				if (l.StartsWith("mody=") && mody == null) mody = l.Substring(5);
			}
			if (mody == null) return null;
			HashSet<string> s = new HashSet<string>();
			foreach (string t in mody.Split(new char[] { ',' }, StringSplitOptions.RemoveEmptyEntries))
			{
				string id = t.Trim();
				if (!nowe)
					for (int i = 0; i < StareNumery.GetLength(0); i++)
						if (StareNumery[i, 0] == id) { id = StareNumery[i, 1]; break; }
				s.Add(id);
			}
			return s;
		}

		static string SavedValue(string path, string key)
		{
			if (!File.Exists(path)) return null;
			foreach (string l in File.ReadAllLines(path))
				if (l.StartsWith(key + "=")) return l.Substring(key.Length + 1).Trim();
			return null;
		}

		static string Joined(HashSet<string> sel)
		{
			List<string> l = new List<string>(sel);
			l.Sort(StringComparer.Ordinal);
			return string.Join(",", l.ToArray());
		}

		// ------------------------------------------------------------------ klient

		static string AskClient()
		{
			string guess = null;
			string parent = Path.GetDirectoryName(Pkg);
			foreach (string c in new string[] { parent, "D:\\Metin2 Singleplayer", "D:\\Klient", "C:\\Metin2 Singleplayer" })
				if (!string.IsNullOrEmpty(c) && File.Exists(Path.Combine(c, "metin2client.exe"))) { guess = c; break; }
			Console.WriteLine();
			Console.WriteLine("  Folder klienta (ten, w ktorym jest metin2client.exe).");
			string p = guess != null ? Ask("  Enter = " + guess + ", albo wpisz inna sciezke > ") : Ask("  Sciezka > ");
			if (p == "" && guess != null) p = guess;
			p = p.Trim().Trim('"').TrimEnd('\\');
			if (!File.Exists(Path.Combine(p, "metin2client.exe"))) throw new Exception("W " + p + " nie ma metin2client.exe.");
			if (!File.Exists(Path.Combine(p, "pack\\root.index"))) throw new Exception("W " + p + " nie ma pack\\root.index.");
			return p;
		}

		static void InstallClient(string client, HashSet<string> sel, HashSet<string> prev)
		{
			Clear();
			Title("Instalacja - KLIENT: " + client);
			Console.WriteLine();
			if (Process.GetProcessesByName("metin2client").Length > 0) throw new Exception("Najpierw zamknij gre (metin2client).");
			if (Process.GetProcessesByName("MT2009-Patcher").Length > 0) throw new Exception("Najpierw zamknij patcher (MT2009-Patcher).");

			string kp = Path.Combine(Pkg, "klient\\pack");
			Console.WriteLine("  Sprawdzam pliki paczki...");
			CheckPkg(Path.Combine(kp, "root.data"), PkgRootData, "klient\\pack\\root.data");
			Ok("Pliki paczki kompletne.");

			// Wersja klienta z CLIENT_VERSION: starsza niz ta, na ktora jest paczka, nie jest obslugiwana
			// (najpierw patcher), nowsza - tylko po pytaniu.
			string ver = Path.Combine(client, "CLIENT_VERSION");
			if (!File.Exists(ver)) throw new Exception("W " + client + " nie ma pliku CLIENT_VERSION - uruchom najpierw MT2009-Patcher.exe.");
			string v = File.ReadAllText(ver).Trim();
			Version cv;
			try { cv = new Version(v); } catch (Exception) { throw new Exception("Nieczytelna wersja w CLIENT_VERSION: '" + v + "'."); }
			int cmp = cv.CompareTo(new Version(ClientVersion));
			if (cmp < 0)
				throw new Exception("Klient " + v + " jest NIEAKTUALNY i nie jest obslugiwany - ta paczka jest na klienta " + ClientVersion + ". Zaktualizuj klienta programem MT2009-Patcher.exe.");
			if (cmp > 0)
			{
				Warn("Klient ma wersje " + v + ", a mody sa zrobione na " + ClientVersion + " (potrzebna nowsza paczka).");
				if (!Yes("  Mimo to wgrac root " + ClientVersion + " z modami? [t/N] > ")) throw new Exception("Przerwano.");
			}
			else Ok("Klient " + v + ".");

			string saveFile = Path.Combine(client, ClientSave);
			string pack = Path.Combine(client, "pack");

			// root
			string rootIdx = Path.Combine(pack, "root.index");
			string have = Md5(rootIdx);
			if (Array.IndexOf(KnownRoot, have) < 0 && have != SavedValue(saveFile, "root"))
			{
				Warn("pack\\root.index nie jest ani czystym " + ClientVersion + ", ani wersja z tej paczki (moze patcher wgral nowsza?).");
				if (!Yes("  Zastapic go rootem " + ClientVersion + " z wybranymi modami? [t/N] > ")) throw new Exception("Przerwano - nic nie zostalo zmienione.");
			}
			byte[] rootIndex = EncodeIndex(Apply(File.ReadAllBytes(Path.Combine(Pkg, "instalator\\root.base")),
				Path.Combine(Pkg, "instalator\\root.var"), sel));

			// etc
			bool doEtc = false;
			byte[] etcIndex = null;
			string etcIdx = Path.Combine(pack, "etc.index");
			if (File.Exists(etcIdx))
			{
				string e = Md5(etcIdx);
				if (Array.IndexOf(KnownEtc, e) >= 0 || e == SavedValue(saveFile, "etc"))
				{
					CheckPkg(Path.Combine(kp, "etc.data"), PkgEtcData, "klient\\pack\\etc.data");
					etcIndex = EncodeIndex(Apply(File.ReadAllBytes(Path.Combine(Pkg, "instalator\\etc.base")),
						Path.Combine(Pkg, "instalator\\etc.var"), sel));
					doEtc = true;
				}
				else
				{
					if (sel.Contains("07") || sel.Contains("08")) Warn("pack\\etc w nieznanej wersji - mody 07 i 08 nie zostana wgrane.");
					if (sel.Contains("07")) Fail("07", "pack\\etc w nieznanej wersji - pominiety");
					if (sel.Contains("08")) Fail("08", "pack\\etc w nieznanej wersji - pominiety");
				}
			}
			else
			{
				if (sel.Contains("07")) Fail("07", "brak pack\\etc.index w kliencie");
				if (sel.Contains("08")) Fail("08", "brak pack\\etc.index w kliencie");
			}

			// gamedata (ikona 76009)
			bool doGd = false;
			string gdIdx = Path.Combine(pack, "gamedata.index");
			if (sel.Contains("05") && File.Exists(gdIdx))
			{
				string g = Md5(gdIdx);
				if (g == PkgGdIndex) Done("05", "ikona 76009 juz byla");
				else if (g == CleanGdIndex || Array.IndexOf(OldGdIndex, g) >= 0)
				{
					CheckPkg(Path.Combine(kp, "gamedata.index"), PkgGdIndex, "klient\\pack\\gamedata");
					CheckPkg(Path.Combine(kp, "gamedata.data"), PkgGdData, "klient\\pack\\gamedata");
					doGd = true;
				}
				else { Warn("pack\\gamedata w nieznanej wersji - bez nowej ikony 76009 (wykrywacz dziala)."); Done("05", "bez nowej ikony - gamedata w innej wersji"); }
			}

			// kopia zapasowa, potem zapis
			Save(client, "pack\\root.index"); Save(client, "pack\\root.data");
			if (doEtc) { Save(client, "pack\\etc.index"); Save(client, "pack\\etc.data"); }
			if (doGd) { Save(client, "pack\\gamedata.index"); Save(client, "pack\\gamedata.data"); }
			Save(client, ClientSave);
			Ok("Kopia zapasowa: " + Backup);

			File.Copy(Path.Combine(kp, "root.data"), Path.Combine(pack, "root.data"), true);
			File.WriteAllBytes(rootIdx, rootIndex);
			Ok("pack\\root wgrany (mody: " + ClientMods(sel, "01 02 03 04 05 06 09 11 13 14") + ").");
			foreach (string id in "01 02 03 04 05 06 09 11 13 14".Split(' ')) if (sel.Contains(id)) Done(id, "klient");
			if (doEtc)
			{
				File.Copy(Path.Combine(kp, "etc.data"), Path.Combine(pack, "etc.data"), true);
				File.WriteAllBytes(etcIdx, etcIndex);
				Ok("pack\\etc wgrany (mody: " + ClientMods(sel, "07 08") + ").");
				foreach (string id in new string[] { "07", "08" }) if (sel.Contains(id)) Done(id, "klient");
			}
			if (doGd)
			{
				File.Copy(Path.Combine(kp, "gamedata.index"), gdIdx, true);
				File.Copy(Path.Combine(kp, "gamedata.data"), Path.Combine(pack, "gamedata.data"), true);
				Ok("pack\\gamedata wgrany (ikona Wykrywacza Bossow 76009).");
				Done("05", "ikona 76009");
			}
			if (Directory.Exists(Path.Combine(pack, "root")))
				Warn("Masz rozpakowany pack\\root - instalator go nie zmienia (pliki .py z modami sa w klient\\root w paczce).");

			// FPS w exe (mod 01): wlaczany z 01, wylaczany, gdy 01 bylo, a teraz nie ma
			string fpsSrc = Path.Combine(Pkg, "klient\\Ustaw_FPS.bat");
			string fpsArg = null;
			if (sel.Contains("01")) fpsArg = "1";
			else if (prev != null && prev.Contains("01")) fpsArg = "0";
			if (fpsArg != null && File.Exists(fpsSrc))
			{
				Save(client, "metin2client.exe");
				string fpsBat = Path.Combine(client, "Ustaw_FPS.bat");
				File.Copy(fpsSrc, fpsBat, true);
				Console.WriteLine();
				Console.WriteLine("  Latka FPS w exe (Ustaw_FPS.bat " + fpsArg + "):");
				int rc = Run("cmd.exe", "/c \"\"" + fpsBat + "\" " + fpsArg + "\"", client);
				if (rc != 0)
				{
					Warn("Latka FPS w exe nie zostala zmieniona (komunikat wyzej). Reszta jest wgrana.");
					if (fpsArg == "1") Fail("01", "latka FPS w metin2client.exe nie zostala nalozona");
				}
				else if (fpsArg == "1") { Ok("Latka FPS w metin2client.exe nalozona."); Done("01", "latka exe"); }
				else Ok("Latka FPS w metin2client.exe cofnieta (mod 01 usuniety).");
			}

			StringBuilder sb = new StringBuilder();
			sb.Append("mody=" + Joined(sel) + "\r\n");
			sb.Append("numeracja=2\r\n");
			sb.Append("root=" + Md5(rootIdx) + "\r\n");
			if (File.Exists(etcIdx)) sb.Append("etc=" + Md5(etcIdx) + "\r\n");
			sb.Append("data=" + DateTime.Now.ToString("yyyy-MM-dd HH:mm") + "\r\n");
			File.WriteAllText(saveFile, sb.ToString(), Latin);
			Info("Cofniecie: skopiuj pliki z " + Backup + " z powrotem do klienta.");
		}

		static string ClientMods(HashSet<string> sel, string ids)
		{
			List<string> l = new List<string>();
			foreach (string id in ids.Split(' ')) if (sel.Contains(id)) l.Add(id);
			return l.Count == 0 ? "zadne" : string.Join(" ", l.ToArray());
		}

		static void CheckPkg(string path, string md5, string zip)
		{
			if (!File.Exists(path) || Md5(path) != md5)
				throw new Exception("Plik paczki " + path + " jest niepelny albo z innej paczki (" + zip + "). Pobierz i rozpakuj paczke ponownie.");
		}

		// ---- EterPack: indeks = naglowek (12 B) + rekordy po 192 B
		// rekord: 0 id, 4 nazwa (161 B), 168 crc nazwy, 172 rozmiar slotu, 176 dlugosc,
		// 180 crc danych, 184 pozycja w .data, 188 typ. Rekordy z .var maja juz pozycje.
		static byte[] Apply(byte[] baseIdx, string varPath, HashSet<string> sel)
		{
			int cnt = BitConverter.ToInt32(baseIdx, 8);
			Dictionary<string, int> at = new Dictionary<string, int>(StringComparer.Ordinal);
			for (int i = 0; i < cnt; i++)
			{
				int o = 12 + i * 192;
				int e = o + 4;
				while (e < o + 165 && baseIdx[e] != 0) e++;
				at[Latin.GetString(baseIdx, o + 4, e - o - 4)] = o;
			}
			SortedDictionary<string, Dictionary<string, string[]>> byName = new SortedDictionary<string, Dictionary<string, string[]>>(StringComparer.Ordinal);
			foreach (string line in File.ReadAllLines(varPath))
			{
				if (line.Trim() == "") continue;
				string[] p = line.Split('|');
				if (p.Length != 4) throw new Exception("Uszkodzony plik " + varPath);
				Dictionary<string, string[]> d;
				if (!byName.TryGetValue(p[0], out d)) { d = new Dictionary<string, string[]>(); byName[p[0]] = d; }
				d[p[1]] = p;
			}
			List<byte> extra = new List<byte>();
			byte[] idx = (byte[])baseIdx.Clone();
			foreach (KeyValuePair<string, Dictionary<string, string[]>> kv in byName)
			{
				HashSet<string> touching = new HashSet<string>();
				foreach (string k in kv.Value.Keys) foreach (string m in k.Split(',')) touching.Add(m);
				List<string> sub = new List<string>();
				foreach (string m in touching) if (sel.Contains(m)) sub.Add(m);
				if (sub.Count == 0) continue;
				sub.Sort(StringComparer.Ordinal);
				string key = string.Join(",", sub.ToArray());
				string[] v;
				if (!kv.Value.TryGetValue(key, out v)) throw new Exception("Brak wariantu " + kv.Key + " dla " + key);
				byte[] rec = Hex(v[3]);
				if (rec.Length != 192) throw new Exception("Zly rekord " + kv.Key);
				if (v[2] == "1")
				{
					Array.Copy(BitConverter.GetBytes(cnt), 0, rec, 0, 4);
					extra.AddRange(rec);
					cnt++;
				}
				else
				{
					int o;
					if (!at.TryGetValue(kv.Key, out o)) throw new Exception("Brak " + kv.Key + " w indeksie");
					Array.Copy(rec, 4, idx, o + 4, 188);
				}
			}
			byte[] outb = new byte[idx.Length + extra.Count];
			Array.Copy(idx, outb, idx.Length);
			extra.CopyTo(outb, idx.Length);
			Array.Copy(BitConverter.GetBytes(cnt), 0, outb, 8, 4);
			return outb;
		}

		// MCOZ: "MCOZ", rozmiar zaszyfrowany, rozmiar LZO, rozmiar surowy + XTEA("MCOZ" + LZO).
		// LZO1X zapisane jako jeden ciag literalow (poprawny strumien dla lzo1x_decompress).
		static byte[] EncodeIndex(byte[] raw)
		{
			int n = raw.Length;
			MemoryStream lz = new MemoryStream(n + n / 255 + 16);
			if (n <= 238) lz.WriteByte((byte)(17 + n));
			else
			{
				int tt = n - 18;
				lz.WriteByte(0);
				while (tt > 255) { tt -= 255; lz.WriteByte(0); }
				lz.WriteByte((byte)tt);
			}
			lz.Write(raw, 0, n);
			lz.WriteByte(0x11); lz.WriteByte(0); lz.WriteByte(0);
			byte[] comp = lz.ToArray();
			int enc = ((comp.Length + 4 + 7) / 8) * 8 + 16;
			byte[] plain = new byte[enc];
			plain[0] = (byte)'M'; plain[1] = (byte)'C'; plain[2] = (byte)'O'; plain[3] = (byte)'Z';
			Array.Copy(comp, 0, plain, 4, comp.Length);
			Xtea(plain, IndexKey);
			byte[] o = new byte[16 + enc];
			o[0] = (byte)'M'; o[1] = (byte)'C'; o[2] = (byte)'O'; o[3] = (byte)'Z';
			Array.Copy(BitConverter.GetBytes((uint)enc), 0, o, 4, 4);
			Array.Copy(BitConverter.GetBytes((uint)comp.Length), 0, o, 8, 4);
			Array.Copy(BitConverter.GetBytes((uint)n), 0, o, 12, 4);
			Array.Copy(plain, 0, o, 16, enc);
			return o;
		}

		static void Xtea(byte[] d, uint[] k)
		{
			const uint delta = 0x9E3779B9;
			for (int i = 0; i + 8 <= d.Length; i += 8)
			{
				uint y = BitConverter.ToUInt32(d, i), z = BitConverter.ToUInt32(d, i + 4), s = 0;
				for (int r = 0; r < 32; r++)
				{
					y += (((z << 4) ^ (z >> 5)) + z) ^ (s + k[s & 3]);
					s += delta;
					z += (((y << 4) ^ (y >> 5)) + y) ^ (s + k[(s >> 11) & 3]);
				}
				Array.Copy(BitConverter.GetBytes(y), 0, d, i, 4);
				Array.Copy(BitConverter.GetBytes(z), 0, d, i + 4, 4);
			}
		}

		// ------------------------------------------------------------------ serwer

		static string AskLinuxPort()
		{
			Console.WriteLine();
			Console.WriteLine("  Folder linux-port serwera (ten, w ktorym jest docker\\docker-compose.yml).");
			string p = Ask("  Sciezka > ").Trim().Trim('"').TrimEnd('\\');
			if (!File.Exists(Path.Combine(p, "docker\\docker-compose.yml"))) throw new Exception("W " + p + " nie ma docker\\docker-compose.yml.");
			return p;
		}

		static void InstallServer(string lp, HashSet<string> sel)
		{
			Clear();
			Title("Instalacja - SERWER: " + lp);
			Console.WriteLine();
			string sdir = Path.Combine(Pkg, "instalator\\serwer");
			SortedDictionary<string, Dictionary<string, string>> files = new SortedDictionary<string, Dictionary<string, string>>(StringComparer.Ordinal);
			foreach (string line in File.ReadAllLines(Path.Combine(Pkg, "instalator\\serwer.var")))
			{
				if (line.Trim() == "") continue;
				string[] p = line.Split('|');
				Dictionary<string, string> d;
				if (!files.TryGetValue(p[0], out d)) { d = new Dictionary<string, string>(); files[p[0]] = d; }
				d[p[1]] = p[2];
			}
			int changed = 0, same = 0, skipped = 0;
			foreach (KeyValuePair<string, Dictionary<string, string>> kv in files)
			{
				string rel = kv.Key.Replace('/', '\\');
				string dst = Path.Combine(lp, rel);
				HashSet<string> touching = new HashSet<string>();
				foreach (string k in kv.Value.Keys) if (k != "-") foreach (string m in k.Split(',')) touching.Add(m);
				List<string> sub = new List<string>();
				foreach (string m in touching) if (sel.Contains(m)) sub.Add(m);
				sub.Sort(StringComparer.Ordinal);
				string key = sub.Count == 0 ? "-" : string.Join(",", sub.ToArray());
				string tf;
				if (!kv.Value.TryGetValue(key, out tf)) continue;   // nowy plik moda, mod niewybrany: zostaje jak jest
				byte[] target = File.ReadAllBytes(Path.Combine(sdir, tf));
				byte[] cur = File.Exists(dst) ? File.ReadAllBytes(dst) : null;
				if (cur != null && SameText(cur, target))
				{
					same++;
					foreach (string m in sub) Done(m, "serwer");
					continue;
				}
				if (cur != null)
				{
					bool known = false;
					foreach (string f in kv.Value.Values)
						if (SameText(cur, File.ReadAllBytes(Path.Combine(sdir, f)))) { known = true; break; }
					if (!known)
					{
						Warn(rel + " ma zmiany spoza tych modow (Twoje wlasne?).");
						if (!Yes("         Nadpisac (stara wersja idzie do kopii zapasowej)? [t/N] > "))
						{
							skipped++;
							Say(ConsoleColor.Yellow, "  [POMINIETO] ", rel);
							foreach (string m in sub) Fail(m, "plik " + rel + " pominiety (Twoje zmiany) - wgraj go recznie z serwer\\linux-port w paczce");
							continue;
						}
					}
					Save(lp, rel);
				}
				Directory.CreateDirectory(Path.GetDirectoryName(dst));
				File.WriteAllBytes(dst, target);
				Ok(rel + (key == "-" ? "  (przywrocony bez modow)" : "  (mody " + key + ")"));
				foreach (string m in sub) Done(m, "serwer");
				changed++;
			}
			Console.WriteLine();
			Console.WriteLine(string.Format("  Pliki serwera: wgrane {0}, juz aktualne {1}, pominiete {2}.", changed, same, skipped));

			if (sel.Contains("05")) LocaleString(lp);
			if (sel.Contains("05"))
			{
				Console.WriteLine();
				if (Yes("  Dodac przedmiot 76009 do bazy teraz (docker, INSERT IGNORE)? [t/N] > "))
				{
					string db = Ask("  Nazwa kontenera bazy (Enter = metin2-db) > ");
					if (db == "") db = "metin2-db";
					string sql = Path.Combine(Pkg, "serwer\\wykrywacz\\wykrywacz_bossow.sql");
					if (Run("docker", "cp \"" + sql + "\" " + db + ":/tmp/wykrywacz_bossow.sql", lp) != 0
						|| Run("docker", "exec " + db + " sh -c \"mariadb -uroot -p\\\"$MARIADB_ROOT_PASSWORD\\\" < /tmp/wykrywacz_bossow.sql\"", lp) != 0)
						Warn("Nie udalo sie dodac 76009 do bazy - dodaj recznie serwer\\wykrywacz\\wykrywacz_bossow.sql.");
					else { Ok("Przedmiot 76009 jest w bazie."); Done("05", "76009 w bazie"); }
				}
			}
			if (sel.Contains("14"))
			{
				Console.WriteLine();
				Warn("14 (towarzysz): przed pierwszym startem zrob kopie tabel towarzysza:");
				Console.WriteLine("  mysqldump player playerbot_sidekick playerbot_sidekick_gift playerbot_sidekick_pin > sidekick_backup.sql");
				Console.WriteLine("  Migracja bazy robi sie sama przy starcie. Limity w docker\\.env: M2_SIDEKICK_MAX_ACTIVE=2, M2_SIDEKICK_ROSTER=4.");
			}
			if (sel.Contains("23"))
			{
				Console.WriteLine();
				Info("23 (rebalans botow): flagi i opis w serwer\\rebalans\\README_PL.md w paczce (reb_lock_break_days, m2_bot_craft_errand_off, m2_bot_rotation).");
			}
			if (sel.Contains("22"))
			{
				Console.WriteLine();
				Info("22 (panel): Edytor bazy danych > Drop > \"Zmiana masowa\"; ksiega z metinow na stronie \"Kupony SM, szarfy, Cor\".");
				Console.WriteLine("  Zmiany dropu i ksiegi dzialaja po \"Zastosuj\" w panelu.");
			}
			StringBuilder sb = new StringBuilder();
			sb.Append("mody=" + Joined(sel) + "\r\n");
			sb.Append("numeracja=2\r\n");
			sb.Append("data=" + DateTime.Now.ToString("yyyy-MM-dd HH:mm") + "\r\n");
			File.WriteAllText(Path.Combine(lp, ServerSave), sb.ToString(), Latin);
			if (Directory.Exists(Backup)) Ok("Kopia zapasowa: " + Backup);

			Console.WriteLine();
			if (Yes("  Przebudowac i uruchomic serwer teraz (docker compose up -d --build)? [t/N] > "))
			{
				int rc = Run("docker", "compose up -d --build", Path.Combine(lp, "docker"));
				if (rc == 0) Ok("Serwer przebudowany i uruchomiony.");
				else Say(ConsoleColor.Red, "  [BLAD] ", "docker compose zakonczyl sie bledem (" + rc + ") - pliki sa wgrane, przebuduj recznie.");
			}
			else Info("Przebudowa pominieta. Recznie: cd linux-port\\docker ; docker compose up -d --build");
		}

		static void LocaleString(string lp)
		{
			string ls = Path.Combine(lp, "docker\\game\\src\\serverfiles\\share\\locale\\poland\\locale_string.txt");
			string add = Path.Combine(Pkg, "serwer\\wykrywacz\\locale_string_dodatek.txt");
			if (!File.Exists(ls) || !File.Exists(add)) { Warn("locale_string.txt - dopisz recznie serwer\\wykrywacz\\locale_string_dodatek.txt."); return; }
			byte[] cur = File.ReadAllBytes(ls);
			if (Latin.GetString(cur).Contains("no bosses were detected")) { Ok("locale_string.txt: komunikat wykrywacza juz jest."); return; }
			Save(lp, "docker\\game\\src\\serverfiles\\share\\locale\\poland\\locale_string.txt");
			MemoryStream ms = new MemoryStream();
			ms.Write(cur, 0, cur.Length);
			if (cur.Length > 0 && cur[cur.Length - 1] != 10) { ms.WriteByte(13); ms.WriteByte(10); }
			ms.WriteByte(13); ms.WriteByte(10);
			byte[] a = File.ReadAllBytes(add);
			ms.Write(a, 0, a.Length);
			File.WriteAllBytes(ls, ms.ToArray());
			Ok("locale_string.txt: dopisano komunikat wykrywacza.");
		}

		// ------------------------------------------------------------------ pomocnicze

		static string Ask(string prompt)
		{
			Console.Write(prompt);
			string s = Console.ReadLine();
			return s == null ? "" : s.Trim();
		}

		static bool Yes(string prompt)
		{
			string a = Ask(prompt);
			return a.StartsWith("t", StringComparison.OrdinalIgnoreCase) || a.StartsWith("y", StringComparison.OrdinalIgnoreCase);
		}

		static void Save(string root, string rel)
		{
			string src = Path.Combine(root, rel);
			if (!File.Exists(src)) return;
			string dst = Path.Combine(Backup, rel);
			if (File.Exists(dst)) return;
			Directory.CreateDirectory(Path.GetDirectoryName(dst));
			File.Copy(src, dst, false);
		}

		static string Md5(string path)
		{
			using (MD5 md5 = MD5.Create())
			using (FileStream fs = File.OpenRead(path))
			{
				byte[] h = md5.ComputeHash(fs);
				StringBuilder sb = new StringBuilder();
				foreach (byte b in h) sb.Append(b.ToString("X2"));
				return sb.ToString();
			}
		}

		static byte[] Hex(string s)
		{
			byte[] b = new byte[s.Length / 2];
			for (int i = 0; i < b.Length; i++) b[i] = Convert.ToByte(s.Substring(i * 2, 2), 16);
			return b;
		}

		// porownanie plikow tekstowych bez \r (plik zapisany na Windowsie z CRLF to ten sam plik)
		static bool SameText(byte[] a, byte[] b)
		{
			int i = 0, j = 0;
			while (true)
			{
				while (i < a.Length && a[i] == 13) i++;
				while (j < b.Length && b[j] == 13) j++;
				if (i >= a.Length || j >= b.Length) return i >= a.Length && j >= b.Length;
				if (a[i] != b[j]) return false;
				i++; j++;
			}
		}

		static int Run(string exe, string args, string dir)
		{
			try
			{
				ProcessStartInfo psi = new ProcessStartInfo(exe, args);
				psi.UseShellExecute = false;
				psi.WorkingDirectory = dir;
				using (Process p = Process.Start(psi))
				{
					p.WaitForExit();
					return p.ExitCode;
				}
			}
			catch (Exception e)
			{
				Warn("Nie moge uruchomic " + exe + ": " + e.Message);
				return -1;
			}
		}
	}
}
