import React, { useState } from 'react';

export default function TestAuth() {
  const [code, setCode] = useState('');
  const [state, setState] = useState('');
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult('');
    setError('');

    try {
      console.log('Sending code and state:', { code, state });

      // For this specific backend endpoint, we need to use POST method
      // but send parameters in the query string
      const callbackUrl = new URL('http://localhost:8000/api/auth/google-callback');
      callbackUrl.searchParams.append('code', code);
      callbackUrl.searchParams.append('state', state);

      console.log('Full callback URL:', callbackUrl.toString());

      const response = await fetch(callbackUrl.toString(), {
        method: 'POST',  // Use POST as the backend expects
        credentials: 'include',
      });

      const text = await response.text();
      console.log('Raw response:', text);

      try {
        const data = JSON.parse(text);
        console.log('Parsed response:', data);
        
        if (response.ok) {
          setResult(JSON.stringify(data, null, 2));
        } else {
          setError(`Error: ${data.detail || 'Unknown error'}`);
        }
      } catch (e) {
        setError(`Error parsing response: ${text}`);
      }
    } catch (e) {
      setError(`Fetch error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Test Auth Callback</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>
            Authorization Code:
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={{ width: '100%', marginTop: '5px' }}
              required
            />
          </label>
        </div>
        <div style={{ marginTop: '10px' }}>
          <label>
            State:
            <input
              type="text"
              value={state}
              onChange={(e) => setState(e.target.value)}
              style={{ width: '100%', marginTop: '5px' }}
              required
            />
          </label>
        </div>
        <button 
          type="submit" 
          disabled={loading}
          style={{ marginTop: '10px' }}
        >
          {loading ? 'Submitting...' : 'Submit'}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: '20px' }}>
          <h2>Success Result:</h2>
          <pre>{result}</pre>
        </div>
      )}

      {error && (
        <div style={{ marginTop: '20px', color: 'red' }}>
          <h2>Error:</h2>
          <pre>{error}</pre>
        </div>
      )}
    </div>
  );
}