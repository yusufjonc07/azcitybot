import { createFileRoute, redirect } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  beforeLoad: async () => {
    // Check if user is admin and redirect to chat page
    const token = localStorage.getItem("access_token")
    if (token) {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        if (response.ok) {
          const user = await response.json()
          // Check if user is admin (is_superuser flag)
          if (user.is_superuser) {
            throw redirect({ to: "/chat" })
          }
        }
      } catch (e) {
        // If it's a redirect, throw it
        if ((e as any)?.to) {
          throw e
        }
        // Otherwise ignore errors and show dashboard
      }
    }
  },
  head: () => ({
    meta: [
      {
        title: "Dashboard - AzCity CRM",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  // For regular users, redirect to support page
  if (currentUser && !currentUser.is_superuser) {
    return <UserDashboard user={currentUser} />
  }

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Hi, {currentUser?.full_name || (currentUser?.username ? `@${currentUser.username}` : "User")} 👋
        </h1>
        <p className="text-muted-foreground">
          Welcome back, nice to see you again!!!
        </p>
      </div>
    </div>
  )
}

// Simple dashboard for regular users
function UserDashboard({ user }: { user: any }) {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2">
          Welcome, {user?.full_name || (user?.username ? `@${user.username}` : "User")} 👋
        </h1>
        <p className="text-muted-foreground">
          How can we help you today?
        </p>
      </div>

      <div className="grid gap-4">
        <a
          href="/support"
          className="block p-6 rounded-lg border bg-card hover:bg-accent transition-colors"
        >
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-primary"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-lg">Contact Support</h3>
              <p className="text-sm text-muted-foreground">
                Chat with our support team for assistance
              </p>
            </div>
          </div>
        </a>
      </div>
    </div>
  )
}
