"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle, Info, Save, X, Eye, Calendar, Database, ShieldAlert, Award } from 'lucide-react';
import Link from 'next/link';
import { getImportPreview, confirmImport, cancelImport } from '@/lib/api';
import { ImportPreview } from '@/types';

export default function ImportPreviewPage({ params }: { params: { id: string } }) {
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  
  const router = useRouter();
  const importId = params.id;

  useEffect(() => {
    getImportPreview(importId)
      .then((data) => {
        setPreview(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load import preview");
        setLoading(false);
      });
  }, [importId]);

  const handleConfirm = async () => {
    setConfirming(true);
    setError(null);
    try {
      const res = await confirmImport(importId);
      router.push(`/portfolio/${res.portfolio_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to confirm import");
      setConfirming(false);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelImport(importId);
      router.push('/import');
    } catch (err) {
      console.error(err);
      router.push('/import');
    }
  };

  if (loading) {
    return (
      <div className="container flex flex-col justify-center items-center py-20">
        <div className="spinner mb-4"></div>
        <p className="text-secondary">Loading import preview details...</p>
      </div>
    );
  }

  const formatCurrencyString = (val: string | null) => {
    if (val === null) return "-";
    const num = parseFloat(val);
    if (isNaN(num)) return val;
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(num);
  };

  const holdings = preview?.holdings || [];
  const summary = preview?.summary;
  const breakdown = preview?.transaction_breakdown;

  return (
    <div className="container animate-fade-in" style={{ maxWidth: "900px" }}>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold m-0 flex items-center gap-3">
            <Eye className="text-primary"/> Import Preview
          </h1>
          <p className="m-0 mt-1">Review the parsed statement before saving it to your portfolio.</p>
        </div>
        <div className="flex gap-3">
          <button className="btn btn-outline" onClick={handleCancel}>
            <X size={18}/> Cancel
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleConfirm}
            disabled={confirming || holdings.length === 0}
          >
            {confirming ? (
              <>Saving...</>
            ) : (
              <><Save size={18}/> Confirm & Import</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-md" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)' }}>
          <p className="text-error mb-0 font-medium">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="glass-card flex flex-col items-center text-center justify-center py-6">
          <Calendar size={24} className="text-secondary mb-2" />
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-1">Statement Period</h3>
          <p className="text-base font-bold">
            {summary?.statement_period_start || "Start Date"} <br/>
            <span className="text-xs text-secondary font-normal">to</span> <br/>
            {summary?.statement_period_end || "End Date"}
          </p>
        </div>
        <div className="glass-card flex flex-col items-center text-center justify-center py-6 border-primary border">
          <Database size={24} className="text-primary mb-2" />
          <h3 className="text-sm font-semibold text-primary uppercase tracking-wider mb-1">New Transactions</h3>
          <p className="text-4xl font-bold text-primary">{summary?.transactions || 0}</p>
          <p className="text-xs text-secondary mt-1">Staged in preview</p>
        </div>
        <div className="glass-card flex flex-col items-center text-center justify-center py-6">
          <CheckCircle size={24} className="text-success mb-2" />
          <h3 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-1">Parsed Folios</h3>
          <p className="text-4xl font-bold text-success">{summary?.folios || 0}</p>
          <p className="text-xs text-secondary mt-1">Unique Folios</p>
        </div>
      </div>

      <div className="glass-card mb-8">
        <h2 className="text-xl mb-4 border-b border-slate-700 pb-3">Transaction Breakdown</h2>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 bg-slate-800/40 rounded-lg">
            <span className="text-xs text-secondary uppercase block mb-1">Purchases</span>
            <span className="text-lg font-bold text-success">{breakdown?.purchases || 0}</span>
          </div>
          <div className="p-3 bg-slate-800/40 rounded-lg">
            <span className="text-xs text-secondary uppercase block mb-1">Redemptions</span>
            <span className="text-lg font-bold text-error">{breakdown?.redemptions || 0}</span>
          </div>
          <div className="p-3 bg-slate-800/40 rounded-lg">
            <span className="text-xs text-secondary uppercase block mb-1">Switches</span>
            <span className="text-lg font-bold text-primary">{breakdown?.switches || 0}</span>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h2 className="text-xl mb-4 border-b border-slate-700 pb-3 flex justify-between">
          <span>Staged Scheme Valuations</span>
          <span className="text-sm text-secondary font-normal flex items-center gap-1">
            <Info size={14}/> Consolidated values from statement
          </span>
        </h2>
        
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Scheme</th>
                <th>Folios</th>
                <th className="text-right">Units</th>
                <th className="text-right">NAV</th>
                <th className="text-right">Valuation</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h, idx) => (
                <tr key={idx}>
                  <td>
                    <span className="font-medium text-slate-200">{h.scheme_name}</span>
                    <span className="text-xs text-secondary block mt-0.5">{h.isin ? `ISIN: ${h.isin}` : "No ISIN"}</span>
                  </td>
                  <td>
                    {h.folios.map((folio, fIdx) => (
                      <span key={fIdx} className="text-xs text-secondary block">
                        {folio}
                      </span>
                    ))}
                  </td>
                  <td className="text-right text-slate-200">{parseFloat(h.total_units).toFixed(3)}</td>
                  <td className="text-right text-slate-300">{h.nav ? `₹${parseFloat(h.nav).toFixed(4)}` : "-"}</td>
                  <td className="text-right font-bold text-primary">{formatCurrencyString(h.current_value)}</td>
                </tr>
              ))}
              {holdings.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-secondary py-8">
                    No holdings preview found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
