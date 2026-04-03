export interface ErrorResponse {
  code?: string;
  description?: string;
  detail?: Record<string, unknown>;
  solution?: string;
  link?: string;
}

export interface PaginatedResponse<T> {
  total?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
  has_next?: boolean;
  has_prev?: boolean;
  data?: T[];
}

export type OperatorStatus = "unpublish" | "published" | "offline" | "editing";
export type OperatorType = "basic" | "composite";
export type ExecutionMode = "sync" | "async";
export type OperatorCategory =
  | "other_category"
  | "data_process"
  | "data_transform"
  | "data_store"
  | "data_analysis"
  | "data_query"
  | "data_extract"
  | "data_split"
  | "model_train";
export type OperatorSource = "system" | "unknown";
export type MetadataType = "openapi" | "function";

export interface RetryPolicy {
  max_attempts?: number;
  initial_delay?: number;
  max_delay?: number;
  backoff_factor?: number;
  retry_conditions?: {
    status_code?: number[];
    error_codes?: string[];
  };
}

export interface OperatorExecuteControl {
  timeout?: number;
  retry_policy?: RetryPolicy;
}

export interface OperatorInfo {
  operator_type?: OperatorType;
  execution_mode?: ExecutionMode;
  category?: OperatorCategory;
  category_name?: string;
  source?: OperatorSource;
  is_data_source?: boolean;
}

export interface APISpec {
  parameters?: Array<{
    name?: string;
    in?: string;
    description?: string;
    required?: boolean;
    schema?: ParameterSchema;
  }>;
  request_body?: {
    description?: string;
    required?: boolean;
    content?: Record<string, { schema?: ExampleRequest; example?: ExampleRequest }>;
  };
  responses?: Record<string, {
    description?: string;
    content?: Record<string, { schema?: ExampleResponse; example?: ExampleResponse }>;
  }>;
  schemas?: Record<string, ParameterSchema>;
  security?: Array<{ securityScheme?: "apiKey" | "http" | "oauth2" }>;
}

export interface ParameterSchema {
  type?: "string" | "number" | "integer" | "boolean" | "array";
  format?: "int32" | "int64" | "float" | "double" | "byte";
  example?: string;
}

export interface ExampleRequest {
  field1?: string;
  field2?: number;
}

export interface ExampleResponse {
  code?: number;
  data?: { result?: string };
}

export interface FunctionContent {
  script_type?: "python";
  code?: string;
  dependencies?: Array<{ name?: string; version?: string }>;
  dependencies_url?: string;
}

export interface MetadataInfo {
  summary?: string;
  path?: string;
  method?: string;
  description?: string;
  server_url?: string | string[];
  api_spec?: APISpec;
  function_content?: FunctionContent;
}

export interface OperatorDataInfo {
  name?: string;
  operator_id: string;
  version: string;
  status?: OperatorStatus;
  metadata_type?: MetadataType;
  metadata?: MetadataInfo;
  operator_info?: OperatorInfo;
  operator_execute_control?: OperatorExecuteControl;
  extend_info?: Record<string, unknown>;
  create_time?: number;
  update_time?: number;
  create_user?: string;
  update_user?: string;
  release_user?: string;
  release_time?: number;
  tag?: string;
  is_internal?: boolean;
}

export interface OperatorRegisterReq {
  data?: string;
  function_input?: FunctionInput;
  operator_metadata_type: MetadataType;
  operator_info?: OperatorInfo;
  operator_execute_control?: OperatorExecuteControl;
  extend_info?: Record<string, unknown>;
  direct_publish?: boolean;
  user_token?: string;
}

export interface OperatorRegisterRespItem {
  status: "success" | "failed";
  operator_id?: string;
  version?: string;
  error?: ErrorResponse;
}

export type OperatorRegisterResp = OperatorRegisterRespItem[];

export interface OperatorEditReq {
  operator_id: string;
  name?: string;
  description?: string;
  operator_info?: OperatorInfoEdit;
  operator_execute_control?: OperatorExecuteControl;
  extend_info?: Record<string, unknown>;
  metadata_type?: MetadataType;
  data?: string;
  function_input?: FunctionInputEdit;
}

export interface OperatorInfoEdit {
  operator_type?: OperatorType;
  execution_mode?: ExecutionMode;
  category?: string;
  source?: OperatorSource;
  is_data_source?: boolean;
}

export interface OperatorDeleteItem {
  operator_id: string;
  version: string;
}

export type OperatorDeleteReq = OperatorDeleteItem[];

export interface OperatorStatusItem {
  operator_id: string;
  status: "unpublish" | "published" | "offline";
}

export type OperatorStatusUpdateReq = OperatorStatusItem[];

export interface OperatorDebugReq {
  operator_id: string;
  version: string;
  header?: Record<string, unknown>;
  body?: Record<string, unknown>;
  query?: Record<string, unknown>;
  path?: Record<string, string>;
}

export interface OperatorDebugResp {
  status_code?: number;
  headers?: Record<string, unknown>;
  body?: Record<string, unknown>;
  error?: string;
  duration_ms?: number;
}

export interface OperatorIntCompReq {
  operator_id: string;
  name: string;
  metadata_type: MetadataType;
  data?: string;
  function_input?: FunctionInput;
  operator_type: OperatorType;
  execution_mode: ExecutionMode;
  source?: string;
  operator_execute_control?: OperatorExecuteControl;
  extend_info?: Record<string, unknown>;
  config_source: "auto" | "manual";
  config_version: string;
  protected_flag?: boolean;
  is_data_source?: boolean;
}

export interface OperatorIntCompResp {
  status: "success" | "failed";
  operator_id: string;
  version: string;
}

export interface FunctionParameterDef {
  name?: string;
  description?: string;
  default?: unknown;
  type?: "string" | "object" | "number" | "boolean" | "array";
  required?: boolean;
  example?: unknown;
  enum?: unknown[];
  sub_parameters?: FunctionParameterDef[];
}

export interface FunctionInput {
  name?: string;
  description?: string;
  inputs?: FunctionParameterDef[];
  outputs?: FunctionParameterDef[];
  code?: string;
  script_type?: "python";
  dependencies?: Array<{ name?: string; version?: string }>;
  dependencies_url?: string;
}

export interface FunctionInputEdit {
  inputs?: FunctionParameterDef[];
  outputs?: FunctionParameterDef[];
  code?: string;
  script_type?: "python";
  dependencies?: Array<{ name?: string; version?: string }>;
  dependencies_url?: string;
}

export type ToolBoxStatus = "unpublish" | "published" | "offline";
export type ToolStatus = "enabled" | "disabled";
export type ToolBoxSource = "custom" | "internal";

export interface ToolInfo {
  tool_id?: string;
  name?: string;
  description?: string;
  status?: ToolStatus;
  metadata_type?: MetadataType;
  metadata?: MetadataInfo;
  create_time?: number;
  create_user?: string;
  update_time?: number;
  update_user?: string;
  extend_info?: Record<string, unknown>;
  resource_object?: "tool" | "operator";
}

export interface ToolBoxToolInfo {
  metadata_type?: MetadataType;
  business_domain_id?: string;
  box_id?: string;
  box_name?: string;
  box_desc?: string;
  box_svc_url?: string;
  status?: ToolBoxStatus;
  category_type?: string;
  category_name?: string;
  is_internal?: boolean;
  source?: ToolBoxSource;
  tools?: ToolInfo[];
  create_time?: number;
  create_user?: string;
  update_time?: number;
  update_user?: string;
  release_user?: string;
  release_time?: number;
}

export interface CreateToolBoxRequest {
  box_name?: string;
  box_desc?: string;
  box_svc_url?: string;
  box_category?: string;
  metadata_type: MetadataType;
  data?: string;
  source?: ToolBoxSource;
}

export interface CreateToolBoxResult {
  box_id?: string;
}

export interface UpdateToolBoxRequest {
  box_name: string;
  box_desc: string;
  box_svc_url: string;
  box_category: string;
  extend_info?: Record<string, unknown>;
  metadata_type: MetadataType;
  data?: string;
}

export interface UpdateToolBoxResult {
  box_id?: string;
  edit_tools?: Array<{
    tool_id?: string;
    status?: "enable" | "disable";
    name?: string;
    description?: string;
  }>;
}

export interface DeleteToolBoxResult {
  box_id?: string;
}

export interface UpdateToolBoxStatusReq {
  status?: ToolBoxStatus;
}

export interface UpdateToolBoxStatusResp {
  box_id?: string;
  status?: ToolBoxStatus;
}

export interface CreateToolReq {
  metadata_type: MetadataType;
  data?: string;
  function_input?: FunctionInput;
  use_rule?: string;
  global_parameters?: Parameters;
  extend_info?: Record<string, unknown>;
}

export interface CreateToolResp {
  box_id?: string;
  success_count?: number;
  success_ids?: string[];
  failure_count?: number;
  failures?: Array<{
    tool_name?: string;
    error?: ErrorResponse;
  }>;
}

export interface UpdateToolReq {
  name: string;
  description: string;
  use_rule?: string;
  global_parameters?: Parameters;
  extend_info?: Record<string, unknown>;
  metadata_type?: MetadataType;
  data?: string;
  function_input?: FunctionInputEdit;
}

export interface UpdateToolResp {
  box_id?: string;
  tool_id?: string;
}

export interface UpdateToolStatusReq {
  tool_id: string;
  status: ToolStatus;
}

export type UpdateToolStatusResp = Array<{
  tool_id?: string;
  status?: "unpublish" | "published" | "offline";
}>;

export interface BatchDeleteToolReq {
  tool_ids: string[];
}

export interface BatchDeleteToolResp {
  box_id?: string;
  tool_ids?: string[];
}

export interface ConvertToolReq {
  box_id: string;
  operator_id: string;
  operator_version: string;
  global_parameters?: Parameters;
}

export interface ConvertToolResp {
  box_id?: string;
  tool_id?: string;
}

export interface Parameters {
  name?: string;
  description?: string;
  required?: boolean;
  in?: "path" | "query" | "header" | "cookie" | "body";
  type?: "string" | "object" | "integer" | "boolean" | "array";
  value?: string | number | boolean | object | unknown[];
}

export interface BoxToolList {
  box_id?: string;
  status?: ToolBoxStatus;
  total?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
  has_next?: boolean;
  has_prev?: boolean;
  tools?: ToolInfo[];
}

export interface ToolBoxInfoList extends PaginatedResponse<{
  metadata_type?: MetadataType;
  business_domain_id?: string;
  box_id?: string;
  box_name?: string;
  box_desc?: string;
  box_svc_url?: string;
  status?: ToolBoxStatus;
  category_type?: string;
  category_name?: string;
  is_internal?: boolean;
  source?: ToolBoxSource;
  tools?: string[];
  create_time?: number;
  create_user?: string;
  update_time?: number;
  update_user?: string;
}> {}

export interface GetToolBoxMarketInfoResult {
  metadata_type?: MetadataType;
  box_id: string;
  box_name?: string;
  box_desc?: string;
  box_svc_url?: string;
  status?: ToolBoxStatus;
  category_type?: string;
  category_name?: string;
  is_internal?: boolean;
  source?: ToolBoxSource;
  tools?: ToolInfo[];
  create_user?: string;
  update_user?: string;
  release_user?: string;
}

export interface CreateInternalToolBoxReq {
  box_id: string;
  box_name: string;
  box_desc: string;
  metadata_type: MetadataType;
  data: string;
  source?: "custom" | "internal";
  config_version: string;
  config_source: "auto" | "manual";
  protected_flag?: boolean;
  functions?: FunctionInput[];
}

export interface CreateInternalToolBoxResp {
  box_id?: string;
  box_name?: string;
  tools?: ToolInfo[];
}

export interface APIProxyRequest {
  header?: Record<string, unknown>;
  body?: Record<string, unknown>;
  query?: Record<string, unknown>;
  path?: Record<string, string>;
}

export interface APIProxyResponse {
  status_code: number;
  headers?: Record<string, string>;
  body?: unknown;
  error?: string;
}

export interface FunctionExecuteReq {
  code: string;
  event?: Record<string, unknown>;
  timeout?: number;
  dependencies?: Array<{ name?: string; version?: string }>;
  dependencies_url?: string;
}

export interface FunctionExecuteResp {
  stdout?: string;
  stderr?: string;
  result?: unknown;
  metrics?: Record<string, unknown>;
}

export interface FunctionAIGenerateReq {
  query?: string;
  code?: string;
  inputs?: FunctionParameterDef[];
  outputs?: FunctionParameterDef[];
  stream?: boolean;
}

export interface FunctionAIGenerateResp {
  content?: {
    name?: string;
    description?: string;
    use_rule?: string;
    inputs?: FunctionParameterDef[];
    outputs?: FunctionParameterDef[];
  } | string;
}

export interface PromptTemplate {
  prompt_id?: string;
  name?: string;
  description?: string;
  system_prompt?: string;
  user_prompt_template?: string;
}

export interface DependenciesInfo {
  dependencies?: Array<{ name?: string; version?: string }>;
  session_id?: string;
}

export interface DependencyVersion {
  package_name?: string;
  versions?: string[];
}

export type MCPStatus = "unpublish" | "published" | "offline" | "editing";
export type MCPMode = "sse" | "stream";
export type MCPCreationType = "custom" | "tool_imported";

export interface MCPToolConfig {
  box_id?: string;
  tool_id?: string;
  box_name?: string;
  tool_name?: string;
  description?: string;
  use_rule?: string;
}

export interface MCPServerRegisterRequest {
  name: string;
  description?: string;
  creation_type?: MCPCreationType;
  mode: MCPMode;
  command?: string;
  args?: string[];
  url?: string;
  headers?: Record<string, string>;
  env?: Record<string, string>;
  source?: string;
  category?: string;
  tool_configs?: MCPToolConfig[];
}

export interface MCPServerUpdateRequest {
  name?: string;
  description?: string;
  creation_type?: MCPCreationType;
  mode: MCPMode;
  url?: string;
  headers?: Record<string, string>;
  command?: string;
  env?: Record<string, string>;
  args?: string[];
  source?: string;
  category?: string;
  tool_configs?: MCPToolConfig[];
}

export interface MCPServerConfigInfo {
  business_domain_id?: string;
  mcp_id?: string;
  name?: string;
  description?: string;
  creation_type?: MCPCreationType;
  mode?: MCPMode;
  url?: string;
  headers?: Record<string, string>;
  command?: string;
  env?: Record<string, string>;
  args?: string[];
  status?: MCPStatus;
  is_internal?: boolean;
  source?: string;
  category?: string;
  create_user?: string;
  create_time?: number;
  update_user?: string;
  update_time?: number;
}

export interface MCPConnectionInfo {
  sse_url?: string;
  stream_url?: string;
}

export interface MCPServerListResponse extends PaginatedResponse<MCPServerConfigInfo & { tool_configs?: MCPToolConfig[] }> {}

export interface MCPServerDetailResponse {
  base_info?: MCPServerConfigInfo & { tool_configs?: MCPToolConfig[] };
  connection_info?: MCPConnectionInfo;
}

export interface MCPServerReleaseInfo extends MCPServerConfigInfo {
  release_user?: string;
  release_time?: number;
}

export interface MCPServerReleaseListResponse extends PaginatedResponse<MCPServerReleaseInfo> {}

export interface MCPServerReleaseDetailResponse {
  base_info?: MCPServerReleaseInfo;
  connection_info?: MCPConnectionInfo;
}

export interface MCPParseSSERequest {
  mode: MCPMode;
  url: string;
  headers: Record<string, string>;
}

export interface ToolInputSchema {
  type?: string;
  properties?: Record<string, unknown>;
  required?: string[];
  $defs?: Record<string, unknown>;
}

export interface Tool {
  name?: string;
  description?: string;
  inputSchema?: ToolInputSchema;
  annotations?: {
    title?: string;
    readOnlyHint?: boolean;
    destructiveHint?: boolean;
    idempotentHint?: boolean;
    openWorldHint?: boolean;
  };
}

export interface MCPParseSSEResponse {
  tools?: Tool[];
}

export interface MCPToolDebugRequest extends Record<string, unknown> {}

export interface MCPToolDebugResponse {
  content?: Array<TextContent | ImageContent | AudioContent | EmbeddedResource>;
  isError?: boolean;
}

export interface TextContent {
  type: "text";
  text: string;
}

export interface ImageContent {
  type: "image";
  data: string;
  mimeType: string;
}

export interface AudioContent {
  type: "audio";
  data: string;
  mimeType: string;
}

export interface EmbeddedResource {
  type: "resource";
  resource: unknown;
}

export interface McpProxyCallToolRequest {
  tool_name: string;
  parameters: Record<string, unknown>;
}

export interface McpProxyCallToolResponse {
  content?: Array<TextContent | ImageContent | AudioContent | EmbeddedResource>;
  isError?: boolean;
}

export interface McpProxyToolListResponse {
  tools?: Tool[];
}

export interface ExportResp {
  operator?: OperatorImpexItem[];
  toolbox?: ToolBoxImpexItem[];
  mcp?: MCPConfigItem[];
}

export interface OperatorImpexItem {
  operator_id?: string;
  version?: string;
  status?: string;
  metadata_type?: string;
  metadata?: Record<string, unknown>;
  extend_info?: Record<string, unknown>;
  operator_info?: OperatorInfo;
  operator_execute_control?: OperatorExecuteControl;
  create_user?: string;
  create_time?: number;
  update_user?: string;
  update_time?: number;
  is_internal?: boolean;
}

export interface ToolBoxImpexItem {
  box_id?: string;
  box_name?: string;
  box_desc?: string;
  box_svc_url?: string;
  status?: string;
  category_type?: string;
  category_name?: string;
  is_internal?: boolean;
  source?: string;
  tools?: ToolInfo[];
  create_time?: number;
  create_user?: string;
  update_time?: number;
  update_user?: string;
}

export interface MCPConfigItem {
  mcp_id?: string;
  version?: string;
  creation_type?: string;
  name?: string;
  description?: string;
  status?: string;
  source?: string;
  is_internal?: boolean;
  category?: string;
  mode?: string;
  command?: string;
  args?: string[];
  url?: string;
  headers?: Record<string, string>;
  env?: Record<string, string>;
  create_user?: string;
  create_time?: number;
  update_user?: string;
  update_time?: number;
  mcp_tools?: MCPToolInfo[];
}

export interface MCPToolInfo {
  mcp_tool_id?: string;
  mcp_id?: string;
  mcp_version?: string;
  box_id?: string;
  box_name?: string;
  tool_id?: string;
  name?: string;
  description?: string;
  use_rule?: string;
}

export interface ImportReq {
  data: string;
  mode: "create" | "upsert";
}

export interface ImportResp {
  type?: "operator" | "toolbox" | "mcp";
  id?: string;
}
