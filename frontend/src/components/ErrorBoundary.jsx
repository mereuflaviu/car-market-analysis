import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen bg-white flex items-center justify-center px-6">
          <div className="max-w-md text-center">
            <div className="text-6xl font-black text-black mb-4">!</div>
            <h1 className="text-2xl font-bold text-black mb-2">Something went wrong</h1>
            <p className="text-as-body text-sm mb-6">
              An unexpected error occurred. Refresh the page or go back to the dashboard.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                className="btn-primary"
                onClick={() => window.location.reload()}
              >
                Refresh page
              </button>
              <a href="/app" className="btn-secondary">
                Dashboard
              </a>
            </div>
            {import.meta.env.DEV && (
              <pre className="mt-6 text-left text-xs bg-[#f9f9f9] border border-[#e8e8e8] rounded-lg p-4 overflow-auto text-red-600">
                {this.state.error?.toString()}
              </pre>
            )}
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
