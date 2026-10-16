import React, { useState, useEffect } from 'react';
import { Truck, ShieldCheck, Activity, AlertCircle, Layers, SlidersHorizontal, Map as MapIcon } from 'lucide-react';
import RouteForm from './components/RouteForm';
import RouteComparison from './components/RouteComparison';
import MapViewer from './components/MapViewer';
import TimelineSlider from './components/TimelineSlider';
import { analyzeRoutes } from './services/api';

export default function App() {
  const [routes, setRoutes] = useState([]);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [corridorHeatmap, setCorridorHeatmap] = useState(null);
  const [currentHour, setCurrentHour] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mobileTab, setMobileTab] = useState('controls'); // 'controls' or 'map' on mobile

  // Load initial demo analysis
  useEffect(() => {
    handleRunAnalysis({
      origin: 'Chicago, IL',
      destination: 'Dallas, TX',
      departure_time: new Date().toISOString(),
      load_weight_lbs: 35000,
      sample_interval_miles: 25,
    });
  }, []);

  const handleRunAnalysis = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeRoutes(payload);
      setRoutes(data.routes || []);
      setCorridorHeatmap(data.corridor_heatmap || null);
      setCurrentHour(0);

      if (data.routes && data.routes.length > 0) {
        setSelectedRouteId(data.routes[0].id);
      }
      // On mobile, switch to map view upon successful calculation
      if (window.innerWidth < 1024) {
        setMobileTab('map');
      }
    } catch (err) {
      console.error('Error analyzing routes:', err);
      setError(err.message || 'Failed to retrieve routes and weather data.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0b0f19]">
      {/* Top Navigation */}
      <header className="h-16 shrink-0 bg-slate-950/90 backdrop-blur-md border-b border-white/10 px-4 md:px-6 flex items-center justify-between z-30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-slate-950 shadow-lg shadow-emerald-500/20">
            <Truck size={22} className="stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base md:text-lg tracking-tight text-white">
                Spotter TruckRouter
              </span>
              <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full uppercase tracking-wider">
                Weather-Aware AI
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Route optimization with dynamic checkpoint weather & cargo weight escalation
            </p>
          </div>
        </div>

        {/* Right Nav Status Badges & Mobile View Switcher */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-1.5">
              <Activity size={15} className="text-emerald-400" />
              <span>OSRM & Open-Meteo</span>
            </div>
            <div className="flex items-center gap-1.5">
              <ShieldCheck size={15} className="text-blue-400" />
              <span>Load Safety Rules</span>
            </div>
          </div>

          {/* Mobile Tab Toggle */}
          <div className="flex lg:hidden bg-slate-900 border border-white/10 rounded-lg p-0.5">
            <button
              onClick={() => setMobileTab('controls')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                mobileTab === 'controls'
                  ? 'bg-emerald-500 text-slate-950'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <SlidersHorizontal size={14} /> Config
            </button>
            <button
              onClick={() => setMobileTab('map')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                mobileTab === 'map'
                  ? 'bg-emerald-500 text-slate-950'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <MapIcon size={14} /> Map
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar (Config & Comparison) */}
        <aside
          className={`w-full lg:w-[450px] shrink-0 bg-slate-900/95 lg:bg-slate-900/70 border-r border-white/10 flex flex-col overflow-y-auto z-20 transition-all ${
            mobileTab === 'controls' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          <div className="p-4 md:p-5 flex flex-col gap-4">
            {error && (
              <div className="bg-rose-950/50 border border-rose-500/40 rounded-xl p-3.5 text-rose-300 text-xs md:text-sm flex items-start gap-2.5">
                <AlertCircle size={18} className="text-rose-400 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <RouteForm onSubmit={handleRunAnalysis} loading={loading} />

            <RouteComparison
              routes={routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={(id) => {
                setSelectedRouteId(id);
                if (window.innerWidth < 1024) {
                  setMobileTab('map');
                }
              }}
            />
          </div>
        </aside>

        {/* Right Map Canvas & Timeline */}
        <main
          className={`flex-1 relative flex flex-col h-full w-full ${
            mobileTab === 'map' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          <MapViewer
            routes={routes}
            selectedRouteId={selectedRouteId}
            onSelectRoute={setSelectedRouteId}
            corridorHeatmap={corridorHeatmap}
            currentHour={currentHour}
          />

          {corridorHeatmap && corridorHeatmap.num_hours > 0 && (
            <TimelineSlider
              currentHour={currentHour}
              onChangeHour={setCurrentHour}
              maxHours={corridorHeatmap.num_hours}
              timestamps={corridorHeatmap.timestamps}
            />
          )}
        </main>
      </div>
    </div>
  );
}
