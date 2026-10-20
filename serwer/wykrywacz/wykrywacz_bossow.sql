-- BOSS_DETECTOR_V1: Wykrywacz Bossow (76009). Autor: Vekirion
-- A copy of the metin detector 27989 (same type/subtype USE_SPECIAL, flags, price
-- 3000 Yang, tradeable) under its own vnum and name. Idempotent (INSERT IGNORE):
-- safe to run again, an existing 76009 is never overwritten.
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`)
SELECT 76009,'Wykrywacz Bossow',_cp1250 X'57796B72797761637A20426F7373F377',`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`
FROM world.item_proto WHERE vnum = 27989;
