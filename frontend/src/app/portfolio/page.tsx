"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUserPortfolios } from "@/lib/api";
import { PortfolioSummary } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Briefcase, Plus, FolderOpen, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

export default function PortfolioIndexPage() {
  const router = useRouter();
  const [portfolios, setPortfolios] = useState<PortfolioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getUserPortfolios();
        setPortfolios(data);
      } catch (err: any) {
        setError(err.message || "Failed to load portfolios.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <p className="text-muted-foreground animate-pulse">Loading portfolios...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Your Portfolios</h1>
          <p className="text-muted-foreground">Select a family member's portfolio to view its details and assets.</p>
        </div>
        <Link href="/import">
          <Button className="flex items-center gap-2">
            <Plus size={16} /> Import New CAS
          </Button>
        </Link>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {portfolios.length === 0 && !error ? (
        <Card className="border-dashed border-2 bg-muted/30 mt-8">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div className="bg-primary/10 p-4 rounded-full">
              <FolderOpen className="w-10 h-10 text-primary" />
            </div>
            <h2 className="text-2xl font-semibold">No Portfolios Found</h2>
            <p className="text-muted-foreground max-w-md">
              You don't have any portfolios yet. Create a family member and import a CAS to get started.
            </p>
            <div className="flex gap-4 mt-4">
              <Link href="/profile">
                <Button variant="outline">Manage Family</Button>
              </Link>
              <Link href="/import">
                <Button>Import CAS</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mt-6">
          {portfolios.map((portfolio) => (
            <Card key={portfolio.id} className="group hover:shadow-md transition-all border-border/50 cursor-pointer overflow-hidden flex flex-col" onClick={() => router.push(`/portfolio/${portfolio.id}`)}>
              <div className="h-2 bg-primary/20 group-hover:bg-primary transition-colors"></div>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-2">
                    <Briefcase size={20} />
                  </div>
                  <Badge variant="outline" className="bg-background">Active</Badge>
                </div>
                <CardTitle className="text-xl">{portfolio.display_name}</CardTitle>
                <CardDescription>
                  {portfolio.folio_count} {portfolio.folio_count === 1 ? 'Folio' : 'Folios'} • {portfolio.transaction_count} Transactions
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="pt-4 border-t border-border/50 mt-2">
                  <p className="text-sm text-muted-foreground mb-1">Total Current Value</p>
                  <p className="text-2xl font-bold text-foreground">
                    {portfolio.total_current_value 
                      ? `₹${parseFloat(portfolio.total_current_value).toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0})}` 
                      : "₹0"}
                  </p>
                </div>
              </CardContent>
              <CardFooter className="bg-muted/30 py-3 flex justify-between items-center group-hover:bg-muted/50 transition-colors">
                <span className="text-sm font-medium text-primary">View details</span>
                <ArrowRight size={16} className="text-primary group-hover:translate-x-1 transition-transform" />
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
