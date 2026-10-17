import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default Leaflet icon paths
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const RISK_COLORS = {
  'Low': '#10b981',        // Emerald Green
  'Moderate': '#f59e0b',   // Amber Yellow
  'High': '#f97316',       // Orange
  'Severe': '#ef4444',     // Crimson Red
  'No Travel': '#8b5cf6',  // Deep Purple
};

export default function MapViewer({
  routes = [],
  selectedRouteId,
  onSelectRoute,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const routeLayersRef = useRef([]);
  const checkpointLayersRef = useRef([]);
  const lastFittedRouteRef = useRef(null);

  // Initialize Map with proper zoom bounds
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [39.8283, -98.5795],
        zoom: 5,
        minZoom: 4,      // 🛑 Prevents zooming out into the whole universe
        maxZoom: 18,     // Allows deep street-level zooming
        zoomControl: false,
      });

      L.control.zoom({ position: 'topright' }).addTo(map);

      // Colorful OpenStreetMap with noWrap to prevent world repetition
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
        noWrap: true,   // 🛑 Prevents repeated horizontal worlds
      }).addTo(map);

      mapInstanceRef.current = map;

      // Force map to fill 100% of container smoothly without gray empty bars
      setTimeout(() => {
        map.invalidateSize();
      }, 200);

      const resizeObserver = new ResizeObserver(() => {
        map.invalidateSize();
      });
      resizeObserver.observe(mapContainerRef.current);

      return () => {
        resizeObserver.disconnect();
      };
    }
  }, []);

  // Render Routes and Checkpoints
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !routes || routes.length === 0) return;

    // Clear previous layers
    routeLayersRef.current.forEach((layer) => map.removeLayer(layer));
    routeLayersRef.current = [];

    checkpointLayersRef.current.forEach((layer) => map.removeLayer(layer));
    checkpointLayersRef.current = [];

    const allLatLngs = [];

    routes.forEach((route) => {
      const isSelected = route.id === selectedRouteId;
      const isRec = route.is_recommended;
      const coords = route.geometry?.coordinates || [];

      const latLngs = coords.map(([lon, lat]) => [lat, lon]);
      if (latLngs.length === 0) return;

      if (isSelected) {
        latLngs.forEach((pt) => allLatLngs.push(pt));
      }

      // 1. Outer contrast border (so line never disappears when zooming in over streets!)
      const outline = L.polyline(latLngs, {
        color: isSelected ? '#0f172a' : '#475569',
        weight: isSelected ? 8 : 4,
        opacity: isSelected ? 0.8 : 0.3,
      }).addTo(map);

      // 2. Main colorful route line
      const polyline = L.polyline(latLngs, {
        color: isSelected
          ? isRec ? '#10b981' : '#3b82f6'
          : '#94a3b8',
        weight: isSelected ? 5 : 2.5,
        opacity: isSelected ? 1 : 0.6,
      }).addTo(map);

      const clickHandler = () => {
        if (onSelectRoute) onSelectRoute(route.id);
      };

      outline.on('click', clickHandler);
      polyline.on('click', clickHandler);

      routeLayersRef.current.push(outline, polyline);

      // Render Checkpoints along the active selected route
      if (isSelected && route.checkpoints) {
        route.checkpoints.forEach((cp, idx) => {
          const riskLevel = cp.risk?.overall_risk || 'Low';
          const color = RISK_COLORS[riskLevel] || '#10b981';

          const marker = L.circleMarker([cp.latitude, cp.longitude], {
            radius: riskLevel === 'No Travel' ? 9 : 7,
            fillColor: color,
            color: '#ffffff',
            weight: 2.5,
            opacity: 1,
            fillOpacity: 1,
            zIndexOffset: 1000, // Keeps markers always on top!
          }).addTo(map);

          const etaFormatted = new Date(cp.eta).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
          });

          const reasonsHtml = (cp.risk?.explanations || [])
            .map((r) => `<div style="background: rgba(245, 158, 11, 0.15); border-left: 3px solid #d97706; padding: 4px 8px; font-size: 11px; margin-top: 5px; border-radius: 4px; color: #92400e;">${r}</div>`)
            .join('');

          const popupContent = `
            <div style="min-width: 210px; font-family: system-ui, sans-serif; padding: 2px; color: #0f172a;">
              <div style="font-weight: 700; font-size: 13px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 6px;">
                Checkpoint #${idx + 1} (${cp.distance_from_origin_miles} mi)
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0;">
                <span style="color: #64748b;">ETA:</span>
                <strong>${etaFormatted}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0;">
                <span style="color: #64748b;">Risk Level:</span>
                <span style="color: ${color}; font-weight: 700; text-transform: uppercase;">${riskLevel}</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0;">
                <span style="color: #64748b;">Wind Speed:</span>
                <strong>${cp.weather?.wind_speed_mph || 0} mph</strong>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0;">
                <span style="color: #64748b;">Precipitation:</span>
                <strong>${cp.weather?.precipitation_in_hr || 0} in/hr</strong>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 10px; margin: 3px 0; color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 4px;">
                <span>Truck Cargo:</span>
                <strong>${Number(cp.risk?.load_weight_lbs || 0).toLocaleString()} lbs</strong>
              </div>
              ${reasonsHtml}
            </div>
          `;

          marker.bindPopup(popupContent);
          checkpointLayersRef.current.push(marker);
        });
      }
    });

    // Auto-fit to route only when the selected route actually changes
    const routeKey = `${selectedRouteId}_${routes.length}`;
    if (allLatLngs.length > 0 && lastFittedRouteRef.current !== routeKey) {
      map.fitBounds(L.latLngBounds(allLatLngs), { padding: [60, 60], maxZoom: 12 });
      lastFittedRouteRef.current = routeKey;
    }
  }, [routes, selectedRouteId, onSelectRoute]);

  return (
    <div className="relative w-full h-full flex-1 min-h-[450px]">
      <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: '100%' }} />
    </div>
  );
}
