import React, { useState, useEffect, useRef } from 'react';
import './MessageCenter.css';

interface Message {
  id: string;
  senderId: string;
  receiverId: string;
  content: string;
  timestamp: Date;
  read: boolean;
}

interface User {
  id: string;
  username: string;
  role: 'client' | 'freelancer';
  avatar?: string;
}

interface MessageCenterProps {
  currentUser: User;
  apiBaseUrl: string;
}

const MessageCenter: React.FC<MessageCenterProps> = ({ currentUser, apiBaseUrl }) => {
  const [conversations, setConversations] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch conversations
  const fetchConversations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/messages/conversations/${currentUser.id}`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch messages for a specific conversation
  const fetchMessages = async (otherUserId: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/messages/between/${currentUser.id}/${otherUserId}`
      );
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
        // Mark messages as read
        markMessagesAsRead(otherUserId);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mark messages from a user as read
  const markMessagesAsRead = async (senderId: string) => {
    try {
      await fetch(`${apiBaseUrl}/messages/read/${currentUser.id}/${senderId}`, {
        method: 'PUT',
      });
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  };

  // Send a new message
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedUser || !newMessage.trim()) return;
    
    try {
      const response = await fetch(`${apiBaseUrl}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          senderId: currentUser.id,
          receiverId: selectedUser.id,
          content: newMessage,
        }),
      });
      
      if (response.ok) {
        const sentMessage = await response.json();
        setMessages([...messages, sentMessage]);
        setNewMessage('');
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Setup WebSocket for real-time messaging
  useEffect(() => {
    if (!currentUser.id) return;
    
    // Connect to WebSocket
    const ws = new WebSocket(`ws://${apiBaseUrl.replace('http://', '')}/ws/messages/${currentUser.id}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected for messaging');
    };
    
    ws.onmessage = (event) => {
      const newMessage = JSON.parse(event.data);
      
      // Update messages if the sender is the currently selected user
      if (selectedUser && newMessage.senderId === selectedUser.id) {
        setMessages(prev => [...prev, newMessage]);
        markMessagesAsRead(newMessage.senderId);
      }
      
      // Update conversations list to show new message
      fetchConversations();
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    // Initial fetch of conversations
    fetchConversations();
    
    // Cleanup
    return () => {
      ws.close();
    };
  }, [currentUser.id, apiBaseUrl, selectedUser]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch messages when selected user changes
  useEffect(() => {
    if (selectedUser) {
      fetchMessages(selectedUser.id);
    }
  }, [selectedUser]);

  return (
    <div className="message-center">
      <div className="conversations-panel">
        <h2>Conversations</h2>
        {loading && conversations.length === 0 ? (
          <div className="loading">Loading conversations...</div>
        ) : (
          <ul className="conversation-list">
            {conversations.length === 0 ? (
              <li className="no-conversations">No conversations yet</li>
            ) : (
              conversations.map(user => (
                <li 
                  key={user.id} 
                  className={`conversation-item ${selectedUser?.id === user.id ? 'active' : ''}`}
                  onClick={() => setSelectedUser(user)}
                >
                  <div className="avatar">
                    {user.avatar ? (
                      <img src={user.avatar} alt={user.username} />
                    ) : (
                      <div className="avatar-placeholder">
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="conversation-info">
                    <span className="username">{user.username}</span>
                    <span className="role">{user.role}</span>
                  </div>
                </li>
              ))
            )}
          </ul>
        )}
      </div>
      
      <div className="messages-panel">
        {selectedUser ? (
          <>
            <div className="messages-header">
              <h2>Chat with {selectedUser.username}</h2>
            </div>
            
            <div className="messages-container">
              {loading ? (
                <div className="loading">Loading messages...</div>
              ) : (
                <>
                  {messages.length === 0 ? (
                    <div className="no-messages">No messages yet. Start the conversation!</div>
                  ) : (
                    messages.map(message => (
                      <div 
                        key={message.id} 
                        className={`message ${message.senderId === currentUser.id ? 'sent' : 'received'}`}
                      >
                        <div className="message-content">{message.content}</div>
                        <div className="message-time">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>
            
            <form className="message-form" onSubmit={sendMessage}>
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
                required
              />
              <button type="submit">Send</button>
            </form>
          </>
        ) : (
          <div className="no-selected-conversation">
            <p>Select a conversation to start messaging</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageCenter;
