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
  AttachFile as AttachFileIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  VolumeOff as VolumeOffIcon
} from '@mui/icons-material';
import { conversationService, ttsService } from '../services/api';

const ChatWindow = ({ conversation, onConversationUpdate, uploadedFiles, sidebarCollapsed }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [playingAudio, setPlayingAudio] = useState(null); // Track which message is playing
  const [loadingAudio, setLoadingAudio] = useState(null); // Track which message is loading audio
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);

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
      timestamp: new Date().toISOString()
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

  const handlePlayAudio = async (messageIndex, text) => {
    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      
      // If this message is already playing, stop it
      if (playingAudio === messageIndex) {
        setPlayingAudio(null);
        return;
      }

      setLoadingAudio(messageIndex);
      
      // Convert text to speech
      const audioUrl = await ttsService.convertToSpeech(text);
      
      // Create and configure audio element
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onloadeddata = () => {
        setLoadingAudio(null);
        setPlayingAudio(messageIndex);
        audio.play();
      };
      
      audio.onended = () => {
        setPlayingAudio(null);
        URL.revokeObjectURL(audioUrl); // Clean up blob URL
      };
      
      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        setLoadingAudio(null);
        setPlayingAudio(null);
        URL.revokeObjectURL(audioUrl);
      };
      
    } catch (error) {
      console.error('Failed to convert text to speech:', error);
      setLoadingAudio(null);
      setPlayingAudio(null);
    }
  };

  const handleStopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setPlayingAudio(null);
  };

  // Cleanup audio when component unmounts
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return (
    <Box className="flex-1 flex flex-col h-full bg-white">
      {/* Chat Header */}
      {conversation && (
        <Box 
          className="p-4 border-b border-gray-200 bg-white"
          sx={{ 
            marginLeft: sidebarCollapsed ? '60px' : '0px',
            transition: 'margin-left 0.3s ease-in-out'
          }}
        >
          <Typography 
            variant="h6" 
            className="font-semibold text-gray-800"
            sx={{ fontSize: '1.125rem' }}
          >
            {conversation.title || `Chat ${conversation.id.slice(0, 8)}`}
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
                  sx={{
                    backgroundColor: '#f3f4f6',
                    border: '1px solid #e5e7eb'
                  }}
                />
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Messages Area */}
      <Box 
        className={`flex-1 overflow-y-auto ${messages.length === 0 ? 'chat-background-empty' : 'chat-background'}`}
        sx={{
          paddingLeft: sidebarCollapsed ? '60px' : '0px',
          transition: 'padding-left 0.3s ease-in-out'
        }}
      >
        {messages.length === 0 ? (
          <Box className="flex flex-col items-center justify-center h-full text-center px-4">
            <Box className="mb-8">
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 600,
                  color: '#374151',
                  mb: 2
                }}
              >
                How can I help you today?
              </Typography>
              <Typography variant="body1" sx={{ color: '#6b7280' }}>
                I'm your IT HelpDesk assistant. Ask me anything about technical issues, software problems, or IT support.
              </Typography>
            </Box>
          </Box>
        ) : (
          <Box className="max-w-4xl mx-auto px-4 py-6">
            {messages.map((message, index) => (
              <Box
                key={index}
                className="mb-8"
              >
                <Box 
                  className={`flex items-start gap-4 ${
                    message.role === 'user' ? 'justify-end' : ''
                  }`}
                >
                  {message.role === 'user' ? (
                    // User message layout (right-aligned)
                    <>
                      <Box className="flex-1 min-w-0 max-w-2xl">
                        <Box 
                          sx={{
                            backgroundColor: '#f7f7f8',
                            borderRadius: '18px',
                            padding: '12px 16px',
                            marginLeft: 'auto',
                            maxWidth: 'fit-content'
                          }}
                        >
                          <Typography
                            variant="body1"
                            sx={{
                              color: '#374151',
                              fontSize: '1rem',
                              lineHeight: 1.6,
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word'
                            }}
                          >
                            {message.content}
                          </Typography>

                          {message.files && message.files.length > 0 && (
                            <Box className="mt-3 flex flex-wrap gap-2">
                              {message.files.map((filename, i) => (
                                <Chip
                                  key={i}
                                  label={filename}
                                  size="small"
                                  sx={{
                                    backgroundColor: '#e5e7eb',
                                    border: '1px solid #d1d5db',
                                    fontSize: '0.75rem'
                                  }}
                                />
                              ))}
                            </Box>
                          )}

                          <Typography
                            variant="caption"
                            sx={{ 
                              display: 'block',
                              mt: 1,
                              color: '#9ca3af',
                              fontSize: '0.75rem',
                              textAlign: 'right'
                            }}
                          >
                            {formatTime(message.timestamp)}
                          </Typography>
                        </Box>
                      </Box>
                      <Avatar
                        sx={{
                          width: 32,
                          height: 32,
                          backgroundColor: '#10a37f',
                          fontSize: '1rem'
                        }}
                      >
                        <PersonIcon fontSize="small" />
                      </Avatar>
                    </>
                  ) : (
                    // Assistant message layout (left-aligned)
                    <>
                      <Avatar
                        sx={{
                          width: 32,
                          height: 32,
                          backgroundColor: '#6b7280',
                          fontSize: '1rem'
                        }}
                      >
                        <BotIcon fontSize="small" />
                      </Avatar>
                      
                      <Box className="flex-1 min-w-0">
                        <Typography
                          variant="body1"
                          sx={{
                            color: '#374151',
                            fontSize: '1rem',
                            lineHeight: 1.6,
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                          }}
                        >
                          {message.content}
                        </Typography>

                        {/* Play button for bot messages */}
                        {!message.error && (
                          <Box className="mt-2">
                            <IconButton
                              size="small"
                              onClick={() => {
                                if (playingAudio === index) {
                                  handleStopAudio();
                                } else {
                                  handlePlayAudio(index, message.content);
                                }
                              }}
                              disabled={loadingAudio === index}
                              sx={{ 
                                padding: '6px',
                                color: '#6b7280',
                                '&:hover': {
                                  backgroundColor: '#f3f4f6',
                                  color: '#374151'
                                }
                              }}
                            >
                              {loadingAudio === index ? (
                                <CircularProgress size={16} />
                              ) : playingAudio === index ? (
                                <StopIcon fontSize="small" />
                              ) : (
                                <PlayIcon fontSize="small" />
                              )}
                            </IconButton>
                          </Box>
                        )}
                        
                        {message.files && message.files.length > 0 && (
                          <Box className="mt-3 flex flex-wrap gap-2">
                            {message.files.map((filename, i) => (
                              <Chip
                                key={i}
                                label={filename}
                                size="small"
                                sx={{
                                  backgroundColor: '#f3f4f6',
                                  border: '1px solid #e5e7eb',
                                  fontSize: '0.75rem'
                                }}
                              />
                            ))}
                          </Box>
                        )}

                        {message.functionCalls && message.functionCalls.length > 0 && (
                          <Box className="mt-2">
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                color: '#6b7280',
                                fontStyle: 'italic'
                              }}
                            >
                              Function calls executed: {message.functionCalls.join(', ')}
                            </Typography>
                          </Box>
                        )}

                        <Typography
                          variant="caption"
                          sx={{ 
                            display: 'block',
                            mt: 1,
                            color: '#9ca3af',
                            fontSize: '0.75rem'
                          }}
                        >
                          {formatTime(message.timestamp)}
                        </Typography>
                      </Box>
                    </>
                  )}
                </Box>
              </Box>
            ))}
            
            {isLoading && (
              <Box className="mb-8">
                <Box className="flex items-start gap-4">
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      backgroundColor: '#6b7280'
                    }}
                  >
                    <BotIcon fontSize="small" />
                  </Avatar>
                  <Box className="flex items-center gap-2">
                    <CircularProgress 
                      size={16} 
                      sx={{ color: '#6b7280' }}
                    />
                    <Typography 
                      variant="body2" 
                      sx={{ color: '#6b7280' }}
                    >
                      Thinking...
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box 
        className="p-4 bg-white border-t border-gray-200"
        sx={{
          paddingLeft: sidebarCollapsed ? '76px' : '16px',
          transition: 'padding-left 0.3s ease-in-out'
        }}
      >
        <Box className="max-w-4xl mx-auto">
          <Box 
            className="relative"
            sx={{
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              backgroundColor: '#ffffff',
              '&:focus-within': {
                borderColor: '#10a37f',
                boxShadow: '0 0 0 3px rgba(16, 163, 127, 0.1)'
              }
            }}
          >
            <TextField
              fullWidth
              multiline
              maxRows={6}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Message IT HelpDesk..."
              variant="outlined"
              disabled={isLoading}
              sx={{
                '& .MuiOutlinedInput-root': {
                  border: 'none',
                  '& fieldset': { border: 'none' },
                  '&:hover fieldset': { border: 'none' },
                  '&.Mui-focused fieldset': { border: 'none' },
                  paddingRight: '60px',
                  paddingTop: '12px',
                  paddingBottom: '12px',
                  fontSize: '1rem',
                  lineHeight: 1.5
                },
                '& .MuiInputBase-input': {
                  color: '#374151',
                  '&::placeholder': {
                    color: '#9ca3af',
                    opacity: 1
                  }
                }
              }}
            />
            <IconButton
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              sx={{
                position: 'absolute',
                right: '8px',
                bottom: '8px',
                backgroundColor: inputMessage.trim() && !isLoading ? '#10a37f' : '#f3f4f6',
                color: inputMessage.trim() && !isLoading ? 'white' : '#9ca3af',
                width: 32,
                height: 32,
                '&:hover': {
                  backgroundColor: inputMessage.trim() && !isLoading ? '#0d8f69' : '#e5e7eb'
                },
                '&:disabled': {
                  backgroundColor: '#f3f4f6',
                  color: '#9ca3af'
                }
              }}
            >
              <SendIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              textAlign: 'center',
              mt: 2,
              color: '#9ca3af',
              fontSize: '0.75rem'
            }}
          >
            IT HelpDesk can make mistakes. Consider checking important information.
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatWindow; 