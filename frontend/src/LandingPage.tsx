import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, Sparkles, Shield, Zap, Users, BarChart3, Globe, ArrowRight, Database, UserCheck, Cpu, Network, FileSearch } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import './LandingPage.css'

const AGENT_FEATURES = [
  {
    icon: Shield,
    title: "Account Security",
    description: "Handle login issues, 2FA setup, account lockouts, and security events with precision",
    color: "#f59e0b"
  },
  {
    icon: Zap,
    title: "Technical Support",
    description: "Diagnose API errors, system status, and create support tickets with deep technical expertise",
    color: "#06b6d4"
  },
  {
    icon: Users,
    title: "Customer Success",
    description: "Monitor health scores, prevent churn, and create renewal offers to retain customers",
    color: "#8b5cf6"
  },
  {
    icon: BarChart3,
    title: "Billing & Finance",
    description: "Process invoices, refunds, plan changes, and credit applications with financial oversight",
    color: "#22c55e"
  },
  {
    icon: Globe,
    title: "Linguistic Analysis",
    description: "Detect language, translate text, analyze sentiment, and assess communication quality",
    color: "#0ea5e9"
  },
  {
    icon: Shield,
    title: "Audit & Compliance",
    description: "Check for hallucinations, policy compliance, and generate QA reports for quality assurance",
    color: "#ef4444"
  }
]

const TECH_STACK = [
  { name: "OpenAI Agents SDK", description: "Multi-agent orchestration" },
  { name: "FastAPI", description: "High-performance backend" },
  { name: "PostgreSQL", description: "Enterprise database" },
  { name: "MCP Integration", description: "Real-time database access" },
  { name: "React 19 + Vite", description: "Modern frontend" },
  { name: "Ollama", description: "Local inference engine" }
]

const FEATURE_ICONS = {
  database: Database,
  approval: UserCheck,
  shield: Shield,
  orchestrate: Network,
  ai: Cpu,
  audit: FileSearch
}

export default function LandingPage({ onGetStarted }: { onGetStarted: () => void }) {
  const [currentFeature, setCurrentFeature] = useState(0)
  const [, setIsVisible] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    setIsVisible(true)
    const interval = setInterval(() => {
      setCurrentFeature(prev => (prev + 1) % AGENT_FEATURES.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <motion.div
      ref={containerRef}
      className="landing-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      {/* Animated background elements */}
      <div className="background-effects">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
        <div className="grid-pattern" />
      </div>

      {/* Hero section */}
      <section className="hero-section">
        <motion.div
          className="hero-content"
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div className="hero-badge">
            <Sparkles size={14} />
            <span>Production-Grade Multi-Agent Platform</span>
          </div>

          <h1 className="hero-title">
            Automate Complex Support <span className="gradient-text">With Precision</span>
          </h1>

          <p className="hero-description">
            Empower your team with a coordinated virtual workforce. Actuator AI orchestrates specialized agents 
            to resolve technical, security, and billing crises in seconds, not hours.
          </p>

          <div className="hero-actions">
            <motion.button
              className="primary-button"
              onClick={onGetStarted}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Get Started
              <ArrowRight size={16} />
            </motion.button>

            <button className="secondary-button" onClick={() => navigate('/docs')}>
              View Documentation
              <ChevronRight size={16} />
            </button>
          </div>
        </motion.div>

        {/* Animated feature showcase */}
        <motion.div
          className="feature-showcase"
          initial={{ x: 50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={currentFeature}
              className="feature-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              style={{ borderColor: AGENT_FEATURES[currentFeature].color + '30' }}
            >
              <div
                className="feature-icon"
                style={{
                  background: AGENT_FEATURES[currentFeature].color + '15',
                  borderColor: AGENT_FEATURES[currentFeature].color + '30'
                }}
              >
                {AGENT_FEATURES[currentFeature].icon && React.createElement(AGENT_FEATURES[currentFeature].icon, {
                  size: 24,
                  color: AGENT_FEATURES[currentFeature].color
                })}
              </div>
              <h3 style={{ color: AGENT_FEATURES[currentFeature].color }}>
                {AGENT_FEATURES[currentFeature].title}
              </h3>
              <p>{AGENT_FEATURES[currentFeature].description}</p>
            </motion.div>
          </AnimatePresence>
        </motion.div>
      </section>

      {/* Features grid */}
      <section className="features-section">
        <div className="section-header">
          <h2>Enterprise-Grade Architecture</h2>
          <p>Built for scale, security, and seamless integration</p>
        </div>

        <div className="features-grid">
          {[
            {
              title: "Real-time Database Access",
              description: "All agents have direct PostgreSQL read access via MCP integration",
              icon: "database"
            },
            {
              title: "Human-in-the-Loop",
              description: "Critical operations require manager approval before execution",
              icon: "approval"
            },
            {
              title: "Guardrail Pipeline",
              description: "Three-layer security: jailbreak detection, PII scanning, SQL injection prevention",
              icon: "shield"
            },
            {
              title: "Multi-Agent Orchestration",
              description: "Supervisor routes to specialized agents based on request classification",
              icon: "orchestrate"
            },
            {
              title: "Local Inference",
              description: "Powered by Ollama with OpenAI-compatible API support",
              icon: "ai"
            },
            {
              title: "Audit & Compliance",
              description: "Complete conversation auditing and policy compliance checking",
              icon: "audit"
            }
          ].map((feature, index) => {
            const IconComponent = FEATURE_ICONS[feature.icon as keyof typeof FEATURE_ICONS]
            return (
              <motion.div
                key={index}
                className="feature-item"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <div className="feature-item-icon">
                  {IconComponent && React.createElement(IconComponent, { size: 24 })}
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </motion.div>
            )
          })}
        </div>
      </section>

      {/* Tech stack */}
      <section className="tech-section">
        <div className="section-header">
          <h2>Modern Technology Stack</h2>
          <p>Built with industry-leading tools and frameworks</p>
        </div>

        <div className="tech-grid">
          {TECH_STACK.map((tech, index) => (
            <motion.div
              key={index}
              className="tech-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <h3>{tech.name}</h3>
              <p>{tech.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Documentation section */}
      <section id="docs" className="documentation-section">
        <div className="section-header">
          <h2>Complete Customer Support Solution</h2>
          <p>Handle every aspect of customer support with our multi-agent platform</p>
        </div>

        <div className="documentation-grid">
          <div className="doc-card">
            <h3>🤖 8 Specialized Agents</h3>
            <p>From technical support to billing, security to success - each agent handles specific domains with expert knowledge</p>
            <ul>
              <li>Technical Specialist: API errors, system diagnostics</li>
              <li>Account Security: Login issues, 2FA setup</li>
              <li>Billing Finance: Invoices, refunds, plan changes</li>
              <li>Success Retention: Health scores, churn prevention</li>
            </ul>
          </div>

          <div className="doc-card">
            <h3>🛡️ Enterprise Security</h3>
            <p>Built-in guardrails and compliance measures for secure operations</p>
            <ul>
              <li>Jailbreak detection and prevention</li>
              <li>PII scanning (credit cards, SSN)</li>
              <li>SQL injection protection</li>
              <li>Complete audit logging</li>
            </ul>
          </div>

          <div className="doc-card">
            <h3>⚡ Real-time Performance</h3>
            <p>Lightning-fast responses with WebSocket streaming and local inference</p>
            <ul>
              <li>WebSocket-based streaming responses</li>
              <li>Ollama local inference engine</li>
              <li>Fresh MCP server per request</li>
              <li>Optimized database queries</li>
            </ul>
          </div>

          <div className="doc-card">
            <h3>🔧 Integration Ready</h3>
            <p>Seamlessly connect with your existing systems and workflows</p>
            <ul>
              <li>CRM system integration</li>
              <li>Jira ticket creation</li>
              <li>Support ticket management</li>
              <li>Custom tool development</li>
            </ul>
          </div>
        </div>
      </section>

      {/* CTA section */}
      <section className="cta-section">
        <motion.div
          className="cta-content"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h2>Ready to Transform Your Customer Support?</h2>
          <p>
            Join enterprises leveraging AI-powered multi-agent systems for
            scalable, secure, and intelligent customer interactions.
          </p>

          <motion.button
            className="primary-button large"
            onClick={onGetStarted}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Start Using Actuator AI
            <ArrowRight size={18} />
          </motion.button>
        </motion.div>
      </section>
    </motion.div>
  )
}