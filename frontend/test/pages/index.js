import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

export default function Home() {
  const [authUrl, setAuthUrl] = useState('')
  const [loading, setLoading] = useState(true)
  const [authenticated, setAuthenticated] = useState(false)
  const router = useRouter()

  // Check if user is already authenticated
  useEffect(() => {
    async function checkAuth() {
      try {
        const response = await fetch('http://localhost:8000/api/auth/check', {
          method: 'GET',
          credentials: 'include',
        })
        const data = await response.json()
        
        if (data.authenticated) {
          setAuthenticated(true)
        } else {
          // Get the auth URL from the backend
          const urlResponse = await fetch('http://localhost:8000/api/auth/google-url', {
            method: 'GET',
            credentials: 'include',
          })
          const urlData = await urlResponse.json()
          setAuthUrl(urlData.auth_url)
          console.log("Auth URL:", urlData.auth_url)
        }
      } catch (error) {
        console.error('Error checking auth status:', error)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  // Handle logout
  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
      setAuthenticated(false)
      window.location.reload()
    } catch (error) {
      console.error('Error logging out:', error)
    }
  }

  if (loading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h1>AskIt Test App</h1>
      
      {authenticated ? (
        <>
          <p>You are logged in!</p>
          <button onClick={handleLogout}>Logout</button>
        </>
      ) : (
        <>
          <p>Please log in with Google to continue</p>
            <button onClick={() => window.open(authUrl, '_blank')}>
            Login with Google
          </button>
        </>
      )}
    </div>
  )
}