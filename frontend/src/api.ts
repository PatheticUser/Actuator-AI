const API_BASE = 'http://localhost:8000/api/v1';

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

export const sendMessage = async (
  message: string,
  email: string,
  conversationId?: string
): Promise<ChatResponse> => {
  const res = await fetch(`${API_BASE}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      customer_email: email,
      conversation_id: conversationId,
    }),
  });
  return res.json();
};

export const fetchMessages = async (conversationId: string): Promise<Message[]> => {
  const res = await fetch(`${API_BASE}/chat/conversations/${conversationId}/messages`);
  return res.json();
};
