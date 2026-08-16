import Link from 'next/link';
import { ArrowRight, ShieldCheck, PieChart, Users, TrendingUp } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background blobs for premium feel */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-success/20 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="container max-w-5xl px-6 py-20 z-10 text-center animate-fade-in">
        <div className="inline-block px-4 py-1.5 rounded-full bg-slate-800/50 border border-slate-700 text-sm font-medium text-primary mb-8 animate-slide-up">
          <span className="text-white">🚀 Introducing WealthNest</span> — Family Portfolio Management
        </div>
        
        <h1 className="text-6xl md:text-7xl font-extrabold tracking-tight mb-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          Unify Your Family's <br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-success">
            Mutual Fund Wealth
          </span>
        </h1>
        
        <p className="text-xl text-secondary max-w-2xl mx-auto mb-10 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          Stop managing investments in silos. Seamlessly import CAMS/KFintech CAS statements, aggregate portfolios across family members, and track real-time NAVs in one beautiful dashboard.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <Link href="/login" className="btn btn-primary px-8 py-4 text-lg w-full sm:w-auto shadow-[0_0_20px_rgba(var(--primary-rgb),0.4)]">
            Log In
          </Link>
          <Link href="/signup" className="btn btn-outline px-8 py-4 text-lg w-full sm:w-auto flex items-center gap-2 group">
            Create an Account <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform"/>
          </Link>
        </div>

        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8 text-left animate-slide-up" style={{ animationDelay: '0.5s' }}>
          <div className="glass-card p-6 border-t-4 border-t-primary">
            <PieChart className="text-primary mb-4" size={32}/>
            <h3 className="text-xl font-bold mb-2 text-slate-100">Automated Parsing</h3>
            <p className="text-secondary text-sm">Upload your detailed CAS statements. We extract, normalize, and validate every transaction instantly.</p>
          </div>
          <div className="glass-card p-6 border-t-4 border-t-success">
            <Users className="text-success mb-4" size={32}/>
            <h3 className="text-xl font-bold mb-2 text-slate-100">Family Aggregation</h3>
            <p className="text-secondary text-sm">Group individual portfolios into a unified household view. See exactly who owns what and understand collective asset allocation.</p>
          </div>
          <div className="glass-card p-6 border-t-4 border-t-warning">
            <TrendingUp className="text-warning mb-4" size={32}/>
            <h3 className="text-xl font-bold mb-2 text-slate-100">Real-Time NAVs</h3>
            <p className="text-secondary text-sm">Our valuation engine fetches daily mutual fund NAVs automatically, giving you the true current value of your investments.</p>
          </div>
        </div>

        <div className="mt-20 flex items-center justify-center gap-2 text-sm text-secondary animate-fade-in" style={{ animationDelay: '0.8s' }}>
          <ShieldCheck size={16} className="text-success"/>
          <span>Bank-grade security. Read-only parsing. Your data is private.</span>
        </div>
      </div>
    </div>
  );
}
