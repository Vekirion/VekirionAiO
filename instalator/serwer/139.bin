#ifndef __INC_METIN2_PLAYERBOT_REBALANCE_H__
#define __INC_METIN2_PLAYERBOT_REBALANCE_H__

// MT2009_PLUS_BOT_REBALANCE_V1: the owner's rebalance of 28 October 2026, read
// off a world where the bots did not get on ("boty strasznie wolno sie
// rozwijaja", the owner). What this fragment holds - the rest of the
// rebalance is small changes beside the rules they change, every one marked
// MT2009_PLUS_BOT_REBALANCE_V1:
//
//   * A1/A2, the locks: a main is never held under its farmer (the farmer's
//     hold and the link's gap over it), and a Grinder's lock is a break, not a
//     home - a bot held at it for reb_lock_break_days days (an event flag,
//     3 when unset, 100 and over switches it off) has it moved up
//     PLAYERBOT_REB_LOCK_STEP levels. 77% of the mains were held at 26 or 35
//     on 28 October and 122 farmers stood over their main.
//   * A3/B1, the crafting errand: a Rada Pustelnika (the read made certain),
//     a Zwoj Egzorcyzmu (the day's wait waved, only with the fast books off)
//     and a Zwoj Wojny (UP_TO_3TH_LEVEL: +0..+3 at 100%) are made at whichever
//     NPC's crafting window has a row for one - read at run time from the
//     quest's own crafting_data, so a world without the owner's rows #85002,
//     #85003, #1 and #4 simply has none. The item is known by what it does,
//     not by vnum. With no row, or no materials, the market (a share of the
//     purse); with neither, nothing - the book is read without and the anvil
//     takes the step as before. Event flag m2_bot_craft_errand_off stops it.
//     A helper row short of a material is fed: by a feeder row of any window
//     that makes it (a Pergamin out of the Zagadkowa Szkatulka 50033, should
//     the owner add one - the chest pass then keeps the boxes the row needs
//     shut), or for the Pergamin by Soon's book exchange (20023), with books
//     the bot has no use for only.
//   * C1, the deaths: the second death within PLAYERBOT_REB_RESTART_WINDOW_MS
//     on one ground stands the bot up at the map's restart point instead of
//     in the pack that killed it (the Monkey Dungeon's medal droppers died
//     339 times a day each), and a farmer that dies
//     PLAYERBOT_REB_STRUGGLE_DEATHS times in an hour keeps
//     PLAYERBOT_REB_STRUGGLE_KEEP_PCT of what it earns for its own gear.
//   * C2, the rotation's bench (playerbot_manager.cpp, ManageLifeSchedule).
//   * D2, the counters: five to eight edits of one line a day, and a keeper
//     short of yang asks near the bottom of what the line may ask.
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, last, after everything it borrows; the earlier fragments
// that call into it declare what they call.

#if defined(PLAYERBOT_ENGINE_MT2009)
#include "crafting_manager.h"
#endif

namespace
{
	// Defined further down playerbot_manager.cpp.
	int FindPlayerBotBookAffectCell(LPCHARACTER ch, DWORD affectType);
	bool PlayerBotHoldsReadableClassBook(LPCHARACTER ch);

	// ------------------------------------------------------------------ C2

	// When each identity last left the cohort for the bench (global time); one
	// that never did counts as the oldest of all.
	std::map<DWORD, long> s_mapPlayerBotRotationBenchedAt;

	// ------------------------------------------------------------------ A1/A2

	const char* const PLAYERBOT_REB_LOCK_LV_FLAG = "playerbot.reb_lock_lv";
	const char* const PLAYERBOT_REB_LOCK_AT_FLAG = "playerbot.reb_lock_at";
	const char* const PLAYERBOT_REB_LOCK_ADD_FLAG = "playerbot.reb_lock_add";
	const int PLAYERBOT_REB_LOCK_BREAK_DAYS_DEFAULT = 3;
	const int PLAYERBOT_REB_LOCK_STEP = 5;
	const int PLAYERBOT_REB_LOCK_ADD_MAX = 40;

	// The days a Grinder's lock holds before it moves; 0 is "never".
	int GetPlayerBotRebLockBreakDays()
	{
		const int v = quest::CQuestManager::instance().GetEventFlag("reb_lock_break_days");
		if (v <= 0)
			return PLAYERBOT_REB_LOCK_BREAK_DAYS_DEFAULT;
		return v >= 100 ? 0 : v;
	}

	// The lock ManagePlayerBotExpLock holds an ordinary bot at, after the
	// rebalance: never under its farmer (GetPlayerBotMainLockFloor), and for a
	// Grinder's lock the steps its breaks have earned. readOnly answers the
	// panel without moving anything.
	int AdjustPlayerBotRebalanceLock(LPCHARACTER ch, int lockLevel, bool persona, bool readOnly)
	{
		if (!ch || lockLevel <= 0)
			return lockLevel;
		int lock = std::max(lockLevel, GetPlayerBotMainLockFloor(ch->GetPlayerID()));
		// A spot farmer's lock is its ground's, held on purpose.
		if (!persona || IsPlayerBotFarmerPID(ch->GetPlayerID()))
			return lock;
		const int days = GetPlayerBotRebLockBreakDays();
		if (days <= 0)
			return lock;
		int add = std::max(0, std::min(PLAYERBOT_REB_LOCK_ADD_MAX, ch->GetQuestFlag(PLAYERBOT_REB_LOCK_ADD_FLAG)));
		lock += add;
		if (readOnly || (int)ch->GetLevel() < lock)
			return lock;
		// Held at it now: since when, and the step once the days are up.
		const int now = (int)get_global_time();
		const int seen = ch->GetQuestFlag(PLAYERBOT_REB_LOCK_LV_FLAG);
		const int since = ch->GetQuestFlag(PLAYERBOT_REB_LOCK_AT_FLAG);
		if (seen != lock || since <= 0)
		{
			ch->SetQuestFlag(PLAYERBOT_REB_LOCK_LV_FLAG, lock);
			ch->SetQuestFlag(PLAYERBOT_REB_LOCK_AT_FLAG, now);
			return lock;
		}
		if (now - since >= days * 86400 && add < PLAYERBOT_REB_LOCK_ADD_MAX)
		{
			add = std::min(PLAYERBOT_REB_LOCK_ADD_MAX, add + PLAYERBOT_REB_LOCK_STEP);
			ch->SetQuestFlag(PLAYERBOT_REB_LOCK_ADD_FLAG, add);
			ch->SetQuestFlag(PLAYERBOT_REB_LOCK_AT_FLAG, 0);
			sys_log(0, "PLAYERBOT_REBALANCE: lock break pid=%u name=%s level=%u lock=%d -> %d held_days=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), lock,
					lockLevel + add, (now - since) / 86400);
			lock = std::max(lockLevel, GetPlayerBotMainLockFloor(ch->GetPlayerID())) + add;
		}
		return lock;
	}

	// ------------------------------------------------------------------ C1

	const DWORD PLAYERBOT_REB_DEATH_HOUR_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_REB_RESTART_WINDOW_MS = 4 * 60 * 1000;
	const int PLAYERBOT_REB_STRUGGLE_DEATHS = 6;
	const int PLAYERBOT_REB_STRUGGLE_KEEP_PCT = 70;
	// The restart point closer than this is no way out of anything.
	const int PLAYERBOT_REB_RESTART_MIN_DISTANCE = 3000;

	struct TPlayerBotRebDeaths
	{
		std::deque<DWORD> at;
		long map;
		bool down;
		TPlayerBotRebDeaths() : map(0), down(false) {}
	};
	std::map<DWORD, TPlayerBotRebDeaths> s_mapPlayerBotRebDeaths;

	// Every tick, before the death pass: a fall is the tick its HP goes to
	// nothing. The deaths of the last hour on the map it fell on.
	void NotePlayerBotRebalanceLife(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return;
		TPlayerBotRebDeaths& d = s_mapPlayerBotRebDeaths[ch->GetPlayerID()];
		const bool down = ch->GetHP() <= 0 || ch->IsDead();
		if (down && !d.down)
		{
			if (d.map != ch->GetMapIndex())
			{
				d.at.clear();
				d.map = ch->GetMapIndex();
			}
			d.at.push_back(dwNow);
			if (d.at.size() > 64)
				d.at.pop_front();
		}
		d.down = down;
		while (!d.at.empty() && dwNow - d.at.front() > PLAYERBOT_REB_DEATH_HOUR_MS)
			d.at.pop_front();
	}

	int CountPlayerBotRecentDeaths(DWORD pid, DWORD dwNow, DWORD windowMs)
	{
		std::map<DWORD, TPlayerBotRebDeaths>::const_iterator it = s_mapPlayerBotRebDeaths.find(pid);
		if (it == s_mapPlayerBotRebDeaths.end())
			return 0;
		int n = 0;
		for (std::deque<DWORD>::const_reverse_iterator t = it->second.at.rbegin(); t != it->second.at.rend(); ++t)
		{
			if (dwNow - *t > windowMs)
				break;
			++n;
		}
		return n;
	}

	bool IsPlayerBotStruggling(DWORD pid)
	{
		return CountPlayerBotRecentDeaths(pid, get_dword_time(), PLAYERBOT_REB_DEATH_HOUR_MS) >= PLAYERBOT_REB_STRUGGLE_DEATHS;
	}

	// The share of its earnings a farmer keeps (ServePlayerBotFarmerPurse).
	int GetPlayerBotStrugglingKeepPct(DWORD pid, int keepPct)
	{
		return IsPlayerBotStruggling(pid) ? std::max(keepPct, PLAYERBOT_REB_STRUGGLE_KEEP_PCT) : keepPct;
	}

	// Called by HandleDeath the moment a bot stands up where it fell.
	void NotePlayerBotRebalanceRevived(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead())
			return;
		const DWORD pid = ch->GetPlayerID();
		const long map = ch->GetMapIndex();
		// Not where a ground of its own decides (the temples, Arezzo, a run, a
		// war, a village), nor beside a person.
		if (IsPlayerBotSidekickPID(pid) || IsPlayerBotOnDungeonRun(pid) || map >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ||
				IsPlayerBotVillageMap(map) || map == PLAYERBOT_MAP_OCHAO || ch->GetWarMap() != NULL ||
				IsPlayerBotArezzoHeldHere(ch) || (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())))
			return;
		if (CountPlayerBotRecentDeaths(pid, dwNow, PLAYERBOT_REB_RESTART_WINDOW_MS) < 2)
			return;
		PIXEL_POSITION pos;
		if (!SECTREE_MANAGER::instance().GetRecallPositionByEmpire(map, ch->GetEmpire(), pos))
			return;
		if (DISTANCE_APPROX(ch->GetX() - pos.x, ch->GetY() - pos.y) < PLAYERBOT_REB_RESTART_MIN_DISTANCE)
			return;
		const long fromX = ch->GetX(), fromY = ch->GetY();
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ClearPlayerBotRoute(state, true);
		ch->Stop();
		if (!ch->Show(map, pos.x, pos.y, 0))
			return;
		ch->Stop();
		ch->SendMovePacket(FUNC_MOVE, 0, pos.x, pos.y, 0, dwNow);
		// The recovery's step away from the death spot means nothing here.
		state.lDeathX = 0;
		state.lDeathY = 0;
		sys_log(0, "PLAYERBOT_REBALANCE: restart point pid=%u name=%s map=%ld from=(%ld,%ld) to=(%ld,%ld) deaths_4min=%d deaths_hour=%d",
				pid, ch->GetName(), map, fromX, fromY, (long)pos.x, (long)pos.y,
				CountPlayerBotRecentDeaths(pid, dwNow, PLAYERBOT_REB_RESTART_WINDOW_MS),
				CountPlayerBotRecentDeaths(pid, dwNow, PLAYERBOT_REB_DEATH_HOUR_MS));
	}

	// ------------------------------------------------------------------ D2

	// A keeper with less than this to spare asks near the bottom of what a line
	// may ask: the floor and this share of the way up from it.
	const long long PLAYERBOT_REB_NEEDY_SPARE = 1000000LL;
	const long long PLAYERBOT_REB_NEEDY_SHARE_PERCENT = 30;
	// Edits of one line a day: five, and up to three more by pid.
	const int PLAYERBOT_REB_LINE_EDITS_MIN = 5;
	const DWORD PLAYERBOT_REB_LINE_EDITS_SPREAD = 4;

	struct TPlayerBotLineEdits
	{
		int day;
		int count;
	};
	std::map<DWORD, TPlayerBotLineEdits> s_mapPlayerBotLineEdits;

	long long AdjustPlayerBotNeedyPrice(LPCHARACTER ch, long long price, long long floor)
	{
		if (!ch || price <= 0 || floor <= 0 || price <= floor)
			return price;
		const long long spare = (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch);
		if (spare >= PLAYERBOT_REB_NEEDY_SPARE)
			return price;
		return floor + (price - floor) * PLAYERBOT_REB_NEEDY_SHARE_PERCENT / 100;
	}

	int GetPlayerBotLineEditCap(DWORD pid)
	{
		return PLAYERBOT_REB_LINE_EDITS_MIN + (int)(PlayerBotNavHash(pid ^ 0x45444954U) % PLAYERBOT_REB_LINE_EDITS_SPREAD);
	}

	// A line under its floor is always mended; anything else within the day's
	// edits of the line.
	bool IsPlayerBotLineEditAllowed(DWORD pid, DWORD itemId, bool underFloor)
	{
		if (underFloor)
			return true;
		std::map<DWORD, TPlayerBotLineEdits>::const_iterator it = s_mapPlayerBotLineEdits.find(itemId);
		const int today = (int)(get_global_time() / 86400);
		if (it == s_mapPlayerBotLineEdits.end() || it->second.day != today)
			return true;
		return it->second.count < GetPlayerBotLineEditCap(pid);
	}

	void NotePlayerBotLineEdited(DWORD pid, DWORD itemId)
	{
		(void)pid;
		const int today = (int)(get_global_time() / 86400);
		if (s_mapPlayerBotLineEdits.size() > 400000)
			s_mapPlayerBotLineEdits.clear();
		TPlayerBotLineEdits& e = s_mapPlayerBotLineEdits[itemId];
		if (e.day != today)
		{
			e.day = today;
			e.count = 0;
		}
		++e.count;
	}

	// ------------------------------------------------------------------ A3/B1

	enum
	{
		PLAYERBOT_REB_HELPER_NONE = 0,
		PLAYERBOT_REB_HELPER_ADVICE,    // Rada Pustelnika: AFFECT_SKILL_BOOK_BONUS
		PLAYERBOT_REB_HELPER_EXORCISM,  // Zwoj Egzorcyzmu: AFFECT_SKILL_NO_BOOK_DELAY
		PLAYERBOT_REB_HELPER_WAR,       // Zwoj Wojny: UP_TO_3TH_LEVEL_SCROLL
		PLAYERBOT_REB_HELPER_COUNT
	};

	// How many a bot keeps in hand while it has the work for them, and the
	// share of its spare purse one line off a counter may take.
	const int PLAYERBOT_REB_HELPER_KEEP[PLAYERBOT_REB_HELPER_COUNT] = { 0, 2, 1, 3 };
	const int PLAYERBOT_REB_HELPER_PURSE_PERCENT[PLAYERBOT_REB_HELPER_COUNT] = { 0, 25, 10, 10 };
	// The vnums a market trip is asked about (the ledger counts by vnum); the
	// crafting rows' own products are added to these.
	const DWORD PLAYERBOT_REB_HELPER_VNUMS[] = { 71094, 39030, 71294, 71001, 39008, 71201, 72310, 25044, 71021 };
	// What a craft leaves in the purse over its price.
	const long long PLAYERBOT_REB_CRAFT_SPARE = 300000LL;
	const DWORD PLAYERBOT_REB_ERRAND_CHECK_MIN_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_REB_ERRAND_CHECK_MAX_MS = 9 * 60 * 1000;
	const DWORD PLAYERBOT_REB_ERRAND_VISIT_MS = 4 * 60 * 1000;
	const int PLAYERBOT_REB_ERRAND_CRAFTS = 4;
	const DWORD PLAYERBOT_REB_RECIPES_REFRESH_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_REB_MISSING_CACHE_MS = 30 * 1000;
	// The package's own book exchange (libs/crafting/item_exchange.lua,
	// SKILLBOOK_EXCHANGE, item_exchange_manage.quest): Soon takes any skill book
	// for a Pergamin, a thousand yang a book, every time. Not a crafting row,
	// so it is known here by its numbers; a world without the NPC or without a
	// recipe that wants a Pergamin never uses it. Only a book the bot has no
	// use for goes (IsPlayerBotUselessBook) - the owner's rule of 28 October.
	const DWORD PLAYERBOT_REB_BOOK_EXCHANGE_NPC = 20023;
	const DWORD PLAYERBOT_REB_BOOK_EXCHANGE_PRODUCT = 30366;
	const long long PLAYERBOT_REB_BOOK_EXCHANGE_FEE = 1000;

	int GetPlayerBotRebHelperKindOfProto(const TItemTable* p)
	{
		if (!p || p->bType != ITEM_USE)
			return PLAYERBOT_REB_HELPER_NONE;
#if defined(PLAYERBOT_ENGINE_MT2009)
		if (p->bSubType == USE_AFFECT && p->alValues[0] == AFFECT_SKILL_BOOK_BONUS)
			return PLAYERBOT_REB_HELPER_ADVICE;
		if (p->bSubType == USE_AFFECT && p->alValues[0] == AFFECT_SKILL_NO_BOOK_DELAY)
			return PLAYERBOT_REB_HELPER_EXORCISM;
		if (p->bSubType == USE_TUNING && p->alValues[0] == UP_TO_3TH_LEVEL_SCROLL)
			return PLAYERBOT_REB_HELPER_WAR;
#endif
		return PLAYERBOT_REB_HELPER_NONE;
	}

	int CountPlayerBotRebHelperUnits(LPCHARACTER ch, int kind)
	{
		int units = 0;
		for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && GetPlayerBotRebHelperKindOfProto(item->GetProto()) == kind)
				units += std::max<int>(1, (int)item->GetCount());
		}
		return units;
	}

	// A worn piece - or the weapon made ready for the hand (B4) - at +0..+3
	// that is to go further: what a War scroll is for.
	bool PlayerBotHasWarScrollWork(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		static const WORD cells[] = { WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD, WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR };
		for (size_t i = 0; i < sizeof(cells) / sizeof(cells[0]); ++i)
		{
			LPITEM item = ch->GetWear(cells[i]);
			if (item && item->GetRefinedVnum() != 0 && item->GetRefineLevel() < 4 && !IsPlayerBotScrollFreeGear(item) &&
					item->GetRefineLevel() < GetPlayerBotRefineTarget(ch, item))
				return true;
		}
		LPITEM project = FindPlayerBotFutureProject(ch, WEAR_WEAPON);
		return project && project->GetRefinedVnum() != 0 && project->GetRefineLevel() < 4 &&
				project->GetRefineLevel() < GetPlayerBotRefineTarget(ch, project);
	}

	int GetPlayerBotRebHelperWant(LPCHARACTER ch, int kind)
	{
		if (!ch || !ch->IsItemLoaded() || IsPlayerBotSidekickPID(ch->GetPlayerID()) || IsPlayerBotShouterPID(ch->GetPlayerID()))
			return 0;
		switch (kind)
		{
			case PLAYERBOT_REB_HELPER_ADVICE:
				return ch->GetSkillGroup() != 0 && PlayerBotHoldsReadableClassBook(ch) ? PLAYERBOT_REB_HELPER_KEEP[kind] : 0;
			case PLAYERBOT_REB_HELPER_EXORCISM:
				return !IsPlayerBotFastBooksEnabled() && ch->GetSkillGroup() != 0 && PlayerBotHoldsReadableClassBook(ch)
						? PLAYERBOT_REB_HELPER_KEEP[kind] : 0;
			case PLAYERBOT_REB_HELPER_WAR:
				return PlayerBotHasWarScrollWork(ch) ? PLAYERBOT_REB_HELPER_KEEP[kind] : 0;
			default:
				return 0;
		}
	}

	// A skill book this bot has no use for: another class's or build's, one of
	// a skill past Master, or one over what it keeps of its skill (counted in
	// bag order, the way the merchant and the counter count them). The only
	// books Soon's exchange may take.
	bool IsPlayerBotUselessBook(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetType() != ITEM_SKILLBOOK || item->GetWindow() != INVENTORY ||
				item->isLocked() || item->IsEquipped() || item->IsExchanging() || IsPlayerBotSidekickHeld(ch, item))
			return false;
		const DWORD skill = GetPlayerBotSkillBookSkillVnum(item);
		if (skill == 0 || !IsPlayerBotOwnSkill(ch, skill))
			return true;
		const int keep = GetPlayerBotBookKeepLimit(ch, skill);
		if (keep <= 0)
			return true;
		int ahead = 0;
		for (WORD cell = 0; cell < item->GetCell() && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM held = ch->GetInventoryItem(cell);
			if (held && held != item && held->GetCell() == cell && held->GetType() == ITEM_SKILLBOOK &&
					GetPlayerBotSkillBookSkillVnum(held) == skill)
				++ahead;
		}
		return ahead >= keep;
	}

	int CountPlayerBotUselessBooks(LPCHARACTER ch)
	{
		int n = 0;
		for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && IsPlayerBotUselessBook(ch, item))
				++n;
		}
		return n;
	}

	// ---- the recipes, from the quest's crafting_data -------------------------

	struct TPlayerBotRebRecipe
	{
		DWORD row;
		DWORD window;
		DWORD npc;
		int kind;      // a helper's kind, or NONE for a feeder
		DWORD product; // the row's item
	};
	// The rows that make a helper, and the feeders: rows of any window that make
	// a material one of those rows takes (a Pergamin out of a Zagadkowa
	// Szkatulka, if the owner adds that row to Uriel's window).
	std::vector<TPlayerBotRebRecipe> s_vecPlayerBotRebRecipes;
	std::vector<TPlayerBotRebRecipe> s_vecPlayerBotRebFeeders;
	DWORD s_dwPlayerBotRebRecipesAt = 0;
	size_t s_uPlayerBotRebRecipesLogged = (size_t)-1;

	// The NPC that opens a crafting window: crafting_manage.quest and
	// acce_costume_uriel.quest of the package ("when <npc>.chat ...
	// crafting.open(<window>)"). A window whose NPC is not here is not used.
	DWORD GetPlayerBotCraftWindowNpc(DWORD window)
	{
		switch (window)
		{
			case 101: return 20016; // CRAFTING_BLACKSMITH, Kowal
			case 103: return 20008; // CRAFTING_CHEF
			case 104: return 20090; // CRAFTING_HALFDEMON
			case 108: return 20364; // CRAFTING_NAKAJIMA
			case 109: return 20001; // CRAFTING_ALCHEMIST_ORE, Alchemik
			case 110: return 20041; // CRAFTING_BUM
			case 111: return 20011; // CRAFTING_URIEL, Uriel
			default: return 0;
		}
	}

#if defined(PLAYERBOT_ENGINE_MT2009)
	bool IsPlayerBotRebHelperMaterial(DWORD vnum)
	{
		for (size_t i = 0; i < s_vecPlayerBotRebRecipes.size(); ++i)
		{
			const TCraftingItem* r = CCraftingManager::instance().GetCraftingRecipe(s_vecPlayerBotRebRecipes[i].row);
			for (int k = 0; r && k < CRAFTING_MATERIAL_MAX_NUM; ++k)
				if (r->materials[k].vnum == vnum && r->materials[k].count > 0)
					return true;
		}
		return false;
	}

	void RefreshPlayerBotRebRecipes(DWORD dwNow)
	{
		if (s_dwPlayerBotRebRecipesAt != 0 && dwNow - s_dwPlayerBotRebRecipesAt < PLAYERBOT_REB_RECIPES_REFRESH_MS)
			return;
		s_dwPlayerBotRebRecipesAt = dwNow != 0 ? dwNow : 1;
		s_vecPlayerBotRebRecipes.clear();
		s_vecPlayerBotRebFeeders.clear();
		lua_State* L = quest::CQuestManager::instance().GetLuaState();
		if (!L)
			return;
		std::vector<TPlayerBotRebRecipe> all;
		const int top = lua_gettop(L);
		lua_getglobal(L, "crafting_data");
		if (lua_istable(L, -1))
		{
			lua_pushnil(L);
			while (lua_next(L, -2) != 0)
			{
				// key at -2, the window's list at -1
				if (lua_type(L, -2) == LUA_TNUMBER && lua_istable(L, -1))
				{
					const DWORD window = (DWORD)lua_tonumber(L, -2);
					const DWORD npc = GetPlayerBotCraftWindowNpc(window);
					if (npc != 0)
					{
						lua_pushnil(L);
						while (lua_next(L, -2) != 0)
						{
							if (lua_type(L, -1) == LUA_TNUMBER)
							{
								const DWORD row = (DWORD)lua_tonumber(L, -1);
								const TCraftingItem* r = CCraftingManager::instance().GetCraftingRecipe(row);
								if (r && r->itemVnum != 0)
								{
									TPlayerBotRebRecipe rec = { row, window, npc,
											GetPlayerBotRebHelperKindOfProto(ITEM_MANAGER::instance().GetTable(r->itemVnum)),
											r->itemVnum };
									all.push_back(rec);
								}
							}
							lua_pop(L, 1);
						}
					}
				}
				lua_pop(L, 1);
			}
		}
		lua_settop(L, top);
		for (size_t i = 0; i < all.size(); ++i)
			if (all[i].kind != PLAYERBOT_REB_HELPER_NONE)
				s_vecPlayerBotRebRecipes.push_back(all[i]);
		for (size_t i = 0; i < all.size(); ++i)
			if (all[i].kind == PLAYERBOT_REB_HELPER_NONE && IsPlayerBotRebHelperMaterial(all[i].product))
				s_vecPlayerBotRebFeeders.push_back(all[i]);
		const size_t seen = s_vecPlayerBotRebRecipes.size() * 1000 + s_vecPlayerBotRebFeeders.size();
		if (s_uPlayerBotRebRecipesLogged != seen)
		{
			s_uPlayerBotRebRecipesLogged = seen;
			std::string rows;
			for (int pass = 0; pass < 2; ++pass)
			{
				const std::vector<TPlayerBotRebRecipe>& v = pass == 0 ? s_vecPlayerBotRebRecipes : s_vecPlayerBotRebFeeders;
				for (size_t i = 0; i < v.size(); ++i)
				{
					char one[64];
					snprintf(one, sizeof(one), "%s%s%u@%u>%u", rows.empty() ? "" : ",", pass ? "feed:" : "",
							v[i].row, v[i].npc, v[i].product);
					rows += one;
				}
			}
			sys_log(0, "PLAYERBOT_REBALANCE: crafting rows for the bots' helpers=%u feeders=%u [%s]",
					(unsigned int)s_vecPlayerBotRebRecipes.size(), (unsigned int)s_vecPlayerBotRebFeeders.size(), rows.c_str());
		}
	}

	long long GetPlayerBotRebRecipePrice(const TCraftingItem* r)
	{
		if (!r)
			return 0;
		// crafting_data.get_data: the row's price or the event flag's, the higher.
		char flag[48];
		snprintf(flag, sizeof(flag), "crafting_price%u", r->vnum);
		return std::max<long long>((long long)r->price, (long long)quest::CQuestManager::instance().GetEventFlag(flag));
	}

	// Everything crafting.create asks, minus the window: the level, the
	// knowledge, every material in the bag - none the worn gear's own next
	// step needs - and the price with the spare over it.
	bool CanPlayerBotMakeRebRecipe(LPCHARACTER ch, const TCraftingItem* r)
	{
		if (!ch || !r || r->itemVnum == 0 || (int)ch->GetLevel() < (int)r->reqLevel)
			return false;
		if (r->reqProgress > 0 && GetPlayerBotCraftProgress(ch, r->recipeVnum) < (int)r->reqProgress)
			return false;
		for (int i = 0; i < CRAFTING_MATERIAL_MAX_NUM; ++i)
		{
			const DWORD vnum = r->materials[i].vnum;
			const int need = (int)r->materials[i].count;
			if (vnum == 0 || need <= 0)
				continue;
			if ((int)ch->CountSpecifyItem(vnum) < need || PlayerBotNeedsRefineMaterial(ch, vnum))
				return false;
		}
		return (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) >=
				GetPlayerBotRebRecipePrice(r) + PLAYERBOT_REB_CRAFT_SPARE;
	}

	// The first recipe of a kind the bot is short of that it can make now, of
	// this NPC when npc is set; the Rada first, then the War scroll.
	const TPlayerBotRebRecipe* ChoosePlayerBotRebRecipe(LPCHARACTER ch, DWORD npc, int onlyKind = PLAYERBOT_REB_HELPER_NONE)
	{
		static const int order[] = { PLAYERBOT_REB_HELPER_ADVICE, PLAYERBOT_REB_HELPER_WAR, PLAYERBOT_REB_HELPER_EXORCISM };
		for (size_t k = 0; k < sizeof(order) / sizeof(order[0]); ++k)
		{
			const int kind = order[k];
			if (onlyKind != PLAYERBOT_REB_HELPER_NONE && kind != onlyKind)
				continue;
			if (CountPlayerBotRebHelperUnits(ch, kind) >= GetPlayerBotRebHelperWant(ch, kind))
				continue;
			for (size_t i = 0; i < s_vecPlayerBotRebRecipes.size(); ++i)
			{
				const TPlayerBotRebRecipe& rec = s_vecPlayerBotRebRecipes[i];
				if (rec.kind != kind || (npc != 0 && rec.npc != npc))
					continue;
				if (CanPlayerBotMakeRebRecipe(ch, CCraftingManager::instance().GetCraftingRecipe(rec.row)))
					return &rec;
			}
		}
		return NULL;
	}
#endif

	// ---- what the bot is short of, cached a little ---------------------------

	struct TPlayerBotRebMissing
	{
		DWORD at;
		int missing[PLAYERBOT_REB_HELPER_COUNT];
		bool craftable[PLAYERBOT_REB_HELPER_COUNT];
		// The materials of the first row of each kind it is short of and cannot
		// make yet, and how many units short: what a feeder row or Soon's
		// exchange is for.
		std::map<DWORD, int> shortOf;
		TPlayerBotRebMissing() : at(0)
		{
			for (int i = 0; i < PLAYERBOT_REB_HELPER_COUNT; ++i)
			{
				missing[i] = 0;
				craftable[i] = false;
			}
		}
	};
	std::map<DWORD, TPlayerBotRebMissing> s_mapPlayerBotRebMissing;

	const TPlayerBotRebMissing& GetPlayerBotRebMissing(LPCHARACTER ch)
	{
		static const TPlayerBotRebMissing none;
		if (!ch)
			return none;
		const DWORD now = get_dword_time();
		TPlayerBotRebMissing& m = s_mapPlayerBotRebMissing[ch->GetPlayerID()];
		if (m.at != 0 && now - m.at < PLAYERBOT_REB_MISSING_CACHE_MS)
			return m;
		// Stamped first: a rule asked from inside this one gets the old answer.
		m.at = now != 0 ? now : 1;
#if defined(PLAYERBOT_ENGINE_MT2009)
		RefreshPlayerBotRebRecipes(now);
#endif
		std::map<DWORD, int> shortOf;
		for (int kind = 0; kind < PLAYERBOT_REB_HELPER_COUNT; ++kind)
		{
			m.missing[kind] = 0;
			m.craftable[kind] = false;
			if (kind == PLAYERBOT_REB_HELPER_NONE)
				continue;
			m.missing[kind] = std::max(0, GetPlayerBotRebHelperWant(ch, kind) - CountPlayerBotRebHelperUnits(ch, kind));
#if defined(PLAYERBOT_ENGINE_MT2009)
			m.craftable[kind] = m.missing[kind] > 0 && ChoosePlayerBotRebRecipe(ch, 0, kind) != NULL;
			if (m.missing[kind] > 0 && !m.craftable[kind])
			{
				for (size_t i = 0; i < s_vecPlayerBotRebRecipes.size(); ++i)
				{
					if (s_vecPlayerBotRebRecipes[i].kind != kind)
						continue;
					const TCraftingItem* r = CCraftingManager::instance().GetCraftingRecipe(s_vecPlayerBotRebRecipes[i].row);
					for (int k = 0; r && k < CRAFTING_MATERIAL_MAX_NUM; ++k)
					{
						const DWORD vnum = r->materials[k].vnum;
						if (vnum == 0 || r->materials[k].count <= 0)
							continue;
						const int lack = (int)r->materials[k].count * m.missing[kind] - (int)ch->CountSpecifyItem(vnum);
						if (lack > 0)
							shortOf[vnum] = std::max(shortOf[vnum], lack);
					}
					break; // the first row of the kind
				}
			}
#endif
		}
		m.shortOf.swap(shortOf);
		return m;
	}

#if defined(PLAYERBOT_ENGINE_MT2009)
	// A feeder row the bot can make now for a material it is short of, at this
	// NPC when npc is set.
	const TPlayerBotRebRecipe* ChoosePlayerBotRebFeeder(LPCHARACTER ch, DWORD npc)
	{
		const TPlayerBotRebMissing& m = GetPlayerBotRebMissing(ch);
		for (size_t i = 0; i < s_vecPlayerBotRebFeeders.size(); ++i)
		{
			const TPlayerBotRebRecipe& rec = s_vecPlayerBotRebFeeders[i];
			if (npc != 0 && rec.npc != npc)
				continue;
			std::map<DWORD, int>::const_iterator lack = m.shortOf.find(rec.product);
			if (lack == m.shortOf.end() || lack->second <= 0)
				continue;
			if (CanPlayerBotMakeRebRecipe(ch, CCraftingManager::instance().GetCraftingRecipe(rec.row)))
				return &rec;
		}
		return NULL;
	}

	// Soon's exchange is worth a walk: a Pergamin short, a useless book in the
	// bag, and the fee.
	bool PlayerBotWantsBookExchange(LPCHARACTER ch)
	{
		const TPlayerBotRebMissing& m = GetPlayerBotRebMissing(ch);
		std::map<DWORD, int>::const_iterator lack = m.shortOf.find(PLAYERBOT_REB_BOOK_EXCHANGE_PRODUCT);
		return lack != m.shortOf.end() && lack->second > 0 && CountPlayerBotUselessBooks(ch) > 0 &&
				(long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) >= PLAYERBOT_REB_BOOK_EXCHANGE_FEE;
	}
#endif

	// ---- the hooks the earlier fragments call --------------------------------

	// The units of a crafting row's material the bag keeps while the row could
	// make what the bot is short of: a helper row's materials, and a feeder's
	// while its product is short (playerbot_workshop.h - the merchant and the
	// counter - and playerbot_consumables.h, whose chest pass leaves a box
	// shut while a feeder row takes it).
	int GetPlayerBotRebCraftMaterialKeep(LPCHARACTER ch, DWORD vnum)
	{
#if defined(PLAYERBOT_ENGINE_MT2009)
		if (!ch || vnum == 0 || s_vecPlayerBotRebRecipes.empty())
			return 0;
		const TPlayerBotRebMissing& m = GetPlayerBotRebMissing(ch);
		int keep = 0;
		for (size_t i = 0; i < s_vecPlayerBotRebRecipes.size(); ++i)
		{
			const TPlayerBotRebRecipe& rec = s_vecPlayerBotRebRecipes[i];
			if (m.missing[rec.kind] <= 0)
				continue;
			const TCraftingItem* r = CCraftingManager::instance().GetCraftingRecipe(rec.row);
			for (int k = 0; r && k < CRAFTING_MATERIAL_MAX_NUM; ++k)
				if (r->materials[k].vnum == vnum)
					keep = std::max(keep, (int)r->materials[k].count * m.missing[rec.kind]);
		}
		for (size_t i = 0; i < s_vecPlayerBotRebFeeders.size(); ++i)
		{
			const TPlayerBotRebRecipe& rec = s_vecPlayerBotRebFeeders[i];
			std::map<DWORD, int>::const_iterator lack = m.shortOf.find(rec.product);
			if (lack == m.shortOf.end() || lack->second <= 0)
				continue;
			const TCraftingItem* r = CCraftingManager::instance().GetCraftingRecipe(rec.row);
			const int perCraft = r && r->count > 0 ? (int)r->count : 1;
			const int crafts = (lack->second + perCraft - 1) / perCraft;
			for (int k = 0; r && k < CRAFTING_MATERIAL_MAX_NUM; ++k)
				if (r->materials[k].vnum == vnum)
					keep = std::max(keep, (int)r->materials[k].count * crafts);
		}
		return keep;
#else
		(void)ch;
		(void)vnum;
		return 0;
#endif
	}

	// A line of a helper the bot is short of and could not make itself: the
	// market is the second source, after the crafting window.
	bool WantsPlayerBotRebHelperOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer)
			return false;
		const int kind = GetPlayerBotRebHelperKindOfProto(offer->GetProto());
		if (kind == PLAYERBOT_REB_HELPER_NONE)
			return false;
		const TPlayerBotRebMissing& m = GetPlayerBotRebMissing(ch);
		return m.missing[kind] > 0 && !m.craftable[kind] && (int)offer->GetCount() <= m.missing[kind];
	}

	bool CanPlayerBotPayForRebHelperOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
		if (!ch || !offer || price <= 0)
			return false;
		const int kind = GetPlayerBotRebHelperKindOfProto(offer->GetProto());
		const long long spare = (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return kind != PLAYERBOT_REB_HELPER_NONE && spare > 0 &&
				price <= spare * PLAYERBOT_REB_HELPER_PURSE_PERCENT[kind] / 100;
	}

	void CollectPlayerBotRebHelperMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		if (!ch)
			return;
		const TPlayerBotRebMissing& m = GetPlayerBotRebMissing(ch);
		for (size_t i = 0; i < sizeof(PLAYERBOT_REB_HELPER_VNUMS) / sizeof(PLAYERBOT_REB_HELPER_VNUMS[0]); ++i)
		{
			const int kind = GetPlayerBotRebHelperKindOfProto(ITEM_MANAGER::instance().GetTable(PLAYERBOT_REB_HELPER_VNUMS[i]));
			if (kind != PLAYERBOT_REB_HELPER_NONE && m.missing[kind] > 0 && !m.craftable[kind])
				missing[PLAYERBOT_REB_HELPER_VNUMS[i]] = std::max(missing[PLAYERBOT_REB_HELPER_VNUMS[i]], m.missing[kind]);
		}
#if defined(PLAYERBOT_ENGINE_MT2009)
		for (size_t i = 0; i < s_vecPlayerBotRebRecipes.size(); ++i)
		{
			const TPlayerBotRebRecipe& rec = s_vecPlayerBotRebRecipes[i];
			if (m.missing[rec.kind] > 0 && !m.craftable[rec.kind])
				missing[rec.product] = std::max(missing[rec.product], m.missing[rec.kind]);
		}
#endif
	}

	// ---- the errand ----------------------------------------------------------

	struct TPlayerBotRebErrand
	{
		BYTE phase;
		BYTE crafts;
		DWORD npc;
		long npcX;
		long npcY;
		DWORD nextCheck;
		DWORD nextAction;
		DWORD visitStart;
	};
	std::map<DWORD, TPlayerBotRebErrand> s_mapPlayerBotRebErrand;

	struct TPlayerBotRebStats
	{
		unsigned trips, visits, crafts, made, failed, exchanged;
	};
	TPlayerBotRebStats s_kPlayerBotRebStats = { 0, 0, 0, 0, 0, 0 };

	bool ArePlayerBotCraftErrandsOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_craft_errand_off") != 0;
	}

	// The NPC of a race on a map, the nearest to `near` when given.
	LPCHARACTER FindPlayerBotCraftNpc(long mapIndex, DWORD race, LPCHARACTER near)
	{
		CharacterVectorInteractor npcs;
		if (race == 0 || !CHARACTER_MANAGER::instance().GetCharactersByRaceNum(race, npcs))
			return NULL;
		LPCHARACTER best = NULL;
		long bestDistance = 0;
		for (CharacterVectorInteractor::iterator it = npcs.begin(); it != npcs.end(); ++it)
		{
			LPCHARACTER npc = *it;
			if (!npc || npc->GetMapIndex() != mapIndex || !npc->GetSectree())
				continue;
			const long distance = near ? DISTANCE_APPROX(near->GetX() - npc->GetX(), near->GetY() - npc->GetY()) : 0;
			if (!best || distance < bestDistance)
			{
				best = npc;
				bestDistance = distance;
			}
		}
		return best;
	}

	void EndPlayerBotCraftErrand(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotRebErrand& e, DWORD dwNow, const char* why)
	{
		if (e.phase != 0 && ch)
			sys_log(0, "PLAYERBOT_REBALANCE: craft errand over pid=%u name=%s why=%s steps=%d gold=%lld",
					ch->GetPlayerID(), ch->GetName(), why, (int)e.crafts, (long long)ch->GetGold());
		e.phase = 0;
		e.nextAction = 0;
		e.nextCheck = dwNow + number(PLAYERBOT_REB_ERRAND_CHECK_MIN_MS, PLAYERBOT_REB_ERRAND_CHECK_MAX_MS);
		ClearPlayerBotRoute(state, true);
	}

#if defined(PLAYERBOT_ENGINE_MT2009)
	// The craft itself, in crafting.create's order: materials out, gold out,
	// the roll, the product in. One unit at a time.
	bool CraftPlayerBotRebRecipe(LPCHARACTER ch, const TPlayerBotRebRecipe* rec)
	{
		const TCraftingItem* r = rec ? CCraftingManager::instance().GetCraftingRecipe(rec->row) : NULL;
		if (!ch || !r || !CanPlayerBotMakeRebRecipe(ch, r) || CountPlayerBotFreeInventoryCells(ch) < 1)
			return false;
		const long long price = GetPlayerBotRebRecipePrice(r);
		for (int i = 0; i < CRAFTING_MATERIAL_MAX_NUM; ++i)
		{
			if (r->materials[i].vnum == 0 || r->materials[i].count <= 0)
				continue;
			ch->RemoveSpecifyItem(r->materials[i].vnum, r->materials[i].count);
		}
		if (price > 0)
			PlayerBotChangeGold(ch, -price);
		const bool made = number(1, 100) <= r->chance;
		if (made)
			ch->AutoGiveItem(r->itemVnum, r->count);
		++s_kPlayerBotRebStats.crafts;
		if (made)
			++s_kPlayerBotRebStats.made;
		else
			++s_kPlayerBotRebStats.failed;
		s_mapPlayerBotRebMissing.erase(ch->GetPlayerID());
		sys_log(0, "PLAYERBOT_REBALANCE: craft pid=%u name=%s row=%u npc=%u item=%u kind=%d price=%lld %s",
				ch->GetPlayerID(), ch->GetName(), r->vnum, rec->npc, r->itemVnum, rec->kind, price,
				made ? "OK" : "FAILED");
		return true;
	}

	// One book into a Pergamin at Soon, as item_exchange.exchange does it: the
	// book out, the fee, the product in.
	bool ExchangePlayerBotUselessBook(LPCHARACTER ch)
	{
		if (!ch || CountPlayerBotFreeInventoryCells(ch) < 1 ||
				(long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) < PLAYERBOT_REB_BOOK_EXCHANGE_FEE)
			return false;
		const TPlayerBotRebMissing& m = GetPlayerBotRebMissing(ch);
		std::map<DWORD, int>::const_iterator lack = m.shortOf.find(PLAYERBOT_REB_BOOK_EXCHANGE_PRODUCT);
		if (lack == m.shortOf.end() || lack->second <= 0)
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotUselessBook(ch, item))
				continue;
			const DWORD skill = GetPlayerBotSkillBookSkillVnum(item);
			if (item->GetCount() > 1)
				item->SetCount(item->GetCount() - 1);
			else
				ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_BOOK_EXCHANGE");
			PlayerBotChangeGold(ch, -PLAYERBOT_REB_BOOK_EXCHANGE_FEE);
			ch->AutoGiveItem(PLAYERBOT_REB_BOOK_EXCHANGE_PRODUCT, 1);
			++s_kPlayerBotRebStats.exchanged;
			s_mapPlayerBotRebMissing.erase(ch->GetPlayerID());
			sys_log(0, "PLAYERBOT_REBALANCE: book exchange pid=%u name=%s skill=%u -> %u",
					ch->GetPlayerID(), ch->GetName(), skill, PLAYERBOT_REB_BOOK_EXCHANGE_PRODUCT);
			return true;
		}
		return false;
	}

	// The next step at this NPC: a helper, else a feeder, else - at Soon - a book.
	bool DoPlayerBotCraftErrandStep(LPCHARACTER ch, DWORD npc)
	{
		const TPlayerBotRebRecipe* pick = ChoosePlayerBotRebRecipe(ch, npc);
		if (!pick)
			pick = ChoosePlayerBotRebFeeder(ch, npc);
		if (pick)
			return CraftPlayerBotRebRecipe(ch, pick);
		return npc == PLAYERBOT_REB_BOOK_EXCHANGE_NPC && ExchangePlayerBotUselessBook(ch);
	}
#endif

	// The tick, beside the workshop (playerbot_manager.cpp): true while the
	// errand has the bot.
	bool ManagePlayerBotCraftErrand(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
#if defined(PLAYERBOT_ENGINE_MT2009)
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || ch->IsDead() || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				IsPlayerBotShouterPID(ch->GetPlayerID()))
			return false;
		TPlayerBotRebErrand& e = s_mapPlayerBotRebErrand[ch->GetPlayerID()];
		const bool otherErrand = state.bVisitingShop || state.bVisitingBiologist || state.bVisitingHerbalist ||
				state.bVisitingStable || state.bVisitingAlchemist || state.bVisitingUriel || state.bFishingSession ||
				state.bMarketTrip || state.bVisitingYonah;
		if (otherErrand || ArePlayerBotCraftErrandsOff() || (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) ||
				IsPlayerBotHeldForCompany(ch) || ch->GetMyShop() != NULL || ch->GetExchange() ||
				IsPlayerBotArezzoHeldHere(ch) || IsPlayerBotOnDungeonRun(ch->GetPlayerID()))
		{
			if (e.phase != 0)
				EndPlayerBotCraftErrand(ch, state, e, dwNow, "interrupted");
			return false;
		}
		if (e.phase == 0 && (int)(dwNow - e.nextCheck) < 0)
			return false;

		if (e.phase == 0)
		{
			e.nextCheck = dwNow + number(PLAYERBOT_REB_ERRAND_CHECK_MIN_MS, PLAYERBOT_REB_ERRAND_CHECK_MAX_MS);
			RefreshPlayerBotRebRecipes(dwNow);
			if (s_vecPlayerBotRebRecipes.empty())
				return false;
			// Where to: the helper's row, else the feeder's, else Soon for a
			// Pergamin a helper row lacks.
			DWORD npcRace = 0;
			const TPlayerBotRebRecipe* pick = ChoosePlayerBotRebRecipe(ch, 0);
			if (!pick)
				pick = ChoosePlayerBotRebFeeder(ch, 0);
			if (pick)
				npcRace = pick->npc;
			else if (PlayerBotWantsBookExchange(ch))
				npcRace = PLAYERBOT_REB_BOOK_EXCHANGE_NPC;
			if (npcRace == 0)
				return false;
			LPCHARACTER npc = FindPlayerBotCraftNpc(ch->GetMapIndex(), npcRace, ch);
			if (!npc)
			{
				// The first village of its kingdom, where every one of these NPCs
				// stands, by the road the other errands take - not from a fight.
				long homeMap = 0, homeX = 0, homeY = 0;
				if (ch->GetVictim() != NULL || state.dwTargetVID != 0)
				{
					e.nextCheck = dwNow + number(20000, 60000);
					return false;
				}
				if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, homeMap, homeX, homeY) ||
						!IsPlayerBotMapHostedHere(homeMap) || !FindPlayerBotCraftNpc(homeMap, npcRace, NULL))
					return false;
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				if (!TransitionPlayerBotMap(ch, state, homeMap, homeX, homeY, dwNow, "craft_errand"))
					return false;
				++s_kPlayerBotRebStats.trips;
				e.nextCheck = 0;
				return true;
			}
			e.phase = 1;
			e.crafts = 0;
			e.npc = npcRace;
			e.npcX = npc->GetX();
			e.npcY = npc->GetY();
			e.visitStart = dwNow;
			e.nextAction = 0;
			++s_kPlayerBotRebStats.visits;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_REBALANCE: craft errand pid=%u name=%s lv=%d npc=%u row=%u gold=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), npcRace, pick ? pick->row : 0U,
					(long long)ch->GetGold());
		}

		if (dwNow - e.visitStart > PLAYERBOT_REB_ERRAND_VISIT_MS)
		{
			EndPlayerBotCraftErrand(ch, state, e, dwNow, "timeout");
			return false;
		}
		SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		long approachX = 0, approachY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), e.npcX, e.npcY, 0x43524654U, approachX, approachY);
		if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > 650)
		{
			if (!MovePlayerBot(ch, approachX, approachY, dwNow, 20, true, true, false, true) && state.bStuckCounter >= 6)
			{
				EndPlayerBotCraftErrand(ch, state, e, dwNow, "route_failed");
				return false;
			}
			return true;
		}

		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (e.nextAction == 0)
		{
			e.nextAction = dwNow + number(3000, 6000);
			return true;
		}
		if ((int)(dwNow - e.nextAction) < 0)
			return true;
		if (e.crafts >= PLAYERBOT_REB_ERRAND_CRAFTS || !DoPlayerBotCraftErrandStep(ch, e.npc))
		{
			EndPlayerBotCraftErrand(ch, state, e, dwNow, "done");
			// Straight on to the next NPC when a step here made what the next
			// one takes (Soon's Pergamin for Uriel's Rada).
			if (e.crafts > 0)
				e.nextCheck = dwNow + 5000;
			return false;
		}
		++e.crafts;
		e.nextAction = dwNow + number(2500, 5000);
		return true;
#else
		(void)ch;
		(void)state;
		(void)dwNow;
		return false;
#endif
	}
}

#endif
