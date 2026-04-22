import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Zap, Shield, Users, BarChart3, ArrowRight, ChevronRight } from 'lucide-react'
import { useChatStore } from './store'
import { API_BASE } from './api'
import './LandingPage.css'

const FEATURES = [
  {
    icon: Shield,
    title: "Real-time Database Access",
    description: "All agents have direct PostgreSQL read access via MCP integration",
    color: "#f59e0b"
  },
  {
    icon: Zap,
    title: "Multi-Agent Orchestration",
    description: "Supervisor routes to 8 specialized agents based on request classification",
    color: "#06b6d4"
  },
  {
    icon: Users,
    title: "Human-in-the-Loop",
    description: "Critical operations require manager approval before execution",
    color: "#8b5cf6"
  },
  {
    icon: BarChart3,
    title: "Guardrail Pipeline",
    description: "Three-layer security: jailbreak detection, PII scanning, SQL injection prevention",
    color: "#22c55e"
  }
]

export default function EnhancedAuth() {
  const store = useChatStore()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [showFeatures, setShowFeatures] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/signup'
      const body = isLogin ? { email, password } : { email, password, name }
      const res = await fetch(API_BASE + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Auth failed')
      store.setUser({ email: data.email, name: data.name, token: data.access_token })
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="auth-container">
      {/* Background effects */}
      <div className="background-effects">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
        <div className="grid-pattern" />
      </div>

      <div className="auth-content">
        {/* Left side - Auth form */}
        <motion.div
          className="auth-form-section"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="auth-header">
            <div className="auth-logo">
              <div className="auth-logo-icon">
                <Zap size={24} />
              </div>
              <h2>Actuator AI</h2>
            </div>
            <p className="auth-subtitle">
              {isLogin ? 'Welcome back' : 'Create your account'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="auth-tabs">
              <button
                type="button"
                onClick={() => setIsLogin(true)}
                className={`auth-tab ${isLogin ? 'active' : ''}`}
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => setIsLogin(false)}
                className={`auth-tab ${!isLogin ? 'active' : ''}`}
              >
                Sign Up
              </button>
            </div>

            {!isLogin && (
              <div className="input-group">
                <input
                  type="text"
                  placeholder="Full Name"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  required
                  className="auth-input"
                />
              </div>
            )}

            <div className="input-group">
              <input
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="auth-input"
              />
            </div>

            <div className="input-group">
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="auth-input"
              />
            </div>

            {error && (
              <div className="auth-error">
                {error}
              </div>
            )}

            <motion.button
              type="submit"
              className="auth-submit-btn"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isLogin ? 'Log In' : 'Create Account'}
              <ArrowRight size={16} />
            </motion.button>
          </form>

          <button
            className="features-toggle"
            onClick={() => setShowFeatures(!showFeatures)}
          >
            {showFeatures ? 'Hide Features' : 'View Platform Features'}
            <ChevronRight size={16} />
          </button>
        </motion.div>

        {/* Right side - Features */}
        <motion.div
          className="auth-features-section"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <h3>Enterprise-Grade AI Support Platform</h3>

          <div className="auth-features-grid">
            {FEATURES.map((feature, index) => (
              <motion.div
                key={index}
                className="auth-feature-item"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <div
                  className="auth-feature-icon"
                  style={{
                    background: feature.color + '15',
                    borderColor: feature.color + '30'
                  }}
                >
                  {feature.icon && React.createElement(feature.icon, {
                    size: 20,
                    color: feature.color
                  })}
                </div>
                <div className="auth-feature-content">
                  <h4 style={{ color: feature.color }}>{feature.title}</h4>
                  <p>{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>

          {showFeatures && (
            <motion.div
              className="expanded-features"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
            >
              <h4>Additional Capabilities:</h4>
              <ul>
                <li>Real-time WebSocket communication</li>
                <li>Ollama local inference engine</li>
                <li>Complete audit and compliance tracking</li>
                <li>Multi-language support with linguistic analysis</li>
                <li>CRM and ticketing system integration</li>
              </ul>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}