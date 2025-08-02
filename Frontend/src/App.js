import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import { Chat as ChatIcon, BugReport as BugReportIcon } from '@mui/icons-material';
import ConversationList from './components/ConversationList';
import ChatWindow from './components/ChatWindow';
import FileUpload from './components/FileUpload';
import TicketManager from './components/TicketManager';
import { conversationService } from './services/api';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [showTicketManager, setShowTicketManager] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

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

  const handleNewConversation = () => {
    setSelectedConversation(null);
  };

  const handleConversationSelect = (conversation) => {
    setSelectedConversation(conversation);
  };

  const handleFileUpload = (files) => {
    setUploadedFiles(prev => [...prev, ...files]);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box className="h-screen flex flex-col">
        {/* Header */}
        <AppBar position="static" className="shadow-md">
          <Toolbar>
            <ChatIcon className="mr-2" />
            <Typography variant="h6" component="div" className="flex-grow">
              IT HelpDesk Chatbot
            </Typography>
            <IconButton
              color="inherit"
              onClick={() => setShowTicketManager(!showTicketManager)}
              className="ml-2"
            >
              <BugReportIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box className="flex-1 flex overflow-hidden">
          {/* Left Sidebar - Conversations */}
          <Box className="w-80 border-r border-gray-200 bg-gray-50">
            <ConversationList
              conversations={conversations}
              selectedConversation={selectedConversation}
              onConversationSelect={handleConversationSelect}
              onNewConversation={handleNewConversation}
              onRefresh={loadConversations}
            />
          </Box>

          {/* Main Chat Area */}
          <Box className="flex-1 flex flex-col">
            {showTicketManager ? (
              <TicketManager />
            ) : (
              <>
                {/* File Upload Section */}
                <Box className="p-4 border-b border-gray-200 bg-white">
                  <FileUpload
                    onFileUpload={handleFileUpload}
                    uploadedFiles={uploadedFiles}
                  />
                </Box>

                {/* Chat Window */}
                <ChatWindow
                  conversation={selectedConversation}
                  onConversationUpdate={loadConversations}
                  uploadedFiles={uploadedFiles}
                />
              </>
            )}
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App; 