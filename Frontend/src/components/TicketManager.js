import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { ticketService } from '../services/api';

const TicketManager = () => {
  const [tickets, setTickets] = useState([]);
  const [open, setOpen] = useState(false);
  const [editingTicket, setEditingTicket] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    status: 'open',
    assignee: ''
  });

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    try {
      const ticketList = await ticketService.getTickets();
      setTickets(ticketList);
    } catch (error) {
      console.error('Failed to load tickets:', error);
    }
  };

  const handleOpen = (ticket = null) => {
    if (ticket) {
      setEditingTicket(ticket);
      setFormData({
        title: ticket.title,
        description: ticket.description,
        priority: ticket.priority,
        status: ticket.status,
        assignee: ticket.assignee || ''
      });
    } else {
      setEditingTicket(null);
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        status: 'open',
        assignee: ''
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingTicket(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingTicket) {
        await ticketService.updateTicket(editingTicket.id, formData);
      } else {
        await ticketService.createTicket(formData);
      }
      handleClose();
      loadTickets();
    } catch (error) {
      console.error('Failed to save ticket:', error);
      alert('Failed to save ticket. Please try again.');
    }
  };

  const handleDelete = async (ticketId) => {
    if (!window.confirm('Are you sure you want to delete this ticket?')) {
      return;
    }

    try {
      await ticketService.deleteTicket(ticketId);
      loadTickets();
    } catch (error) {
      console.error('Failed to delete ticket:', error);
      alert('Failed to delete ticket. Please try again.');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'primary';
      case 'in_progress': return 'warning';
      case 'resolved': return 'success';
      case 'closed': return 'default';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString() + ' ' + 
           new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box className="p-6 h-full overflow-y-auto">
      <Box className="flex items-center justify-between mb-6">
        <Typography variant="h4" className="font-bold">
          Ticket Management
        </Typography>
        <Box className="space-x-2">
          <IconButton onClick={loadTickets}>
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpen()}
          >
            New Ticket
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assignee</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tickets.map((ticket) => (
              <TableRow key={ticket.id}>
                <TableCell>
                  <Typography variant="body2" className="font-mono">
                    {ticket.id.slice(0, 8)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="subtitle2" className="font-medium">
                    {ticket.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" className="truncate max-w-xs">
                    {ticket.description}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={ticket.priority.toUpperCase()}
                    color={getPriorityColor(ticket.priority)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={ticket.status.replace('_', ' ').toUpperCase()}
                    color={getStatusColor(ticket.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{ticket.assignee || 'Unassigned'}</TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDate(ticket.created_at)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleOpen(ticket)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(ticket.id)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {tickets.length === 0 && (
        <Box className="text-center py-8">
          <Typography variant="h6" color="textSecondary">
            No tickets found
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Create your first ticket to get started
          </Typography>
        </Box>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingTicket ? 'Edit Ticket' : 'Create New Ticket'}
        </DialogTitle>
        <DialogContent>
          <Box className="space-y-4 pt-2">
            <TextField
              fullWidth
              label="Title"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
            />
            <TextField
              fullWidth
              label="Description"
              multiline
              rows={4}
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: e.target.value})}
                label="Priority"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                onChange={(e) => setFormData({...formData, status: e.target.value})}
                label="Status"
              >
                <MenuItem value="open">Open</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="resolved">Resolved</MenuItem>
                <MenuItem value="closed">Closed</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Assignee"
              value={formData.assignee}
              onChange={(e) => setFormData({...formData, assignee: e.target.value})}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingTicket ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TicketManager; 