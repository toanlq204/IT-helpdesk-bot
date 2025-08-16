import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { 
  Box, 
  Typography, 
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button
} from '@mui/material';
import { 
  Chat as ChatIcon, 
  BugReport as BugReportIcon,
  Menu as MenuIcon,
  Add as AddIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import ConversationList from './components/ConversationList';
import ChatWindow from './components/ChatWindow';
import FileUpload from './components/FileUpload';
import TicketManager from './components/TicketManager';
import { conversationService } from './services/api';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#10a37f',
    },
    secondary: {
      main: '#6b7280',
    },
    background: {
      default: '#ffffff',
      paper: '#f7f7f8',
    },
    text: {
      primary: '#374151',
      secondary: '#6b7280',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  shape: {
    borderRadius: 8,
  },
});

function App() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [showTicketManager, setShowTicketManager] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedRole, setSelectedRole] = useState('User');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const convList = await conversationService.getConversations();
      setConversations(convList);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };
  
  const onConversationUpdate = async (response) => {
    try {
      loadConversations();
      setSelectedConversation({
        id: response.conversation_id,
        messages: response.messages
      });
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const handleNewConversation = () => {
    setSelectedConversation(null);
  };

  const handleConversationSelect = (conversation) => {
    setSelectedConversation(conversation);
  };

  const handleFileUpload = (files) => {
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const handleRoleChange = (event) => {
    setSelectedRole(event.target.value);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box className="h-screen flex bg-gray-50">
        {/* Left Sidebar */}
        <Box 
          className={`${sidebarCollapsed ? 'w-0' : 'w-80'} transition-all duration-300 ease-in-out bg-gray-900 text-white flex flex-col overflow-hidden`}
          sx={{ 
            borderRight: '1px solid #374151',
            minWidth: sidebarCollapsed ? 0 : 320
          }}
        >
          {!sidebarCollapsed && (
            <>
              {/* Sidebar Header */}
              <Box className="p-4 border-b border-gray-700">
                <Box className="flex items-center justify-between mb-4">
                  <Typography variant="h6" className="font-semibold text-white">
                    IT HelpDesk
                  </Typography>
                  <IconButton 
                    size="small" 
                    onClick={() => setSidebarCollapsed(true)}
                    sx={{ color: 'white' }}
                  >
                    <MenuIcon />
                  </IconButton>
                </Box>
                
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={handleNewConversation}
                  fullWidth
                  sx={{
                    borderColor: '#374151',
                    color: 'white',
                    '&:hover': {
                      borderColor: '#6b7280',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)'
                    }
                  }}
                >
                  New Chat
                </Button>
              </Box>

              {/* File Upload Section */}
              <Box className="p-4 border-b border-gray-700">
                <FileUpload
                  onFileUpload={handleFileUpload}
                  uploadedFiles={uploadedFiles}
                />
              </Box>
              
              {/* Conversations List */}
              <Box className="flex-1 overflow-y-auto">
                <ConversationList
                  conversations={conversations}
                  selectedConversation={selectedConversation}
                  onConversationSelect={handleConversationSelect}
                  onNewConversation={handleNewConversation}
                  onRefresh={loadConversations}
                />
              </Box>

              {/* Sidebar Footer */}
              <Box className="p-4 border-t border-gray-700">
                <Box className="flex items-center justify-between mb-2">
                  <FormControl variant="outlined" size="small" fullWidth>
                    <InputLabel sx={{ color: '#9ca3af' }}>Role</InputLabel>
                    <Select
                      value={selectedRole}
                      onChange={handleRoleChange}
                      label="Role"
                      sx={{
                        color: 'white',
                        '.MuiOutlinedInput-notchedOutline': {
                          borderColor: '#374151'
                        },
                        '&:hover .MuiOutlinedInput-notchedOutline': {
                          borderColor: '#6b7280'
                        },
                        '.MuiSelect-icon': { color: '#9ca3af' }
                      }}
                    >
                      <MenuItem value="Admin">Admin</MenuItem>
                      <MenuItem value="User">User</MenuItem>
                      <MenuItem value="Officer">Officer</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                
                <IconButton
                  onClick={() => setShowTicketManager(!showTicketManager)}
                  sx={{ 
                    color: showTicketManager ? '#10a37f' : '#9ca3af',
                    '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.05)' }
                  }}
                >
                  <BugReportIcon />
                </IconButton>
              </Box>
            </>
          )}
        </Box>

        {/* Main Chat Area */}
        <Box className="flex-1 flex flex-col relative">
          {/* Collapsed Sidebar Toggle */}
          {sidebarCollapsed && (
            <IconButton
              onClick={() => setSidebarCollapsed(false)}
              sx={{
                position: 'absolute',
                top: 16,
                left: 16,
                zIndex: 1000,
                backgroundColor: 'white',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                '&:hover': {
                  backgroundColor: '#f9fafb'
                }
              }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {showTicketManager ? (
            <TicketManager />
          ) : (
            <ChatWindow
              conversation={selectedConversation}
              onConversationUpdate={onConversationUpdate}
              uploadedFiles={uploadedFiles}
              sidebarCollapsed={sidebarCollapsed}
            />
          )}
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App; 