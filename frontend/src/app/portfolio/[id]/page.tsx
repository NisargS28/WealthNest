"use client";

import { useEffect, useState } from "react";
import { getPortfolio, refreshNav } from "@/lib/api";
import { PortfolioDetail } from "@/types";
import { useRouter } from "next/navigation";
import PortfolioTable from "@/components/PortfolioTable";
import { AlertTriangle, Trash2, X, Search, Filter, PieChart, TrendingUp, ChevronDown } from "lucide-react";
import { createClient } from "@/utils/supabase/client";

export default function PortfolioPage({ params }: { params: { id: string } }) {
  const [portfolio, setPortfolio] = useState<PortfolioDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Deletion state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const router = useRouter();

  useEffect(() => {
    async function load() {
      try {
        const data = await getPortfolio(params.id);
        setPortfolio(data);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("An unknown error occurred");
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshNav(params.id);
      // Re-fetch entire portfolio to get updated HoldingDetail (with newly calculated returns based on new NAV)
      const data = await getPortfolio(params.id);
      setPortfolio(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert("Refresh failed: " + err.message);
      }
    } finally {
      setRefreshing(false);
    }
  };

  const handleDelete = async () => {
    if (deleteConfirmText !== "DELETE") return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      const res = await fetch(`/api/portfolio/${params.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        }
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to delete portfolio");
      }
      
      router.push('/dashboard');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setDeleteError(err.message);
      } else {
        setDeleteError("Failed to delete portfolio");
      }
      setIsDeleting(false);
    }
  };

  if (loading) return <div className="container text-center py-20"><div className="spinner mx-auto"></div></div>;
  if (error) return <div className="container py-10"><div className="text-error">{error}</div></div>;
  if (!portfolio) return null;

  // Compute totals
  const totalValue = portfolio.holdings.reduce((sum, h) => sum + parseFloat(h.current_value), 0);
  const investedValue = portfolio.holdings.reduce((sum, h) => sum + parseFloat(h.invested), 0);
  const unrealisedAbs = totalValue - investedValue;
  const unrealisedPct = investedValue > 0 ? (unrealisedAbs / investedValue) * 100 : 0;
  
  // Mock totals
  const mock1DAbsolute = 1405;
  const mock1DPercent = 0.55;
  const mockRealisedAbs = 10618;
  const mockRealisedPct = 4.88;
  const mockXirr = 17.07;

  return (
    <div className="container max-w-6xl animate-fade-in py-8">
      {/* Back button */}
      <div className="text-sm text-secondary mb-6 cursor-pointer hover:text-primary w-fit flex items-center gap-2" onClick={() => router.push("/")}>
        ← Back to Members
      </div>

      {/* TOP SECTION */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6 mb-8">
        <div>
          <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-2">
            {portfolio.holdings.length} ACTIVE FUNDS
          </div>
          <div className="text-5xl font-bold text-white/90 mb-2">
            ₹{totalValue.toLocaleString('en-IN', {maximumFractionDigits: 0})}
          </div>
          <div className="text-sm font-semibold text-green-500">
            ▲ ₹{mock1DAbsolute.toLocaleString('en-IN')} (+{mock1DPercent}%) today
          </div>
        </div>

        <div className="flex flex-col gap-4 items-end">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
              <input 
                type="text" 
                placeholder="Search current holdings..." 
                className="bg-[#1a1814] border border-white/10 rounded-full py-2 pl-10 pr-4 text-sm w-64 focus:outline-none focus:border-white/30 transition-colors"
              />
            </div>
            <button className="flex items-center gap-2 bg-[#1a1814] border border-white/10 hover:bg-white/5 rounded-full px-4 py-2 text-sm transition-colors">
              <Filter size={16} /> All {portfolio.holdings.length}
            </button>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 bg-[#1a1814] border border-white/10 hover:bg-white/5 rounded-full px-4 py-2 text-sm transition-colors">
              <PieChart size={16} /> Composition
            </button>
            <button className="flex items-center gap-2 bg-[#1a1814] border border-white/10 hover:bg-white/5 rounded-full px-4 py-2 text-sm transition-colors">
              <TrendingUp size={16} /> Performance
            </button>
            <button 
              className="flex items-center gap-2 bg-[#1a1814] border border-white/10 hover:bg-white/5 rounded-full px-4 py-2 text-sm transition-colors"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              {refreshing ? "Refreshing..." : "Refresh NAV"}
            </button>
          </div>
        </div>
      </div>

      {/* SUMMARY ROW */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 py-6 border-y border-white/10 mb-8">
        <div>
          <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-1">
            Invested Value
          </div>
          <div className="font-semibold text-base">
            ₹{investedValue.toLocaleString('en-IN', {maximumFractionDigits: 0})}
          </div>
        </div>
        <div>
          <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-1">
            Unrealised P&L
          </div>
          <div className={`font-semibold text-base ${unrealisedAbs >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            ₹{Math.abs(unrealisedAbs).toLocaleString('en-IN', {maximumFractionDigits: 0})} ({unrealisedAbs >= 0 ? '+' : '-'}{Math.abs(unrealisedPct).toFixed(2)}%)
          </div>
        </div>
        <div>
          <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-1 flex items-center gap-1">
            Realised P&L <ChevronDown size={12} className="text-secondary" />
          </div>
          <div className="font-semibold text-base text-green-500">
            ₹{mockRealisedAbs.toLocaleString('en-IN')} (+{mockRealisedPct}%)
          </div>
        </div>
        <div>
          <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-1 flex items-center gap-1">
            XIRR <ChevronDown size={12} className="text-secondary" />
          </div>
          <div className="font-semibold text-base text-green-500">
            {mockXirr}%
          </div>
        </div>
        <div className="text-right md:text-left">
          <div className="text-xs font-semibold text-secondary uppercase tracking-widest mb-1">
            Holding Since
          </div>
          <div className="font-semibold text-base text-white/90">
            Jun 2022 • 4y 2m
          </div>
        </div>
      </div>

      {/* PORTFOLIO TABLE */}
      <div className="mb-10">
        <PortfolioTable holdings={portfolio.holdings} />
      </div>

      {/* DANGER ZONE */}
      <div className="mt-16 pt-10 border-t border-red-500/20">
        <h2 className="mb-4 text-red-500 flex items-center gap-2">
          <AlertTriangle size={24} /> Danger Zone
        </h2>
        <div className="glass-card p-6 border border-red-500/30 bg-red-500/5">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <h3 className="text-lg font-bold text-red-400 mb-1">Delete Entire Portfolio</h3>
              <p className="text-sm text-secondary max-w-xl">
                This will permanently delete this portfolio and its associated financial data (transactions, investments, SIP records, valuation history, and imports). This action cannot be undone.
              </p>
            </div>
            <button 
              className="btn bg-red-600 hover:bg-red-700 text-white border-none shrink-0"
              onClick={() => setShowDeleteModal(true)}
            >
              <Trash2 size={16} className="mr-2 inline" /> Delete Portfolio
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-card border border-border shadow-2xl rounded-xl w-full max-w-md overflow-hidden animate-slide-up">
            <div className="flex items-center justify-between p-4 border-b border-border/50">
              <h3 className="font-bold text-lg text-red-500 flex items-center gap-2">
                <AlertTriangle size={20} /> Delete Portfolio?
              </h3>
              <button 
                onClick={() => setShowDeleteModal(false)}
                className="text-muted-foreground hover:text-foreground transition-colors p-1"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-red-500/10 text-red-500 p-4 rounded-lg text-sm border border-red-500/20">
                <p className="font-bold mb-2">This permanently deletes:</p>
                <ul className="list-disc pl-5 space-y-1">
                  <li>transactions</li>
                  <li>investments</li>
                  <li>SIP records</li>
                  <li>valuation history</li>
                  <li>imports</li>
                </ul>
                <p className="mt-3 font-semibold underline">This action cannot be undone.</p>
              </div>

              {deleteError && (
                <div className="text-red-500 text-sm p-3 bg-red-500/10 rounded-md border border-red-500/20">
                  {deleteError}
                </div>
              )}

              <div className="space-y-2 pt-2">
                <label className="text-sm font-medium">Type <span className="font-mono bg-muted px-1 py-0.5 rounded text-red-400">DELETE</span> to confirm:</label>
                <input 
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  className="w-full bg-background border border-input rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="DELETE"
                />
              </div>
            </div>
            
            <div className="p-4 border-t border-border/50 flex justify-end gap-3 bg-muted/20">
              <button 
                className="btn btn-outline"
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button 
                className="btn bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed border-none"
                disabled={deleteConfirmText !== "DELETE" || isDeleting}
                onClick={handleDelete}
              >
                {isDeleting ? "Deleting..." : "Delete Permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
