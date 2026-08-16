"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { uploadCAS, getImportStatus, getImportPreview, confirmImport } from "@/lib/api"
import { ImportSessionResponse, ImportPreview } from "@/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Upload, FileText, Lock, CheckCircle2, ArrowRight, Loader2, AlertCircle, RefreshCw } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function ImportPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [password, setPassword] = useState("")
  const [isUploading, setIsUploading] = useState(false)
  const [step, setStep] = useState(1) // 1: Upload, 2: Parsing, 3: Preview, 4: Success
  const [error, setError] = useState<string | null>(null)
  const [importSession, setImportSession] = useState<ImportSessionResponse | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [isConfirming, setIsConfirming] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setIsUploading(true)
    setError(null)
    
    try {
      const session = await uploadCAS(file, password || undefined)
      setImportSession(session)
      setStep(2)
      pollStatus(session.import_id)
    } catch (err: any) {
      setError(err.message || "Upload failed")
      setIsUploading(false)
    }
  }

  const pollStatus = async (importId: string) => {
    try {
      const statusRes = await getImportStatus(importId)
      
      if (statusRes.status === "FAILED") {
        setError(statusRes.error_message || "Parsing failed")
        setStep(1)
        setIsUploading(false)
        return
      }

      if (statusRes.status === "PREVIEW_READY") {
        const previewData = await getImportPreview(importId)
        setPreview(previewData)
        setStep(3)
        setIsUploading(false)
        return
      }

      // Keep polling
      setTimeout(() => pollStatus(importId), 2000)
    } catch (err: any) {
      setError(err.message || "Failed to check status")
      setStep(1)
      setIsUploading(false)
    }
  }

  const handleConfirm = async () => {
    if (!preview) return
    setIsConfirming(true)
    setError(null)
    
    try {
      await confirmImport(preview.import_id)
      setStep(4)
    } catch (err: any) {
      setError(err.message || "Failed to confirm import")
      setIsConfirming(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto mt-10 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload & Update</h1>
        <p className="text-muted-foreground">Upload your CAMS/KFintech Consolidated Account Statement (CAS) PDF to update your portfolio.</p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6">
        {step === 1 && (
          <Card className="border-border/50 shadow-sm transition-all hover:shadow-md">
            <CardHeader>
              <CardTitle>Select CAS PDF</CardTitle>
              <CardDescription>
                Ensure you are uploading a detailed CAS generated from CAMS or KFintech.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div 
                className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-10 flex flex-col items-center justify-center text-center bg-muted/30 hover:bg-muted/60 transition-colors cursor-pointer"
                onClick={() => document.getElementById('cas-upload')?.click()}
              >
                <Upload className="h-10 w-10 text-muted-foreground mb-4" />
                <h3 className="font-semibold text-lg mb-1">Click to upload or drag and drop</h3>
                <p className="text-sm text-muted-foreground">PDF files only (max 10MB)</p>
                <input 
                  id="cas-upload" 
                  type="file" 
                  accept=".pdf" 
                  className="hidden" 
                  onChange={handleFileChange}
                />
              </div>

              {file && (
                <div className="flex items-center gap-3 p-3 bg-card border rounded-md shadow-sm">
                  <FileText className="text-primary" />
                  <div className="flex-1 overflow-hidden">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="password">PDF Password (if encrypted)</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input 
                    id="password" 
                    type="password" 
                    placeholder="Enter password" 
                    className="pl-9" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Usually your PAN in uppercase.</p>
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full" 
                onClick={handleUpload} 
                disabled={!file || isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    Upload CAS
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        )}

        {step === 2 && (
          <Card className="border-border/50 shadow-sm">
            <CardContent className="p-16 flex flex-col items-center justify-center text-center space-y-6">
              <RefreshCw className="w-16 h-16 text-primary animate-spin" />
              <div>
                <h2 className="text-2xl font-semibold mb-2">Processing CAS...</h2>
                <p className="text-muted-foreground max-w-md">This may take a few moments. We are securely parsing your transactions and fetching the latest NAV data.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {step === 3 && preview && (
          <Card className="border-border/50 shadow-sm animate-fade-in">
            <CardHeader>
              <CardTitle>Review Import</CardTitle>
              <CardDescription>
                We found {preview.summary.transactions} transactions across {preview.summary.folios} folios. Please review before confirming.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-muted/30 border">
                  <p className="text-sm text-muted-foreground mb-1">Funds</p>
                  <p className="text-2xl font-semibold">{preview.summary.funds}</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/30 border">
                  <p className="text-sm text-muted-foreground mb-1">Folios</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-2xl font-semibold">{preview.summary.folios}</p>
                    <span className="text-xs text-muted-foreground">({preview.summary.new_folios} New, {preview.summary.existing_folios} Existing)</span>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-muted/30 border">
                  <p className="text-sm text-muted-foreground mb-1">Transactions</p>
                  <p className="text-2xl font-semibold">{preview.summary.transactions}</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/30 border">
                  <p className="text-sm text-muted-foreground mb-1">Total Value</p>
                  <p className="text-2xl font-semibold text-primary">₹{Number(preview.summary.total_current_value).toLocaleString('en-IN')}</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-3">Detected Assets (Grouped by Folio)</h3>
                <div className="border rounded-md bg-card overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-muted/50">
                        <TableHead>Scheme</TableHead>
                        <TableHead>Folio</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Units</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {preview.holdings.map((h, i) => (
                        <TableRow key={i} className={`hover:bg-muted/30 ${!h.is_new_investment ? 'opacity-70' : ''}`}>
                          <TableCell className="font-medium">{h.scheme_name}</TableCell>
                          <TableCell>
                            {h.folios.map(f => (
                              <Badge key={f} variant="outline" className="mr-1">{f}</Badge>
                            ))}
                          </TableCell>
                          <TableCell>
                            {h.is_new_investment ? (
                              <Badge className="bg-green-500/10 text-green-600 border-green-200">NEW INVESTMENT</Badge>
                            ) : (
                              <Badge variant="secondary" className="text-muted-foreground">ALREADY IMPORTED</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">{Number(h.total_units).toFixed(3)}</TableCell>
                          <TableCell className="text-right font-medium">₹{Number(h.current_value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex gap-4">
              <Button variant="outline" onClick={() => {setStep(1); setFile(null)}} disabled={isConfirming}>
                Cancel
              </Button>
              <Button onClick={handleConfirm} disabled={isConfirming} className="flex-1">
                {isConfirming ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Confirming...
                  </>
                ) : (
                  "Confirm & Import"
                )}
              </Button>
            </CardFooter>
          </Card>
        )}

        {step === 4 && (
          <Card className="border-green-500/50 shadow-sm animate-fade-in">
            <CardContent className="p-16 flex flex-col items-center justify-center text-center space-y-6">
              <div className="bg-green-500/10 p-4 rounded-full">
                <CheckCircle2 className="w-16 h-16 text-green-500" />
              </div>
              <div>
                <h2 className="text-2xl font-semibold mb-2">Portfolio Updated Successfully!</h2>
                <p className="text-muted-foreground max-w-md">Your CAS has been parsed and transactions have been added to your portfolio securely.</p>
              </div>
              <div className="mt-6 flex gap-4 w-full max-w-sm">
                <Button className="flex-1" onClick={() => router.push('/dashboard')}>View Dashboard</Button>
                <Button variant="outline" className="flex-1" onClick={() => {
                  setStep(1)
                  setFile(null)
                  setPassword("")
                  setImportSession(null)
                  setPreview(null)
                }}>Upload Another</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
