import React from 'react'
import { motion } from 'framer-motion'
import { Cpu, Shield, Database, Zap, ArrowRight, Network, FileSearch } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import './LandingPage.css'

const CAPABILITIES = [
  {
    icon: Database,
    title: "Proprietary Data Integration",
    description: "Every agent we deploy can be fine-tuned or grounded using your company's private silos, CRM, and ERP data safely.",
    color: "#06b6d4"
  },
  {
    icon: Cpu,
    title: "Custom Agent Engineering",
    description: "Beyond our 8 core agents, we actively engineer specialized AI roles tailored to your exact business logic—HR, Legal, Sales, and Logistics.",
    color: "#6366f1"
  },
  {
    icon: Network,
    title: "Scalable Multi-Agent Clusters",
    description: "Need 50 specialized agents? Our supervisor routing architecture scales horizontally to accommodate entire virtual departments.",
    color: "#8b5cf6"
  },
  {
    icon: Shield,
    title: "Enterprise Compliance Framework",
    description: "All agents inherit our three-layer security guardrails. You focus on the prompt logic; we guarantee the data safety.",
    color: "#f59e0b"
  }
]

export default function Docs() {
  const navigate = useNavigate()
  return (
    <div className="landing-container" style={{ overflowY: 'auto', height: '100vh' }}>
      <div className="background-effects">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
        <div className="grid-pattern" />
      </div>

      <nav className="topbar" style={{ background: 'transparent', border: 'none', padding: '20px 5%' }}>
        <div className="logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
          <div className="logo-icon">
            <Zap size={18} />
          </div>
          <div className="logo-text">
            <div className="logo-name" style={{ color: 'var(--text-1)'}}>Actuator AI</div>
            <div className="logo-sub" style={{ color: 'var(--text-2)'}}>Documentation</div>
          </div>
        </div>
        <div className="hero-actions">
          <button className="secondary-button" style={{ padding: '8px 16px', fontSize: '14px' }} onClick={() => navigate('/login')}>
            Sign In
          </button>
        </div>
      </nav>

      <section className="hero-section" style={{ minHeight: '60vh', paddingTop: '40px' }}>
        <motion.div
          className="hero-content"
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
          style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}
        >
          <div className="hero-badge" style={{ margin: '0 auto 24px' }}>
            <FileSearch size={14} />
            <span>Platform Overview & Architecture</span>
          </div>

          <h1 className="hero-title">
            The Extensible <span className="gradient-text">Virtual Workforce</span>
          </h1>

          <p className="hero-description" style={{ fontSize: '1.25rem' }}>
            Actuator AI is not just a chatbot. It is a highly robust multi-agent orchestration platform designed for enterprise scale. We provide the infrastructure for an intelligent, integrated AI workforce.
          </p>
        </motion.div>
      </section>

      <section className="documentation-section" style={{ paddingTop: '40px', paddingBottom: '100px' }}>
        <div className="section-header">
          <h2 style={{ fontSize: '2rem' }}>Our Promise: Unlimited Expansion</h2>
          <p style={{ maxWidth: '700px' }}>
            While we ship with 8 highly-capable core agents, our true value lies in execution. We partner with enterprises to design, securely train, and deploy novel agents entirely customized to their operational needs. Let us build the automation layer your business actually needs.
          </p>
        </div>

        <div className="auth-features-grid" style={{ maxWidth: '1000px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '32px' }}>
          {CAPABILITIES.map((cap, index) => (
            <motion.div
              key={index}
              className="doc-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div
                className="feature-icon"
                style={{
                  background: cap.color + '15',
                  borderColor: cap.color + '30',
                  marginBottom: '20px',
                  width: '48px', height: '48px', borderRadius: '12px'
                }}
              >
                {cap.icon && React.createElement(cap.icon, {
                  size: 24,
                  color: cap.color
                })}
              </div>
              <h3 style={{ color: cap.color, fontSize: '1.25rem', marginBottom: '12px' }}>{cap.title}</h3>
              <p style={{ color: 'var(--text-2)', lineHeight: 1.6 }}>{cap.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="cta-section" style={{ background: 'transparent' }}>
        <motion.div
          className="cta-content"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h2 style={{ fontSize: '2rem' }}>Ready to Scale Your Operations?</h2>
          <p>
            Join visionary enterprises who leverage our multi-agent architecture as their operational backbone.
          </p>

          <button
            className="primary-button large"
            onClick={() => navigate('/login')}
          >
            Deploy Your Matrix
            <ArrowRight size={18} />
          </button>
        </motion.div>
      </section>
    </div>
  )
}
