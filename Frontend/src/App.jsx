import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard, Truck, Users, Map, Bell, Search, TrendingUp, TrendingDown,
  Activity, CheckCircle2, AlertTriangle, Radio, ChevronRight, MapPin, Clock, Navigation, Filter, Lock
} from 'lucide-react';

const LiveClock = () => {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  return (
    <span className="font-mono text-sm text-cyan-400/90 tabular-nums tracking-wide hidden sm:block">
      {now.toLocaleTimeString('en-US', { hour12: false })}
    </span>
  );
};

const statusStyles = {
  ACTIVE: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  AVAILABLE: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  IN_SHOP: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  ON_SHIFT: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  RESTING: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
};

const navItems = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'vehicles', label: 'Fleet Registry', icon: Truck },
  { id: 'drivers', label: 'Personnel', icon: Users },
  { id: 'trips', label: 'Live Routing', icon: Map },
];

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authData, setAuthData] = useState({ email: 'admin@transitops.com', password: 'admin123' });
  const [authError, setAuthError] = useState('');

  const [currentTab, setCurrentTab] = useState('dashboard');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    registration_number: '', vehicle_name: '', vehicle_type: 'Truck', max_load_capacity: 10000, acquisition_cost: 150000
  });

  const [kpis, setKpis] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [trips, setTrips] = useState([]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const res = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authData)
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data.user);
        setIsAuthenticated(true);
      } else {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 422 && errorData.detail) {
          const msg = Array.isArray(errorData.detail)
            ? errorData.detail.map(d => d.msg).join(', ')
            : errorData.detail;
          setAuthError(`Validation Error: ${msg}`);
        } else {
          setAuthError(errorData.detail || 'Invalid credentials or backend offline.');
        }
      }
    } catch (err) {
      setAuthError('Cannot reach server. Is Python running?');
    }
  };

  const handleRegisterUnit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/api/vehicles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        setIsModalOpen(false);
        setFormData({ registration_number: '', vehicle_name: '', vehicle_type: 'Truck', max_load_capacity: 10000, acquisition_cost: 150000 });
      }
    } catch (error) {
      console.error("Failed to register:", error);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchAllData = async () => {
      try {
        const kRes = await fetch('http://localhost:8000/api/dashboard/kpis');
        if (kRes.ok) setKpis(await kRes.json());

        const vRes = await fetch('http://localhost:8000/api/vehicles');
        if (vRes.ok) {
          const rawVehicles = await vRes.json();
          setVehicles(rawVehicles.map(v => ({
            id: v.registration_number,
            name: v.vehicle_name,
            status: v.status === 'on_trip' ? 'ACTIVE' : v.status.toUpperCase(),
            efficiency: 85 + (v.id % 15), 
            battery: 95 - (v.id % 20),
            lastPing: 'LIVE'
          })));
        }

        const dRes = await fetch('http://localhost:8000/api/drivers');
        if (dRes.ok) {
          const rawDrivers = await dRes.json();
          setDrivers(rawDrivers.map(d => ({
            id: d.license_number,
            name: d.name,
            role: d.license_category.toUpperCase() + ' Operator',
            status: d.status === 'on_trip' ? 'ON_SHIFT' : 'RESTING',
            fatigue: Math.max(0, 100 - d.safety_score),
            shiftEnd: 'Active'
          })));
        }

        const tRes = await fetch('http://localhost:8000/api/trips');
        if (tRes.ok) {
          const rawTrips = await tRes.json();
          setTrips(rawTrips.map(t => ({
            id: t.trip_number,
            unit: t.vehicle ? `${t.vehicle.vehicle_name} (${t.vehicle.registration_number})` : 'Deployed Asset', 
            origin: t.source_location,
            dest: t.destination_location,
            progress: t.status === 'completed' ? 100 : (t.status === 'dispatched' ? 60 : 10),
            eta: t.status === 'completed' ? 'Arrived' : 'In Transit',
            status: t.status.toUpperCase()
          })));
        }
      } catch (error) {
        console.error("Data sync failed", error);
      }
    };

    fetchAllData();
    const interval = setInterval(fetchAllData, 3000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#0A0E17] font-sans selection:bg-cyan-500/30">
        <div className="w-full max-w-md p-8 bg-[#0D1220] border border-white/5 rounded-2xl shadow-2xl shadow-cyan-500/10 text-center animate-in fade-in zoom-in duration-500">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mb-6 shadow-lg shadow-cyan-500/20">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="font-display text-2xl font-bold text-white mb-2">TransitOps Gateway</h1>
          <p className="text-sm text-slate-400 mb-8">Secure authentication required for Command Center access.</p>
          
          <form onSubmit={handleLogin} className="space-y-4 text-left">
            <div>
              <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-1.5">Operator Email</label>
              <input type="email" value={authData.email} onChange={e => setAuthData({...authData, email: e.target.value})} className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 outline-none transition-all" />
            </div>
            <div>
              <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-1.5">Authorization Code</label>
              <input type="password" value={authData.password} onChange={e => setAuthData({...authData, password: e.target.value})} className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 outline-none transition-all" />
            </div>
            {authError && <p className="text-xs text-rose-400 text-center font-mono">{authError}</p>}
            <button type="submit" className="w-full py-3 mt-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-sm font-bold rounded-xl shadow-lg shadow-cyan-500/20 transition-all">
              Initialize Uplink
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#0A0E17] text-slate-200 antialiased selection:bg-cyan-500/30 overflow-hidden" style={{ fontFamily: "'Inter', ui-sans-serif, system-ui, sans-serif" }}>
      
      <aside className="w-72 bg-[#0D1220] border-r border-white/5 flex flex-col shrink-0 z-20 relative">
        <div className="px-6 py-6 flex items-center gap-3 border-b border-white/5">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Radio className="w-5 h-5 text-white" />
            </div>
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <div>
            <h1 className="font-display text-lg font-bold text-white tracking-tight leading-none">TransitOps</h1>
            <p className="text-[10px] text-slate-500 font-mono tracking-[0.2em] uppercase mt-1">Command Center</p>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1">
          <p className="px-3 pb-2 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-600">Modules</p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button key={item.id} onClick={() => setCurrentTab(item.id)} className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group relative ${isActive ? 'bg-white/[0.06] text-white' : 'text-slate-400 hover:bg-white/[0.03] hover:text-slate-200'}`}>
                {isActive && <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-0.5 rounded-full bg-cyan-400" />}
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <span className="flex-1 text-left">{item.label}</span>
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-slate-500" />}
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden relative">
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 z-10 shrink-0 bg-[#0A0E17]/80 backdrop-blur-md">
          <div className="flex items-center text-sm font-medium text-slate-500">
            <span className="text-slate-600">Workspace</span>
            <span className="mx-2 text-slate-700">/</span>
            <span className="text-slate-200 capitalize">{currentTab.replace('_', ' ')}</span>
          </div>
          <div className="flex items-center gap-3">
            <LiveClock />
            <span className="text-sm font-medium text-slate-300 hidden md:block">
              {currentUser ? currentUser.full_name : 'Om Sawant'}
            </span>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 text-white flex items-center justify-center text-xs font-bold font-display shadow-sm cursor-pointer ring-1 ring-white/10" title={currentUser ? currentUser.full_name : 'Om Sawant'}>
              {currentUser ? currentUser.full_name.split(' ').map(n => n[0]).join('') : 'OS'}
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 relative z-10">
          
          {currentTab === 'dashboard' && (
            <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-300">
              <div>
                <h1 className="font-display text-3xl font-bold text-white tracking-tight">Fleet Overview</h1>
                <p className="text-slate-500 mt-1.5 text-sm">Real-time metrics for your autonomous operations.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="relative bg-white/[0.03] border border-white/5 rounded-2xl p-6 overflow-hidden">
                  <div className="flex justify-between items-start mb-5">
                    <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400"><Truck className="w-4.5 h-4.5" /></div>
                  </div>
                  <h2 className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-2">Active Assets</h2>
                  <p className="font-display text-4xl font-bold text-white">{kpis ? kpis.active_vehicles : '--'}</p>
                </div>

                <div className="relative bg-white/[0.03] border border-white/5 rounded-2xl p-6 overflow-hidden">
                  <div className="flex justify-between items-start mb-5">
                    <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400"><CheckCircle2 className="w-4.5 h-4.5" /></div>
                  </div>
                  <h2 className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-2">Available on Lot</h2>
                  <p className="font-display text-4xl font-bold text-white">{kpis ? kpis.available_vehicles : '--'}</p>
                </div>

                <div className="relative bg-white/[0.03] border border-white/5 rounded-2xl p-6 overflow-hidden">
                  <div className="flex justify-between items-start mb-5">
                    <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400"><Activity className="w-4.5 h-4.5" /></div>
                  </div>
                  <h2 className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-2">Fleet Utilization</h2>
                  <p className="font-display text-4xl font-bold text-white">{kpis ? `${kpis.fleet_utilization.toFixed(1)}%` : '--'}</p>
                </div>
              </div>
            </div>
          )}

          {currentTab === 'vehicles' && (
            <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-300">
              <div className="flex justify-between items-end mb-6">
                <div>
                  <h1 className="font-display text-3xl font-bold text-white tracking-tight">Fleet Registry</h1>
                  <p className="text-slate-500 mt-1.5 text-sm">Manage and override autonomous units.</p>
                </div>
                <button onClick={() => setIsModalOpen(true)} className="px-4 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 text-sm font-semibold rounded-lg transition-all flex items-center gap-2 cursor-pointer">
                  + Register Unit
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {vehicles.map((v) => (
                  <div key={v.id} className="bg-white/[0.02] border border-white/5 rounded-xl p-5 hover:bg-white/[0.04] transition-colors">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-display font-bold text-white">{v.name}</h3>
                        <p className="font-mono text-xs text-slate-500 mt-1">{v.id}</p>
                      </div>
                      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono font-semibold border ${statusStyles[v.status] || statusStyles.AVAILABLE}`}>
                        {v.status.replace('_', ' ')}
                      </span>
                    </div>
                    
                    <div className="space-y-4 mb-5">
                      <div>
                        <div className="flex justify-between text-xs mb-1.5"><span className="text-slate-400">System Efficiency</span><span className="font-mono text-slate-200">{v.efficiency}%</span></div>
                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-emerald-400 rounded-full" style={{ width: `${v.efficiency}%` }} /></div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs mb-1.5"><span className="text-slate-400">Power Cell</span><span className="font-mono text-slate-200">{v.battery}%</span></div>
                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden"><div className={`h-full rounded-full ${v.battery > 30 ? 'bg-cyan-400' : 'bg-rose-400'}`} style={{ width: `${v.battery}%` }} /></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentTab === 'drivers' && (
            <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-300">
              <div>
                <h1 className="font-display text-3xl font-bold text-white tracking-tight">Personnel Registry</h1>
                <p className="text-slate-500 mt-1.5 text-sm">Manage operators and monitor performance.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {drivers.map((d) => (
                  <div key={d.id} className="bg-white/[0.02] border border-white/5 rounded-xl p-5 hover:bg-white/[0.04] transition-colors">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-display font-bold text-white">{d.name}</h3>
                        <p className="font-mono text-xs text-slate-500 mt-1">{d.id}</p>
                      </div>
                      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono font-semibold border ${statusStyles[d.status] || statusStyles.RESTING}`}>
                        {d.status.replace('_', ' ')}
                      </span>
                    </div>
                    
                    <div className="space-y-4 mb-3">
                      <div className="flex justify-between text-xs"><span className="text-slate-400">Designation</span><span className="text-slate-200">{d.role}</span></div>
                      <div>
                        <div className="flex justify-between text-xs mb-1.5"><span className="text-slate-400">Fatigue Index</span><span className="font-mono text-slate-200">{d.fatigue}%</span></div>
                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden"><div className={`h-full rounded-full ${d.fatigue < 60 ? 'bg-emerald-400' : 'bg-rose-400'}`} style={{ width: `${d.fatigue}%` }} /></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentTab === 'trips' && (
            <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-300">
              <div>
                <h1 className="font-display text-3xl font-bold text-white tracking-tight">Active Live Routing</h1>
                <p className="text-slate-500 mt-1.5 text-sm">Monitor asset progress, origin and destination paths.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {trips.map((t) => (
                  <div key={t.id} className="bg-white/[0.02] border border-white/5 rounded-xl p-5 hover:bg-white/[0.04] transition-colors">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-display font-bold text-white">{t.unit}</h3>
                        <p className="font-mono text-xs text-slate-500 mt-1">{t.id}</p>
                      </div>
                      <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono font-semibold border bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                        {t.status}
                      </span>
                    </div>
                    
                    <div className="space-y-4 mb-3">
                      <div className="flex justify-between text-xs"><span className="text-slate-400">Route</span><span className="text-slate-200">{t.origin} ➔ {t.dest}</span></div>
                      <div className="flex justify-between text-xs"><span className="text-slate-400">ETA Status</span><span className="text-slate-200">{t.eta}</span></div>
                      <div>
                        <div className="flex justify-between text-xs mb-1.5"><span className="text-slate-400">Trip Progress</span><span className="font-mono text-slate-200">{t.progress}%</span></div>
                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-cyan-400 rounded-full" style={{ width: `${t.progress}%` }} /></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-[#0D1220] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl">
              <h2 className="font-display text-xl font-bold text-white mb-1">Register New Asset</h2>
              <form onSubmit={handleRegisterUnit} className="space-y-4 mt-6">
                <div>
                  <label className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">Registration ID</label>
                  <input type="text" required placeholder="e.g. TRK-099" value={formData.registration_number} onChange={(e) => setFormData({...formData, registration_number: e.target.value})} className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none" />
                </div>
                <div>
                  <label className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">Asset Designation</label>
                  <input type="text" required placeholder="e.g. Heavy Hauler Gamma" value={formData.vehicle_name} onChange={(e) => setFormData({...formData, vehicle_name: e.target.value})} className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none" />
                </div>
                <div className="flex gap-3 pt-4 mt-2 border-t border-white/10">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-2 bg-white/[0.05] text-white text-sm font-semibold rounded-lg">Cancel</button>
                  <button type="submit" className="flex-1 py-2 bg-cyan-600 text-white text-sm font-semibold rounded-lg">Deploy Unit</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}