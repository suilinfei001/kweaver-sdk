import { HttpError } from "../utils/http.js";

const VEGA_BASE = "/api/vega-backend/v1";

function buildHeaders(accessToken: string, businessDomain: string): Record<string, string> {
  return {
    accept: "application/json, text/plain, */*",
    "accept-language": "zh-cn",
    authorization: `Bearer ${accessToken}`,
    token: accessToken,
    "x-business-domain": businessDomain,
    "x-language": "zh-cn",
  };
}

export interface VegaHealthOptions {
  baseUrl: string;
  accessToken: string;
  businessDomain?: string;
}

export async function vegaHealth(options: VegaHealthOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    businessDomain = "bd_public",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = `${base}/health`;

  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(accessToken, businessDomain),
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}

export interface ListVegaCatalogsOptions {
  baseUrl: string;
  accessToken: string;
  status?: string;
  limit?: number;
  offset?: number;
  businessDomain?: string;
}

export async function listVegaCatalogs(options: ListVegaCatalogsOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    status,
    limit,
    offset,
    businessDomain = "bd_public",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = new URL(`${base}${VEGA_BASE}/catalogs`);
  if (status) url.searchParams.set("status", status);
  if (limit !== undefined) url.searchParams.set("limit", String(limit));
  if (offset !== undefined) url.searchParams.set("offset", String(offset));

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: buildHeaders(accessToken, businessDomain),
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}

export interface GetVegaCatalogOptions {
  baseUrl: string;
  accessToken: string;
  id: string;
  businessDomain?: string;
}

export async function getVegaCatalog(options: GetVegaCatalogOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    id,
    businessDomain = "bd_public",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = `${base}${VEGA_BASE}/catalogs/${encodeURIComponent(id)}`;

  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(accessToken, businessDomain),
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}

export interface VegaCatalogHealthStatusOptions {
  baseUrl: string;
  accessToken: string;
  ids: string;
  businessDomain?: string;
}

export async function vegaCatalogHealthStatus(options: VegaCatalogHealthStatusOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    ids,
    businessDomain = "bd_public",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = new URL(`${base}${VEGA_BASE}/catalogs/health-status`);
  url.searchParams.set("ids", ids);

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: buildHeaders(accessToken, businessDomain),
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}

export interface TestVegaCatalogConnectionOptions {
  baseUrl: string;
  accessToken: string;
  id: string;
  businessDomain?: string;
}

export async function testVegaCatalogConnection(options: TestVegaCatalogConnectionOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    id,
    businessDomain = "bd_public",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = `${base}${VEGA_BASE}/catalogs/${encodeURIComponent(id)}/test-connection`;

  const response = await fetch(url, {
    method: "POST",
    headers: buildHeaders(accessToken, businessDomain),
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}

export interface DiscoverVegaCatalogOptions {
  baseUrl: string;
  accessToken: string;
  id: string;
  wait?: boolean;
  businessDomain?: string;
}

export async function discoverVegaCatalog(options: DiscoverVegaCatalogOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    id,
    wait,
    businessDomain = "bd_public",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const endpoint = `${base}${VEGA_BASE}/catalogs/${encodeURIComponent(id)}/discover`;

  let url: string;
  if (wait !== undefined) {
    const u = new URL(endpoint);
    u.searchParams.set("wait", String(wait));
    url = u.toString();
  } else {
    url = endpoint;
  }

  const response = await fetch(url, {
    method: "POST",
    headers: buildHeaders(accessToken, businessDomain),
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}

export interface ListVegaCatalogResourcesOptions {
  baseUrl: string;
  accessToken: string;
  id: string;
  category?: string;
  limit?: number;
  offset?: number;
  businessDomain?: string;
}

export async function listVegaCatalogResources(options: ListVegaCatalogResourcesOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    id,
    category,
    limit,
    offset,
    businessDomain = "bd_public",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = new URL(`${base}${VEGA_BASE}/catalogs/${encodeURIComponent(id)}/resources`);
  if (category) url.searchParams.set("category", category);
  if (limit !== undefined) url.searchParams.set("limit", String(limit));
  if (offset !== undefined) url.searchParams.set("offset", String(offset));

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: buildHeaders(accessToken, businessDomain),
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}
