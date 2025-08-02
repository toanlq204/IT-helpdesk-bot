import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Button,
  IconButton,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Chat as ChatIcon
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
      {/* Header */}
      <Box className="p-4 border-b border-gray-200">
        <Box className="flex items-center justify-between mb-3">
          <Typography variant="h6" className="font-semibold">
            Conversations
          </Typography>
          <IconButton size="small" onClick={onRefresh}>
            <RefreshIcon />
          </IconButton>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onNewConversation}
          fullWidth
          className="mb-2"
        >
          New Chat
        </Button>
      </Box>

      {/* Conversation List */}
      <Box className="flex-1 overflow-y-auto">
        <List className="p-0">
          {conversations.length === 0 ? (
            <Box className="p-4 text-center">
              <ChatIcon className="text-gray-400 mb-2" fontSize="large" />
              <Typography variant="body2" color="textSecondary">
                No conversations yet
              </Typography>
            </Box>
          ) : (
            conversations.map((conversation) => (
              <React.Fragment key={conversation.id}>
                <ListItem disablePadding>
                  <ListItemButton
                    selected={selectedConversation?.id === conversation.id}
                    onClick={() => onConversationSelect(conversation)}
                    className="px-4 py-3"
                  >
                    <ListItemText
                      primary={
                        <Typography
                          variant="subtitle2"
                          className="font-medium truncate"
                        >
                          {conversation.title || `Chat ${conversation.id.slice(0, 8)}`}
                        </Typography>
                      }
                      secondary={
                        <Box>
                          <Typography
                            variant="body2"
                            color="textSecondary"
                            className="truncate"
                          >
                            {conversation.lastMessage || 'No messages yet'}
                          </Typography>
                          <Typography
                            variant="caption"
                            color="textSecondary"
                            className="mt-1"
                          >
                            {formatDate(conversation.updatedAt)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))
          )}
        </List>
      </Box>
    </Box>
  );
};

export default ConversationList; 