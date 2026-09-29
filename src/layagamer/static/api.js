function apiUrl(path) {
  const relativePath = path.replace(/^\/+/, '');
  const configuredBase = globalThis.LAYAGAMER_API_BASE;
  if (configuredBase) return new URL(relativePath, configuredBase).toString();
  if (!globalThis.document?.baseURI) return `/${relativePath}`;
  const url = new URL(relativePath, document.baseURI);
  return `${url.pathname}${url.search}`;
}

export async function requestJson(path, options) {
  let response;
  try {
    response = await fetch(apiUrl(path), options);
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    throw new Error('Could not reach the Laya inference backend.');
  }
  try {
    return {response, data: await response.json()};
  } catch {
    throw new Error('This static site needs the Python Laya backend to run games.');
  }
}
