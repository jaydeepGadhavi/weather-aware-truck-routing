import React, { useState } from 'react';
import { Navigation, Clock, Scale, Compass, Play, Loader2, Sparkles } from 'lucide-react';

const PRESET_ROUTES = [
  { origin: 'Chicago, IL', dest: 'Dallas, TX', weight: 35000, label: 'Chicago → Dallas (35k lb)' },
  { origin: 'Atlanta, GA', dest: 'Denver, CO', weight: 42000, label: 'Atlanta → Denver (42k lb)' },
  { origin: 'Seattle, WA', dest: 'Los Angeles, CA', weight: 25000, label: 'Seattle → LA (25k lb)' },
];

export default function RouteForm({ onSubmit, loading }) {
  const [origin, setOrigin] = useState('Chicago, IL');
  const [destination, setDestination] = useState('Dallas, TX');
  const nowStr = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
  const [departureTime, setDepartureTime] = useState(nowStr);
  const [weight, setWeight] = useState(35000);
  const [interval, setInterval] = useState(25);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!origin.trim() || !destination.trim()) return;

    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      departure_time: new Date(departureTime).toISOString(),
      load_weight_lbs: Number(weight),
      sample_interval_miles: Number(interval),
    });
  };

  const handleApplyPreset = (preset) => {
    setOrigin(preset.origin);
    setDestination(preset.dest);
    setWeight(preset.weight);
  };

  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-white/10 rounded-2xl p-4 md:p-5 shadow-xl">
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
          <Navigation size={15} className="text-emerald-400" />
          <span>Route & Load Parameters</span>
        </div>
        <div className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
          <Sparkles size={12} />
          <span>Live Corridor</span>
        </div>
      </div>

      {/* Corridor Presets */}
      <div className="flex flex-wrap gap-1.5 mb-3.5">
        {PRESET_ROUTES.map((p, idx) => (
          <button
            key={idx}
            type="button"
            className="px-2.5 py-1 text-[11px] font-medium rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-all hover:text-white"
            onClick={() => handleApplyPreset(p)}
          >
            {p.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-3.5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              Origin
            </label>
            <input
              type="text"
              className="w-full bg-slate-950/80 border border-white/10 rounded-lg text-slate-100 px-3 py-2 text-sm focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition-all placeholder-slate-600"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g. Chicago, IL"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              Destination
            </label>
            <input
              type="text"
              className="w-full bg-slate-950/80 border border-white/10 rounded-lg text-slate-100 px-3 py-2 text-sm focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition-all placeholder-slate-600"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Dallas, TX"
              required
            />
          </div>
        </div>

        <div>
          <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 mb-1">
            <Clock size={13} className="text-slate-400" />
            Departure Date & Time
          </label>
          <input
            type="datetime-local"
            className="w-full bg-slate-950/80 border border-white/10 rounded-lg text-slate-100 px-3 py-2 text-sm focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition-all [color-scheme:dark]"
            value={departureTime}
            onChange={(e) => setDepartureTime(e.target.value)}
            required
          />
        </div>

        {/* Load Weight Section */}
        <div className="bg-slate-950/40 border border-white/5 rounded-xl p-3">
          <div className="flex items-center justify-between mb-1.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-400">
              <Scale size={13} className="text-slate-400" />
              Load Weight (lbs)
            </label>
            <span className="text-xs font-bold font-mono text-emerald-400">
              {Number(weight).toLocaleString()} lbs
            </span>
          </div>

          <input
            type="range"
            min="5000"
            max="80000"
            step="1000"
            className="w-full accent-emerald-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
          />

          <div className="flex gap-1.5 mt-2">
            <button
              type="button"
              className={`flex-1 py-1 px-2 text-[11px] rounded-md border transition-all ${
                weight === 20000
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-semibold'
                  : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => setWeight(20000)}
            >
              20k (Light)
            </button>
            <button
              type="button"
              className={`flex-1 py-1 px-2 text-[11px] rounded-md border transition-all ${
                weight === 35000
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-semibold'
                  : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => setWeight(35000)}
            >
              35k (&gt;30k rule)
            </button>
            <button
              type="button"
              className={`flex-1 py-1 px-2 text-[11px] rounded-md border transition-all ${
                weight === 45000
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-semibold'
                  : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => setWeight(45000)}
            >
              45k (&gt;40k rule)
            </button>
          </div>
        </div>

        {/* Sampling Interval */}
        <div>
          <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 mb-1.5">
            <Compass size={13} className="text-slate-400" />
            Weather Checkpoint Interval
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[10, 25, 50].map((val) => (
              <button
                key={val}
                type="button"
                className={`py-1.5 text-xs rounded-lg border font-medium transition-all ${
                  interval === val
                    ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300 font-bold shadow-sm'
                    : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setInterval(val)}
              >
                Every {val} mi
              </button>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="w-full py-2.5 px-4 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={17} />
              <span className="text-xs font-semibold">Evaluating Weather & Routes...</span>
            </>
          ) : (
            <>
              <Play size={16} className="fill-slate-950" />
              <span className="text-xs tracking-wide uppercase font-extrabold">Analyze 3 Routes</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
