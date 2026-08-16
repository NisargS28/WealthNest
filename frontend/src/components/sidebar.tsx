import Link from "next/link";
import { 
  LayoutDashboard, 
  PieChart, 
  ArrowRightLeft, 
  BarChart3, 
  Calculator, 
  Upload 
} from "lucide-react";

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-card hidden md:flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6">
        <Link href="/dashboard" className="flex items-center gap-2 font-bold text-xl">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-primary">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          WealthNest
        </Link>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4">
        <Link href="/dashboard" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent text-accent-foreground transition-colors">
          <LayoutDashboard size={18} />
          Dashboard
        </Link>
        <Link href="/holdings" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent text-muted-foreground hover:text-accent-foreground transition-colors">
          <PieChart size={18} />
          Current Holdings
        </Link>
        <Link href="/transactions" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent text-muted-foreground hover:text-accent-foreground transition-colors">
          <ArrowRightLeft size={18} />
          Transactions
        </Link>
        <Link href="/analysis" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent text-muted-foreground hover:text-accent-foreground transition-colors">
          <BarChart3 size={18} />
          Analysis
        </Link>
        <Link href="/capital-gains" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent text-muted-foreground hover:text-accent-foreground transition-colors">
          <Calculator size={18} />
          Capital Gains
        </Link>
        <Link href="/import" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent text-muted-foreground hover:text-accent-foreground transition-colors">
          <Upload size={18} />
          Upload & Update
        </Link>
        <Link href="/profile" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent text-muted-foreground hover:text-accent-foreground transition-colors">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-user"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          Account & Family
        </Link>
      </nav>
      
      <div className="p-4 border-t">
        <div className="text-xs text-muted-foreground text-center">
          WealthNest v0.4
        </div>
      </div>
    </aside>
  );
}
