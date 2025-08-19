import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  IconButton
} from '@mui/material';
import {
  Chat as ChatIcon,
  MoreHoriz as MoreIcon
} from '@mui/icons-material';

const ConversationList = ({
  conversations,
  selectedConversation,
  onConversationSelect,
  onNewConversation,
  onRefresh
}) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box className="h-full flex flex-col">
      {/* Conversation List */}
      <Box className="flex-1 overflow-y-auto">
        <List sx={{ padding: 0 }}>
          {conversations.length === 0 ? (
            <Box className="p-4 text-center">
              <ChatIcon sx={{ color: '#6b7280', fontSize: 40, mb: 1 }} />
              <Typography variant="body2" sx={{ color: '#9ca3af' }}>
                No conversations yet
              </Typography>
            </Box>
          ) : (
            conversations.map((conversation) => (
              <ListItem 
                key={conversation.id} 
                disablePadding
                sx={{ mb: 0.5 }}
              >
                <ListItemButton
                  selected={selectedConversation?.id === conversation.id}
                  onClick={() => onConversationSelect(conversation)}
                  sx={{
                    mx: 2,
                    borderRadius: 2,
                    py: 2,
                    px: 3,
                    '&.Mui-selected': {
                      backgroundColor: '#374151',
                      '&:hover': {
                        backgroundColor: '#374151',
                      }
                    },
                    '&:hover': {
                      backgroundColor: '#374151',
                    }
                  }}
                >
                  <Box className="flex items-center w-full">
                    <ChatIcon sx={{ color: '#9ca3af', fontSize: 16, mr: 2 }} />
                    <Box className="flex-1 min-w-0">
                      <Typography
                        variant="body2"
                        sx={{ 
                          color: 'white',
                          fontWeight: 500,
                          fontSize: '0.875rem',
                          lineHeight: 1.2,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {conversation.title || conversation.lastMessage || `Chat ${conversation.id.slice(0, 8)}`}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{ 
                          color: '#9ca3af',
                          fontSize: '0.75rem',
                          lineHeight: 1,
                          mt: 0.5,
                          display: 'block'
                        }}
                      >
                        {formatDate(conversation.updatedAt)}
                      </Typography>
                    </Box>
                    <IconButton
                      size="small"
                      sx={{ 
                        color: '#6b7280',
                        opacity: 0,
                        transition: 'opacity 0.2s',
                        '.MuiListItemButton-root:hover &': {
                          opacity: 1
                        }
                      }}
                    >
                      <MoreIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </ListItemButton>
              </ListItem>
            ))
          )}
        </List>
      </Box>
    </Box>
  );
};

export default ConversationList; 