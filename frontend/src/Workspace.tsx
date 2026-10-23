import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Activity,
  BarChart3,
  Bot,
  ChevronDown,
  ChevronRight,
  Command,
  LayoutDashboard,
  MessageSquare,
  Plus,
  Settings,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react'
import { useChatStore } from './store'
import './Workspace.css'

const NAV_ITEMS = [
  { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/app/chat', label: 'New conversation', icon: MessageSquare },
  { to: '/app/conversations', label: 'Conversations', icon: Activity },
  { to: '/app/agents', label: 'Agents', icon: Bot },
  { to: '/app/analytics', label: 'Analytics', icon: BarChart3 },
]

function Logo() {
  return (
    <div className="workspace-logo">
      <span className="workspace-logo-mark"><Zap size={16} /></span>
      <span><strong>Actuator</strong><small>AI operations</small></span>
    </div>
  )
}

export function WorkspaceLayout() {
  const store = useChatStore()
  const navigate = useNavigate()

  return (
    <div className="workspace">
      <aside className="workspace-sidebar">
        <div className="workspace-sidebar-top">
          <button className="workspace-logo-button" onClick={() => navigate('/')} aria-label="Back to Actuator AI home"><Logo /></button>
          <button className="workspace-create" onClick={() => navigate('/app/chat')}><Plus size={15} /> New conversation</button>
        </div>
        <nav className="workspace-nav" aria-label="Workspace navigation">
          <div className="workspace-nav-label">Workspace</div>
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `workspace-nav-item ${isActive ? 'active' : ''}`}>
              <Icon size={16} /><span>{label}</span>{label === 'Conversations' && store.conversationsHistory.length > 0 && <b>{store.conversationsHistory.length}</b>}
            </NavLink>
          ))}
          <div className="workspace-nav-label agents-label">Manage</div>
          <NavLink to="/app/settings" className={({ isActive }) => `workspace-nav-item ${isActive ? 'active' : ''}`}><Settings size={16} /><span>Settings</span></NavLink>
        </nav>
        <div className="workspace-sidebar-bottom">
          <div className="workspace-guardrail"><ShieldCheck size={16} /><span><strong>Guardrails active</strong><small>All systems operational</small></span><i /></div>
          <div className="workspace-user">
            <span className="workspace-avatar">{(store.user?.name || store.user?.email || 'A').slice(0, 1).toUpperCase()}</span>
            <span className="workspace-user-copy"><strong>{store.user?.name || 'Workspace owner'}</strong><small>{store.user?.email}</small></span>
            <button onClick={() => store.logout()} title="Log out"><ChevronDown size={15} /></button>
          </div>
        </div>
      </aside>
      <main className="workspace-main">
        <header className="workspace-header">
          <div className="workspace-breadcrumb"><Command size={14} /><span>Actuator workspace</span><ChevronRight size={13} /><strong>Operations</strong></div>
          <div className="workspace-header-actions"><span className="workspace-live"><i /> Live</span><button className="workspace-icon-button" title="Open settings" onClick={() => navigate('/app/settings')}><Settings size={16} /></button><button className="workspace-help" onClick={() => navigate('/docs')}>Docs</button></div>
        </header>
        <div className="workspace-content"><Outlet /></div>
      </main>
    </div>
  )
}

const agentRows = [
  ['Supervisor Router', 'Routes every request to the right specialist', '#8b7cf6', 'Routing'],
  ['Technical Specialist', 'Incidents, APIs, integrations, and diagnostics', '#22d3ee', 'Technical'],
  ['Account Security Agent', 'Identity, access, and account protection', '#f59e0b', 'Security'],
  ['Billing Finance Agent', 'Invoices, plans, refunds, and credits', '#34d399', 'Billing'],
  ['Success Retention Agent', 'Health scores, renewals, and customer outcomes', '#c084fc', 'Success'],
]

export function OverviewPage() {
  const navigate = useNavigate()
  const store = useChatStore()
  return (
    <div className="page-stack">
      <div className="page-heading"><div><div className="eyebrow">MONDAY, OCTOBER 24, 2026</div><h1>Good morning, {store.user?.name?.split(' ')[0] || 'there'}.</h1><p>Your operations command center is ready.</p></div><button className="primary-action" onClick={() => navigate('/app/chat')}><Sparkles size={16} /> Start a conversation</button></div>
      <div className="overview-metrics"><Metric label="Requests resolved" value="2,840" trend="+18.4%" /><Metric label="Avg. response time" value="1.8s" trend="-32%" positive={false} /><Metric label="Active agents" value="8 / 8" trend="All online" /><Metric label="Approval queue" value="03" trend="Needs review" warning /></div>
      <div className="overview-grid"><section className="workspace-card activity-overview"><CardTitle title="Recent activity" action="View all" onClick={() => navigate('/app/conversations')} />{['Invoice question routed to Billing', 'Login issue escalated to Security', 'Spanish sentiment analysis completed', 'Audit report generated'].map((item, i) => <div className="overview-activity" key={item}><span className={`activity-dot dot-${i}`} /><span><strong>{item}</strong><small>{i + 2} minutes ago · {i === 2 ? 'Linguistic Agent' : i === 1 ? 'Account Security Agent' : 'Supervisor Router'}</small></span><ChevronRight size={15} /></div>)}</section><section className="workspace-card"><CardTitle title="Agent health" action="Manage" onClick={() => navigate('/app/agents')} />{agentRows.slice(0, 4).map(([name, , color]) => <div className="health-row" key={name}><span className="agent-health-icon" style={{ color, background: `${color}18` }}><Bot size={14} /></span><span><strong>{name}</strong><small>Ready for requests</small></span><i className="health-online" /></div>)}</section></div>
      <section className="workspace-card quick-start"><div><span className="eyebrow">QUICK START</span><h2>What do you want to solve?</h2><p>Start with a prompt, attach context, and let the right agents collaborate.</p></div><div className="quick-start-actions"><button onClick={() => navigate('/app/chat')}><MessageSquare size={16} /> Ask a question</button><button onClick={() => navigate('/app/agents')}><Bot size={16} /> Explore agents</button><button onClick={() => navigate('/app/analytics')}><BarChart3 size={16} /> View insights</button></div></section>
    </div>
  )
}

function Metric({ label, value, trend, positive = true, warning = false }: { label: string; value: string; trend: string; positive?: boolean; warning?: boolean }) {
  return <div className="metric"><small>{label}</small><strong>{value}</strong><span className={warning ? 'metric-warning' : positive ? 'metric-positive' : 'metric-negative'}>{trend}</span></div>
}

function CardTitle({ title, action, onClick }: { title: string; action: string; onClick: () => void }) {
  return <div className="card-title"><h2>{title}</h2><button onClick={onClick}>{action} <ChevronRight size={14} /></button></div>
}

export function AgentsPage() {
  return <div className="page-stack"><div className="page-heading"><div><div className="eyebrow">WORKFORCE</div><h1>Agents</h1><p>Monitor and manage the specialists powering your operations.</p></div><button className="secondary-action"><Plus size={15} /> Add agent</button></div><div className="agent-page-grid">{agentRows.concat([['Operations Sync Agent', 'Tasks, handoffs, and internal workflows', '#f472b6', 'Operations'], ['Linguistic Agent', 'Language detection, translation, and sentiment', '#38bdf8', 'Language'], ['Audit Agent', 'Quality assurance and compliance checks', '#fb7185', 'Compliance']]).map(([name, description, color, category]) => <article className="agent-card" key={name}><div className="agent-card-top"><span className="agent-health-icon large" style={{ color, background: `${color}18` }}><Bot size={19} /></span><span className="agent-card-status"><i /> Online</span></div><div className="agent-card-category">{category}</div><h2>{name}</h2><p>{description}</p><div className="agent-card-footer"><span>0 issues today</span><button>Configure <ChevronRight size={14} /></button></div></article>)}</div></div>
}

export function ConversationsPage() {
  const store = useChatStore()
  const navigate = useNavigate()
  return <div className="page-stack"><div className="page-heading"><div><div className="eyebrow">WORKSPACE HISTORY</div><h1>Conversations</h1><p>Search, review, and continue every customer request.</p></div><button className="primary-action" onClick={() => navigate('/app/chat')}><Plus size={16} /> New conversation</button></div><div className="table-toolbar"><div className="fake-search">Search conversations...</div><span>All conversations <ChevronDown size={14} /></span></div><section className="workspace-card conversation-table">{store.conversationsHistory.length ? store.conversationsHistory.map((conversation) => <button className="conversation-row" key={conversation.id} onClick={() => navigate(`/app/chat?conversation=${conversation.id}`)}><span className="conversation-icon"><MessageSquare size={15} /></span><span><strong>{conversation.summary || 'Untitled conversation'}</strong><small>{conversation.customer_email || store.user?.email} · {new Date(conversation.started_at).toLocaleDateString()}</small></span><span className="conversation-status">Resolved</span><ChevronRight size={15} /></button>) : <div className="empty-state"><MessageSquare size={22} /><h2>No conversations yet</h2><p>Start your first conversation to see it here.</p><button className="primary-action" onClick={() => navigate('/app/chat')}>Start a conversation</button></div>}</section></div>
}

export function AnalyticsPage() {
  return <div className="page-stack"><div className="page-heading"><div><div className="eyebrow">PERFORMANCE</div><h1>Analytics</h1><p>Understand how your agent workforce is changing operations.</p></div><button className="date-filter">Last 30 days <ChevronDown size={14} /></button></div><div className="overview-metrics"><Metric label="Total requests" value="12,482" trend="+24.8%" /><Metric label="Resolution rate" value="94.6%" trend="+6.2%" /><Metric label="Customer sentiment" value="4.8 / 5" trend="+0.4" /><Metric label="Human handoffs" value="8.2%" trend="-14.2%" positive={false} /></div><div className="analytics-grid"><section className="workspace-card chart-card"><CardTitle title="Request volume" action="Export" onClick={() => {}} /><div className="fake-chart"><div className="chart-y"><span>800</span><span>600</span><span>400</span><span>200</span><span>0</span></div><div className="chart-bars">{[34, 46, 41, 58, 52, 76, 68, 84, 73, 91, 82, 98].map((height, i) => <i key={i} style={{ height: `${height}%` }} />)}</div></div><div className="chart-labels"><span>Oct 01</span><span>Oct 08</span><span>Oct 15</span><span>Oct 24</span></div></section><section className="workspace-card"><CardTitle title="Top intents" action="Details" onClick={() => {}} />{[['Billing questions', '32%', '#8b7cf6'], ['Account access', '24%', '#22d3ee'], ['Technical issues', '19%', '#34d399'], ['Other requests', '25%', '#64748b']].map(([label, percentage, color]) => <div className="intent-row" key={label}><span><i style={{ background: color }} />{label}</span><strong>{percentage}</strong><div><b style={{ width: percentage, background: color }} /></div></div>)}</section></div></div>
}

export function SettingsPage() {
  const store = useChatStore()
  return <div className="page-stack settings-page"><div className="page-heading"><div><div className="eyebrow">WORKSPACE</div><h1>Settings</h1><p>Manage your workspace preferences and account.</p></div></div><section className="workspace-card settings-card"><h2>Workspace profile</h2><label>Workspace name<input defaultValue="Actuator AI Operations" /></label><label>Owner email<input defaultValue={store.user?.email || ''} readOnly /></label><button className="primary-action save-button">Save changes</button></section><section className="workspace-card settings-card"><h2>Preferences</h2><div className="setting-toggle"><span><strong>Approval notifications</strong><small>Notify me when an agent needs human approval</small></span><i className="toggle-on" /></div><div className="setting-toggle"><span><strong>Weekly performance digest</strong><small>Receive a summary of agent performance</small></span><i className="toggle-on" /></div></section></div>
}
