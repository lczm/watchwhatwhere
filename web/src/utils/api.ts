export class ApiService {
  private static baseUrl = import.meta.env.VITE_API_BASE_URL;

  static getEndpoint(path: string): string {
    return `${this.baseUrl}/watchwhatwhere${path}`;
  }
}
