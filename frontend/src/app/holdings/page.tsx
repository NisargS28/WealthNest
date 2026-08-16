"use client"

import { useEffect, useState } from "react"
import { getHoldings } from "@/lib/api"
import { HoldingDetail } from "@/types"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Loader2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function HoldingsPage() {
  const [holdings, setHoldings] = useState<HoldingDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchHoldings() {
      try {
        const data = await getHoldings()
        setHoldings(data)
      } catch (err: any) {
        setError(err.message || "Failed to load holdings")
      } finally {
        setLoading(false)
      }
    }
    fetchHoldings()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <p className="text-muted-foreground animate-pulse">Loading your holdings...</p>
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

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Current Holdings</h1>
        <p className="text-muted-foreground">A detailed breakdown of all active mutual fund holdings in your portfolio.</p>
      </div>

      <div className="border rounded-md bg-card shadow-sm">
        {holdings.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No holdings found. Import a CAS statement to get started.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[300px]">Scheme Name</TableHead>
                <TableHead>Folio</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Units</TableHead>
                <TableHead className="text-right">NAV</TableHead>
                <TableHead className="text-right">Invested</TableHead>
                <TableHead className="text-right">Current Value</TableHead>
                <TableHead className="text-right">Returns</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {holdings.map((holding) => (
                <TableRow key={holding.id} className="transition-colors hover:bg-muted/50">
                  <TableCell className="font-medium">
                    {holding.scheme_name}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{holding.folio_number}</TableCell>
                  <TableCell>
                    {holding.category && (
                      <Badge variant="outline" className="font-normal text-xs bg-muted/20">
                        {holding.category}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">{Number(holding.units).toFixed(3)}</TableCell>
                  <TableCell className="text-right">₹{Number(holding.nav).toFixed(2)}</TableCell>
                  <TableCell className="text-right">₹{Number(holding.invested).toLocaleString('en-IN')}</TableCell>
                  <TableCell className="text-right font-medium">₹{Number(holding.current_value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</TableCell>
                  <TableCell className={`text-right font-bold ${Number(holding.returns) > 0 ? "text-green-500" : Number(holding.returns) < 0 ? "text-red-500" : ""}`}>
                    {Number(holding.returns) > 0 ? "+" : ""}{Number(holding.returns).toFixed(2)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}
