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
      <Box className="flex items-center justify-between mb-3">
        <Typography variant="h6" className="font-semibold">
          File Upload
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
            startIcon={<UploadIcon />}
            disabled={uploading}
          >
            Upload Files
          </Button>
        </label>
      </Box>

      {uploading && (
        <Box className="mb-3">
          <Typography variant="body2" color="textSecondary" className="mb-1">
            Uploading... {Math.round(uploadProgress)}%
          </Typography>
          <LinearProgress variant="determinate" value={uploadProgress} />
        </Box>
      )}

      {uploadedFiles.length > 0 && (
        <Box>
          <Typography variant="subtitle2" className="mb-2">
            Uploaded Files ({uploadedFiles.length})
          </Typography>
          <Box className="flex flex-wrap gap-2">
            {uploadedFiles.map((file, index) => (
              <Chip
                key={index}
                icon={<FileIcon />}
                label={`${file.filename} (${formatFileSize(file.size)})`}
                variant="outlined"
                className="max-w-xs"
              />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default FileUpload; 