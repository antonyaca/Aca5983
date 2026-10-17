//+------------------------------------------------------------------+
//| Nasdaq3Strategies.mq5                                            |
//| Robot MT5 : pré-marché + Williams + ORB 30 min sur le Nasdaq.    |
//| Mêmes règles que l'indicateur TradingView nasdaq_3_strategies et |
//| que les backtests 2020-2026 du repo Aca5983.                     |
//|                                                                  |
//| Heure de New York (heure d'été gérée automatiquement) :          |
//| 1. Pré-marché : range 04:00-09:30. À 09:30, achat stop au haut + |
//|    vente stop au bas, stop = bord opposé. Le 1er déclenché annule|
//|    l'autre. Si l'ouverture est déjà au-delà : entrée au marché.  |
//|    Ordres supprimés à 15:00 s'ils n'ont pas été déclenchés.      |
//| 2. Williams : ouverture 09:30 ± k × amplitude de la séance       |
//|    précédente (09:30-16:00). Stop = ouverture. Le 1er déclenché  |
//|    annule l'autre. Entrées possibles jusqu'à la clôture.         |
//| 3. ORB 30 min, achats seuls : range 09:30-10:00. À 10:00, achat  |
//|    stop au haut, stop loss au bas. Annulé si le bas casse        |
//|    d'abord. Ordre supprimé à 15:00.                              |
//| Toutes : pas de take profit, clôture forcée avant 16:00 NY.      |
//| Un seul trade par stratégie et par jour.                         |
//| À poser sur un graphique M1 du Nasdaq (US100, NAS100...).        |
//+------------------------------------------------------------------+
#property copyright "Antony Cauche — repo Aca5983"
#property version   "1.00"
#property description "Pré-marché + Williams + ORB 30 min — Nasdaq, heure de New York"

#include <Trade\Trade.mqh>

input double RiskPerTrade      = 100.0; // Risque par trade (devise du compte, ex. €)
input double WilliamsK         = 0.5;   // Williams : k
input bool   UsePremarket      = true;  // Activer le pré-marché
input bool   UseWilliams       = true;  // Activer Williams
input bool   UseORB            = true;  // Activer l'ORB 30 min (achats seuls)
input long   MagicBase         = 598300;// Numéro magique de base (+1, +2, +3 par stratégie)
input int    CloseHourNY       = 15;    // Heure de clôture forcée (New York)
input int    CloseMinuteNY     = 59;    // Minute de clôture forcée (New York)
input int    ServerMinusNYHours = 0;    // 0 = automatique. Testeur : écart fixe serveur - New York (souvent 7)
input int    SlippagePoints    = 50;    // Glissement max accepté (points) sur les ordres au marché

#define LEG_PRE 1
#define LEG_W   2
#define LEG_ORB 3

CTrade trade;

//--------------------------------------------------------------------
// Heure de New York
//--------------------------------------------------------------------
datetime NthSunday(int year, int mon, int n)
{
   MqlDateTime d;
   ZeroMemory(d);
   d.year = year; d.mon = mon; d.day = 1;
   datetime t = StructToTime(d);
   TimeToStruct(t, d);
   int first = (7 - d.day_of_week) % 7;
   return t + (datetime)((first + 7 * (n - 1)) * 86400);
}

bool IsUSDst(datetime utc)
{
   MqlDateTime t;
   TimeToStruct(utc, t);
   datetime start = NthSunday(t.year, 3, 2) + 7 * 3600;  // 2:00 heure d'hiver NY = 07:00 UTC
   datetime end   = NthSunday(t.year, 11, 1) + 6 * 3600; // 2:00 heure d'été NY = 06:00 UTC
   return (utc >= start && utc < end);
}

int NYOffsetSec(datetime utc) { return IsUSDst(utc) ? -4 * 3600 : -5 * 3600; }

int ServerOffsetSec()
{
   long s = (long)TimeTradeServer() - (long)TimeGMT();
   return (int)(MathRound(s / 1800.0) * 1800);
}

datetime NowNY()
{
   if(ServerMinusNYHours != 0)
      return TimeTradeServer() - ServerMinusNYHours * 3600;
   datetime u = TimeGMT();
   return u + NYOffsetSec(u);
}

datetime NYToServer(datetime ny)
{
   if(ServerMinusNYHours != 0)
      return ny + ServerMinusNYHours * 3600;
   datetime utc = ny - NYOffsetSec(ny + 5 * 3600);
   return utc + ServerOffsetSec();
}

datetime NYMidnight(datetime ny) { return (datetime)((long)ny - (long)ny % 86400); }

//--------------------------------------------------------------------
// Données M1
//--------------------------------------------------------------------
// Plus haut / plus bas des bougies M1 dont l'ouverture est dans [nyFrom, nyTo[
int RangeHL(datetime nyFrom, datetime nyTo, double &hi, double &lo, double &firstOpen)
{
   MqlRates r[];
   datetime s = NYToServer(nyFrom);
   datetime e = NYToServer(nyTo) - 1;
   int n = CopyRates(_Symbol, PERIOD_M1, s, e, r);
   if(n <= 0) return 0;
   hi = r[0].high; lo = r[0].low; firstOpen = r[0].open;
   for(int i = 1; i < n; i++)
   {
      if(r[i].high > hi) hi = r[i].high;
      if(r[i].low  < lo) lo = r[i].low;
   }
   return n;
}

// Amplitude de la dernière séance complète avant aujourd'hui
bool PrevSessionRange(datetime nyMid, double &range)
{
   for(int d = 1; d <= 7; d++)
   {
      datetime day = nyMid - d * 86400;
      double h, l, o;
      int n = RangeHL(day + 570 * 60, day + 960 * 60, h, l, o);
      if(n >= 300) { range = h - l; return true; }
   }
   return false;
}

//--------------------------------------------------------------------
// Ordres, positions, historique
//--------------------------------------------------------------------
long Magic(int leg) { return MagicBase + leg; }

string LegName(int leg)
{
   if(leg == LEG_PRE) return "Pré-marché";
   if(leg == LEG_W)   return "Williams";
   return "ORB";
}

double NormPrice(double p)
{
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(ts > 0) p = MathRound(p / ts) * ts;
   return NormalizeDouble(p, _Digits);
}

double LotsFor(double dist)
{
   if(dist <= 0) return 0;
   double tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tv <= 0) tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tv <= 0 || ts <= 0) return 0;
   double lots = RiskPerTrade / (dist / ts * tv);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step > 0) lots = MathFloor(lots / step + 1e-9) * step;
   if(lots < vmin)
   {
      PrintFormat("Taille %.4f lot < minimum %.2f : trade ignoré pour ne pas dépasser le risque.", lots, vmin);
      return 0;
   }
   return MathMin(lots, vmax);
}

int CountPending(int leg)
{
   int c = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == Magic(leg)) c++;
   }
   return c;
}

bool HasPosition(int leg)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == Magic(leg)) return true;
   }
   return false;
}

// Une stratégie a-t-elle déjà agi aujourd'hui (ordre posé, exécuté ou annulé) ?
bool LegUsedToday(int leg, datetime nyMid)
{
   if(CountPending(leg) > 0 || HasPosition(leg)) return true;
   if(!HistorySelect(NYToServer(nyMid), TimeTradeServer() + 60)) return false;
   for(int i = HistoryOrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = HistoryOrderGetTicket(i);
      if(t == 0) continue;
      if(HistoryOrderGetString(t, ORDER_SYMBOL) == _Symbol && HistoryOrderGetInteger(t, ORDER_MAGIC) == Magic(leg)) return true;
   }
   return false;
}

// Une entrée a-t-elle été exécutée aujourd'hui pour cette stratégie ?
bool LegFilledToday(int leg, datetime nyMid)
{
   if(HasPosition(leg)) return true;
   if(!HistorySelect(NYToServer(nyMid), TimeTradeServer() + 60)) return false;
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong t = HistoryDealGetTicket(i);
      if(t == 0) continue;
      if(HistoryDealGetString(t, DEAL_SYMBOL) == _Symbol && HistoryDealGetInteger(t, DEAL_MAGIC) == Magic(leg)
         && HistoryDealGetInteger(t, DEAL_ENTRY) == DEAL_ENTRY_IN) return true;
   }
   return false;
}

void DeletePending(int leg, string why)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == Magic(leg))
      {
         if(trade.OrderDelete(t)) PrintFormat("[%s] ordre %I64u supprimé : %s", LegName(leg), t, why);
      }
   }
}

void ClosePositions(int leg)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == Magic(leg))
      {
         if(trade.PositionClose(t)) PrintFormat("[%s] position %I64u clôturée (fin de séance)", LegName(leg), t);
      }
   }
}

bool Ok(bool sent, int leg)
{
   uint rc = trade.ResultRetcode();
   if(sent && (rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_PLACED)) return true;
   PrintFormat("[%s] ordre refusé : %u %s", LegName(leg), rc, trade.ResultRetcodeDescription());
   return false;
}

// Pose un ordre stop ; passe au marché si le prix a déjà franchi le niveau
void PlaceEntry(int leg, int dir, double level, double sl)
{
   trade.SetExpertMagicNumber(Magic(leg));
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double minDist = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
   level = NormPrice(level); sl = NormPrice(sl);
   string cmt = LegName(leg) + (dir > 0 ? " achat" : " vente");

   if(dir > 0)
   {
      if(ask >= level - minDist)
      {
         if(ask - sl <= minDist) { PrintFormat("[%s] achat ignoré : prix déjà sous le stop", LegName(leg)); return; }
         double lots = LotsFor(ask - sl);
         if(lots > 0 && Ok(trade.Buy(lots, _Symbol, 0, sl, 0, cmt), leg))
            PrintFormat("[%s] ACHAT au marché %.2f lot, stop %s", LegName(leg), lots, DoubleToString(sl, _Digits));
      }
      else
      {
         double lots = LotsFor(level - sl);
         if(lots > 0 && Ok(trade.BuyStop(lots, level, _Symbol, sl, 0, ORDER_TIME_GTC, 0, cmt), leg))
            PrintFormat("[%s] achat stop %s, stop %s, %.2f lot", LegName(leg), DoubleToString(level, _Digits), DoubleToString(sl, _Digits), lots);
      }
   }
   else
   {
      if(bid <= level + minDist)
      {
         if(sl - bid <= minDist) { PrintFormat("[%s] vente ignorée : prix déjà au-dessus du stop", LegName(leg)); return; }
         double lots = LotsFor(sl - bid);
         if(lots > 0 && Ok(trade.Sell(lots, _Symbol, 0, sl, 0, cmt), leg))
            PrintFormat("[%s] VENTE au marché %.2f lot, stop %s", LegName(leg), lots, DoubleToString(sl, _Digits));
      }
      else
      {
         double lots = LotsFor(sl - level);
         if(lots > 0 && Ok(trade.SellStop(lots, level, _Symbol, sl, 0, ORDER_TIME_GTC, 0, cmt), leg))
            PrintFormat("[%s] vente stop %s, stop %s, %.2f lot", LegName(leg), DoubleToString(level, _Digits), DoubleToString(sl, _Digits), lots);
      }
   }
}

//--------------------------------------------------------------------
// Logique journalière
//--------------------------------------------------------------------
string g_status = "";

void SetupOpen(datetime nyMid)
{
   double h, l, o;
   // Ouverture du jour : première bougie M1 de 09:30
   double dayOpen;
   if(RangeHL(nyMid + 570 * 60, nyMid + 571 * 60, h, l, dayOpen) <= 0)
      dayOpen = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   if(UsePremarket && !LegUsedToday(LEG_PRE, nyMid))
   {
      double pmH, pmL, x;
      int n = RangeHL(nyMid + 240 * 60, nyMid + 570 * 60, pmH, pmL, x);
      if(n < 100)
         PrintFormat("[Pré-marché] pas assez de cotations 04:00-09:30 (%d bougies) : pas de trade aujourd'hui", n);
      else if(dayOpen > pmH)      PlaceEntry(LEG_PRE, 1, pmH, pmL);
      else if(dayOpen < pmL) PlaceEntry(LEG_PRE, -1, pmL, pmH);
      else
      {
         PlaceEntry(LEG_PRE, 1, pmH, pmL);
         if(!HasPosition(LEG_PRE)) PlaceEntry(LEG_PRE, -1, pmL, pmH);
      }
      g_status += StringFormat("Pré-marché %s – %s\n", DoubleToString(pmL, _Digits), DoubleToString(pmH, _Digits));
   }

   if(UseWilliams && !LegUsedToday(LEG_W, nyMid))
   {
      double pr;
      if(!PrevSessionRange(nyMid, pr) || pr <= 0)
         Print("[Williams] séance précédente introuvable : pas de trade aujourd'hui");
      else
      {
         double up = dayOpen + WilliamsK * pr, dn = dayOpen - WilliamsK * pr;
         PlaceEntry(LEG_W, 1, up, dayOpen);
         if(!HasPosition(LEG_W)) PlaceEntry(LEG_W, -1, dn, dayOpen);
         g_status += StringFormat("Williams %s / %s, stop %s\n", DoubleToString(dn, _Digits), DoubleToString(up, _Digits), DoubleToString(dayOpen, _Digits));
      }
   }
}

void SetupORB(datetime nyMid)
{
   if(!UseORB || LegUsedToday(LEG_ORB, nyMid)) return;
   double h, l, o;
   int n = RangeHL(nyMid + 570 * 60, nyMid + 600 * 60, h, l, o);
   if(n < 20) { PrintFormat("[ORB] range 09:30-10:00 incomplet (%d bougies) : pas de trade", n); return; }
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(bid < l) { Print("[ORB] le bas du range est déjà cassé : pas de trade"); return; }
   PlaceEntry(LEG_ORB, 1, h, l);
   g_status += StringFormat("ORB achat stop %s, stop %s\n", DoubleToString(h, _Digits), DoubleToString(l, _Digits));
}

void Process()
{
   datetime ny = NowNY();
   MqlDateTime t;
   TimeToStruct(ny, t);
   if(t.day_of_week == 0 || t.day_of_week == 6) return;
   datetime nyMid = NYMidnight(ny);
   int m = t.hour * 60 + t.min;
   int closeM = CloseHourNY * 60 + CloseMinuteNY;

   static datetime lastDay = 0;
   if(nyMid != lastDay) { lastDay = nyMid; g_status = ""; }

   // 09:30-09:40 : pré-marché et Williams
   if(m >= 570 && m < 580) SetupOpen(nyMid);
   // 10:00-10:10 : ORB
   if(m >= 600 && m < 610) SetupORB(nyMid);

   // Ordres liés (OCO) : une entrée exécutée annule l'ordre opposé
   if(m >= 570 && m < closeM)
   {
      if(CountPending(LEG_PRE) > 0 && LegFilledToday(LEG_PRE, nyMid)) DeletePending(LEG_PRE, "l'autre côté a été déclenché");
      if(CountPending(LEG_W)   > 0 && LegFilledToday(LEG_W, nyMid))   DeletePending(LEG_W, "l'autre côté a été déclenché");
   }

   // ORB annulé si le bas casse avant le haut
   if(CountPending(LEG_ORB) > 0)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         ulong tk = OrderGetTicket(i);
         if(tk == 0) continue;
         if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == Magic(LEG_ORB)
            && bid < OrderGetDouble(ORDER_SL))
            DeletePending(LEG_ORB, "le bas du range a cassé en premier");
      }
   }

   // 15:00 : plus de nouvelles entrées pré-marché / ORB
   if(m >= 900)
   {
      if(CountPending(LEG_PRE) > 0) DeletePending(LEG_PRE, "15:00 NY, plus d'entrée");
      if(CountPending(LEG_ORB) > 0) DeletePending(LEG_ORB, "15:00 NY, plus d'entrée");
   }

   // Clôture forcée avant 16:00
   if(m >= closeM || m < 240)
   {
      for(int leg = LEG_PRE; leg <= LEG_ORB; leg++)
      {
         if(CountPending(leg) > 0) DeletePending(leg, "fin de séance");
         if(HasPosition(leg)) ClosePositions(leg);
      }
   }

   Comment("Nasdaq 3 stratégies — heure NY " + TimeToString(ny, TIME_MINUTES) + "\n" + g_status);
}

//--------------------------------------------------------------------
int OnInit()
{
   trade.SetDeviationInPoints(SlippagePoints);
   trade.SetTypeFillingBySymbol(_Symbol);
   if(_Period != PERIOD_M1) Print("Conseil : pose le robot sur un graphique M1.");
   PrintFormat("Nasdaq3Strategies démarré sur %s. Heure NY %s, heure serveur %s.", _Symbol,
               TimeToString(NowNY(), TIME_DATE | TIME_MINUTES), TimeToString(TimeTradeServer(), TIME_DATE | TIME_MINUTES));
   EventSetTimer(5);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) { EventKillTimer(); Comment(""); }
void OnTick()  { Process(); }
void OnTimer() { Process(); }
//+------------------------------------------------------------------+
