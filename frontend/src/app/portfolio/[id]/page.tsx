"use client";

import { useEffect, useState } from "react";
import { getPortfolio, refreshNav } from "@/lib/api";
import { PortfolioDetail } from "@/types";
import { useRouter } from "next/navigation";
import HoldingsTable from "@/components/HoldingsTable";

export default function PortfolioPage({ params }: { params: { id: string } }) {
  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const router = useRouter();

  useEffect(() => {
    async function load() {
      try {
        const data = await getPortfolio(params.id);
        setPortfolio(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const updatedValuation = await refreshNav(params.id);
      if (portfolio) {
        setPortfolio({
          ...portfolio,
          valuation: updatedValuation,
          holdings: updatedValuation.holdings
        });
      }
    } catch (err: any) {
      alert("Refresh failed: " + err.message);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <div className="container text-center py-20"><div className="spinner mx-auto"></div></div>;
  if (error) return <div className="container py-10"><div className="text-error">{error}</div></div>;
  if (!portfolio) return null;

  return (
    <div className="container animate-fade-in">
      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="text-sm text-secondary mb-1 cursor-pointer hover:text-primary" onClick={() => router.push("/")}>
            ← Back to Members
          </div>
          <h1>{portfolio.display_name}</h1>
          <p className="mb-0">
            {portfolio.valuation 
              ? `Last valued on ${new Date(portfolio.valuation.generated_at).toLocaleString()}` 
              : "No valuation data available"}
          </p>
        </div>
        
        <button 
          className="btn btn-outline" 
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing..." : "Refresh NAV"}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="glass-card p-6">
          <span className="text-secondary text-sm font-medium uppercase tracking-wider">Total Value</span>
          <div className="text-3xl font-bold text-success mt-2">
            ₹ {portfolio.valuation ? parseFloat(portfolio.valuation.total_current_value).toLocaleString('en-IN', {minimumFractionDigits: 2}) : "0.00"}
          </div>
        </div>
        <div className="glass-card p-6">
          <span className="text-secondary text-sm font-medium uppercase tracking-wider">Active Schemes</span>
          <div className="text-3xl font-bold mt-2">{portfolio.holdings.length}</div>
        </div>
        <div className="glass-card p-6">
          <span className="text-secondary text-sm font-medium uppercase tracking-wider">Linked Folios</span>
          <div className="text-3xl font-bold mt-2">{portfolio.folios.length}</div>
        </div>
      </div>

      <div className="mb-10">
        <h2 className="mb-4">Current Holdings</h2>
        <HoldingsTable holdings={portfolio.holdings} />
      </div>

      <div className="mb-10">
        <h2 className="mb-4">Folio Breakdown</h2>
        <div className="grid grid-cols-2 gap-4">
          {portfolio.folios.map(f => (
            <div key={f.folio_number} className="glass-card p-5">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="font-bold text-lg">{f.scheme_name}</div>
                  <div className="text-secondary text-sm mt-1">{f.amc}</div>
                </div>
                <div className="badge badge-neutral">Folio: {f.folio_number}</div>
              </div>
              <div className="flex justify-between mt-4 border-t border-[rgba(255,255,255,0.1)] pt-4">
                <div>
                  <div className="text-xs text-secondary">Units</div>
                  <div className="font-medium">{f.opening_units}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-secondary">Transactions</div>
                  <div className="font-medium">{f.transaction_count}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
