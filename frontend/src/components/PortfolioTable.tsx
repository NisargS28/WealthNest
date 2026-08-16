import { HoldingDetail } from "@/types";
import { ChevronDown, LineChart } from "lucide-react";

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
  return (
    <div className="w-full overflow-x-auto bg-[#1a1814] rounded-xl border border-white/5">
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

            // Mock Data
            const mock1DAbsolute = Math.random() * 500;
            const mock1DPercent = (mock1DAbsolute / currentVal) * 100;
            const is1DProfit = Math.random() > 0.3; // 70% chance of green
            const mockXirr = 15.0 + (Math.random() * 10 - 5);

            return (
              <tr key={h.id || i} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
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
                        1 folio • Since Jun 2022 • 4y 2m
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
                  <div className={`font-semibold flex items-center justify-end gap-1 ${is1DProfit ? 'text-green-500' : 'text-red-500'}`}>
                    {is1DProfit ? '▲' : '▼'} ₹{mock1DAbsolute.toLocaleString('en-IN', {maximumFractionDigits: 0})}
                  </div>
                  <div className={`text-xs mt-1 ${is1DProfit ? 'text-green-500' : 'text-red-500'}`}>
                    {is1DProfit ? '+' : '-'}{mock1DPercent.toFixed(2)}%
                  </div>
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
                  <div className="font-semibold text-green-500">
                    {mockXirr.toFixed(2)}%
                  </div>
                </td>

                <td className="px-6 py-4 text-right">
                  <button className="px-3 py-1.5 rounded bg-transparent border border-white/10 hover:border-white/30 text-xs text-white/80 transition-colors flex items-center gap-2">
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
    </div>
  );
}
