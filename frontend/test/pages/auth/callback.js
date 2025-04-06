import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

export default function AuthCallback() {
  const router = useRouter()
  const [status, setStatus] = useState('Loading...')
  const [error, setError] = useState('')

  useEffect(() => {
    // Only run when router.query contains the needed parameters
    if (router.isReady && router.query.code) {
      handleCallback()
    }
  }, [router.isReady, router.query])

  const handleCallback = async () => {
    try {
      console.log('Query parameters:', router.query);
      
      // Extract query parameters
      const { code, state } = router.query
      
      if (!code || !state) {
        setError('Missing required parameters (code or state)')
        return
      }

      // Call the backend endpoint to handle the OAuth code exchange
      // For this specific backend endpoint, we need to use POST method
      // but send code and state as query parameters
      console.log('Sending auth code:', code.substring(0, 10) + '...');
      console.log('Sending state:', state);
      
      // Build the URL with query parameters
      const callbackUrl = new URL('http://localhost:8000/api/auth/google-callback');
      callbackUrl.searchParams.append('code', code);
      callbackUrl.searchParams.append('state', state);
      
      console.log('Full callback URL:', callbackUrl.toString());
      
      const response = await fetch(callbackUrl.toString(), {
        method: 'POST',  // Use POST as the backend expects
        credentials: 'include',
      })

      let data
      try {
        const text = await response.text()
        console.log('Raw response:', text)
        try {
          data = JSON.parse(text)
          console.log('Parsed data:', data)
        } catch (parseError) {
          console.error('Error parsing JSON:', parseError)
          setError(`Error parsing response: ${text}`)
          return
        }
      } catch (textError) {
        console.error('Error getting response text:', textError)
        setError('Error reading response')
        return
      }

      if (response.ok) {
        setStatus('Authentication successful!')
        // Redirect to home page after a short delay
        setTimeout(() => {
          // Redirect to home page after a short delay
          window.open("http://localhost:3000/", '_self');
        }, 1500)
      } else {
        // Handle various error formats
        let errorMessage = 'Unknown error';
        
        if (data) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (typeof data.detail === 'object') {
            errorMessage = JSON.stringify(data.detail);
          } else if (data.message) {
            errorMessage = data.message;
          } else if (data.error) {
            errorMessage = data.error;
          }
        }
        
        if (errorMessage.includes('Invalid or expired state parameter')) {
          // Special handling for expired state
          setError(
            'Authentication session has expired or the server was restarted. ' +
            'Please try logging in again.'
          );
          
          // Add a button to go back to login
          setTimeout(() => {
            router.push('/');
          }, 3000);
        } else {
          console.error('Authentication failed:', errorMessage);
          setError(`Authentication failed: ${errorMessage}`);
        }
      }
    } catch (err) {
      console.error('Error in authentication callback:', err)
      setError(`Error: ${err.message}`)
    }
  }

  if (error) {
    return (
      <div>
        <h1>Authentication Error</h1>
        <p>{error}</p>
        <div>
          <h3>Debug Info:</h3>
          <p>Query Parameters: {JSON.stringify(router.query)}</p>
        </div>
        <div style={{ marginTop: '20px' }}>
          <button onClick={() => router.push('/')}>Back to Home</button>
          {' | '}
          <button onClick={() => window.location.reload()}>Retry</button>
          {' | '}
          <Link href="/test-auth">Try Manual Test</Link>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1>Google Auth Callback</h1>
      <p>{status}</p>
    </div>
  )
}