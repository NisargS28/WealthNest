"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUserPortfolios } from "@/lib/api";

export default function PortfolioRedirectPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUserPortfolios()
      .then((portfolios) => {
        if (portfolios && portfolios.length > 0) {
          // Redirect to the first (default) portfolio
          router.replace(`/portfolio/${portfolios[0].id}`);
        } else {
          // No portfolio found, redirect to import
          router.replace("/import");
        }
      })
      .catch((err) => {
        setError(err.message || "Failed to load portfolio details.");
      });
  }, [router]);

  if (error) {
    return (
      <div className="container py-10">
        <div className="glass-card p-6 border-error border">
          <h3 className="text-xl font-bold text-error mb-2">Error Loading Portfolio</h3>
          <p className="text-secondary">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container flex flex-col justify-center items-center py-20">
      <div className="spinner mb-4"></div>
      <p className="text-secondary">Redirecting to your portfolio...</p>
    </div>
  );
}
