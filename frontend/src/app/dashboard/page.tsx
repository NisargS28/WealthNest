"use client"

import { useEffect, useState } from "react"
import { getDashboard } from "@/lib/api"
import { DashboardResponse } from "@/types"
import { StatCard } from "@/components/stat-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { IndianRupee, TrendingUp, Wallet, Activity, AlertCircle, Loader2 } from "lucide-react"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, PieChart, Pie, Cell } from "recharts"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        const dashboardData = await getDashboard()
        setData(dashboardData)
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard data")
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <p className="text-muted-foreground animate-pulse">Loading your portfolio data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!data || Number(data.total_invested) === 0) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back! Here&apos;s an overview of your mutual fund portfolio.</p>
        </div>
        <Card className="border-dashed border-2 bg-muted/30">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div className="bg-primary/10 p-4 rounded-full">
              <Wallet className="w-10 h-10 text-primary" />
            </div>
            <h2 className="text-2xl font-semibold">No Portfolio Data</h2>
            <p className="text-muted-foreground max-w-md">
              You haven&apos;t imported any CAS data yet. Head over to the Import section to upload your first Consolidated Account Statement.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const formatCurrency = (val: string | number) => `₹${Number(val).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  const formatLakhs = (val: string | number) => `₹${(Number(val) / 100000).toFixed(1)}L`;
  const formatPercent = (val: string | number) => `${Number(val).toFixed(2)}%`;

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back! Here&apos;s an overview of your mutual fund portfolio.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Current Value"
          value={formatCurrency(data.total_value)}
          icon={<IndianRupee size={20} />}
          description={`${Number(data.profit_loss) >= 0 ? '+' : ''}${formatCurrency(data.profit_loss)} (${formatPercent(data.profit_percentage)})`}
          trend={Number(data.profit_loss) >= 0 ? "up" : "down"}
        />
        <StatCard
          title="Total Invested"
          value={formatCurrency(data.total_invested)}
          icon={<Wallet size={20} />}
          description={`Across ${data.top_holdings.length} schemes`}
          trend="neutral"
        />
        <StatCard
          title="Profit / Loss"
          value={formatCurrency(data.profit_loss)}
          icon={<Activity size={20} />}
          description="Overall return"
          trend={Number(data.profit_loss) >= 0 ? "up" : "down"}
        />
        <StatCard
          title="Portfolios"
          value={data.portfolio_count.toString()}
          icon={<TrendingUp size={20} />}
          description="Family members"
          trend="neutral"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-7 lg:grid-cols-7">
        <Card className="md:col-span-4 lg:col-span-5 border-border/50 shadow-sm transition-all hover:shadow-md">
          <CardHeader>
            <CardTitle>Portfolio Growth</CardTitle>
            <CardDescription>Value vs Invested amount history</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            {data.valuation_history && data.valuation_history.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.valuation_history} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorInvested" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--muted-foreground))" stopOpacity={0.1} />
                      <stop offset="95%" stopColor="hsl(var(--muted-foreground))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="month" 
                    stroke="hsl(var(--muted-foreground))" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false} 
                  />
                  <YAxis 
                    stroke="hsl(var(--muted-foreground))" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={formatLakhs}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "hsl(var(--card))", borderColor: "hsl(var(--border))", borderRadius: "8px" }}
                    itemStyle={{ color: "hsl(var(--foreground))" }}
                    formatter={(value: any) => formatLakhs(value)}
                  />
                  <Area type="monotone" dataKey="invested" stroke="hsl(var(--muted-foreground))" fillOpacity={1} fill="url(#colorInvested)" />
                  <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorValue)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg bg-muted/10">
                <Activity className="h-10 w-10 mb-2 opacity-20" />
                <p>Not enough history data available to chart.</p>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card className="md:col-span-3 lg:col-span-2 border-border/50 shadow-sm transition-all hover:shadow-md">
          <CardHeader>
            <CardTitle>Asset Allocation</CardTitle>
            <CardDescription>Distribution across asset classes</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center h-[300px]">
            {data.asset_allocation && data.asset_allocation.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.asset_allocation}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {data.asset_allocation.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: "hsl(var(--card))", borderColor: "hsl(var(--border))", borderRadius: "8px" }}
                    formatter={(value: any) => formatCurrency(value)}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-full h-full flex items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg bg-muted/10">
                <p>No allocation data.</p>
              </div>
            )}
          </CardContent>
          {data.asset_allocation && data.asset_allocation.length > 0 && (
            <div className="flex flex-wrap justify-center gap-4 pb-6 text-sm text-muted-foreground px-4">
              {data.asset_allocation.map((entry, index) => (
                <div key={index} className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                  <span>{entry.name}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
