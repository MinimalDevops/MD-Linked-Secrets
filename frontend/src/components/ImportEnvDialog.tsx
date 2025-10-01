import React, { useState, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  Typography,
  Box,
  TextField,
  FormControlLabel,
  Checkbox,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Card,
  CardContent,
  LinearProgress,
  IconButton,
  Collapse,
  Select,
  MenuItem,
  FormControl,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Preview as PreviewIcon,
  FileUpload as FileIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { apiClient, EnvImportPreview, EnvImportResult, EnvImportRequest } from '../api/client';

interface ImportEnvDialogProps {
  open: boolean;
  onClose: () => void;
  projectId: number;
  projectName: string;
  onImportComplete?: () => void;
}

const ImportEnvDialog: React.FC<ImportEnvDialogProps> = ({
  open,
  onClose,
  projectId,
  projectName,
  onImportComplete,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [envContent, setEnvContent] = useState('');
  const [importOptions, setImportOptions] = useState({
    overwrite_existing: false,
    strip_prefix: '',
    strip_suffix: '',
    add_prefix: '',
    add_suffix: '',
    description: '',
  });
  const [preview, setPreview] = useState<EnvImportPreview | null>(null);
  const [importResult, setImportResult] = useState<EnvImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflictActions, setConflictActions] = useState<Record<string, 'skip' | 'overwrite'>>({});
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    conflicts: true,
    newVars: true,
    warnings: false,
    skipped: false,
  });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = ['Upload/Paste', 'Configure', 'Preview', 'Import'];

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.env') && file.name !== '.env') {
      setError('Please select a .env file');
      return;
    }

    setSelectedFile(file);
    setError(null);

    try {
      const content = await file.text();
      setEnvContent(content);
      setActiveStep(1);
    } catch (err) {
      setError('Failed to read file content');
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      
      file.text().then(content => {
        setEnvContent(content);
        setActiveStep(1);
      }).catch(() => {
        setError('Failed to read file content');
      });
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const handleContentPaste = (content: string) => {
    setEnvContent(content);
    setSelectedFile(null);
    setActiveStep(1);
  };

  const handlePreview = async () => {
    if (!envContent.trim()) {
      setError('Please provide .env content');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: EnvImportRequest = {
        project_id: projectId,
        env_content: envContent,
        overwrite_existing: importOptions.overwrite_existing,
        strip_prefix: importOptions.strip_prefix || undefined,
        strip_suffix: importOptions.strip_suffix || undefined,
        add_prefix: importOptions.add_prefix || undefined,
        add_suffix: importOptions.add_suffix || undefined,
        description: importOptions.description || undefined,
      };

      const previewResult = await apiClient.previewEnvImport(request);
      setPreview(previewResult);
      
      // Initialize conflict actions based on current overwrite setting
      const initialActions: Record<string, 'skip' | 'overwrite'> = {};
      previewResult.conflicts.forEach(conflict => {
        initialActions[conflict.variable_name] = importOptions.overwrite_existing ? 'overwrite' : 'skip';
      });
      setConflictActions(initialActions);
      
      setActiveStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preview');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!preview) return;

    setLoading(true);
    setError(null);

    try {
      let result: EnvImportResult;

      if (selectedFile) {
        // Use file upload endpoint
        result = await apiClient.uploadEnvFile(projectId, selectedFile, {
          overwrite_existing: importOptions.overwrite_existing,
          strip_prefix: importOptions.strip_prefix || undefined,
          strip_suffix: importOptions.strip_suffix || undefined,
          add_prefix: importOptions.add_prefix || undefined,
          add_suffix: importOptions.add_suffix || undefined,
          description: importOptions.description || undefined,
        });
      } else {
        // Use content import endpoint
        const request: EnvImportRequest = {
          project_id: projectId,
          env_content: envContent,
          overwrite_existing: importOptions.overwrite_existing,
          strip_prefix: importOptions.strip_prefix || undefined,
          strip_suffix: importOptions.strip_suffix || undefined,
          add_prefix: importOptions.add_prefix || undefined,
          add_suffix: importOptions.add_suffix || undefined,
          description: importOptions.description || undefined,
          conflict_resolutions: conflictActions,
        };
        result = await apiClient.importEnvVariables(request);
      }

      setImportResult(result);
      setActiveStep(3);

      if (result.success && onImportComplete) {
        onImportComplete();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import variables');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setSelectedFile(null);
    setEnvContent('');
    setImportOptions({
      overwrite_existing: false,
      strip_prefix: '',
      strip_suffix: '',
      add_prefix: '',
      add_suffix: '',
      description: '',
    });
    setPreview(null);
    setImportResult(null);
    setError(null);
    setConflictActions({});
    setExpandedSections({
      conflicts: true,
      newVars: true,
      warnings: false,
      skipped: false,
    });
    onClose();
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleConflictActionChange = (variableName: string, action: 'skip' | 'overwrite') => {
    setConflictActions(prev => ({
      ...prev,
      [variableName]: action
    }));
  };

  const renderUploadStep = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Import .env File into {projectName}
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Choose how to provide your .env content:
        </Typography>
        
        {/* File Upload */}
        <Paper
          sx={{
            p: 3,
            mb: 2,
            border: '2px dashed',
            borderColor: 'primary.main',
            cursor: 'pointer',
            '&:hover': { backgroundColor: 'action.hover' }
          }}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
        >
          <Box display="flex" flexDirection="column" alignItems="center">
            <FileIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              Click to upload or drag & drop
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Select your .env file
            </Typography>
            {selectedFile && (
              <Chip 
                label={selectedFile.name} 
                color="primary" 
                sx={{ mt: 1 }}
                icon={<SuccessIcon />}
              />
            )}
          </Box>
        </Paper>

        <input
          ref={fileInputRef}
          type="file"
          accept=".env"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />

        <Typography variant="body2" sx={{ textAlign: 'center', my: 1 }}>
          OR
        </Typography>

        {/* Paste Content */}
        <TextField
          fullWidth
          multiline
          rows={8}
          label="Paste .env content here"
          placeholder="DATABASE_URL=postgresql://localhost:5432/mydb
API_KEY=your-api-key
DEBUG=true"
          value={envContent}
          onChange={(e) => handleContentPaste(e.target.value)}
          sx={{ mb: 2 }}
        />
      </Box>

      <Box display="flex" justifyContent="space-between">
        <Button onClick={handleClose}>
          Cancel
        </Button>
        <Button 
          variant="contained"
          onClick={() => setActiveStep(1)}
          disabled={!envContent.trim()}
        >
          Next: Configure
        </Button>
      </Box>
    </Box>
  );

  const renderConfigureStep = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Configure Import Options
      </Typography>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Name Transformations
          </Typography>
          
          <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
            <TextField
              label="Strip Prefix"
              value={importOptions.strip_prefix}
              onChange={(e) => setImportOptions(prev => ({ ...prev, strip_prefix: e.target.value }))}
              placeholder="e.g., PROD_"
              helperText="Remove prefix from variable names"
            />
            <TextField
              label="Strip Suffix"
              value={importOptions.strip_suffix}
              onChange={(e) => setImportOptions(prev => ({ ...prev, strip_suffix: e.target.value }))}
              placeholder="e.g., _PROD"
              helperText="Remove suffix from variable names"
            />
            <TextField
              label="Add Prefix"
              value={importOptions.add_prefix}
              onChange={(e) => setImportOptions(prev => ({ ...prev, add_prefix: e.target.value }))}
              placeholder="e.g., APP_"
              helperText="Add prefix to variable names"
            />
            <TextField
              label="Add Suffix"
              value={importOptions.add_suffix}
              onChange={(e) => setImportOptions(prev => ({ ...prev, add_suffix: e.target.value }))}
              placeholder="e.g., _LOCAL"
              helperText="Add suffix to variable names"
            />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Conflict Resolution
          </Typography>
          
          <FormControlLabel
            control={
              <Checkbox
                checked={importOptions.overwrite_existing}
                onChange={(e) => setImportOptions(prev => ({ ...prev, overwrite_existing: e.target.checked }))}
              />
            }
            label="Overwrite existing variables"
          />
          <Typography variant="body2" color="text.secondary">
            If unchecked, existing variables will be skipped
          </Typography>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Variable Description
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Custom Description"
            value={importOptions.description}
            onChange={(e) => setImportOptions(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Enter a custom description for the imported variables (optional)"
            helperText="This description will be applied to all imported variables. Leave empty to use default descriptions."
          />
        </CardContent>
      </Card>

      <Box display="flex" justifyContent="space-between">
        <Button onClick={handleClose}>
          Cancel
        </Button>
        <Box display="flex" gap={1}>
          <Button onClick={() => setActiveStep(0)}>
            Back
          </Button>
          <Button 
            variant="contained"
            onClick={handlePreview}
            disabled={loading}
            startIcon={loading ? <LinearProgress /> : <PreviewIcon />}
          >
            {loading ? 'Generating Preview...' : 'Preview Import'}
          </Button>
        </Box>
      </Box>
    </Box>
  );

  const renderPreviewStep = () => {
    if (!preview) return null;

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Import Preview
        </Typography>

        {/* Summary */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Summary
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Chip 
                label={`${preview.total_variables} Total Variables`}
                color="primary"
              />
              <Chip 
                label={`${preview.new_variables.length} New`}
                color="success"
              />
              <Chip 
                label={`${preview.conflicts.length} Conflicts`}
                color={preview.conflicts.length > 0 ? "warning" : "default"}
              />
              <Chip 
                label={`${preview.skipped_lines.length} Skipped Lines`}
                color="default"
              />
            </Box>
          </CardContent>
        </Card>

        {/* Description */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Variable Description
            </Typography>
            {importOptions.description ? (
              <Typography variant="body1" sx={{ 
                p: 2, 
                bgcolor: 'grey.50', 
                borderRadius: 1, 
                border: '1px solid',
                borderColor: 'grey.300'
              }}>
                {importOptions.description}
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                No custom description provided. Variables will use default descriptions.
              </Typography>
            )}
          </CardContent>
        </Card>

        {/* New Variables */}
        {preview.new_variables.length > 0 && (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="subtitle1" color="success.main">
                  ✅ New Variables ({preview.new_variables.length})
                </Typography>
                <IconButton 
                  size="small"
                  onClick={() => toggleSection('newVars')}
                >
                  {expandedSections.newVars ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
              
              <Collapse in={expandedSections.newVars}>
                <TableContainer sx={{ mt: 1 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell>Line</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {preview.new_variables.map((variable, index) => (
                        <TableRow key={index}>
                          <TableCell>{variable.name}</TableCell>
                          <TableCell>
                            {variable.value.length > 50 
                              ? `${variable.value.substring(0, 47)}...`
                              : variable.value
                            }
                          </TableCell>
                          <TableCell>{variable.line_number}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Collapse>
            </CardContent>
          </Card>
        )}

        {/* Conflicts */}
        {preview.conflicts.length > 0 && (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="subtitle1" color="warning.main">
                  ⚠️ Conflicts ({preview.conflicts.length})
                </Typography>
                <IconButton 
                  size="small"
                  onClick={() => toggleSection('conflicts')}
                >
                  {expandedSections.conflicts ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
              
              <Collapse in={expandedSections.conflicts}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  These variables already exist. Choose the action for each variable individually.
                </Typography>
                
                {/* Bulk Actions */}
                <Box display="flex" gap={1} mb={2}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => {
                      const bulkActions: Record<string, 'skip' | 'overwrite'> = {};
                      preview.conflicts.forEach(conflict => {
                        bulkActions[conflict.variable_name] = 'skip';
                      });
                      setConflictActions(prev => ({ ...prev, ...bulkActions }));
                    }}
                  >
                    Skip All
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="warning"
                    onClick={() => {
                      const bulkActions: Record<string, 'skip' | 'overwrite'> = {};
                      preview.conflicts.forEach(conflict => {
                        bulkActions[conflict.variable_name] = 'overwrite';
                      });
                      setConflictActions(prev => ({ ...prev, ...bulkActions }));
                    }}
                  >
                    Overwrite All
                  </Button>
                </Box>
                
                <TableContainer sx={{ mt: 1 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Variable</TableCell>
                        <TableCell>Current Type</TableCell>
                        <TableCell>Current Value</TableCell>
                        <TableCell>New Value</TableCell>
                        <TableCell>Action</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {preview.conflicts.map((conflict, index) => (
                        <TableRow key={index}>
                          <TableCell>{conflict.variable_name}</TableCell>
                          <TableCell>
                            <Chip size="small" label={conflict.existing_type} />
                          </TableCell>
                          <TableCell>
                            {conflict.existing_value && conflict.existing_value.length > 30 
                              ? `${conflict.existing_value.substring(0, 27)}...`
                              : conflict.existing_value || 'None'
                            }
                          </TableCell>
                          <TableCell>
                            {conflict.new_value.length > 30 
                              ? `${conflict.new_value.substring(0, 27)}...`
                              : conflict.new_value
                            }
                          </TableCell>
                          <TableCell>
                            <FormControl size="small" sx={{ minWidth: 100 }}>
                              <Select
                                value={conflictActions[conflict.variable_name] || 'skip'}
                                onChange={(e) => handleConflictActionChange(
                                  conflict.variable_name, 
                                  e.target.value as 'skip' | 'overwrite'
                                )}
                                variant="outlined"
                              >
                                <MenuItem value="skip">
                                  <Box display="flex" alignItems="center" gap={1}>
                                    <Chip size="small" label="Skip" color="default" />
                                  </Box>
                                </MenuItem>
                                <MenuItem value="overwrite">
                                  <Box display="flex" alignItems="center" gap={1}>
                                    <Chip size="small" label="Overwrite" color="warning" />
                                  </Box>
                                </MenuItem>
                              </Select>
                            </FormControl>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Collapse>
            </CardContent>
          </Card>
        )}

        {/* Warnings */}
        {preview.warnings.length > 0 && (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="subtitle1" color="warning.main">
                  ⚠️ Warnings ({preview.warnings.length})
                </Typography>
                <IconButton 
                  size="small"
                  onClick={() => toggleSection('warnings')}
                >
                  {expandedSections.warnings ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
              
              <Collapse in={expandedSections.warnings}>
                <Box sx={{ mt: 1 }}>
                  {preview.warnings.map((warning, index) => (
                    <Typography key={index} variant="body2" sx={{ mb: 0.5 }}>
                      • {warning}
                    </Typography>
                  ))}
                </Box>
              </Collapse>
            </CardContent>
          </Card>
        )}

        <Box display="flex" justifyContent="space-between">
          <Button onClick={handleClose}>
            Cancel
          </Button>
          <Box display="flex" gap={1}>
            <Button onClick={() => setActiveStep(1)}>
              Back
            </Button>
            <Button 
              variant="contained"
              onClick={handleImport}
              disabled={loading}
              startIcon={loading ? <LinearProgress /> : <UploadIcon />}
            >
              {loading ? 'Importing...' : 'Import Variables'}
            </Button>
          </Box>
        </Box>
      </Box>
    );
  };

  const renderResultStep = () => {
    if (!importResult) return null;

    return (
      <Box>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          {importResult.success ? (
            <SuccessIcon color="success" />
          ) : (
            <ErrorIcon color="error" />
          )}
          <Typography variant="h6">
            {importResult.success ? 'Import Successful!' : 'Import Failed'}
          </Typography>
        </Box>

        <Alert 
          severity={importResult.success ? 'success' : 'error'} 
          sx={{ mb: 2 }}
        >
          {importResult.message}
        </Alert>

        {importResult.success && (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Import Results
              </Typography>
              <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Variables Imported
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {importResult.variables_imported}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Variables Overwritten
                  </Typography>
                  <Typography variant="h6" color="warning.main">
                    {importResult.variables_overwritten}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Variables Skipped
                  </Typography>
                  <Typography variant="h6" color="text.secondary">
                    {importResult.variables_skipped}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Import ID
                  </Typography>
                  <Typography variant="h6">
                    {importResult.import_id || 'N/A'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}

        {importResult.errors.length > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>Errors:</Typography>
            {importResult.errors.map((error, index) => (
              <Typography key={index} variant="body2">• {error}</Typography>
            ))}
          </Alert>
        )}

        {importResult.warnings.length > 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>Warnings:</Typography>
            {importResult.warnings.map((warning, index) => (
              <Typography key={index} variant="body2">• {warning}</Typography>
            ))}
          </Alert>
        )}

        <Box display="flex" justifyContent="center">
          <Button 
            variant="contained"
            onClick={handleClose}
          >
            Close
          </Button>
        </Box>
      </Box>
    );
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '600px' }
      }}
    >
      <DialogTitle>
        <Typography variant="h5">
          Import Environment Variables
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && activeStep !== 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {activeStep === 0 && renderUploadStep()}
        {activeStep === 1 && renderConfigureStep()}
        {activeStep === 2 && renderPreviewStep()}
        {activeStep === 3 && renderResultStep()}
      </DialogContent>
    </Dialog>
  );
};

export default ImportEnvDialog; 