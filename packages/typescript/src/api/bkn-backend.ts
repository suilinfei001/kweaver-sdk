import { HttpError } from "../utils/http.js";

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

export interface UploadBknOptions {
  baseUrl: string;
  accessToken: string;
  tarBuffer: Buffer;
  businessDomain?: string;
  branch?: string;
}

export async function uploadBkn(options: UploadBknOptions): Promise<string> {
  const {
    baseUrl,
    accessToken,
    tarBuffer,
    businessDomain = "bd_public",
    branch = "main",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = new URL(`${base}/api/bkn-backend/v1/bkns`);
  url.searchParams.set("branch", branch);

  const form = new FormData();
  form.append("file", new Blob([new Uint8Array(tarBuffer)], { type: "application/octet-stream" }), "bkn.tar");

  const headers = buildHeaders(accessToken, businessDomain);
  const response = await fetch(url.toString(), {
    method: "POST",
    headers,
    body: form,
  });

  const body = await response.text();
  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }
  return body;
}

export interface DownloadBknOptions {
  baseUrl: string;
  accessToken: string;
  knId: string;
  businessDomain?: string;
  branch?: string;
}

export async function downloadBkn(options: DownloadBknOptions): Promise<Buffer> {
  const {
    baseUrl,
    accessToken,
    knId,
    businessDomain = "bd_public",
    branch = "main",
  } = options;

  const base = baseUrl.replace(/\/+$/, "");
  const url = new URL(`${base}/api/bkn-backend/v1/bkns/${encodeURIComponent(knId)}`);
  url.searchParams.set("branch", branch);

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: buildHeaders(accessToken, businessDomain),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new HttpError(response.status, response.statusText, body);
  }

  const arrayBuffer = await response.arrayBuffer();
  return Buffer.from(arrayBuffer);
}
