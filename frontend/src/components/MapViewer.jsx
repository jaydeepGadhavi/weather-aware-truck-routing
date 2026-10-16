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
  'Low': '#10b981',
  'Moderate': '#f59e0b',
  'High': '#f97316',
  'Severe': '#ef4444',
  'No Travel': '#8b5cf6',
};

export default function MapViewer({
  routes = [],
  selectedRouteId,
  onSelectRoute,
  corridorHeatmap,
  currentHour = 0,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const routeLayersRef = useRef([]);
  const checkpointLayersRef = useRef([]);
  const heatmapLayerRef = useRef(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [39.8283, -98.5795], // Center of USA
        zoom: 4,
        zoomControl: false,
      });

      L.control.zoom({ position: 'topright' }).addTo(map);

      // Dark theme CartoDB basemap for high-contrast logistics view
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 19,
        subdomains: 'abcd',
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    return () => {
      // Cleanup on unmount
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Route Polylines and Checkpoint Pins
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !routes || routes.length === 0) return;

    // Clear previous route polylines
    routeLayersRef.current.forEach((layer) => map.removeLayer(layer));
    routeLayersRef.current = [];

    // Clear previous checkpoints
    checkpointLayersRef.current.forEach((layer) => map.removeLayer(layer));
    checkpointLayersRef.current = [];

    const allLatLngs = [];

    routes.forEach((route) => {
      const isSelected = route.id === selectedRouteId;
      const isRec = route.is_recommended;
      const coords = route.geometry?.coordinates || [];

      // GeoJSON has [lon, lat], Leaflet requires [lat, lon]
      const latLngs = coords.map(([lon, lat]) => [lat, lon]);
      if (latLngs.length === 0) return;

      latLngs.forEach((pt) => allLatLngs.push(pt));

      // Style line based on whether it is selected/recommended
      const polyline = L.polyline(latLngs, {
        color: isSelected
          ? isRec ? '#10b981' : '#3b82f6'
          : '#475569',
        weight: isSelected ? 6 : 3,
        opacity: isSelected ? 0.95 : 0.45,
        dashArray: isSelected ? null : '5, 8',
      }).addTo(map);

      polyline.on('click', () => {
        if (onSelectRoute) onSelectRoute(route.id);
      });

      routeLayersRef.current.push(polyline);

      // Render Checkpoint Markers along the selected route
      if (isSelected && route.checkpoints) {
        route.checkpoints.forEach((cp, idx) => {
          const riskLevel = cp.risk?.overall_risk || 'Low';
          const color = RISK_COLORS[riskLevel] || '#10b981';

          const marker = L.circleMarker([cp.latitude, cp.longitude], {
            radius: riskLevel === 'No Travel' ? 9 : 7,
            fillColor: color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9,
          }).addTo(map);

          // Rich diagnostic popup
          const etaFormatted = new Date(cp.eta).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
          });

          const reasonsHtml = (cp.risk?.explanations || [])
            .map((r) => `<div style="background: rgba(245, 158, 11, 0.12); border-left: 3px solid #f59e0b; padding: 4px 8px; font-size: 11px; margin-top: 6px; border-radius: 4px; color: #fde68a;">${r}</div>`)
            .join('');

          const popupContent = `
            <div style="min-width: 210px; font-family: system-ui, sans-serif; padding: 2px;">
              <div style="font-weight: 700; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px; margin-bottom: 6px; color: #f8fafc;">
                Checkpoint #${idx + 1} (${cp.distance_from_origin_miles} mi)
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0; color: #cbd5e1;">
                <span>ETA:</span>
                <strong style="color: #f8fafc;">${etaFormatted}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0; color: #cbd5e1;">
                <span>Risk Level:</span>
                <span style="color: ${color}; font-weight: 700; text-transform: uppercase;">${riskLevel}</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0; color: #cbd5e1;">
                <span>Wind Speed:</span>
                <strong style="color: #f8fafc;">${cp.weather?.wind_speed_mph || 0} mph</strong>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0; color: #cbd5e1;">
                <span>Rain Rate:</span>
                <strong style="color: #f8fafc;">${cp.weather?.precipitation_in_hr || 0} in/hr</strong>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin: 3px 0; color: #cbd5e1;">
                <span>Snowfall:</span>
                <strong style="color: #f8fafc;">${cp.weather?.snowfall_in_hr || 0} in/hr</strong>
              </div>
              ${reasonsHtml}
            </div>
          `;

          marker.bindPopup(popupContent);
          checkpointLayersRef.current.push(marker);
        });
      }
    });

    // Auto-fit map to route bounds
    if (allLatLngs.length > 0) {
      map.fitBounds(L.latLngBounds(allLatLngs), { padding: [40, 40] });
    }
  }, [routes, selectedRouteId, onSelectRoute]);

  // Update Corridor Weather Heatmap as currentHour scrubs [0..47]
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !corridorHeatmap || !corridorHeatmap.hours_data) return;

    if (heatmapLayerRef.current) {
      map.removeLayer(heatmapLayerRef.current);
      heatmapLayerRef.current = null;
    }

    const points = corridorHeatmap.hours_data[String(currentHour)] || [];
    if (points.length === 0) return;

    // Use circle markers with gradient opacity for smooth, reliable, high-performance heatmap overlay
    const heatGroup = L.layerGroup();

    points.forEach((pt) => {
      const radius = 35000 + pt.intensity * 45000; // Radius in meters
      const fillColor =
        pt.intensity > 0.75
          ? '#ef4444' // Severe
          : pt.intensity > 0.55
          ? '#f97316' // High
          : pt.intensity > 0.35
          ? '#f59e0b' // Mod
          : '#3b82f6'; // Calm/Rain

      const circle = L.circle([pt.lat, pt.lng], {
        radius: radius,
        fillColor: fillColor,
        fillOpacity: pt.intensity * 0.45,
        color: fillColor,
        weight: 1,
        opacity: 0.3,
      });

      circle.bindTooltip(
        `Corridor Weather at +${currentHour}h: ${pt.wind_mph} mph wind, ${pt.rain_in} in rain`,
        { sticky: true }
      );

      heatGroup.addLayer(circle);
    });

    heatGroup.addTo(map);
    heatmapLayerRef.current = heatGroup;
  }, [corridorHeatmap, currentHour]);

  return (
    <div className="relative w-full h-full flex-1">
      <div ref={mapContainerRef} className="w-full h-full bg-[#0b0f19]" />
    </div>
  );
}
