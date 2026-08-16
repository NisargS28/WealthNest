"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { User, Mail, LogOut, Shield, Plus, Loader2, Users } from "lucide-react"
import { getMembers } from "@/lib/api"
import { FamilyMember } from "@/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { createClient } from "@/utils/supabase/client"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null)
  const [members, setMembers] = useState<FamilyMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [newMemberName, setNewMemberName] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    async function loadProfile() {
      try {
        const supabase = createClient()
        const { data: { user } } = await supabase.auth.getUser()
        setUser(user)
        
        const membersData = await getMembers()
        setMembers(membersData)
      } catch (err: any) {
        setError(err.message || "Failed to load profile")
      } finally {
        setLoading(false)
      }
    }
    loadProfile()
  }, [])

  const handleCreateMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMemberName.trim()) return
    
    setIsCreating(true)
    setCreateError(null)
    
    try {
      // POST to /api/members
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      const res = await fetch("/api/members", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({ display_name: newMemberName })
      })
      
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Failed to create member")
      }
      
      const newMember = await res.json()
      setMembers([...members, newMember])
      setNewMemberName("")
    } catch (err: any) {
      setCreateError(err.message)
    } finally {
      setIsCreating(false)
    }
  }

  const handleSignOut = async () => {
    try {
      const supabase = createClient()
      await supabase.auth.signOut()
      router.push('/login')
      router.refresh()
    } catch (err: any) {
      console.error("Logout failed", err)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <p className="text-muted-foreground animate-pulse">Loading profile...</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-8 animate-fade-in">
      <h1 className="text-3xl font-bold tracking-tight mb-8">Account & Family</h1>
      
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Profile Card */}
        <Card className="border-border/50 shadow-sm h-fit">
          <CardHeader>
            <CardTitle>Your Profile</CardTitle>
            <CardDescription>Manage your primary account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4 pb-6 border-b border-border/50">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                <User size={32} />
              </div>
              <div>
                <h2 className="text-xl font-bold">{user?.user_metadata?.name || 'User'}</h2>
                <p className="text-muted-foreground flex items-center gap-2 text-sm mt-1">
                  <Mail size={14} /> {user?.email}
                </p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-muted-foreground">Account ID</span>
                <span className="font-mono text-xs text-muted-foreground bg-muted px-2 py-1 rounded">{user?.id}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-muted-foreground">Security</span>
                <span className="flex items-center gap-1 text-green-500 text-sm"><Shield size={14}/> Password Enabled</span>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button onClick={handleSignOut} variant="outline" className="w-full text-red-500 hover:text-red-600 hover:bg-red-500/10 border-red-200 dark:border-red-500/30">
              <LogOut size={18} className="mr-2" /> Sign Out
            </Button>
          </CardFooter>
        </Card>

        {/* Family Card */}
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Users size={20} className="text-primary"/> Family Members</CardTitle>
            <CardDescription>Manage family members and their portfolios</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              {members.length === 0 ? (
                <div className="text-sm text-muted-foreground py-4 text-center border border-dashed rounded-lg bg-muted/20">
                  No family members found.
                </div>
              ) : (
                members.map((member) => (
                  <div key={member.id} className="flex justify-between items-center p-3 border rounded-lg hover:bg-muted/30 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-semibold text-sm">
                        {member.display_name.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium">{member.display_name}</span>
                    </div>
                    <Badge variant="outline" className="text-xs font-normal">Active</Badge>
                  </div>
                ))
              )}
            </div>

            <div className="pt-4 border-t">
              <h3 className="text-sm font-medium mb-3">Add New Member</h3>
              {createError && (
                <Alert variant="destructive" className="mb-3 py-2 px-3 text-sm">
                  <AlertDescription>{createError}</AlertDescription>
                </Alert>
              )}
              <form onSubmit={handleCreateMember} className="flex gap-2">
                <Input 
                  placeholder="Enter name (e.g. Spouse, Child)" 
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  disabled={isCreating}
                  className="flex-1"
                />
                <Button type="submit" disabled={!newMemberName.trim() || isCreating}>
                  {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4 mr-1" />}
                  Add
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
