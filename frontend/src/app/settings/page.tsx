import { Settings, Bell, Palette, Globe } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="container max-w-3xl py-8 animate-fade-in">
      <h1 className="text-3xl font-bold mb-6 flex items-center gap-3">
        <Settings size={28} className="text-primary" /> Settings
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-2">
          <div className="p-3 rounded-lg bg-slate-800 text-slate-200 cursor-pointer font-medium border border-slate-700">General</div>
          <div className="p-3 rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 cursor-pointer transition-colors">Notifications</div>
          <div className="p-3 rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 cursor-pointer transition-colors">Appearance</div>
        </div>
        
        <div className="md:col-span-2 space-y-6">
          <div className="glass-card">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-slate-700 pb-2">
              <Globe size={18} className="text-secondary"/> Regional Settings
            </h3>
            
            <div className="space-y-4">
              <div className="form-group mb-0">
                <label className="form-label">Base Currency</label>
                <select className="form-control bg-slate-800" defaultValue="INR">
                  <option value="INR">Indian Rupee (₹)</option>
                  <option value="USD">US Dollar ($)</option>
                </select>
                <p className="text-xs text-secondary mt-1">Currency used for all portfolio valuations.</p>
              </div>
            </div>
          </div>

          <div className="glass-card opacity-50">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-slate-700 pb-2">
              <Bell size={18} className="text-secondary"/> Notifications (Coming Soon)
            </h3>
            <p className="text-sm text-secondary">Configure email alerts for SIP deductions and NAV changes.</p>
          </div>
          
          <div className="glass-card opacity-50">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-slate-700 pb-2">
              <Palette size={18} className="text-secondary"/> Theme (Coming Soon)
            </h3>
            <p className="text-sm text-secondary">Switch between dark mode, light mode, and system preference.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
