import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  AttachFile as FileIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { fileService } from '../services/api';

const FileUpload = ({ onFileUpload, uploadedFiles }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const uploadedFileResults = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setUploadProgress(((i + 1) / files.length) * 100);
        
        const result = await fileService.uploadFile(file);
        uploadedFileResults.push({
          id: result.file_info.file_id,
          filename: result.file_info.filename,
          size: file.size,
          type: file.type
        });
      }

      onFileUpload(uploadedFileResults);
    } catch (error) {
      console.error('File upload failed:', error);
      alert('File upload failed. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      // Reset file input
      event.target.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Box className="mb-3">
        <Typography 
          variant="body2" 
          sx={{ 
            color: '#9ca3af',
            fontWeight: 500,
            mb: 2,
            fontSize: '0.875rem'
          }}
        >
          Attachments
        </Typography>
        <input
          accept="*/*"
          style={{ display: 'none' }}
          id="file-upload"
          multiple
          type="file"
          onChange={handleFileSelect}
          disabled={uploading}
        />
        <label htmlFor="file-upload">
          <Button
            variant="outlined"
            component="span"
            startIcon={<UploadIcon fontSize="small" />}
            disabled={uploading}
            size="small"
            fullWidth
            sx={{
              borderColor: '#374151',
              color: '#9ca3af',
              textTransform: 'none',
              fontSize: '0.8rem',
              py: 1,
              '&:hover': {
                borderColor: '#6b7280',
                backgroundColor: 'rgba(255, 255, 255, 0.05)'
              }
            }}
          >
            Upload Files
          </Button>
        </label>
      </Box>

      {uploading && (
        <Box className="mb-3">
          <Typography 
            variant="caption" 
            sx={{ 
              color: '#9ca3af',
              display: 'block',
              mb: 1,
              fontSize: '0.75rem'
            }}
          >
            Uploading... {Math.round(uploadProgress)}%
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={uploadProgress}
            sx={{
              backgroundColor: '#374151',
              '& .MuiLinearProgress-bar': {
                backgroundColor: '#10a37f'
              }
            }}
          />
        </Box>
      )}

      {uploadedFiles.length > 0 && (
        <Box>
          <Typography 
            variant="caption" 
            sx={{ 
              color: '#9ca3af',
              display: 'block',
              mb: 1,
              fontSize: '0.75rem'
            }}
          >
            Files ({uploadedFiles.length})
          </Typography>
          <Box className="space-y-1">
            {uploadedFiles.map((file, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  p: 1.5,
                  backgroundColor: '#374151',
                  borderRadius: 1,
                  border: '1px solid #4b5563'
                }}
              >
                <FileIcon sx={{ color: '#9ca3af', fontSize: 16 }} />
                <Box className="flex-1 min-w-0">
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'white',
                      fontSize: '0.75rem',
                      display: 'block',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {file.filename}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      color: '#9ca3af',
                      fontSize: '0.6875rem'
                    }}
                  >
                    {formatFileSize(file.size)}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default FileUpload; 