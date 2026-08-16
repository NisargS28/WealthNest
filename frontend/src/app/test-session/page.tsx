'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/utils/supabase/client';

export default function TestSessionPage() {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession()
      .then(({ data, error }) => {
        if (error) {
          setError(error.message);
        } else {
          setSession(data.session);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Client-side Session Test</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}
      {!loading && !error && (
        <div>
          <p>Session exists: {session ? 'YES' : 'NO'}</p>
          {session && (
            <pre className="bg-slate-800 p-4 rounded mt-4 overflow-auto max-w-full text-xs">
              {JSON.stringify({
                user: session.user.email,
                expires_at: session.expires_at,
                access_token_prefix: session.access_token.substring(0, 15) + '...'
              }, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
