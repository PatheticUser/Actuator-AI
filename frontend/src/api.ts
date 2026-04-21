import { useChatStore } from './store';

const API_BASE = '/api/v1';

export interface Agent {
  key: string;
  name: string;
  description: string;
  tool_count: number;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  agent_name?: string;
  created_at?: string;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  agent_name: string;
  needs_approval: boolean;
  approval_items: string[];
}

export const fetchAgents = async (): Promise<Agent[]> => {
  const res = await fetch(`${API_BASE}/agents/`);
  return res.json();
};

export const streamMessage = (
  message: string,
  email: string,
  conversationId?: string
) => {
  const store = useChatStore.getState();
  store.setLoading(true);

  // Add user message
  store.addMessage({ role: 'user', content: message });
  
  // Add initial assistant streaming message
  store.addMessage({ role: 'assistant', content: '', agent_name: 'Supervisor', isStreaming: true });
  
  const wsUrl = new URL(API_BASE + '/chat/ws', window.location.origin).toString().replace(/^http/, 'ws');
  const ws = new WebSocket(wsUrl);

  let tempBuffer = '';

  ws.onopen = () => {
    ws.send(JSON.stringify({
      message,
      customer_email: email,
      conversation_id: conversationId,
    }));
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'conv_id') {
      store.setConversationId(data.conversation_id);
    } 
    else if (data.type === 'content') {
      tempBuffer += data.content;
      store.updateLastMessage(msg => ({ ...msg, content: tempBuffer, agent_name: data.agent_name }));
      store.setActiveAgent(data.agent_name);
    }
    else if (data.type === 'agent_update') {
      store.updateLastMessage(msg => ({ ...msg, agent_name: data.agent_name }));
      store.setActiveAgent(data.agent_name);
    }
    else if (data.type === 'done') {
      store.updateLastMessage(msg => ({
        ...msg,
        isStreaming: false,
        needs_approval: data.needs_approval,
        approval_items: data.approval_items,
        agent_name: data.agent_name,
      }));
      store.setLoading(false);
      store.setActiveAgent('System');
      ws.close();
    }
    else if (data.type === 'error') {
      store.updateLastMessage(msg => ({
        ...msg,
        content: msg.content + '\n\n**Error:** ' + data.content,
        isStreaming: false,
        agent_name: data.agent_name || 'System'
      }));
      store.setLoading(false);
      store.setActiveAgent('System');
      ws.close();
    }
  };

  ws.onerror = (e) => {
    console.error("WebSocket error", e);
    store.updateLastMessage(msg => ({
      ...msg,
      content: msg.content + '\n\n**WebSocket Error**',
      isStreaming: false
    }));
    store.setLoading(false);
    store.setActiveAgent('System');
  };

  ws.onclose = () => {
    if (store.loading) {
      store.setLoading(false);
      store.updateLastMessage(msg => ({ ...msg, isStreaming: false }));
    }
    store.setActiveAgent('System');
  };
};

export const fetchMessages = async (conversationId: string): Promise<Message[]> => {
  const res = await fetch(`${API_BASE}/chat/conversations/${conversationId}/messages`);
  return res.json();
};
