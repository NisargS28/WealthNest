"use client";

import { useState } from "react";
import { HoldingDetail } from "@/types";
import { ChevronDown, LineChart, X, Pencil, Check } from "lucide-react";
import { createClient } from "@/utils/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface Props {
  holdings: HoldingDetail[];
}

// Helper to get initials for the circle icon
const getInitials = (name: string) => {
  const words = name.split(' ');
  if (words.length >= 2) {
    return `${words[0][0]}${words[1][0]}`.toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
};

export default function PortfolioTable({ holdings }: Props) {
  const [selectedHolding, setSelectedHolding] = useState<HoldingDetail | null>(null);
  const [editingSipDay, setEditingSipDay] = useState(false);
  const [newSipDay, setNewSipDay] = useState(15);
  const [savingSip, setSavingSip] = useState(false);

  // Modal derived values
  let modalCurrentVal = 0;
  let modalInvestedVal = 0;
  let modalAbsPl = 0;
  let modalPlPercent = 0;
  let modalIsProfit = false;
  let modalAvgNav = 0;
  let modalAbsReturn = 0;
  let modalUnits = 0;
  
  let modalMock1DPercent = 0.00;
  let modalIs1DProfit = true;
  let modalMockXirr = "N/A";

  if (selectedHolding) {
    modalCurrentVal = parseFloat(selectedHolding.current_value);
    modalInvestedVal = parseFloat(selectedHolding.invested);
    modalAbsPl = modalCurrentVal - modalInvestedVal;
    modalPlPercent = parseFloat(selectedHolding.returns);
    modalIsProfit = modalAbsPl >= 0;
    modalUnits = parseFloat(selectedHolding.units);
    modalAvgNav = modalUnits > 0 ? modalInvestedVal / modalUnits : 0;
    modalAbsReturn = modalInvestedVal > 0 ? (modalAbsPl / modalInvestedVal) * 100 : 0;
    
    if (selectedHolding.one_day_change != null) {
      modalMock1DPercent = Math.abs(parseFloat(selectedHolding.one_day_change_percent || "0"));
      modalIs1DProfit = parseFloat(selectedHolding.one_day_change) >= 0;
    }
  }

  return (
    <div className="w-full overflow-x-auto bg-[#1a1814] rounded-xl border border-white/5 relative">
      <table className="w-full text-sm text-left">
        <thead className="text-[11px] uppercase tracking-wider text-secondary border-b border-white/5 bg-[#1f1d19]">
          <tr>
            <th className="px-6 py-4 font-medium flex items-center gap-1 cursor-pointer hover:text-primary">
              FUND <ChevronDown size={12} />
            </th>
            <th className="px-6 py-4 font-medium text-right cursor-pointer hover:text-primary">
              <div className="flex items-center justify-end gap-1">CURRENT VALUE <ChevronDown size={12} /></div>
            </th>
            <th className="px-6 py-4 font-medium text-right cursor-pointer hover:text-primary">
              <div className="flex items-center justify-end gap-1">1D <ChevronDown size={12} /></div>
            </th>
            <th className="px-6 py-4 font-medium text-right cursor-pointer hover:text-primary">
              <div className="flex items-center justify-end gap-1">P&L <ChevronDown size={12} /></div>
            </th>
            <th className="px-6 py-4 font-medium text-right cursor-pointer hover:text-primary">
              <div className="flex items-center justify-end gap-1">XIRR <ChevronDown size={12} /></div>
            </th>
            <th className="px-6 py-4"></th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((h, i) => {
            const currentVal = parseFloat(h.current_value);
            const investedVal = parseFloat(h.invested);
            const absolutePl = currentVal - investedVal;
            const plPercent = parseFloat(h.returns);
            const isProfit = absolutePl >= 0;

            // Values from backend
            let mock1DAbsolute = 0;
            let mock1DPercent = 0.00;
            let is1DProfit = true;
            if (h.one_day_change != null) {
              mock1DAbsolute = Math.abs(parseFloat(h.one_day_change));
              mock1DPercent = Math.abs(parseFloat(h.one_day_change_percent || "0"));
              is1DProfit = parseFloat(h.one_day_change) >= 0;
            }
            const mockXirr = "N/A";

            // Calculate duration string
            let holdingSinceStr = "";
            if (h.invested_since) {
              const d = new Date(h.invested_since);
              holdingSinceStr = `Since ${d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}`;
              const now = new Date();
              let years = now.getFullYear() - d.getFullYear();
              let months = now.getMonth() - d.getMonth();
              if (months < 0) {
                years--;
                months += 12;
              }
              if (years > 0) {
                holdingSinceStr += ` • ${years}y ${months}m`;
              } else if (months > 0) {
                holdingSinceStr += ` • ${months}m`;
              }
            } else {
              holdingSinceStr = "Date unknown";
            }

            return (
              <tr 
                key={h.id || i} 
                className="border-b border-white/5 hover:bg-white/[0.02] transition-colors cursor-pointer"
                onClick={() => setSelectedHolding(h)}
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-[#2a261f] flex items-center justify-center text-[#d4af37] text-xs font-bold shrink-0">
                      {getInitials(h.scheme_name)}
                    </div>
                    <div>
                      <div className="font-semibold text-white/90 text-base" style={{ maxWidth: "350px", whiteSpace: "normal" }}>
                        {h.scheme_name}
                      </div>
                      <div className="text-xs text-secondary mt-1">
                        {h.investment_type} • {holdingSinceStr}
                      </div>
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-4 text-right">
                  <div className="font-semibold text-white/90 text-base">
                    ₹{currentVal.toLocaleString('en-IN', {maximumFractionDigits: 0})}
                  </div>
                  <div className="text-xs text-secondary mt-1">
                    ₹{investedVal.toLocaleString('en-IN', {maximumFractionDigits: 0})}
                  </div>
                </td>

                <td className="px-6 py-4 text-right">
                  {h.one_day_change != null ? (
                    <>
                      <div className={`font-semibold flex items-center justify-end gap-1 ${is1DProfit ? 'text-green-500' : 'text-red-500'}`}>
                        {is1DProfit ? '▲' : '▼'} ₹{mock1DAbsolute.toLocaleString('en-IN', {maximumFractionDigits: 0})}
                      </div>
                      <div className={`text-xs mt-1 ${is1DProfit ? 'text-green-500' : 'text-red-500'}`}>
                        {is1DProfit ? '+' : '-'}{mock1DPercent.toFixed(2)}%
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="font-semibold flex items-center justify-end gap-1 text-secondary">
                        - ₹0
                      </div>
                      <div className="text-xs mt-1 text-secondary">
                        0.00%
                      </div>
                    </>
                  )}
                </td>

                <td className="px-6 py-4 text-right">
                  <div className={`font-semibold ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
                    ₹{Math.abs(absolutePl).toLocaleString('en-IN', {maximumFractionDigits: 0})}
                  </div>
                  <div className={`text-xs mt-1 ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
                    {isProfit ? '+' : '-'}{Math.abs(plPercent).toFixed(2)}%
                  </div>
                </td>

                <td className="px-6 py-4 text-right">
                  <div className="font-semibold text-secondary">
                    N/A
                  </div>
                </td>

                <td className="px-6 py-4 text-right">
                  <button 
                    className="px-3 py-1.5 rounded bg-transparent border border-white/10 hover:border-white/30 text-xs text-white/80 transition-colors flex items-center gap-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedHolding(h);
                    }}
                  >
                    <LineChart size={14} /> Details
                  </button>
                </td>
              </tr>
            );
          })}
          
          {holdings.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center text-secondary py-12">
                No active funds found in this portfolio.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {/* Details Modal */}
      {selectedHolding && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-fade-in"
          onClick={() => setSelectedHolding(null)}
        >
          <div 
            className="bg-[#1a1814] border border-white/10 shadow-2xl rounded-xl w-full max-w-md overflow-hidden animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10 bg-[#1f1d19]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#2a261f] flex items-center justify-center text-[#d4af37] text-xs font-bold shrink-0">
                  {getInitials(selectedHolding.scheme_name)}
                </div>
                <h3 className="font-bold text-base text-white/90 line-clamp-1">
                  {selectedHolding.scheme_name}
                </h3>
              </div>
              <button 
                onClick={() => setSelectedHolding(null)}
                className="text-secondary hover:text-white transition-colors shrink-0"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-2 gap-y-6 gap-x-4">
                
                {/* Current Value */}
                <div>
                  <div className="text-xs text-secondary mb-1">Current Value</div>
                  <div className="text-lg font-bold text-white/90">
                    ₹{modalCurrentVal.toLocaleString('en-IN', {maximumFractionDigits: 2})}
                  </div>
                  {selectedHolding.one_day_change != null ? (
                    <div className={`text-sm font-medium ${modalIs1DProfit ? 'text-green-500' : 'text-red-500'}`}>
                      {modalIs1DProfit ? '▲' : '▼'} {modalIs1DProfit ? '+' : '-'}{modalMock1DPercent.toFixed(2)}% 1D
                    </div>
                  ) : (
                    <div className="text-sm font-medium text-secondary">
                      - 0.00% 1D
                    </div>
                  )}
                </div>

                {/* P&L */}
                <div>
                  <div className="text-xs text-secondary mb-1">P&L</div>
                  <div className={`text-lg font-bold ${modalIsProfit ? 'text-green-500' : 'text-red-500'}`}>
                    ₹{Math.abs(modalAbsPl).toLocaleString('en-IN', {maximumFractionDigits: 2})}
                  </div>
                  <div className={`text-sm font-medium ${modalIsProfit ? 'text-green-500' : 'text-red-500'}`}>
                    {modalIsProfit ? '▲' : '▼'} {modalIsProfit ? '+' : '-'}{Math.abs(modalPlPercent).toFixed(2)}%
                  </div>
                </div>

                {/* XIRR & Abs Return */}
                <div>
                  <div className="text-xs text-secondary mb-1">XIRR</div>
                  <div className="text-base font-semibold text-white/90">
                    {modalMockXirr}
                  </div>
                  <div className="text-xs text-secondary mt-1">
                    abs rtn: {modalAbsReturn.toFixed(2)}%
                  </div>
                </div>

                {/* Current NAV */}
                <div>
                  <div className="text-xs text-secondary mb-1">Curr. NAV</div>
                  <div className="text-base font-semibold text-white/90">
                    ₹{parseFloat(selectedHolding.nav).toFixed(4)}
                  </div>
                  <div className="text-xs text-secondary mt-1">
                    {selectedHolding.nav_date ? new Date(selectedHolding.nav_date).toLocaleDateString('en-IN') : 'N/A'}
                  </div>
                </div>

                {/* Invested Amount */}
                <div>
                  <div className="text-xs text-secondary mb-1">Invested Amount</div>
                  <div className="text-base font-semibold text-white/90">
                    ₹{modalInvestedVal.toLocaleString('en-IN', {maximumFractionDigits: 2})}
                  </div>
                </div>

                {/* Units Balance */}
                <div>
                  <div className="text-xs text-secondary mb-1">Units Balance</div>
                  <div className="text-base font-semibold text-white/90">
                    {modalUnits.toFixed(3)}
                  </div>
                </div>

                {/* Avg NAV */}
                <div>
                  <div className="text-xs text-secondary mb-1">Avg NAV</div>
                  <div className="text-base font-semibold text-white/90">
                    ₹{modalAvgNav.toFixed(4)}
                  </div>
                </div>

              </div>

              {/* SIP Details Section */}
              {selectedHolding.investment_type.includes("SIP") && selectedHolding.sip_day != null && (
                <div className="mt-6 pt-4 border-t border-white/10">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs font-semibold uppercase tracking-widest text-secondary">SIP Details</p>
                    {selectedHolding.sip_status !== "ACTIVE" && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-amber-900/30 text-amber-400">Pending Confirmation</span>
                    )}
                    {selectedHolding.sip_status === "ACTIVE" && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/30 text-green-400">Active</span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-y-4 gap-x-2">
                    <div>
                      <div className="text-xs text-secondary mb-0.5">SIP Day</div>
                      <div className="text-sm font-semibold text-white/90">{selectedHolding.sip_day}th of month</div>
                    </div>
                    <div>
                      <div className="text-xs text-secondary mb-0.5">Last SIP</div>
                      <div className="text-sm font-semibold text-white/90">
                        {selectedHolding.last_sip_date
                          ? new Date(selectedHolding.last_sip_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                          : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-secondary mb-0.5">Next SIP</div>
                      <div className="text-sm font-semibold text-amber-400">
                        {selectedHolding.next_sip_date
                          ? new Date(selectedHolding.next_sip_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                          : 'N/A'}
                      </div>
                    </div>
                  </div>

                  {/* Edit SIP Day */}
                  {!editingSipDay ? (
                    <button
                      onClick={() => { setEditingSipDay(true); setNewSipDay(selectedHolding.sip_day!); }}
                      className="mt-3 flex items-center gap-1.5 text-xs text-secondary hover:text-white transition-colors border border-white/10 hover:border-white/30 px-3 py-1.5 rounded"
                    >
                      <Pencil size={12} /> Edit SIP Date
                    </button>
                  ) : (
                    <div className="mt-3 flex items-center gap-2">
                      <span className="text-xs text-secondary">SIP day:</span>
                      <input
                        type="number" min={1} max={31} value={newSipDay}
                        onChange={(e) => setNewSipDay(parseInt(e.target.value))}
                        className="w-16 px-2 py-1 text-xs rounded bg-white/10 border border-white/20 text-white text-center"
                      />
                      <button
                        disabled={savingSip}
                        onClick={async () => {
                          if (!selectedHolding.sip_plan_id) return;
                          setSavingSip(true);
                          try {
                            const supabase = createClient();
                            const { data: { session } } = await supabase.auth.getSession();
                            if (!session) return;
                            await fetch(`${API_BASE}/api/sip-plans/${selectedHolding.sip_plan_id}`, {
                              method: "PATCH",
                              headers: { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json" },
                              body: JSON.stringify({ sip_day: newSipDay })
                            });
                            setEditingSipDay(false);
                            // Refresh the page to reflect new sip_day
                            window.location.reload();
                          } catch(e) { console.error(e); }
                          finally { setSavingSip(false); }
                        }}
                        className="px-3 py-1 text-xs rounded bg-amber-500 hover:bg-amber-400 text-black font-semibold flex items-center gap-1 disabled:opacity-50"
                      >
                        <Check size={12} /> {savingSip ? "Saving…" : "Save"}
                      </button>
                      <button onClick={() => setEditingSipDay(false)} className="text-xs text-secondary hover:text-white">Cancel</button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
