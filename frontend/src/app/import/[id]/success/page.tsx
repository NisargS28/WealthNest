"use client";

import { useRouter } from "next/navigation";

export default function SuccessPage({ params }: { params: { id: string } }) {
  const router = useRouter();

  return (
    <div className="container flex justify-center items-center" style={{ minHeight: "70vh" }}>
      <div className="glass-card text-center p-12 max-w-lg w-full animate-fade-in">
        <div className="mx-auto w-20 h-20 bg-success bg-opacity-20 rounded-full flex items-center justify-center mb-6" style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        
        <h1 className="mb-2">Import Successful</h1>
        <p className="text-secondary mb-8">
          The CAS data has been successfully imported and persisted to your database.
        </p>
        
        <div className="flex flex-col gap-3">
          <button className="btn btn-primary" onClick={() => router.push("/")}>
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
