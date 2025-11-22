//+------------------------------------------------------------------+
//|           9/15 EMA Crossover EA - M15, 3 Trades/Day             |
//+------------------------------------------------------------------+
#property strict
#include <Trade/Trade.mqh>

input double Lots               = 0.01;
input int    FastEMA            = 9;
input int    SlowEMA            = 15;
input int    MaxTradesPerDay    = 3;
input ulong  Magic              = 123456;

CTrade trade;

int fastHandle, slowHandle;

int todayCount = 0;
datetime lastDay = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   if(_Period != PERIOD_M15)
   {
      Print("Attach EA to M15 timeframe only!");
      return(INIT_FAILED);
   }

   fastHandle = iMA(_Symbol, PERIOD_M15, FastEMA, 0, MODE_EMA, PRICE_CLOSE);
   slowHandle = iMA(_Symbol, PERIOD_M15, SlowEMA, 0, MODE_EMA, PRICE_CLOSE);

   if(fastHandle == INVALID_HANDLE || slowHandle == INVALID_HANDLE)
   {
      Print("Failed to create EMA handles!");
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(Magic);

   return(INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(fastHandle != INVALID_HANDLE) IndicatorRelease(fastHandle);
   if(slowHandle != INVALID_HANDLE) IndicatorRelease(slowHandle);
}
//+------------------------------------------------------------------+
void OnTick()
{
   // Run only on new M15 candle
   static datetime lastBar = 0;
   datetime currentBar = iTime(_Symbol, PERIOD_M15, 0);
   if(currentBar == lastBar) return;
   lastBar = currentBar;

   // Reset daily counter
   datetime today = TimeCurrent() - (TimeCurrent() % 86400);
   if(today != lastDay)
   {
      todayCount = 0;
      lastDay = today;
   }

   // limit trades per day
   if(todayCount >= MaxTradesPerDay)
   {
      Print("Daily trade limit reached");
      return;
   }

   // If trade already running, skip
   if(PositionSelect(_Symbol))
   {
      Print("Trade already active, waiting...");
      return;
   }

   // Fetch EMA values
   double fast[2], slow[2];
   ArraySetAsSeries(fast, true);
   ArraySetAsSeries(slow, true);

   if(CopyBuffer(fastHandle, 0, 0, 2, fast) < 2) return;
   if(CopyBuffer(slowHandle, 0, 0, 2, slow) < 2) return;

   double fastCurr = fast[0];
   double fastPrev = fast[1];
   double slowCurr = slow[0];
   double slowPrev = slow[1];

   // Equity-based SL & TP
   double equity   = AccountInfoDouble(ACCOUNT_EQUITY);
   double SL_money = equity * 0.01;
   double TP_money = equity * 0.03;

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   int digits       = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   double sl_ticks = SL_money / (tickValue * Lots);
   double tp_ticks = TP_money / (tickValue * Lots);

   double sl_dist = sl_ticks * tickSize;
   double tp_dist = tp_ticks * tickSize;

   // ---------------- BUY SIGNAL ----------------
   if(fastPrev < slowPrev && fastCurr > slowCurr)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl = NormalizeDouble(ask - sl_dist, digits);
      double tp = NormalizeDouble(ask + tp_dist, digits);

      if(trade.Buy(Lots, _Symbol, ask, sl, tp))
      {
         todayCount++;
         Print("BUY placed. Total today:", todayCount);
      }
      return;
   }

   // ---------------- SELL SIGNAL ----------------
   if(fastPrev > slowPrev && fastCurr < slowCurr)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl = NormalizeDouble(bid + sl_dist, digits);
      double tp = NormalizeDouble(bid - tp_dist, digits);

      if(trade.Sell(Lots, _Symbol, bid, sl, tp))
      {
         todayCount++;
         Print("SELL placed. Total today:", todayCount);
      }
      return;
   }
}
//+------------------------------------------------------------------+ 
