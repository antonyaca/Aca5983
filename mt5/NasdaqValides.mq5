//+------------------------------------------------------------------+
//| NasdaqValides.mq5                                                |
//| Les 3 stratégies Nasdaq validées sur 2011-2026 (dépôt Aca5983) :  |
//|  1. Williams « régulier » ACHAT SEULEMENT, si clôture de la veille |
//|     > SMA200 : achat stop à ouverture 09:30 NY + amplitude/2 de   |
//|     la séance précédente, stop = ouverture ; à +0,5 R on encaisse |
//|     50 % et le stop passe au prix d'entrée ; fermeture 15:59 NY.  |
//|  2. RSI2 : à 15:56 NY, si RSI(2) < 20 et prix > SMA200 → achat ;  |
//|     vente à 15:56 NY dès que le prix > SMA5.                      |
//|  3. 3 baisses : à 15:56 NY, si 3 clôtures en baisse → achat ;     |
//|     vente à 15:56 NY au 1er jour en hausse ou après 5 séances.    |
//| Taille : risque fixe en € (Williams : distance au stop ;          |
//| RSI2 / 3 baisses : 1 ATR14 journalier = le risque).               |
//| À tester d'abord dans le testeur (« Chaque tick basé sur des ticks|
//| réels » = vrais spreads du broker), puis en DÉMO.                 |
//+------------------------------------------------------------------+
#property copyright "Aca5983"
#property version   "1.00"
#include <Trade/Trade.mqh>

//--- paramètres
input double RiskPerTrade      = 100;   // Risque par trade (devise du compte)
input bool   UseWilliams       = true;  // Williams régulier (achat seulement)
input bool   UseRSI2           = true;  // RSI2 < 20
input bool   UseDown3          = true;  // 3 baisses
input double RSI2Threshold     = 20;    // Seuil RSI(2)
input double DailyMaxLoss      = 0;     // Perte max du jour (Williams) en devise, 0 = désactivé
input double DailyMaxGain      = 0;     // Gain max du jour (Williams) en devise, 0 = désactivé
input int    ServerMinusNYHours = 0;    // 0 = automatique. Testeur : écart fixe serveur - New York (souvent 7)
input long   MagicBase         = 598400;
input int    MaxSpreadPoints   = 0;     // Spread max accepté à l'entrée (en points), 0 = pas de limite

enum { LEG_W = 1, LEG_RSI = 2, LEG_D3 = 3 };
CTrade trade;
datetime g_lastWDay = 0, g_lastSwingDay = 0;
bool     g_halfDone = false;

//--------------------------------------------------------------------
// Heure de New York (heure d'été US gérée)
//--------------------------------------------------------------------
datetime NthSunday(int year, int month, int n)
{
   MqlDateTime t; t.year = year; t.mon = month; t.day = 1; t.hour = 0; t.min = 0; t.sec = 0;
   datetime d = StructToTime(t);
   TimeToStruct(d, t);
   int add = (7 - t.day_of_week) % 7;
   return d + (add + 7 * (n - 1)) * 86400;
}
bool IsUSDst(datetime utc)
{
   MqlDateTime t; TimeToStruct(utc, t);
   datetime start = NthSunday(t.year, 3, 2) + 7 * 3600;
   datetime end   = NthSunday(t.year, 11, 1) + 6 * 3600;
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
   if(ServerMinusNYHours != 0) return TimeTradeServer() - ServerMinusNYHours * 3600;
   datetime u = TimeGMT();
   return u + NYOffsetSec(u);
}
datetime NYToServer(datetime ny)
{
   if(ServerMinusNYHours != 0) return ny + ServerMinusNYHours * 3600;
   datetime utc = ny - NYOffsetSec(ny + 5 * 3600);
   return utc + ServerOffsetSec();
}
datetime NYMidnight(datetime ny) { return (datetime)((long)ny - (long)ny % 86400); }
int      NYMinute(datetime ny)   { return (int)(((long)ny % 86400) / 60); }

//--------------------------------------------------------------------
// Données
//--------------------------------------------------------------------
int RangeHL(datetime nyFrom, datetime nyTo, double &hi, double &lo, double &firstOpen)
{
   MqlRates r[];
   int n = CopyRates(_Symbol, PERIOD_M1, NYToServer(nyFrom), NYToServer(nyTo) - 1, r);
   if(n <= 0) return 0;
   hi = r[0].high; lo = r[0].low; firstOpen = r[0].open;
   for(int i = 1; i < n; i++) { hi = MathMax(hi, r[i].high); lo = MathMin(lo, r[i].low); }
   return n;
}
bool PrevSessionRange(datetime nyMid, double &range)
{
   for(int d = 1; d <= 7; d++)
   {
      datetime day = nyMid - d * 86400;
      double h, l, o;
      if(RangeHL(day + 570 * 60, day + 960 * 60, h, l, o) >= 300) { range = h - l; return true; }
   }
   return false;
}
// Clôtures journalières (D1 du broker) ; index 0 = aujourd'hui, remplacé par le prix actuel
bool DailyCloses(double &c[], int n)
{
   ArraySetAsSeries(c, true);
   if(CopyClose(_Symbol, PERIOD_D1, 0, n, c) < n) return false;
   c[0] = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   return true;
}
double SMA(const double &c[], int start, int len)
{
   double s = 0; for(int i = start; i < start + len; i++) s += c[i]; return s / len;
}
double RSIWilder(const double &c[], int period, int total)   // c en série (0 = plus récent)
{
   double up = 0, dn = 0; bool init = false;
   for(int i = total - 2; i >= 0; i--)
   {
      double d = c[i] - c[i + 1];
      double u = MathMax(d, 0), w = MathMax(-d, 0);
      if(!init) { up = u; dn = w; init = true; }
      else { up = (up * (period - 1) + u) / period; dn = (dn * (period - 1) + w) / period; }
   }
   if(dn == 0) return 100;
   return 100 - 100 / (1 + up / dn);
}
double ATR14()
{
   MqlRates r[]; ArraySetAsSeries(r, true);
   if(CopyRates(_Symbol, PERIOD_D1, 0, 16, r) < 16) return 0;
   double s = 0;
   for(int i = 0; i < 14; i++)
      s += MathMax(r[i].high, r[i + 1].close) - MathMin(r[i].low, r[i + 1].close);
   return s / 14;
}

//--------------------------------------------------------------------
// Ordres et positions
//--------------------------------------------------------------------
long Magic(int leg) { return MagicBase + leg; }
double NormPrice(double p)
{
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(ts > 0) p = MathRound(p / ts) * ts;
   return NormalizeDouble(p, _Digits);
}
double NormLots(double lots)
{
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step > 0) lots = MathFloor(lots / step + 1e-9) * step;
   return lots;
}
double LotsFor(double dist)
{
   if(dist <= 0) return 0;
   double tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tv <= 0) tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tv <= 0 || ts <= 0) return 0;
   double lots = NormLots(RiskPerTrade / (dist / ts * tv));
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(lots < vmin) { PrintFormat("Taille %.4f < minimum %.2f : trade ignoré (risque trop petit pour ce symbole).", lots, vmin); return 0; }
   return MathMin(lots, vmax);
}
bool SpreadOK()
{
   if(MaxSpreadPoints <= 0) return true;
   long sp = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(sp > MaxSpreadPoints) { PrintFormat("Spread %d points > maximum %d : pas d'entrée.", sp, MaxSpreadPoints); return false; }
   return true;
}
bool HasPosition(int leg, ulong &ticket)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(PositionSelectByTicket(t) && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == Magic(leg))
      { ticket = t; return true; }
   }
   return false;
}
int CountPending(int leg)
{
   int c = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(OrderSelect(t) && OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == Magic(leg)) c++;
   }
   return c;
}
void DeletePending(int leg)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(OrderSelect(t) && OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == Magic(leg)) trade.OrderDelete(t);
   }
}
void ClosePosition(int leg, string why)
{
   ulong t;
   while(HasPosition(leg, t)) { if(!trade.PositionClose(t)) break; PrintFormat("Fermeture %d : %s", leg, why); }
}
// Résultat du jour (NY) du Williams : historique fermé + flottant
double WilliamsDayPnL(datetime nyMid)
{
   double pnl = 0;
   if(HistorySelect(NYToServer(nyMid), TimeTradeServer() + 60))
      for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
      {
         ulong d = HistoryDealGetTicket(i);
         if(HistoryDealGetInteger(d, DEAL_MAGIC) == Magic(LEG_W) && HistoryDealGetString(d, DEAL_SYMBOL) == _Symbol)
            pnl += HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_COMMISSION) + HistoryDealGetDouble(d, DEAL_SWAP);
      }
   ulong t;
   if(HasPosition(LEG_W, t) && PositionSelectByTicket(t)) pnl += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
   return pnl;
}
// Date d'ouverture (NY) d'une position swing
int SessionsHeld(ulong ticket, datetime nyMid)
{
   if(!PositionSelectByTicket(ticket)) return 0;
   datetime openNY = (datetime)PositionGetInteger(POSITION_TIME) - (NYToServer(nyMid) - nyMid);
   int n = 0;
   for(datetime d = NYMidnight(openNY) + 86400; d <= nyMid; d += 86400)
   { MqlDateTime s; TimeToStruct(d, s); if(s.day_of_week != 0 && s.day_of_week != 6) n++; }
   return n;
}

//--------------------------------------------------------------------
// 1. Williams régulier, achat seulement
//--------------------------------------------------------------------
void Williams(datetime ny, datetime nyMid, int m)
{
   ulong t;
   bool limitHit = (DailyMaxLoss > 0 || DailyMaxGain > 0);
   if(limitHit)
   {
      double p = WilliamsDayPnL(nyMid);
      if((DailyMaxLoss > 0 && p <= -DailyMaxLoss) || (DailyMaxGain > 0 && p >= DailyMaxGain))
      {
         if(HasPosition(LEG_W, t) || CountPending(LEG_W) > 0) PrintFormat("Limite du jour atteinte (%.2f) : Williams arrêté.", p);
         DeletePending(LEG_W); ClosePosition(LEG_W, "limite du jour");
         return;
      }
   }
   // placement à 09:30 NY, une fois par jour
   if(m >= 570 && m < 600 && g_lastWDay != nyMid)
   {
      g_lastWDay = nyMid; g_halfDone = false;
      double c[]; if(!DailyCloses(c, 202)) { Print("Historique D1 insuffisant"); return; }
      if(!(c[1] > SMA(c, 1, 200))) { Print("Williams : clôture d'hier sous la SMA200 → pas de trade aujourd'hui."); return; }
      double range;
      if(!PrevSessionRange(nyMid, range)) { Print("Williams : séance précédente introuvable"); return; }
      double h, l, op;
      if(RangeHL(nyMid + 570 * 60, nyMid + 571 * 60, h, l, op) <= 0) { Print("Williams : ouverture 09:30 introuvable"); return; }
      double lvl = NormPrice(op + range / 2), sl = NormPrice(op);
      double lots = LotsFor(lvl - sl);
      if(lots <= 0) return;
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      trade.SetExpertMagicNumber(Magic(LEG_W));
      if(ask >= lvl) { if(SpreadOK()) trade.Buy(lots, _Symbol, 0, sl, 0, "Williams"); }     // niveau déjà dépassé
      else trade.BuyStop(lots, lvl, _Symbol, sl, 0, ORDER_TIME_GTC, 0, "Williams");
      PrintFormat("Williams : ouverture %.2f, amplitude veille %.2f, achat stop %.2f, stop %.2f, %.2f lot", op, range, lvl, sl, lots);
   }
   // gestion : 50 % à +0,5 R puis stop à l'entrée
   if(HasPosition(LEG_W, t) && PositionSelectByTicket(t))
   {
      double entry = PositionGetDouble(POSITION_PRICE_OPEN), sl = PositionGetDouble(POSITION_SL);
      double vol = PositionGetDouble(POSITION_VOLUME), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      if(!g_halfDone && sl < entry && bid >= entry + 0.5 * (entry - sl))
      {
         double half = NormLots(vol / 2);
         trade.SetExpertMagicNumber(Magic(LEG_W));
         if(half >= SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)) trade.PositionClosePartial(t, half);
         if(HasPosition(LEG_W, t)) trade.PositionModify(t, NormPrice(entry), 0);
         g_halfDone = true;
         Print("Williams : +0,5 R → moitié encaissée, stop au prix d'entrée");
      }
   }
   if(m >= 959) { DeletePending(LEG_W); ClosePosition(LEG_W, "15:59 NY"); }
}

//--------------------------------------------------------------------
// 2 et 3. RSI2 et 3 baisses (décision à 15:56 NY, une fois par jour)
//--------------------------------------------------------------------
void Swings(datetime nyMid, int m)
{
   if(m < 956 || m >= 960 || g_lastSwingDay == nyMid) return;
   g_lastSwingDay = nyMid;
   double c[]; if(!DailyCloses(c, 302)) { Print("Historique D1 insuffisant (300 jours requis)"); return; }
   double sma200 = SMA(c, 0, 200), sma5 = SMA(c, 0, 5), rsi = RSIWilder(c, 2, 300), atr = ATR14();
   ulong t;
   // sorties
   if(HasPosition(LEG_RSI, t) && c[0] > sma5) ClosePosition(LEG_RSI, "RSI2 : prix > SMA5");
   if(HasPosition(LEG_D3, t) && (c[0] > c[1] || SessionsHeld(t, nyMid) >= 5)) ClosePosition(LEG_D3, "3 baisses : jour en hausse ou 5 séances");
   // entrées
   if(atr <= 0) return;
   if(UseRSI2 && !HasPosition(LEG_RSI, t) && rsi < RSI2Threshold && c[0] > sma200 && SpreadOK())
   {
      double lots = LotsFor(atr);
      trade.SetExpertMagicNumber(Magic(LEG_RSI));
      if(lots > 0 && trade.Buy(lots, _Symbol, 0, 0, 0, "RSI2")) PrintFormat("RSI2 = %.1f < %.0f, prix > SMA200 → achat %.2f lot", rsi, RSI2Threshold, lots);
   }
   if(UseDown3 && !HasPosition(LEG_D3, t) && c[0] < c[1] && c[1] < c[2] && c[2] < c[3] && SpreadOK())
   {
      double lots = LotsFor(atr);
      trade.SetExpertMagicNumber(Magic(LEG_D3));
      if(lots > 0 && trade.Buy(lots, _Symbol, 0, 0, 0, "3 baisses")) PrintFormat("3 baisses → achat %.2f lot", lots);
   }
}

//--------------------------------------------------------------------
int OnInit()
{
   trade.SetDeviationInPoints(50);
   PrintFormat("NasdaqValides prêt. Heure NY actuelle : %s. Vérifie qu'elle est juste (sinon renseigne ServerMinusNYHours).",
               TimeToString(NowNY(), TIME_DATE | TIME_MINUTES));
   return INIT_SUCCEEDED;
}
void OnTick()
{
   datetime ny = NowNY(), nyMid = NYMidnight(ny);
   MqlDateTime s; TimeToStruct(ny, s);
   if(s.day_of_week == 0 || s.day_of_week == 6) return;
   int m = NYMinute(ny);
   if(UseWilliams) Williams(ny, nyMid, m);
   if(UseRSI2 || UseDown3) Swings(nyMid, m);
}
