import Link from 'next/link';
import { ArrowLeft, Lock, Mail, User, TrendingUp } from 'lucide-react';
import { signup } from '@/app/actions/auth';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

export default function SignupPage({ searchParams }: { searchParams: { error?: string } }) {
  return (
    <div className="min-h-screen flex bg-background text-foreground relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute bottom-[0%] -right-[10%] w-[40%] h-[40%] rounded-full bg-blue-500/5 blur-[100px]" />
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-8 z-10 relative">
        <div className="w-full max-w-[420px] animate-fade-in-up">
          <Link href="/" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary mb-8 transition-colors group">
            <ArrowLeft size={16} className="mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Home
          </Link>
          
          <Card className="border-border/40 bg-card/60 backdrop-blur-xl shadow-2xl shadow-primary/5">
            <CardHeader className="text-center space-y-3 pb-6">
              <div className="mx-auto w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center mb-2 text-primary border border-primary/20">
                <TrendingUp size={24} />
              </div>
              <CardTitle className="text-3xl font-bold tracking-tight">Create Account</CardTitle>
              <CardDescription className="text-base">Join WealthNest to start managing your family&apos;s mutual funds</CardDescription>
            </CardHeader>

            <CardContent>
              {searchParams?.error && (
                <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm text-center animate-shake">
                  {searchParams.error}
                </div>
              )}

              <form action={signup} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none transition-colors group-focus-within:text-primary text-muted-foreground">
                      <User size={18} />
                    </div>
                    <Input 
                      id="name"
                      name="name"
                      type="text" 
                      className="pl-10 h-11 bg-background/50 border-border/50 focus:bg-background transition-colors" 
                      placeholder="John Doe" 
                      required 
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none transition-colors group-focus-within:text-primary text-muted-foreground">
                      <Mail size={18} />
                    </div>
                    <Input 
                      id="email"
                      name="email"
                      type="email" 
                      className="pl-10 h-11 bg-background/50 border-border/50 focus:bg-background transition-colors" 
                      placeholder="you@example.com" 
                      required 
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none transition-colors group-focus-within:text-primary text-muted-foreground">
                      <Lock size={18} />
                    </div>
                    <Input 
                      id="password"
                      name="password"
                      type="password" 
                      className="pl-10 h-11 bg-background/50 border-border/50 focus:bg-background transition-colors" 
                      placeholder="••••••••" 
                      required 
                      minLength={6}
                    />
                  </div>
                </div>

                <Button type="submit" className="w-full h-11 text-base font-medium shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all">
                  Create Account
                </Button>
              </form>
            </CardContent>

            <CardFooter className="flex justify-center border-t border-border/40 pt-6">
              <p className="text-sm text-muted-foreground">
                Already have an account?{' '}
                <Link href="/login" className="text-primary hover:underline font-medium transition-colors">
                  Log In
                </Link>
              </p>
            </CardFooter>
          </Card>
        </div>
      </div>
      
      {/* Right side illustration/branding area */}
      <div className="hidden lg:flex flex-1 bg-muted/30 border-l border-border/50 items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-bl from-primary/5 via-transparent to-transparent pointer-events-none" />
        <div className="max-w-md space-y-6 text-center z-10">
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="bg-background p-6 rounded-2xl shadow-sm border border-border/50">
              <div className="text-2xl font-bold text-primary mb-1">Upload</div>
              <div className="text-sm text-muted-foreground">Any CAMS/KFintech CAS PDF in seconds.</div>
            </div>
            <div className="bg-background p-6 rounded-2xl shadow-sm border border-border/50">
              <div className="text-2xl font-bold text-primary mb-1">Track</div>
              <div className="text-sm text-muted-foreground">Multiple family portfolios automatically.</div>
            </div>
          </div>
          <h2 className="text-3xl font-bold tracking-tight">The Modern Way to <br/>Manage Wealth.</h2>
        </div>
      </div>
    </div>
  );
}
