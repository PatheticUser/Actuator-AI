import { motion } from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  Check,
  ChevronRight,
  Cpu,
  Database,
  FileCheck2,
  LockKeyhole,
  Network,
  Play,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import './LandingPage.css'

const HIGHLIGHTS = [
  { icon: Network, title: 'Route every request', text: 'A supervisor agent coordinates specialists so every issue reaches the right expert.' },
  { icon: ShieldCheck, title: 'Keep control', text: 'Guardrails, audit trails, and human approval protect high-impact actions.' },
  { icon: BarChart3, title: 'See the impact', text: 'Track resolution speed, agent health, and operational outcomes in one place.' },
]

const AGENTS = [
  ['Technical', 'Resolve incidents and API issues', '#22d3ee'],
  ['Security', 'Protect accounts and access', '#f59e0b'],
  ['Billing', 'Handle invoices and plans', '#34d399'],
  ['Success', 'Keep customers moving forward', '#a78bfa'],
]

export default function LandingPage({ onGetStarted }: { onGetStarted: () => void }) {
  const navigate = useNavigate()

  return (
    <main className="landing-container">
      <div className="background-effects" aria-hidden="true">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="grid-pattern" />
      </div>

      <nav className="landing-nav" aria-label="Primary navigation">
        <button className="brand-lockup" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Actuator AI home">
          <span className="brand-mark"><Zap size={17} /></span>
          <span><strong>Actuator</strong><small>AI operations</small></span>
        </button>
        <div className="landing-nav-links">
          <a href="#platform">Platform</a>
          <a href="#security">Security</a>
          <a href="#teams">Teams</a>
          <button className="nav-signin" onClick={() => navigate('/login')}>Sign in</button>
          <button className="nav-cta" onClick={onGetStarted}>Get started <ArrowRight size={15} /></button>
        </div>
      </nav>

      <section className="hero-section landing-hero">
        <motion.div className="hero-content" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
          <div className="hero-badge"><span className="live-dot" /> AI operations, finally coordinated</div>
          <h1 className="hero-title">Your best teams,<br /><span className="gradient-text">working in sync.</span></h1>
          <p className="hero-description">Actuator AI turns complex customer operations into a coordinated workflow of specialist agents — fast, secure, and observable from day one.</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={onGetStarted}>Start building <ArrowRight size={17} /></button>
            <button className="secondary-button" onClick={() => navigate('/docs')}><Play size={15} /> See how it works</button>
          </div>
          <div className="hero-proof"><span><Check size={14} /> No credit card required</span><span><Check size={14} /> Secure by default</span><span><Check size={14} /> Deploy in minutes</span></div>
        </motion.div>

        <motion.div className="product-preview" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.65, delay: 0.15 }}>
          <div className="preview-glow" />
          <div className="preview-window">
            <div className="preview-bar"><div className="window-dots"><i /><i /><i /></div><span>Operations workspace</span><span className="preview-status"><span className="live-dot" /> Live</span></div>
            <div className="preview-body">
              <div className="preview-sidebar">
                <div className="mini-brand"><span className="brand-mark"><Zap size={12} /></span><strong>Actuator</strong></div>
                <div className="mini-nav active"><Sparkles size={13} /> Overview</div><div className="mini-nav"><Users size={13} /> Customers</div><div className="mini-nav"><BarChart3 size={13} /> Analytics</div>
                <div className="mini-label">ACTIVE AGENTS</div>
                {AGENTS.slice(0, 3).map(([name, , color]) => <div className="mini-agent" key={name}><span style={{ background: color }} />{name}<small>online</small></div>)}
              </div>
              <div className="preview-main">
                <div className="preview-heading"><div><small>MONDAY, OCTOBER 24</small><h3>Good morning, Rameez</h3></div><div className="avatar">R</div></div>
                <div className="metric-row"><div className="metric-card"><small>Requests resolved</small><strong>2,840</strong><em>↗ 18.4%</em></div><div className="metric-card"><small>Avg. response time</small><strong>1.8<span>s</span></strong><em>↘ 32%</em></div></div>
                <div className="activity-card"><div className="card-heading"><strong>Live agent activity</strong><span>View all <ChevronRight size={13} /></span></div>{AGENTS.map(([name, text, color], index) => <div className="activity-item" key={name}><span className="activity-icon" style={{ color, background: `${color}18` }}>{index === 0 ? <Cpu size={14} /> : index === 1 ? <LockKeyhole size={14} /> : index === 2 ? <Database size={14} /> : <Users size={14} />}</span><div><strong>{name} agent</strong><small>{text}</small></div><span className="activity-time">{index + 1}m ago</span></div>)}</div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <section className="logo-strip" aria-label="Platform capabilities"><span>BUILT FOR TEAMS THAT RUN ON <strong>TRUST</strong></span><span><LockKeyhole size={14} /> Enterprise guardrails</span><span><Database size={14} /> Private data ready</span><span><FileCheck2 size={14} /> Full audit trail</span></section>

      <section className="highlights-section" id="platform">
        <div className="section-kicker">ONE PLATFORM. EVERY SPECIALIST.</div><h2>Make complex work<br /><span className="muted-heading">feel effortless.</span></h2>
        <div className="highlights-grid">{HIGHLIGHTS.map(({ icon: Icon, title, text }, index) => <motion.article className="highlight-card" key={title} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-60px' }} transition={{ delay: index * 0.08 }}><span className="highlight-icon"><Icon size={19} /></span><h3>{title}</h3><p>{text}</p><span className="card-arrow"><ArrowRight size={15} /></span></motion.article>)}</div>
      </section>

      <section className="teams-section" id="teams"><div><div className="section-kicker">A VIRTUAL WORKFORCE</div><h2>Every role has<br /><span className="gradient-text">a specialist.</span></h2><p>Stop forcing one general-purpose bot to do everything. Give every workflow the context, tools, and guardrails it needs to excel.</p><button className="text-link" onClick={() => navigate('/docs')}>Explore the platform <ArrowRight size={15} /></button></div><div className="agent-stack">{AGENTS.map(([name, text, color], index) => <div className="agent-row" key={name} style={{ transform: `translateX(${index * 18}px)` }}><span className="agent-row-icon" style={{ color, background: `${color}18` }}>{index === 0 ? <Cpu size={17} /> : index === 1 ? <ShieldCheck size={17} /> : index === 2 ? <Database size={17} /> : <Users size={17} />}</span><span><strong>{name} agent</strong><small>{text}</small></span><span className="agent-online"><i /> online</span></div>)}</div></section>

      <section className="security-section" id="security"><div className="security-card"><div className="security-copy"><span className="section-kicker">DESIGNED FOR TRUST</span><h2>Move fast.<br /><span className="muted-heading">Stay in control.</span></h2><p>Every action is observable, every sensitive step is guarded, and every high-impact decision can stay with a human.</p><button className="secondary-button" onClick={() => navigate('/docs')}>Read our security model <ArrowRight size={15} /></button></div><div className="security-list"><div><ShieldCheck size={18} /><span><strong>Guardrail pipeline</strong><small>PII, jailbreak, and injection detection</small></span><Check size={16} /></div><div><LockKeyhole size={18} /><span><strong>Human approvals</strong><small>Keep critical actions behind a review step</small></span><Check size={16} /></div><div><FileCheck2 size={18} /><span><strong>Audit everything</strong><small>Trace every request from prompt to outcome</small></span><Check size={16} /></div></div></div></section>

      <section className="cta-section"><div className="cta-content"><span className="hero-badge"><Sparkles size={14} /> Start with your first workflow</span><h2>Turn busywork into<br /><span className="gradient-text">momentum.</span></h2><p>Give your team an AI workforce they can trust — and customers a faster way forward.</p><button className="primary-button large" onClick={onGetStarted}>Create your workspace <ArrowRight size={17} /></button></div></section>
      <footer className="landing-footer"><span className="brand-lockup"><span className="brand-mark"><Zap size={14} /></span><strong>Actuator AI</strong></span><span>© 2026 Actuator AI. Built for better operations.</span><button onClick={() => navigate('/docs')}>Documentation <ArrowRight size={13} /></button></footer>
    </main>
  )
}
