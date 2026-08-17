import { createClient } from "@/utils/supabase/server";
import { cookies } from "next/headers";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Sidebar } from "@/components/sidebar";
import { Settings, User } from "lucide-react";
import Link from "next/link";
import { ModeToggle } from "@/components/mode-toggle";
import NotificationBell from "@/components/NotificationBell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "WealthNest Dashboard",
  description: "Family Mutual Fund Portfolio Management",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = cookies();
  const supabase = createClient(cookieStore);
  const { data: { session } } = await supabase.auth.getSession();

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          {session ? (
            <div className="min-h-screen bg-background text-foreground flex">
              <Sidebar />
              <div className="flex-1 md:ml-64 flex flex-col min-h-screen">
                <header className="h-16 border-b bg-card flex items-center justify-between px-6 sticky top-0 z-10">
                  <div className="flex items-center gap-4">
                    <h2 className="text-lg font-semibold tracking-tight">Overview</h2>
                  </div>
                  <div className="flex items-center gap-4">
                    <ModeToggle />
                    <NotificationBell />
                    <Link href="/settings" className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-full hover:bg-accent">
                      <Settings size={18} />
                    </Link>
                    <Link href="/profile" className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-primary/60 flex items-center justify-center text-sm font-bold text-primary-foreground ml-2 cursor-pointer hover:opacity-90 transition-opacity">
                      <User size={16} />
                    </Link>
                  </div>
                </header>
                <main className="flex-1 p-6 overflow-x-hidden">
                  {children}
                </main>
              </div>
            </div>
          ) : (
            <main className="min-h-screen bg-background">
              <header className="absolute top-0 w-full p-6 flex justify-between items-center z-50">
                <Link href="/" className="header-logo text-xl font-bold flex items-center gap-2">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-primary">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  WealthNest
                </Link>
                <ModeToggle />
              </header>
              {children}
            </main>
          )}
        </ThemeProvider>
      </body>
    </html>
  );
}
