import axios, { AxiosInstance, AxiosResponse } from 'axios';

export interface Project {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  variables_count?: number;
}

export interface EnvVar {
  id: number;
  name: string;
  description: string;
  value_type: 'raw' | 'linked' | 'concatenated';
  raw_value?: string;
  linked_to?: string;
  concat_parts?: string;
  resolved_value?: string;
  project_id: number;
  created_at: string;
  updated_at: string;
}

export interface Export {
  id: number;
  project_id: number;
  export_path: string;
  exported_at: string;
  with_prefix: boolean;
  with_suffix: boolean;
  prefix_value?: string;
  suffix_value?: string;
  resolved_values: Record<string, string>;
  export_hash?: string;
}

export interface VariableResolutionResponse {
  resolved_values: Record<string, string>;
}

export interface CheckUpdatesResponse {
  outdated_exports: Export[];
  total_checked: number;
  outdated_count: number;
}

export interface DiffResponse {
  export_id: number;
  export_path: string;
  exported_at: string;
  differences: Array<{
    variable: string;
    stored_value: string;
    current_value: string;
    status: 'modified' | 'added' | 'removed';
  }>;
  total_differences: number;
}

export interface VariableImpactAnalysis {
  source_variable: {
    id: number;
    name: string;
    project_id: number;
    project_name: string;
    type: string;
    description?: string;
  };
  impact_summary: {
    total_projects_affected: number;
    total_variables_affected: number;
    total_exports_affected: number;
    has_cross_project_impact: boolean;
  };
  affected_projects: Array<{
    project_id: number;
    project_name: string;
    project_description?: string;
    variables: Array<{
      id: number;
      name: string;
      type: string;
      description?: string;
      reference?: string;
      created_at?: string;
      updated_at?: string;
    }>;
  }>;
  affected_exports: Array<{
    export_id: number;
    project_id: number;
    export_path: string;
    exported_at: string;
    affected_variable: string;
    git_repo_path?: string;
    git_branch?: string;
    git_commit_hash?: string;
    git_remote_url?: string;
    is_git_repo?: boolean;
  }>;
  recommendations: string[];
}

export interface EnvImportRequest {
  project_id: number;
  env_content: string;
  overwrite_existing?: boolean;
  strip_prefix?: string;
  strip_suffix?: string;
  add_prefix?: string;
  add_suffix?: string;
  conflict_resolutions?: Record<string, 'skip' | 'overwrite'>;
  description?: string;
}

export interface ParsedEnvVariable {
  name: string;
  value: string;
  original_name: string;
  line_number: number;
}

export interface ImportConflict {
  variable_name: string;
  existing_value?: string;
  new_value: string;
  existing_type: string;
  action: string;
}

export interface EnvImportPreview {
  total_variables: number;
  new_variables: ParsedEnvVariable[];
  conflicts: ImportConflict[];
  skipped_lines: string[];
  warnings: string[];
}

export interface EnvImportResult {
  success: boolean;
  import_id?: number;
  variables_imported: number;
  variables_skipped: number;
  variables_overwritten: number;
  conflicts_resolved: number;
  errors: string[];
  warnings: string[];
  message: string;
}

export interface EnvImportRecord {
  id: number;
  project_id: number;
  import_source: string;
  imported_at: string;
  variables_imported: number;
  variables_skipped: number;
  variables_overwritten: number;
  import_hash: string;
  created_at: string;
}

// Variable History interfaces
export interface VariableHistoryEntry {
  id: number;
  env_var_id: number;
  project_id: number;
  version_number: number;
  variable_name: string;
  raw_value?: string;
  linked_to?: string;
  concat_parts?: string;
  description?: string;
  is_encrypted: boolean;
  change_type: string;
  change_reason?: string;
  changed_by?: string;
  created_at: string;
}

export interface VariableWithHistory {
  current: any;
  history: VariableHistoryEntry[];
}

export interface ProjectHistorySettings {
  project_id: number;
  history_enabled: boolean;
  history_limit: number;
}

export interface HistorySettingsUpdate {
  history_limit: number;
  confirm_cleanup?: boolean;
}

export interface HistorySettingsResponse {
  success: boolean;
  requires_confirmation?: boolean;
  warning?: string;
  affected_variables?: number;
  entries_to_remove?: number;
  old_limit?: number;
  new_limit?: number;
  message?: string;
  error?: string;
}

export interface RestoreVariableRequest {
  version_number: number;
  change_reason?: string;
  changed_by?: string;
}

// Search interfaces
export type SearchScope = "everything" | "projects" | "env_vars" | "values";

export interface SearchRequest {
  query: string;
  scope: SearchScope;
  project_id?: number;
  limit?: number;
}

export interface BaseSearchResult {
  type: string;
  id: number;
  match_score: number;
  match_field: string;
  highlight: string;
}

export interface ProjectSearchResult extends BaseSearchResult {
  type: "project";
  name: string;
  description?: string;
  variables_count: number;
}

export interface VariableSearchResult extends BaseSearchResult {
  type: "variable";
  name: string;
  project_id: number;
  project_name: string;
  description?: string;
  value_type: string;
}

export interface ValueSearchResult extends BaseSearchResult {
  type: "value";
  variable_name: string;
  project_id: number;
  project_name: string;
  value_preview: string;
  value_type: string;
}

export type SearchResultType = ProjectSearchResult | VariableSearchResult | ValueSearchResult;

export interface SearchResponse {
  query: string;
  scope: SearchScope;
  project_id?: number;
  total_results: number;
  results: SearchResultType[];
  execution_time_ms: number;
}

export interface SearchSuggestion {
  text: string;
  type: string;
  count?: number;
}

export interface SearchSuggestionsResponse {
  suggestions: SearchSuggestion[];
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:8088/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging and error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        
        // Extract meaningful error message from API response
        let errorMessage = 'An unexpected error occurred';
        
        if (error.response?.data?.detail) {
          // Backend returns error details in the 'detail' field
          errorMessage = error.response.data.detail;
        } else if (error.response?.data?.message) {
          // Some APIs use 'message' field
          errorMessage = error.response.data.message;
        } else if (error.response?.status === 400) {
          errorMessage = 'Bad request - please check your input';
        } else if (error.response?.status === 404) {
          errorMessage = 'Resource not found';
        } else if (error.response?.status === 500) {
          errorMessage = 'Server error - please try again later';
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        // Create a new error with the extracted message
        const enhancedError = new Error(errorMessage);
        return Promise.reject(enhancedError);
      }
    );
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    const response: AxiosResponse<{ projects: Project[] }> = await this.client.get('/projects/');
    return response.data.projects;
  }

  async getProject(id: number): Promise<Project> {
    const response: AxiosResponse<Project> = await this.client.get(`/projects/${id}`);
    return response.data;
  }

  async createProject(project: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<Project> {
    const response: AxiosResponse<Project> = await this.client.post('/projects/', project);
    return response.data;
  }

  async updateProject(id: number, project: Partial<Project>): Promise<Project> {
    const response: AxiosResponse<Project> = await this.client.put(`/projects/${id}`, project);
    return response.data;
  }

  async deleteProject(id: number): Promise<void> {
    await this.client.delete(`/projects/${id}`);
  }

  // Environment Variables
  async getEnvVars(projectId?: number): Promise<EnvVar[]> {
    const params = projectId ? { project_id: projectId } : {};
    const response: AxiosResponse<{ variables: EnvVar[] }> = await this.client.get('/env-vars/', { params });
    return response.data.variables;
  }

  async getEnvVar(id: number): Promise<EnvVar> {
    const response: AxiosResponse<EnvVar> = await this.client.get(`/env-vars/${id}`);
    return response.data;
  }

  async createEnvVar(envVar: Omit<EnvVar, 'id' | 'created_at' | 'updated_at'>): Promise<EnvVar> {
    const response: AxiosResponse<EnvVar> = await this.client.post('/env-vars/', envVar);
    return response.data;
  }

  async updateEnvVar(id: number, envVar: Partial<EnvVar>): Promise<EnvVar> {
    const response: AxiosResponse<EnvVar> = await this.client.put(`/env-vars/${id}`, envVar);
    return response.data;
  }

  async changeVariableType(id: number, envVar: Partial<EnvVar>): Promise<EnvVar> {
    const response: AxiosResponse<EnvVar> = await this.client.put(`/env-vars/${id}/change-type`, envVar);
    return response.data;
  }

  async deleteEnvVar(id: number): Promise<void> {
    await this.client.delete(`/env-vars/${id}`);
  }

  async getVariableImpactAnalysis(id: number): Promise<VariableImpactAnalysis> {
    const response: AxiosResponse<VariableImpactAnalysis> = await this.client.get(`/env-vars/${id}/impact-analysis`);
    return response.data;
  }

  async previewEnvImport(request: EnvImportRequest): Promise<EnvImportPreview> {
    const response: AxiosResponse<EnvImportPreview> = await this.client.post('/imports/preview', request);
    return response.data;
  }

  async importEnvVariables(request: EnvImportRequest): Promise<EnvImportResult> {
    const response: AxiosResponse<EnvImportResult> = await this.client.post('/imports/import', request);
    return response.data;
  }

  async uploadEnvFile(
    projectId: number,
    file: File,
    options: {
      overwrite_existing?: boolean;
      strip_prefix?: string;
      strip_suffix?: string;
      add_prefix?: string;
      add_suffix?: string;
      description?: string;
    } = {}
  ): Promise<EnvImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId.toString());
    formData.append('overwrite_existing', (options.overwrite_existing || false).toString());
    
    if (options.strip_prefix) formData.append('strip_prefix', options.strip_prefix);
    if (options.strip_suffix) formData.append('strip_suffix', options.strip_suffix);
    if (options.add_prefix) formData.append('add_prefix', options.add_prefix);
    if (options.add_suffix) formData.append('add_suffix', options.add_suffix);
    if (options.description) formData.append('description', options.description);

    const response: AxiosResponse<EnvImportResult> = await this.client.post('/imports/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getImports(projectId?: number): Promise<EnvImportRecord[]> {
    const params = projectId ? { project_id: projectId } : {};
    const response: AxiosResponse<EnvImportRecord[]> = await this.client.get('/imports/', { params });
    return response.data;
  }

  async resolveVariables(projectId?: number, varId?: number): Promise<VariableResolutionResponse> {
    const data: any = {};
    if (projectId) data.project_id = projectId;
    if (varId) data.var_id = varId;
    
    const response: AxiosResponse<VariableResolutionResponse> = await this.client.post('/env-vars/resolve', data);
    return response.data;
  }

  // Exports
  async getExports(projectId?: number): Promise<Export[]> {
    const params = projectId ? { project_id: projectId } : {};
    const response: AxiosResponse<{ exports: Export[] }> = await this.client.get('/exports/', { params });
    return response.data.exports;
  }

  async deleteExport(exportId: number): Promise<void> {
    await this.client.delete(`/exports/${exportId}`);
  }

  async exportProject(
    projectName: string,
    outDir: string,
    options: {
      withPrefix?: boolean;
      withSuffix?: boolean;
      prefixValue?: string;
      suffixValue?: string;
    } = {}
  ): Promise<{ success: boolean; export_id: number; export_path: string; variables_exported: number; message: string }> {
    const response = await this.client.post('/exports/export', {
      project_name: projectName,
      out_dir: outDir,
      ...options,
    });
    return response.data;
  }

  async checkUpdates(projectId?: number): Promise<CheckUpdatesResponse> {
    const params = projectId ? { project_id: projectId } : {};
    const response: AxiosResponse<CheckUpdatesResponse> = await this.client.get('/exports/check-updates', { params });
    return response.data;
  }

  async getExportDiff(exportId: number): Promise<DiffResponse> {
    const response: AxiosResponse<DiffResponse> = await this.client.post('/exports/diff', { export_id: exportId });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Dropdown options for variable creation
  async getProjectDropdownOptions(currentProjectId?: number): Promise<{ projects: Array<{ id: number; name: string; description: string }> }> {
    const params = currentProjectId ? { current_project_id: currentProjectId } : {};
    const response: AxiosResponse<{ projects: Array<{ id: number; name: string; description: string }> }> = 
      await this.client.get('/projects/dropdown/options', { params });
    return response.data;
  }

  async getVariableDropdownOptions(projectId: number): Promise<{
    project: { id: number; name: string };
    variables: Array<{ id: number; name: string; description: string; value_type: string }>
  }> {
    const response: AxiosResponse<{
      project: { id: number; name: string };
      variables: Array<{ id: number; name: string; description: string; value_type: string }>
    }> = await this.client.get('/env-vars/dropdown/options', { params: { project_id: projectId } });
    return response.data;
  }

  async getConcatenationVariableOptions(projectId: number): Promise<{
    project: { id: number; name: string };
    variables: Array<{ id: number; name: string; description: string; value_type: string }>
  }> {
    const response: AxiosResponse<{
      project: { id: number; name: string };
      variables: Array<{ id: number; name: string; description: string; value_type: string }>
    }> = await this.client.get('/env-vars/concatenation/options', { params: { project_id: projectId } });
    return response.data;
  }

  // Variable History methods
  async getVariableHistory(varId: number, limit?: number): Promise<VariableHistoryEntry[]> {
    const params = limit ? { limit } : {};
    const response: AxiosResponse<VariableHistoryEntry[]> = await this.client.get(`/history/variable/${varId}`, { params });
    return response.data;
  }

  async getVariableWithHistory(varId: number): Promise<VariableWithHistory> {
    const response: AxiosResponse<VariableWithHistory> = await this.client.get(`/history/variable/${varId}/with-current`);
    return response.data;
  }

  async restoreVariableVersion(varId: number, request: RestoreVariableRequest): Promise<{ success: boolean; message: string }> {
    const response: AxiosResponse<{ success: boolean; message: string }> = await this.client.post(`/history/variable/${varId}/restore`, request);
    return response.data;
  }

  async getProjectHistory(projectId: number, limit?: number): Promise<VariableHistoryEntry[]> {
    const params = limit ? { limit } : {};
    const response: AxiosResponse<VariableHistoryEntry[]> = await this.client.get(`/history/project/${projectId}`, { params });
    return response.data;
  }

  async getProjectHistorySettings(projectId: number): Promise<ProjectHistorySettings> {
    const response: AxiosResponse<ProjectHistorySettings> = await this.client.get(`/history/project/${projectId}/settings`);
    return response.data;
  }

  async updateProjectHistorySettings(projectId: number, settings: HistorySettingsUpdate): Promise<HistorySettingsResponse> {
    const response: AxiosResponse<HistorySettingsResponse> = await this.client.put(`/history/project/${projectId}/settings`, settings);
    return response.data;
  }

  // Search methods
  async globalSearch(request: SearchRequest): Promise<SearchResponse> {
    const params = {
      q: request.query,
      scope: request.scope,
      ...(request.project_id && { project_id: request.project_id }),
      ...(request.limit && { limit: request.limit })
    };
    const response: AxiosResponse<SearchResponse> = await this.client.get('/search', { params });
    return response.data;
  }

  async getSearchSuggestions(query: string, limit?: number): Promise<SearchSuggestionsResponse> {
    const params = { q: query, ...(limit && { limit }) };
    const response: AxiosResponse<SearchSuggestionsResponse> = await this.client.get('/search/suggestions', { params });
    return response.data;
  }

  async searchProjects(query: string, limit?: number): Promise<{ results: ProjectSearchResult[] }> {
    const params = { q: query, ...(limit && { limit }) };
    const response: AxiosResponse<{ results: ProjectSearchResult[] }> = await this.client.get('/search/projects', { params });
    return response.data;
  }

  async searchVariables(query: string, projectId?: number, limit?: number): Promise<{ results: VariableSearchResult[] }> {
    const params = { q: query, ...(projectId && { project_id: projectId }), ...(limit && { limit }) };
    const response: AxiosResponse<{ results: VariableSearchResult[] }> = await this.client.get('/search/variables', { params });
    return response.data;
  }

  async searchValues(query: string, projectId?: number, limit?: number): Promise<{ results: ValueSearchResult[] }> {
    const params = { q: query, ...(projectId && { project_id: projectId }), ...(limit && { limit }) };
    const response: AxiosResponse<{ results: ValueSearchResult[] }> = await this.client.get('/search/values', { params });
    return response.data;
  }
}

export const apiClient = new ApiClient(); 