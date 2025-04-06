'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSearchService } from '@/services/SearchService';

export default function AuthCallback() {
  const router = useRouter();
  const searchService = useSearchService();

  useEffect(() => {
    // Function to process the OAuth callback
    const processAuth = async () => {
      try {
        // Get code and state from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');

        if (!code || !state) {
          console.error('Missing authentication parameters');
          router.push('/');
          return;
        }

        // Send code and state to your backend
        await searchService.handleOAuthCallback(code, state);
        
        // Redirect back to main page
        router.push('/');
      } catch (error) {
        console.error('Authentication error:', error);
        router.push('/');
      }
    };

    processAuth();
  }, [router, searchService]);

  // Minimal UI while processing
  return (
    <div className="min-h-screen flex items-center justify-center">
      <p>Processing authentication...</p>
    </div>
  );
}