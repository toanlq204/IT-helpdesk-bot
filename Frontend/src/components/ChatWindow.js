import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  AttachFile as AttachFileIcon
} from '@mui/icons-material';
import { conversationService } from '../services/api';

const ChatWindow = ({ conversation, onConversationUpdate, uploadedFiles }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (conversation) {
      loadMessages();
    } else {
      setMessages([]);
    }
  }, [conversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadMessages = async () => {
    try {
      const messageData = await conversationService.getMessages(conversation.id);
      setMessages(messageData.messages || []);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
      files: uploadedFiles.map(f => f.filename)
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await conversationService.sendMessage(
        inputMessage,
        conversation?.id,
        uploadedFiles.map(f => f.id)
      );

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        functionCalls: response.function_calls || []
      }]);

      // Update conversation list if new conversation was created
      if (!conversation && response.conversation_id) {
        onConversationUpdate(response);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box className="flex-1 flex flex-col h-full">
      {/* Chat Header */}
      <Box className="p-4 border-b border-gray-200 bg-white">
        <Typography variant="h6" className="font-semibold">
          {conversation ? `Chat ${conversation.id.slice(0, 8)}` : 'New Conversation'}
        </Typography>
        {uploadedFiles.length > 0 && (
          <Box className="mt-2 flex flex-wrap gap-1">
            {uploadedFiles.map((file, index) => (
              <Chip
                key={index}
                icon={<AttachFileIcon />}
                label={file.filename}
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        )}
      </Box>

      {/* Messages Area */}
      <Box className="flex-1 overflow-y-auto p-4 bg-gray-50">
        {messages.length === 0 ? (
          <Box className="text-center py-8">
            <BotIcon className="text-gray-400 mb-2" fontSize="large" />
            <Typography variant="body1" color="textSecondary">
              Hello! I'm your IT HelpDesk assistant. How can I help you today?
            </Typography>
          </Box>
        ) : (
          <Box className="space-y-4">
            {messages.map((message, index) => (
              <Box
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <Box
                  className={`flex max-w-xs lg:max-w-md ${
                    message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  <Avatar
                    className={`${message.role === 'user' ? 'ml-2' : 'mr-2'}`}
                    sx={{
                      bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main'
                    }}
                  >
                    {message.role === 'user' ? <PersonIcon /> : <BotIcon />}
                  </Avatar>
                  <Paper
                    className={`p-3 ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : message.error
                        ? 'bg-red-50 border border-red-200'
                        : 'bg-white'
                    }`}
                    elevation={1}
                  >
                    <Typography variant="body1" className="whitespace-pre-wrap">
                      {message.content}
                    </Typography>
                    
                    {message.files && message.files.length > 0 && (
                      <Box className="mt-2">
                        {message.files.map((filename, i) => (
                          <Chip
                            key={i}
                            label={filename}
                            size="small"
                            className="mr-1 mb-1"
                          />
                        ))}
                      </Box>
                    )}

                    {message.functionCalls && message.functionCalls.length > 0 && (
                      <Box className="mt-2">
                        <Typography variant="caption" className="text-gray-600">
                          Function calls executed: {message.functionCalls.join(', ')}
                        </Typography>
                      </Box>
                    )}

                    <Typography
                      variant="caption"
                      className={`block mt-1 ${
                        message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}
                    >
                      {formatTime(message.timestamp)}
                    </Typography>
                  </Paper>
                </Box>
              </Box>
            ))}
            {isLoading && (
              <Box className="flex justify-start">
                <Box className="flex flex-row">
                  <Avatar className="mr-2" sx={{ bgcolor: 'secondary.main' }}>
                    <BotIcon />
                  </Avatar>
                  <Paper className="p-3 bg-white" elevation={1}>
                    <CircularProgress size={20} />
                    <Typography variant="body2" className="ml-2 inline">
                      Thinking...
                    </Typography>
                  </Paper>
                </Box>
              </Box>
            )}
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box className="p-4 border-t border-gray-200 bg-white">
        <Box className="flex items-end space-x-2">
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            variant="outlined"
            disabled={isLoading}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="mb-1"
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatWindow; 