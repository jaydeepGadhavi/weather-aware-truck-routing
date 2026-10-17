import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Flame } from 'lucide-react';

export default function TimelineSlider({
  currentHour,
  onChangeHour,
  maxHours = 48,
  timestamps = [],
}) {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let timer = null;
    if (isPlaying) {
      timer = setInterval(() => {
        onChangeHour((prev) => (prev >= maxHours - 1 ? 0 : prev + 1));
      }, 700);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, maxHours, onChangeHour]);

  const currentTimestamp =
    timestamps && timestamps[currentHour]
      ? new Date(timestamps[currentHour]).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
      : `Hour +${currentHour}`;

  return (
    // Fixed (z-[1000] forces it permanently above Leaflet):
    <div className="absolute bottom-4 md:bottom-6 left-1/2 -translate-x-1/2 w-[94%] max-w-3xl bg-slate-950/95 backdrop-blur-xl border border-white/20 rounded-2xl p-3 md:p-4 shadow-2xl z-[1000] flex flex-col gap-2.5">

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 font-semibold">
          <Flame size={15} className="text-orange-400" />
          <span className="text-white hidden sm:inline">Corridor Weather Forecast</span>
          <span className="text-emerald-400 font-mono font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            +{currentHour}h from departure
          </span>
        </div>

        <div className="text-[11px] md:text-xs text-slate-300 font-mono">
          {currentTimestamp}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setIsPlaying(!isPlaying)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-white text-xs font-semibold transition-all border border-white/10"
        >
          {isPlaying ? <Pause size={13} /> : <Play size={13} />}
          <span>{isPlaying ? 'Pause' : 'Animate'}</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setIsPlaying(false);
            onChangeHour(0);
          }}
          title="Reset to departure time"
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white text-xs font-semibold transition-all border border-white/5"
        >
          <RotateCcw size={12} />
          <span className="hidden sm:inline">Reset</span>
        </button>

        <input
          type="range"
          min="0"
          max={Math.max(1, maxHours - 1)}
          value={currentHour}
          onChange={(e) => {
            setIsPlaying(false);
            onChangeHour(Number(e.target.value));
          }}
          className="flex-1 accent-emerald-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
        />

        <span className="text-[11px] font-mono text-slate-400 shrink-0">
          48 hrs
        </span>
      </div>
    </div>
  );
}
