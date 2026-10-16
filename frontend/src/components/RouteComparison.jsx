import React from 'react';
import { Award, ShieldAlert, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function RouteComparison({ routes, selectedRouteId, onSelectRoute }) {
  if (!routes || routes.length === 0) return null;

  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-white/10 rounded-2xl p-4 md:p-5 shadow-xl">
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
          <Award size={15} className="text-amber-400" />
          <span>Route Ranking & Assessment</span>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          {routes.length} Alternatives
        </span>
      </div>

      <div className="space-y-3">
        {routes.map((route) => {
          const isSelected = route.id === selectedRouteId;
          const isRec = route.is_recommended;
          const m = route.metrics || {};

          return (
            <div
              key={route.id}
              onClick={() => onSelectRoute(route.id)}
              className={`relative rounded-xl p-3.5 border transition-all cursor-pointer ${
                isSelected
                  ? isRec
                    ? 'bg-emerald-950/20 border-emerald-500 ring-2 ring-emerald-500/20 shadow-lg shadow-emerald-950/40'
                    : 'bg-blue-950/20 border-blue-500 ring-2 ring-blue-500/20 shadow-lg shadow-blue-950/40'
                  : 'bg-slate-950/40 border-white/5 hover:border-white/15 hover:bg-slate-950/60'
              }`}
            >
              {isRec && (
                <div className="absolute top-3 right-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full shadow-sm tracking-wider">
                  ★ Recommended
                </div>
              )}

              <div className="flex items-center gap-2 mb-1.5 pr-24">
                {isRec ? (
                  <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                ) : (
                  <span className="text-xs font-mono font-bold text-slate-400 shrink-0">
                    #{route.rank}
                  </span>
                )}
                <span className="text-xs md:text-sm font-bold text-white truncate">
                  {route.name}
                </span>
              </div>

              <p className="text-[11px] text-slate-400 mb-2.5 leading-snug">
                {route.recommendation_reason}
              </p>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-2 mb-2.5">
                <div className="bg-slate-950/60 rounded-lg p-2 border border-white/5 flex flex-col">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-tight">Duration</span>
                  <span className="text-xs font-bold font-mono text-white mt-0.5">
                    {route.duration_hours} hrs
                  </span>
                </div>

                <div className="bg-slate-950/60 rounded-lg p-2 border border-white/5 flex flex-col">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-tight">Distance</span>
                  <span className="text-xs font-bold font-mono text-slate-300 mt-0.5">
                    {route.distance_miles} mi
                  </span>
                </div>

                <div className="bg-slate-950/60 rounded-lg p-2 border border-white/5 flex flex-col">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-tight">Avg Risk</span>
                  <span
                    className={`text-xs font-bold font-mono mt-0.5 ${
                      m.average_risk_score > 3.0
                        ? 'text-rose-400'
                        : m.average_risk_score > 2.0
                        ? 'text-amber-400'
                        : 'text-emerald-400'
                    }`}
                  >
                    {m.average_risk_score} / 5.0
                  </span>
                </div>
              </div>

              {/* Hazard Miles Pills */}
              <div className="flex flex-wrap gap-1 text-[10px] font-semibold">
                {m.no_travel_miles > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-500/40">
                    <ShieldAlert size={10} /> {m.no_travel_miles} mi No Travel
                  </span>
                )}
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-500/40">
                  <AlertTriangle size={10} /> {m.severe_miles} mi Severe
                </span>
                <span className="px-2 py-0.5 rounded bg-orange-950/50 text-orange-300 border border-orange-500/30">
                  {m.high_miles} mi High
                </span>
                <span className="px-2 py-0.5 rounded bg-amber-950/50 text-amber-300 border border-amber-500/30">
                  {m.moderate_miles} mi Mod
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-500/20">
                  {m.low_miles} mi Calm
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
