"use client";

import { useEffect, useState } from "react";
import { getFamily } from "@/lib/api";
import { FamilyView } from "@/types";
import { useRouter } from "next/navigation";

export default function FamilyPage() {
  const [data, setData] = useState<FamilyView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    getFamily()
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container flex justify-center py-20"><div className="spinner"></div></div>;
  if (error) return <div className="container py-10"><div className="text-error">{error}</div></div>;
  if (!data) return null;

  return (
    <div className="container animate-fade-in">
      <div className="flex justify-between items-center mb-10">
        <div>
          <h1>Family Wealth Overview</h1>
          <p>Aggregated view across all family members.</p>
        </div>
      </div>

      <div className="glass-card mb-10 text-center py-10" style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1))' }}>
        <h2 className="text-secondary font-medium text-lg uppercase tracking-wider mb-2">Total Family Wealth</h2>
        <div className="text-5xl font-bold" style={{ background: 'linear-gradient(135deg, var(--primary), var(--accent))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          ₹ {parseFloat(data.aggregate.total_value).toLocaleString('en-IN', {minimumFractionDigits: 2})}
        </div>
      </div>

      <h2 className="mb-6">Member Breakdown</h2>
      <div className="grid grid-cols-2 gap-6">
        {data.aggregate.member_summaries.map(p => (
          <div key={p.id} className="glass-card cursor-pointer hover:border-primary transition-colors" onClick={() => router.push(`/portfolio/${p.id}`)}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="mb-0 text-xl">{p.display_name}</h3>
              <div className="badge badge-success">Active</div>
            </div>
            
            <div className="mb-6">
              <span className="text-secondary text-sm">Portfolio Value</span>
              <div className="text-2xl font-bold text-success mt-1">
                ₹ {p.total_current_value ? parseFloat(p.total_current_value).toLocaleString('en-IN', {minimumFractionDigits: 2}) : "0.00"}
              </div>
            </div>
            
            <div className="flex gap-6 border-t border-[rgba(255,255,255,0.1)] pt-4">
              <div>
                <div className="text-secondary text-xs">Folios</div>
                <div className="font-medium">{p.folio_count}</div>
              </div>
              <div>
                <div className="text-secondary text-xs">Transactions</div>
                <div className="font-medium">{p.transaction_count}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
